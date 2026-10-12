// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import android.app.*;
import android.content.Context;
import android.os.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

/** App-private crash evidence. Export occurs only after the user chooses a destination. */
final class Diagnostics {
    static final String VERSION=ReleaseInfo.VERSION;
    private static String process="ui";
    private static File directory(Context c){File d=new File(c.getFilesDir(),"diagnostics");d.mkdirs();return d;}
    static void initialize(Context c) {
        try(InputStream in=new FileInputStream("/proc/self/cmdline")){byte[] b=new byte[256];int n=in.read(b);String name=new String(b,0,Math.max(0,n),StandardCharsets.UTF_8);if(name.contains(":cad"))process="cad";}catch(Exception ignored){}
    }
    private static void write(File file,String text)throws IOException {
        try(FileOutputStream out=new FileOutputStream(file)){out.write(text.getBytes(StandardCharsets.UTF_8));out.getFD().sync();}
    }
    static synchronized void stage(Context c,String stage) {
        String text=System.currentTimeMillis()+" · "+VERSION+" · "+stage;
        try{write(new File(directory(c),process+"-stage.txt"),text);}catch(Exception ignored){}
        if(Build.VERSION.SDK_INT>=30)try{((ActivityManager)c.getSystemService(Context.ACTIVITY_SERVICE)).setProcessStateSummary(stage.substring(0,Math.min(96,stage.length())).getBytes(StandardCharsets.UTF_8));}catch(Exception ignored){}
        android.util.Log.i("CAD_STARTUP",stage);
    }
    static synchronized void error(Context c,String label,Throwable error) {
        android.util.Log.e("CAD_CRASH",label,error);
        try{StringWriter stack=new StringWriter();error.printStackTrace(new PrintWriter(stack));write(new File(directory(c),process+"-java-crash.txt"),System.currentTimeMillis()+" · "+VERSION+" · "+label+"\n"+stack);}catch(Exception ignored){}
    }
    private static String read(File file){try(InputStream in=new FileInputStream(file);ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[4096];int used=0,n;while(used<65536&&(n=in.read(b,0,Math.min(b.length,65536-used)))!=-1){out.write(b,0,n);used+=n;}return new String(out.toByteArray(),StandardCharsets.UTF_8)+(file.length()>used?"\n[record truncated]":"");}catch(Exception e){return "No record";}}
    static boolean hadStartupFailure(Context c){File f=new File(directory(c),"cad-stage.txt");return f.isFile()&&!read(f).contains("Workspace ready")&&!read(f).contains("Workspace closed");}
    static String report(Context c,boolean traces) {
        StringBuilder s=new StringBuilder("FreeCAD Mobile Lab "+VERSION+"\n");
        s.append(Build.MANUFACTURER).append(' ').append(Build.MODEL).append("\nAndroid ").append(Build.VERSION.RELEASE).append(" / API ").append(Build.VERSION.SDK_INT).append("\nABIs: ").append(Arrays.toString(Build.SUPPORTED_ABIS)).append('\n');
        for(String name:new String[]{"ui-stage.txt","cad-stage.txt","ui-java-crash.txt","cad-java-crash.txt"}){File f=new File(directory(c),name);if(f.isFile())s.append("\n").append(name).append(":\n").append(read(f)).append('\n');}
        if(Build.VERSION.SDK_INT>=30)try {
            ActivityManager manager=(ActivityManager)c.getSystemService(Context.ACTIVITY_SERVICE);
            List<ApplicationExitInfo> exits=manager.getHistoricalProcessExitReasons(c.getPackageName(),0,8);
            s.append("\nAndroid process exit records:\n");
            int traceCount=0;boolean decoded=false;
            for(int i=0;i<exits.size();i++) {
                ApplicationExitInfo e=exits.get(i);s.append(new Date(e.getTimestamp())).append(" · ").append(e.getProcessName()).append(" · ").append(reason(e.getReason())).append(" · status/signal ").append(e.getStatus()).append('\n');
                if(e.getDescription()!=null)s.append(e.getDescription()).append('\n');
                byte[] state=e.getProcessStateSummary();if(state!=null)s.append("Last stage: ").append(new String(state,StandardCharsets.UTF_8)).append('\n');
                boolean nativeCrash=e.getReason()==ApplicationExitInfo.REASON_CRASH_NATIVE;
                if((nativeCrash&&!decoded)||(traces&&traceCount<3&&(nativeCrash||e.getReason()==ApplicationExitInfo.REASON_ANR)))try(InputStream in=e.getTraceInputStream()) {
                    if(in!=null){ByteArrayOutputStream raw=new ByteArrayOutputStream();ArchiveIO.copy(in,raw,4*1024*1024,null);byte[] data=raw.toByteArray();if(nativeCrash&&!decoded){s.append(NativeTombstone.describe(data));decoded=true;}if(traces&&traceCount++<3){File f=new File(directory(c),"exit-"+e.getTimestamp()+(nativeCrash?".pb":".txt"));try(OutputStream out=new FileOutputStream(f)){out.write(data);}s.append("Trace saved: ").append(f.getName()).append('\n');}}
                }catch(Exception err){s.append("Trace unavailable: ").append(err).append('\n');}
            }
            if(exits.isEmpty())s.append("No system exit records are available.\n");
        }catch(Exception e){s.append("System exit records unavailable: ").append(e).append('\n');}
        else s.append("\nSystem exit history requires Android 11 or newer.\n");
        if(traces){File[] old=directory(c).listFiles(f->f.getName().startsWith("exit-"));if(old!=null){Arrays.sort(old,(a,b)->Long.compare(b.lastModified(),a.lastModified()));for(int i=3;i<old.length;i++)old[i].delete();}}
        String result=s.length()>262144?s.substring(0,262144)+"\n[report truncated; export the ZIP for native traces]":s.toString();try{write(new File(directory(c),"report.txt"),result);}catch(Exception ignored){}return result;
    }
    static boolean recentSystemCrash(Context c) {
        if(Build.VERSION.SDK_INT<30)return false;
        try {
            List<ApplicationExitInfo> exits=((ActivityManager)c.getSystemService(Context.ACTIVITY_SERVICE)).getHistoricalProcessExitReasons(c.getPackageName(),0,8);
            for(ApplicationExitInfo e:exits)if(System.currentTimeMillis()-e.getTimestamp()<24*60*60*1000L&&(e.getReason()==ApplicationExitInfo.REASON_CRASH||e.getReason()==ApplicationExitInfo.REASON_CRASH_NATIVE||e.getReason()==ApplicationExitInfo.REASON_ANR||e.getReason()==ApplicationExitInfo.REASON_INITIALIZATION_FAILURE))return true;
        }catch(Exception ignored){}return false;
    }
    private static String reason(int reason) {
        switch(reason){case 4:return "Java crash";case 5:return "native crash";case 6:return "not responding (ANR)";case 7:return "initialization failure";case 3:return "low memory";case 10:return "user requested stop";default:return "reason "+reason;}
    }
    static void export(Context c,OutputStream target)throws IOException {
        report(c,true);File[] files=directory(c).listFiles();if(files==null)throw new IOException("Crash records could not be read");Arrays.sort(files,Comparator.comparing(File::getName));
        try(ZipOutputStream zip=new ZipOutputStream(target)) {
            ArchiveIO.Budget budget=new ArchiveIO.Budget(16*1024*1024);
            for(File file:files){if(!file.isFile()||file.length()>4*1024*1024)continue;zip.putNextEntry(new ZipEntry(file.getName()));try(InputStream in=new FileInputStream(file)){ArchiveIO.copy(in,zip,4*1024*1024,budget);}zip.closeEntry();}
        }
    }
}
