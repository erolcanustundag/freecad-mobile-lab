// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.content.Context;
import java.io.*;
import java.util.zip.*;

/** Installs a versioned private interpreter tree before any native core call. */
final class CoreAssets {
    static File install(Context context)throws IOException{
        File parent=new File(context.getFilesDir(),"freecad-core");
        if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Cannot create runtime directory");
        File home=new File(parent,"runtime-"+ReleaseInfo.CODE),marker=new File(home,"complete");
        if(marker.isFile())return home;
        File staging=new File(parent,"staging-"+ReleaseInfo.CODE);remove(staging);
        if(!staging.mkdirs())throw new IOException("Cannot create runtime staging directory");
        long total=0;int count=0;
        try(InputStream raw=context.getAssets().open("core/python-home.zip");ZipInputStream zip=new ZipInputStream(new BufferedInputStream(raw))){
            ZipEntry entry;byte[] buffer=new byte[65536];
            while((entry=zip.getNextEntry())!=null){
                if(++count>20000||entry.getName().startsWith("/")||entry.getName().contains("\\"))throw new IOException("Invalid runtime archive");
                File destination=new File(staging,entry.getName());
                if(!destination.getCanonicalPath().startsWith(staging.getCanonicalPath()+File.separator))throw new IOException("Invalid runtime path");
                if(entry.isDirectory()){if(!destination.isDirectory()&&!destination.mkdirs())throw new IOException("Cannot create runtime folder");}
                else{
                    File directory=destination.getParentFile();if(!directory.isDirectory()&&!directory.mkdirs())throw new IOException("Cannot create runtime folder");
                    try(OutputStream out=new FileOutputStream(destination)){
                        int n;while((n=zip.read(buffer))!=-1){total+=n;if(total>256L*1024*1024)throw new IOException("Runtime archive exceeds limit");out.write(buffer,0,n);}
                    }
                }
                zip.closeEntry();
            }
        }catch(IOException error){remove(staging);throw error;}
        if(!new File(staging,"lib/python3.13/encodings/__init__.py").isFile())throw new IOException("Runtime is missing encodings");
        if(!new File(staging,"tmp").mkdirs()&&!new File(staging,"tmp").isDirectory())throw new IOException("Cannot create temporary directory");
        // Keep FCStd documents outside the disposable interpreter version directory.
        File prior=new File(parent,"documents");
        if(!prior.isDirectory()&&!prior.mkdirs())throw new IOException("Cannot create saved document directory");
        try(OutputStream out=new FileOutputStream(new File(staging,"complete"))){out.write(1);}
        remove(home);if(!staging.renameTo(home))throw new IOException("Cannot install runtime");
        return home;
    }
    private static void remove(File file)throws IOException{
        if(!file.exists())return;
        File[] children=file.listFiles();if(children!=null)for(File child:children)remove(child);
        if(!file.delete())throw new IOException("Cannot remove incomplete runtime");
    }
}
