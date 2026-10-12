// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.nio.file.*;
import java.util.concurrent.*;

public final class CoreAdapterHostTest {
    private static int count;
    private static void check(boolean condition,String message){if(!condition)throw new AssertionError(message);count++;}
    private static JSONObject call(String text)throws Exception{
        JSONObject r=new JSONObject(CoreNative.request(text));
        check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");
    }
    private static void bad(String text)throws Exception{JSONObject r=new JSONObject(CoreNative.request(text));check(!r.getBoolean("ok"),"Expected a rejected operation");check(!r.getString("error").isEmpty(),"Readable error");}
    private static JSONObject object(JSONObject s,String name)throws Exception{
        JSONArray list=s.getJSONObject("document").getJSONArray("objects");
        for(int i=0;i<list.length();i++)if(list.getJSONObject(i).getString("name").equals(name))return list.getJSONObject(i);
        throw new AssertionError("Missing object "+name);
    }
    private static Object prop(JSONObject s,String obj,String name)throws Exception{
        JSONArray list=object(s,obj).getJSONArray("properties");
        for(int i=0;i<list.length();i++)if(list.getJSONObject(i).getString("name").equals(name))return list.getJSONObject(i).get("value");
        throw new AssertionError("Missing property "+name);
    }
    private static void near(JSONObject s,String obj,String prop,double v)throws Exception{
        check(Math.abs(((JSONObject)prop(s,obj,prop)).getDouble("value")-v)<1e-8,"Value "+obj+"."+prop);
    }
    private static void changedFixture(Path original,Path target,String from,String to)throws Exception{
        try(java.util.zip.ZipInputStream in=new java.util.zip.ZipInputStream(Files.newInputStream(original));java.util.zip.ZipOutputStream out=new java.util.zip.ZipOutputStream(Files.newOutputStream(target))){
            java.util.zip.ZipEntry e;byte[] buffer=new byte[8192];while((e=in.getNextEntry())!=null){
                java.io.ByteArrayOutputStream data=new java.io.ByteArrayOutputStream();int n;while((n=in.read(buffer))!=-1)data.write(buffer,0,n);
                byte[] bytes=data.toByteArray();if(e.getName().equals("Document.xml"))bytes=new String(bytes,java.nio.charset.StandardCharsets.UTF_8).replace(from,to).getBytes(java.nio.charset.StandardCharsets.UTF_8);
                out.putNextEntry(new java.util.zip.ZipEntry(e.getName()));out.write(bytes);out.closeEntry();
            }
        }
    }
    public static void main(String[] args)throws Exception{
        System.load(args[0]);CoreNative.initialize(args[1],args[2],args[1]);
        JSONObject state=call("{\"op\":\"new\",\"name\":\"AdapterReference\"}");
        check(state.getJSONArray("version").getString(2).equals("4"),"Upstream version");
        state=call("{\"op\":\"batch\",\"edits\":[{\"op\":\"add\",\"name\":\"Source\"},{\"op\":\"property\",\"object\":\"Source\",\"name\":\"Width\",\"type\":\"App::PropertyLength\"},{\"op\":\"set\",\"object\":\"Source\",\"property\":\"Width\",\"value\":\"2 cm\"},{\"op\":\"add\",\"name\":\"Driven\"},{\"op\":\"property\",\"object\":\"Driven\",\"name\":\"Width\",\"type\":\"App::PropertyLength\"},{\"op\":\"expression\",\"object\":\"Driven\",\"property\":\"Width\",\"expression\":\"Source.Width * 2\"}]}");
        near(state,"Source","Width",20);near(state,"Driven","Width",40);
        check(object(state,"Driven").getJSONArray("dependencies").getString(0).equals("Source"),"Dependency");
        state=call("{\"op\":\"batch\",\"edits\":[{\"op\":\"set\",\"object\":\"Source\",\"property\":\"Width\",\"value\":\"25 mm\"}]}");
        near(state,"Driven","Width",50);
        state=call("{\"op\":\"undo\"}");near(state,"Driven","Width",40);
        state=call("{\"op\":\"redo\"}");near(state,"Driven","Width",50);
        call("{\"op\":\"begin\"}");call("{\"op\":\"batch\",\"edits\":[{\"op\":\"set\",\"object\":\"Source\",\"property\":\"Width\",\"value\":\"100 mm\"}]}");
        state=call("{\"op\":\"abort\"}");near(state,"Driven","Width",50);
        bad("{\"op\":\"batch\",\"edits\":[{\"op\":\"set\",\"object\":\"Source\",\"property\":\"Width\",\"value\":\"80 mm\"},{\"op\":\"property\",\"object\":\"Missing\",\"name\":\"X\",\"type\":\"App::PropertyFloat\"}]}");
        near(call("{}"),"Source","Width",25);
        state=call("{\"op\":\"batch\",\"edits\":[{\"op\":\"set\",\"object\":\"Source\",\"property\":\"Label\",\"value\":\"Ölçü 💎\"},{\"op\":\"add\",\"name\":\"Group\",\"type\":\"App::DocumentObjectGroup\"},{\"op\":\"group\",\"group\":\"Group\",\"object\":\"Source\"},{\"op\":\"add\",\"name\":\"Instance\",\"type\":\"App::Link\"},{\"op\":\"link\",\"object\":\"Instance\",\"target\":\"Driven\"}]}");
        check(object(state,"Source").getString("label").equals("Ölçü 💎"),"JNI preserves UTF16/UTF8 labels");
        check(((JSONObject)prop(state,"Instance","LinkedObject")).getString("object").equals("Driven"),"Native link");
        check(((JSONArray)prop(state,"Group","Group")).getJSONObject(0).getString("object").equals("Source"),"Native group");
        call("{\"op\":\"save\",\"file\":\"Adapter.FCStd\"}");
        check(Files.isRegularFile(Paths.get(args[1],"documents","Adapter.FCStd")),"Native FCStd exists");
        call("{\"op\":\"close\"}");state=call("{\"op\":\"open\",\"file\":\"Adapter.FCStd\"}");
        near(state,"Driven","Width",50);check(object(state,"Source").getString("label").equals("Ölçü 💎"),"FCStd Unicode restored");
        state=call("{\"op\":\"batch\",\"edits\":[{\"op\":\"set\",\"object\":\"Source\",\"property\":\"Width\",\"value\":\"32 mm\"}]}");near(state,"Driven","Width",64);
        bad("{\"op\":\"batch\",\"edits\":[{\"op\":\"expression\",\"object\":\"Source\",\"property\":\"Width\",\"expression\":\"Driven.Width\"}]}");
        near(call("{}"),"Driven","Width",64);
        call("{\"op\":\"begin\"}");bad("{\"op\":\"save\",\"file\":\"OpenTransaction.FCStd\"}");bad("{\"op\":\"undo\"}");call("{\"op\":\"commit\"}");bad("{\"op\":\"abort\"}");
        Path original=Paths.get(args[1],"documents","Adapter.FCStd");
        changedFixture(original,original.resolveSibling("Unsupported.FCStd"),"App::FeaturePython","Sketcher::SketchObject");
        bad("{\"op\":\"open\",\"file\":\"Unsupported.FCStd\"}");near(call("{}"),"Driven","Width",64);
        changedFixture(original,original.resolveSibling("Proxy.FCStd"),"bnVsbA==","e30=");bad("{\"op\":\"open\",\"file\":\"Proxy.FCStd\"}");
        bad("{\"op\":\"save\",\"file\":\"../escape.FCStd\"}");bad("{\"op\":\"batch\",\"edits\":[{\"op\":\"add\",\"name\":\"UnsupportedSketch\",\"type\":\"Sketcher::SketchObject\"}]}");
        bad("[]");bad("{\"op\":\"eval\",\"code\":\"print(1)\"}");
        state=call(CoreCommandLine.parse("Add Numeric Feature").toString());
        call(CoreCommandLine.parse("AddProperty Numeric Count Integer").toString());
        state=call(CoreCommandLine.parse("Set Numeric.Count 17").toString());check(((Number)prop(state,"Numeric","Count")).intValue()==17,"Integer command");
        call(CoreCommandLine.parse("AddProperty Numeric Enabled Bool").toString());
        state=call(CoreCommandLine.parse("Set Numeric.Enabled true").toString());check(Boolean.TRUE.equals(prop(state,"Numeric","Enabled")),"Boolean command");
        state=call(CoreCommandLine.parse("Set Numeric.Label \"007 💎\"").toString());check(object(state,"Numeric").getString("label").equals("007 💎"),"String command");
        call(CoreCommandLine.parse("Expression Driven.Width \"\"").toString());state=call(CoreCommandLine.parse("State").toString());check(object(state,"Driven").getJSONArray("expressions").length()==0,"Clear expression command");
        for(String invalid:new String[]{"Add X Unknown","Undo extra","Set Source.Width","Set Source.Width \"unterminated","AddProperty X X Color","nonsense"}){try{CoreCommandLine.parse(invalid);throw new AssertionError("Rejected command "+invalid);}catch(IllegalArgumentException expected){count++;}}
        ExecutorService workers=Executors.newFixedThreadPool(3);
        java.util.List<Future<Boolean>> reads=new java.util.ArrayList<>();
        for(int i=0;i<12;i++)reads.add(workers.submit(()->new JSONObject(CoreNative.request("{}")).getBoolean("ok")));
        for(Future<Boolean> read:reads)check(read.get(15,TimeUnit.SECONDS),"Serialized cross-thread JNI/GIL read");workers.shutdown();
        System.out.println("PASS: "+count+" upstream JNI document adapter assertions; Android runtime NOT_RUN");
        System.out.flush();System.exit(0); // Embedded runtime intentionally lives until process exit.
    }
}
