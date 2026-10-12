// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.nio.file.*;
public final class PartAdapterHostTest {
    static int count;
    static void check(boolean ok,String reason){if(!ok)throw new AssertionError(reason);count++;}
    static JSONObject call(String command)throws Exception{JSONObject r=new JSONObject(CoreNative.request(command));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject command(String text)throws Exception{return call(CoreCommandLine.parse(text).toString());}
    static JSONObject shape(JSONObject state,String name)throws Exception{JSONArray a=state.getJSONObject("document").getJSONArray("objects");for(int i=0;i<a.length();i++)if(a.getJSONObject(i).getString("name").equals(name))return a.getJSONObject(i).getJSONObject("shape");throw new AssertionError("Missing shape "+name);}
    static void volume(JSONObject state,String name,double expected)throws Exception{JSONObject s=shape(state,name);check(s.getBoolean("valid"),"Valid native BRep");check(s.getInt("solids")>0,"Native solid");check(Math.abs(s.getDouble("volume")-expected)<1e-6*Math.max(1,expected),"Volume "+name+" expected "+expected+" got "+s);}
    static void bad(String cmd)throws Exception{JSONObject r=new JSONObject(CoreNative.request(cmd));check(!r.getBoolean("ok"),"Must reject "+cmd);}
    static JSONObject python(String source)throws Exception{return call(new JSONObject().put("op","python").put("code",source).toString()).getJSONObject("python").getJSONObject("console");}
    public static void main(String[] args)throws Exception{
        System.load(args[0]);CoreNative.initialize(args[1],args[2],args[1]);
        JSONObject state=command("NewDoc PartReference");check(state.getBoolean("part"),"Genuine Part must be registered");
        command("Add Solid Box");command("Set Solid.Length 20 mm");command("Set Solid.Width 10 mm");state=command("Set Solid.Height 5 mm");volume(state,"Solid",1000);
        bad(CoreCommandLine.parse("Set Solid.Length -1 mm").toString());volume(command("State"),"Solid",1000);
        command("Add Driven Box");command("Set Driven.Width 10 mm");command("Set Driven.Height 5 mm");state=command("Expression Driven.Length Solid.Length * 2");volume(state,"Driven",2000);
        state=command("Set Solid.Length 30 mm");volume(state,"Solid",1500);volume(state,"Driven",3000);
        state=command("Undo");volume(state,"Solid",1000);volume(state,"Driven",2000);state=command("Redo");volume(state,"Solid",1500);volume(state,"Driven",3000);
        state=command("Set Solid.Label \"Türkçe Ölçü 💎\"");command("Save Part.FCStd");command("Close");state=command("Open Part.FCStd");volume(state,"Driven",3000);
        check(python("print(App.ActiveDocument.Solid.Label)").getString("output").contains("Türkçe Ölçü 💎"),"FCStd Unicode survives");
        state=command("Preview Solid 0.2");JSONArray coords=state.getJSONArray("preview");check(coords.length()==108,"Box tessellates to 12 triangles");for(int i=0;i<coords.length();i++)check(Double.isFinite(coords.getDouble(i)),"Finite mesh coordinate");
        MeshFrame mesh=PartMesh.frame(coords);double signedVolume=0;
        check(mesh.x==15&&mesh.y==5&&mesh.z==2.5f,"Native preview bounds equal the analytic box");
        for(int i=0;i<mesh.values.length;i+=30){float[] v=mesh.values;double x=v[i],y=v[i+1],z=v[i+2],ax=v[i+10],ay=v[i+11],az=v[i+12],bx=v[i+20],by=v[i+21],bz=v[i+22];signedVolume+=(x*(ay*bz-az*by)-y*(ax*bz-az*bx)+z*(ax*by-ay*bx))/6;double nx=v[i+3],ny=v[i+4],nz=v[i+5];check(Math.abs(nx*nx+ny*ny+nz*nz-1)<1e-6,"Unit preview normals");check(((x+ax+bx)/3-15)*nx+((y+ay+by)/3-5)*ny+((z+az+bz)/3-2.5)*nz>0,"Outward preview winding");}
        check(Math.abs(signedVolume-1500)<1e-6,"Independent tessellation volume matches native solid");
        SoftwareRasterizer.Image image=SoftwareRasterizer.render(mesh,480,360,-32,-58,1,0,0);int visible=0;for(int pixel:image.pixels)if(pixel!=SoftwareRasterizer.BACKGROUND)visible++;check(visible>1000&&visible<480*360,"Actual Part mesh produces a bounded visible preview");
        try(java.io.OutputStream out=Files.newOutputStream(Paths.get(args[2],"../../../../..","docs","native-part-preview.ppm").normalize())){out.write("P6\n480 360\n255\n".getBytes(java.nio.charset.StandardCharsets.US_ASCII));for(int pixel:image.pixels){out.write((pixel>>16)&255);out.write((pixel>>8)&255);out.write(pixel&255);}}
        bad("{\"op\":\"part_preview\",\"object\":\"Solid\",\"tolerance\":0}");
        bad("{\"op\":\"part_export\",\"object\":\"Solid\",\"file\":\"../escape.step\"}");
        bad("{\"op\":\"part_export\",\"object\":\"Solid\",\"file\":\"wrong.FCStd\"}");
        command("Begin");bad("{\"op\":\"part_export\",\"object\":\"Solid\",\"file\":\"Busy.step\"}");command("Abort");
        state=command("ExportStep Solid Reference.step");check(state.getString("step_file").equals("Reference.step"),"STEP filename");Path step=Paths.get(args[1],"documents","Reference.step");check(Files.size(step)>100,"STEP file produced by native Part.export");
        JSONObject console=python("import Part\ns=Part.read("+JSONObject.quote(step.toString())+")\nassert s.isValid()\nassert abs(s.Volume-1500)<1e-6\nprint('STEP_ROUNDTRIP_OK')");check(console.getString("error").isEmpty(),console.getString("error"));check(console.getString("output").contains("STEP_ROUNDTRIP_OK"),"STEP exact geometry readback");
        command("Add Round Cylinder");command("Set Round.Radius 3 mm");state=command("Set Round.Height 10 mm");volume(state,"Round",Math.PI*90);
        command("Add Ball Sphere");state=command("Set Ball.Radius 4 mm");volume(state,"Ball",4.0/3*Math.PI*64);
        command("Add Taper Cone");command("Add Ring Torus");state=command("State");check(shape(state,"Taper").getBoolean("valid"),"Native cone");check(shape(state,"Ring").getBoolean("valid"),"Native torus");
        state=command("Cut Cut Solid Round");check(shape(state,"Cut").getBoolean("valid"),"Native cut command");volume(state,"Cut",1500-Math.PI*9*5/4);
        state=command("Fuse Union Solid Round");check(shape(state,"Union").getBoolean("valid"),"Native fuse command");volume(state,"Union",1500+Math.PI*90-Math.PI*9*5/4);
        state=command("Common Intersection Solid Round");volume(state,"Intersection",Math.PI*9*5/4);
        bad(CoreCommandLine.parse("Cut Broken Solid Missing").toString());check(python("print(App.ActiveDocument.getObject('Broken') is None)").getString("output").contains("True"),"Failed boolean transaction removes its new object");
        command("Api Part.makeBox");state=command("State");check(state.getJSONObject("python").getJSONObject("api").getString("target").equals("Part.makeBox"),"Original Part API inspection");
        command("Save Boolean.FCStd");command("Close");state=command("Open Boolean.FCStd");check(shape(state,"Cut").getBoolean("valid"),"Native boolean FCStd restoration");volume(state,"Cut",1500-Math.PI*9*5/4);volume(state,"Union",1500+Math.PI*90-Math.PI*9*5/4);volume(state,"Intersection",Math.PI*9*5/4);
        bad("{\"op\":\"batch\",\"edits\":[{\"op\":\"add\",\"name\":\"Sketch\",\"type\":\"Sketcher::SketchObject\"}]}");
        for(String invalid:new String[]{"Preview Solid x","Preview Solid .2 extra","ExportStep Solid","Add X Unknown","Cut X Solid","Common X Solid Round extra"}){try{CoreCommandLine.parse(invalid);throw new AssertionError(invalid);}catch(IllegalArgumentException expected){count++;}}
        System.out.println("PASS: "+count+" genuine Part JNI/FCStd/STEP/parametric geometry assertions; Android execution NOT_RUN");System.out.flush();System.exit(0);
    }
}
