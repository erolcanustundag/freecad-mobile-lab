// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.nio.file.*;
public final class SketchAdapterHostTest {
    static int count;
    static void check(boolean value,String reason){if(!value)throw new AssertionError(reason);count++;}
    static JSONObject call(JSONObject request)throws Exception{JSONObject result=new JSONObject(CoreNative.request(request.toString()));check(result.getBoolean("ok"),result.optString("error"));return result.getJSONObject("state");}
    static JSONObject cmd(String command)throws Exception{return call(CoreCommandLine.parse(command));}
    static void bad(String command)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(command).toString()));check(!r.getBoolean("ok"),"Must reject "+command);}
    static JSONObject sketch(JSONObject state,String name)throws Exception{JSONArray objects=state.getJSONObject("document").getJSONArray("objects");for(int i=0;i<objects.length();i++)if(objects.getJSONObject(i).getString("name").equals(name))return objects.getJSONObject(i).getJSONObject("sketch");throw new AssertionError(name);}
    static void python(String code)throws Exception{JSONObject console=call(new JSONObject().put("op","python").put("code",code)).getJSONObject("python").getJSONObject("console");check(console.getString("error").isEmpty(),console.getString("error"));}
    static void dof(String name,int expected)throws Exception{JSONObject s=sketch(cmd("State"),name);check(s.getInt("dof")==expected,"DOF "+name+" expected "+expected+" got "+s);check(s.getJSONArray("conflicts").length()==0,"No solver conflict");check(s.getJSONArray("redundant").length()==0,"No redundant constraint");}
    public static void main(String[] args)throws Exception{
        System.load(args[0]);CoreNative.initialize(args[1],args[2],args[1]);
        JSONObject state=cmd("NewDoc SketchReference");check(state.getBoolean("sketcher"),"Original builtin Sketcher must load");
        cmd("Eskiz Profile");state=cmd("SketchLine Profile 0 0 30 0");check(sketch(state,"Profile").getInt("geometry_count")==1,"Native line creation");dof("Profile",4);
        cmd("Constraint Profile Horizontal 0");dof("Profile",3);cmd("Constraint Profile Distance 0 30");dof("Profile",2);
        cmd("Constraint Profile Coincident 0 1 -1 1");dof("Profile",0);
        python("s=App.ActiveDocument.Profile\nassert s.Geometry[0].TypeId == 'Part::GeomLineSegment'\nassert abs(s.Geometry[0].length()-30)<1e-7\nassert s.getPoint(0,1).Length<1e-7");
        bad("Constraint Profile Vertical 0");check(sketch(cmd("State"),"Profile").getInt("constraint_count")==3,"Conflict rolled back without corrupting constraints");dof("Profile",0);
        bad("Constraint Profile Horizontal 0");check(sketch(cmd("State"),"Profile").getInt("constraint_count")==3,"Redundant edit rolled back");
        cmd("Datum Profile 1 4 cm");python("assert abs(App.ActiveDocument.Profile.Geometry[0].length()-40)<1e-7");
        cmd("Undo");python("assert abs(App.ActiveDocument.Profile.Geometry[0].length()-30)<1e-7");cmd("Redo");python("assert abs(App.ActiveDocument.Profile.Geometry[0].length()-40)<1e-7");
        state=cmd("SketchPreview Profile");JSONObject preview=state.getJSONObject("sketch_preview");JSONArray points=preview.getJSONArray("curves").getJSONObject(0).getJSONArray("points");check(points.length()==2,"Line display samples are bounded");check(Math.abs(points.getJSONArray(1).getDouble(0)-40)<1e-7,"Preview displays solved geometry");check(preview.getInt("dof")==0,"Preview shows native DOF");
        cmd("Sketch Curves");cmd("SketchCircle Curves 0 0 5");cmd("SketchArc Curves 20 0 10 0 180");cmd("SketchEllipse Curves 0 30 20 10");cmd("SketchSpline Curves 3 0,0;10,20;20,20;30,0 1,2,2,1");
        state=cmd("Construction Curves 3 true");check(sketch(state,"Curves").getJSONArray("geometry").getJSONObject(3).getBoolean("construction"),"Native construction flag");
        python("s=App.ActiveDocument.Curves\nassert abs(s.Geometry[0].Radius-5)<1e-8\nassert abs(s.Geometry[1].length()-10*3.141592653589793)<1e-6\nassert abs(s.Geometry[2].MajorRadius-20)<1e-7\nassert abs(s.Geometry[2].MinorRadius-10)<1e-7\nassert s.Geometry[3].Degree==3\nassert s.Geometry[3].getWeights()==[1.0,2.0,2.0,1.0]\nassert s.getConstruction(3)");
        state=cmd("SketchPreview Curves");JSONArray curves=state.getJSONObject("sketch_preview").getJSONArray("curves");check(curves.length()==4,"All entity types preview");for(int i=0;i<curves.length();i++){JSONArray p=curves.getJSONObject(i).getJSONArray("points");check(p.length()==65,"Bounded curve sample count");for(int j=0;j<p.length();j++)check(Double.isFinite(p.getJSONArray(j).getDouble(0))&&Double.isFinite(p.getJSONArray(j).getDouble(1)),"Finite solved curve point");}
        check(curves.getJSONObject(3).getBoolean("construction"),"Construction preview flag");
        cmd("Constraint Curves Radius 0 8");python("assert abs(App.ActiveDocument.Curves.Geometry[0].Radius-8)<1e-7");cmd("Datum Curves 0 1 cm");python("assert abs(App.ActiveDocument.Curves.Geometry[0].Radius-10)<1e-7");
        cmd("Sketch Move");cmd("SketchLine Move 0 0 10 0");cmd("MovePoint Move 0 2 12 8");python("p=App.ActiveDocument.Move.getPoint(0,2)\nassert abs(p.x-12)<1e-6 and abs(p.y-8)<1e-6");
        cmd("Undo");python("p=App.ActiveDocument.Move.getPoint(0,2)\nassert abs(p.x-10)<1e-7 and abs(p.y)<1e-7");cmd("Redo");
        for(String kind:new String[]{"Parallel","Perpendicular","Equal","Tangent"}){
            cmd("Sketch Test"+kind);String name="Test"+kind;
            if(kind.equals("Equal")){cmd("SketchCircle "+name+" 0 0 5");cmd("SketchCircle "+name+" 20 0 8");}
            else if(kind.equals("Tangent")){cmd("SketchCircle "+name+" 0 0 5");cmd("SketchLine "+name+" -10 5 10 5");}
            else{cmd("SketchLine "+name+" 0 0 20 0");cmd("SketchLine "+name+" 10 10 20 20");}
            state=cmd("Constraint "+name+" "+kind+" 0 1");check(sketch(state,name).getInt("constraint_count")==1,"Original "+kind+" constraint");
            if(kind.equals("Equal"))python("s=App.ActiveDocument.TestEqual\nassert abs(s.Geometry[0].Radius-s.Geometry[1].Radius)<1e-7");
        }
        cmd("Sketch Vertical");cmd("SketchLine Vertical 0 0 0 20");cmd("Constraint Vertical Vertical 0");dof("Vertical",3);
        cmd("Sketch Angled");cmd("SketchLine Angled 0 0 20 20");cmd("Constraint Angled Angle 0 45");dof("Angled",3);cmd("Datum Angled 0 30 deg");python("s=App.ActiveDocument.Angled\nv=s.Geometry[0].EndPoint-s.Geometry[0].StartPoint\nimport math\nassert abs(math.atan2(v.y,v.x)-math.pi/6)<1e-6");
        cmd("Sketch Diameter");cmd("SketchCircle Diameter 0 0 5");cmd("Constraint Diameter Diameter 0 12");python("assert abs(App.ActiveDocument.Diameter.Geometry[0].Radius-6)<1e-7");dof("Diameter",2);
        for(String invalid:new String[]{"SketchLine Curves 0 0 0 0","SketchCircle Curves 0 0 -1","SketchArc Curves 0 0 3 0 360","SketchEllipse Curves 0 0 5 8","SketchSpline Curves 6 0,0;10,10","SketchSpline Curves 1 0,0;10,10 1,0","Construction Curves 99 true","Constraint Profile Horizontal 99","Constraint Profile Coincident 0 0 -1 1","Datum Profile 999 10 mm","DeleteGeometry Curves -1","MovePoint Move 0 0 3 4"})bad(invalid);
        int undo=cmd("State").getJSONObject("document").getInt("undo");
        JSONArray edits=new JSONArray().put(new JSONObject().put("op","sketch_geometry").put("object","Move").put("geometry",new JSONObject().put("kind","Circle").put("center",new JSONArray("[0,0]")).put("radius",5)))
            .put(new JSONObject().put("op","sketch_delete_geometry").put("object","Move").put("index",999));
        check(!new JSONObject(CoreNative.request(new JSONObject().put("op","batch").put("edits",edits).toString())).getBoolean("ok"),"Failed sketch multi-edit rejected");state=cmd("State");check(sketch(state,"Move").getInt("geometry_count")==1,"Atomic sketch edit rollback");check(state.getJSONObject("document").getInt("undo")==undo,"Failed edits preserve history count");
        cmd("Set Profile.Label \"Türkçe Eskiz 💎\"");cmd("Save Sketch.FCStd");cmd("Close");state=cmd("Open Sketch.FCStd");dof("Profile",0);check(sketch(state,"Curves").getInt("geometry_count")==4,"FCStd native geometry restoration");
        python("s=App.ActiveDocument.Profile\nassert s.Label=='Türkçe Eskiz 💎'\nassert abs(s.Geometry[0].length()-40)<1e-7\ns=App.ActiveDocument.Curves\nassert s.getConstruction(3)\nassert s.Geometry[3].getWeights()==[1.0,2.0,2.0,1.0]");
        cmd("DeleteConstraint Profile 1");dof("Profile",1);cmd("Undo");dof("Profile",0);
        cmd("DeleteGeometry Curves 0");check(sketch(cmd("State"),"Curves").getInt("geometry_count")==3,"Delete native geometry");cmd("Undo");check(sketch(cmd("State"),"Curves").getInt("geometry_count")==4,"Geometry delete undo");
        cmd("Api Sketcher.Constraint");check(cmd("State").getJSONObject("python").getJSONObject("api").getString("target").equals("Sketcher.Constraint"),"Original Sketcher API browser");
        Path destination=Paths.get(args[2],"../../../../..","samples","upstream-sketcher").normalize();Files.createDirectories(destination);Files.copy(Paths.get(args[1],"documents","Sketch.FCStd"),destination.resolve("Sketch.FCStd"),StandardCopyOption.REPLACE_EXISTING);
        Files.write(destination.resolve("preview.json"),cmd("SketchPreview Curves").getJSONObject("sketch_preview").toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        System.out.println("PASS: "+count+" genuine original Sketcher JNI/solver/entity/FCStd assertions; Android execution NOT_RUN");System.out.flush();System.exit(0);
    }
}
