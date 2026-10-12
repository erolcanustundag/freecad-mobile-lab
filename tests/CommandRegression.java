package org.freecad.mobilelab;
import org.json.*;
import java.util.*;
import java.io.*;
import java.nio.file.*;
public final class CommandRegression {
    static int checks;
    interface Action{void run()throws Exception;}
    static void check(boolean b,String s){if(!b)throw new AssertionError(s);checks++;}
    static void reject(Action a)throws Exception{try{a.run();}catch(Exception e){checks++;return;}throw new AssertionError("Invalid input accepted");}
    static int run(String text,int id)throws Exception{CommandLine.Request r=CommandLine.parse(text);NativeCad.beginTransaction(r.recordUndo());try{int next=CommandLine.execute(r,id);new MeshFrame(NativeCad.meshAtDetail(next,10000),NativeCad.lines(next));NativeCad.commitTransaction();return next;}catch(Throwable t){NativeCad.rollbackTransaction();throw t;}}
    static JSONObject object(int id)throws Exception{JSONArray a=new JSONArray(NativeCad.objects());for(int i=0;i<a.length();i++)if(a.getJSONObject(i).getInt("id")==id)return a.getJSONObject(i);throw new AssertionError("Missing object");}
    public static void main(String[] args)throws Exception{
        check(CommandLine.parse("_bOx 20, 10, 4").name.equals("Box"),"Case/comma/prefix parsing");check(CommandLine.parse("ZE").name.equals("Fit"),"View alias");check(CommandLine.parse("BooleanDifference 1 2").name.equals("Cut"),"Boolean alias");check(CommandLine.parse("Help Box").args.get(0).equals("Box"),"Help argument");
        reject(()->CommandLine.parse("Box 1 2 3; Clear"));reject(()->CommandLine.parse("Box 1\nClear"));reject(()->CommandLine.parse("Box \"2"));reject(()->CommandLine.parse("java.lang.System.exit"));reject(()->CommandLine.parse("Sphere NaN").values());reject(()->CommandLine.parse("Move Infinity 0 0").values());reject(()->CommandLine.parse("Box 1e999 1 1").values());reject(()->CommandLine.parse("Help "+String.join("",Collections.nCopies(5000,"x"))));
        for(String n:CommandLine.HELP.keySet())check(CommandLine.parse(n).name.equals(n),"Registered command does not parse: "+n);
        NativeCad.clear();int box=run("Box 20 10 4",0);check(Math.abs(object(box).getDouble("volume")-800)<1e-5,"Box dimensions ignored");run("Move 5 -2 3",box);check(object(box).getJSONArray("xyz").getDouble(0)==5,"Absolute move");int copy=run("Copy 30 0 0",box);check(copy!=box&&object(box).getJSONArray("xyz").getDouble(0)==5,"Copy changed source");
        String before=NativeCad.objects();reject(()->run("Scale -1",box));reject(()->run("Box 2 3",box));reject(()->run("Select 999999",box));reject(()->run("Array 2.5 1 0 0",box));check(before.equals(NativeCad.objects()),"Failed command changed scene");
        int circle=run("Circle 2",box),pad=run("Extrude 3",circle);check(Math.abs(object(pad).getDouble("volume")-Math.PI*12)<1e-5,"Command extrusion");check(!object(circle).getBoolean("visible"),"Profile not hidden");run("Undo",pad);check(object(circle).getBoolean("visible"),"Command Undo lost input");
        run("Clear",box);check(new JSONArray(NativeCad.objects()).length()==0,"Clear failed");run("Undo",0);check(new JSONArray(NativeCad.objects()).length()>0,"Clear not recoverable");
        File root=Files.createTempDirectory("command-project").toFile(),cache=new File(root,"cache");cache.mkdir();try{File f=new File(root,"test.fcml");ProjectStore.save(f,cache);NativeCad.beginTransaction(false);try{ProjectStore.restore(f,cache);NativeCad.commitTransaction();}catch(Throwable t){NativeCad.rollbackTransaction();throw t;}check(new JSONArray(NativeCad.objects()).length()>0,"Command-created geometry lost on reopen");}finally{ArchiveIO.deleteTree(root);}
        System.out.println("PASS: "+checks+" command parser, aliases, native geometry, rollback, Undo and project assertions");
    }
}
