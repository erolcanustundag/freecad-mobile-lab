// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.io.*;
import java.nio.file.*;
import org.json.*;
public final class PrecisionCadRegression {
    static int checks;static File cache;
    interface Action{void run()throws Exception;}
    static void near(double a,double b,double eps){checks++;if(Math.abs(a-b)>eps)throw new AssertionError(a+" expected "+b);}
    static void check(boolean value){checks++;if(!value)throw new AssertionError("Check "+checks);}
    static int command(String text,int selected)throws Exception{String old=ProjectStore.workspace();NativeCad.beginTransaction(true);try{int id=CommandLine.execute(CommandLine.parse(text),selected);NativeCad.setWorkspace(ProjectStore.workspace());NativeCad.commitTransaction();return id;}catch(Throwable e){NativeCad.rollbackTransaction();ProjectStore.applyWorkspace(old);throw e;}}
    static void reject(Action action)throws Exception{checks++;try{action.run();}catch(Exception e){return;}throw new AssertionError("Expected rejection");}
    public static void main(String[] args)throws Exception{
        cache=Files.createTempDirectory("precision-cad-").toFile();NativeCad.clear();ProjectStore.reset();command("Set bore 18",0);command("Set outer \"bore+2*1.6\"",0);int ring=command("Ring bore 1.6 3",0);near(PrecisionTools.object(ring).getJSONArray("dims").getDouble(0),18,1e-8);command("Set bore 20",ring);near(Expressions.evaluate("outer"),23.2,1e-8);check(NativeCad.undo());ProjectStore.applyWorkspace(NativeCad.getWorkspace());near(Expressions.evaluate("bore"),18,0);check(NativeCad.redo());ProjectStore.applyWorkspace(NativeCad.getWorkspace());near(Expressions.evaluate("bore"),20,0);reject(()->command("Set bore outer",0));near(Expressions.evaluate("bore"),20,0);
        File project=new File(cache,"variables.fcml");ProjectStore.save(project,cache);NativeCad.clear();ProjectStore.reset();NativeCad.beginTransaction(false);try{ring=ProjectStore.restore(project,cache);NativeCad.commitTransaction();}catch(Throwable e){NativeCad.rollbackTransaction();throw e;}near(Expressions.evaluate("outer"),23.2,1e-8);near(PrecisionTools.object(ring).getJSONArray("dims").getDouble(0),18,1e-8);
        NativeCad.clear();ProjectStore.reset();int a=command("Box 2 4 6",0);int b=command("Box 2 4 6",a);command("Move 10 0 0",b);near(NativeCad.distance(a,b),8,1e-7);check(PrecisionTools.measure(a,java.util.Arrays.asList(""+a,""+b)).contains("8.00000000"));reject(()->PrecisionTools.measure(a,java.util.Arrays.asList(""+a,""+a)));
        command("Move 10 20 30",a);command("RotateAround 0 0 0 0 0 1 90",a);JSONArray bbox=PrecisionTools.object(a).getJSONArray("bbox");for(int i=0;i<6;i++)near(bbox.getDouble(i),new double[]{-22,9,30,-18,11,36}[i],1e-6);check(NativeCad.undo());ProjectStore.applyWorkspace(NativeCad.getWorkspace());near(PrecisionTools.object(a).getJSONArray("bbox").getDouble(0),9,1e-7);command("ScaleAround 0 0 0 2",a);bbox=PrecisionTools.object(a).getJSONArray("bbox");for(int i=0;i<6;i++)near(bbox.getDouble(i),new double[]{18,36,60,22,44,72}[i],1e-6);
        String scene=NativeCad.objects();reject(()->command("RotateAround 0 0 0 0 0 0 90",a));check(scene.equals(NativeCad.objects()));reject(()->command("ScaleAround 0 0 0 -2",a));check(scene.equals(NativeCad.objects()));command("Lock",a);reject(()->command("RotateAround 0 0 0 0 1 0 90",a));command("Unlock",a);
        NativeCad.clear();ProjectStore.reset();int profile=command("Rectangle 2 3",0),pad=command("Extrude 4",profile);command("RotateAround 0 0 0 0 0 1 90",profile);near(PrecisionTools.object(pad).getDouble("volume"),24,1e-7);near(PrecisionTools.object(pad).getJSONArray("bbox").getDouble(0),-1.5,1e-6);
        check(CommandLine.parse("RotateAround").ui());check(CommandLine.parse("ScaleAround").ui());check(CommandLine.parse("Measure 1 2").ui());check(CommandLine.parse("Calc \"sqrt(3^2+4^2)\"").ui());
        ArchiveIO.deleteTree(cache);System.out.println("PASS: "+checks+" native precision assertions (command expressions, project/Undo/Redo, distance, pivot solids, locks, rollback and dependant recompute)");
    }
}
