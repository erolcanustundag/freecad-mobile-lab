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
        Thread.setDefaultUncaughtExceptionHandler((thread,error)->{try{Path failure=Paths.get(args[2],"../../../../..","docs","sketcher-test-failure.txt").normalize();try(java.io.PrintWriter out=new java.io.PrintWriter(Files.newBufferedWriter(failure))){error.printStackTrace(out);}System.out.println("Sketch test failed after "+count+" checks: "+error);System.out.flush();}catch(Exception ignored){}System.exit(1);});
        System.load(args[3]);SignalProbe.capture();System.load(args[0]);CoreNative.initialize(args[1],args[2],args[1]);
        check(SignalProbe.preserved(),"Embedded FreeCAD must preserve JVM SIGSEGV handler, flags and mask");
        java.util.Locale original=java.util.Locale.getDefault();
        try{for(java.util.Locale locale:new java.util.Locale[]{java.util.Locale.US,new java.util.Locale("tr","TR"),java.util.Locale.GERMANY}){
            java.util.Locale.setDefault(locale);
            for(String alias:new String[]{"Sketch","ESKİZ","Skizze"})check(CoreCommandLine.parse(alias+" Profile").getJSONArray("edits").getJSONObject(0).getString("type").equals("Sketcher::SketchObject"),"Locale-stable sketch alias");
            check(CoreCommandLine.parse("Set Profile.Label \"İnci yüzüğüm\"").getJSONArray("edits").getJSONObject(0).getString("value").equals("İnci yüzüğüm"),"Native command Unicode label preserved");
        }}finally{java.util.Locale.setDefault(original);}
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
        bad("Set Curves.FullyConstrained true");bad("Set Curves._ExternalGeoVersion 999");
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
        // Native attachment/reference workflows: actual Part geometry and Sketcher solver.
        cmd("Add SupportBox Box");cmd("Sketch Attached");cmd("SketchLine Attached 0 0 10 0");
        cmd("SketchPlane Attached XZ 5 7 11");
        python("s=App.ActiveDocument.Attached\nassert (s.Placement.Base-App.Vector(5,7,11)).Length<1e-7\nassert (s.Placement.Rotation.multVec(App.Vector(0,1,0))-App.Vector(0,0,1)).Length<1e-7\nassert (s.Shape.Vertexes[0].Point-App.Vector(5,7,11)).Length<1e-7");
        cmd("Undo");python("assert App.ActiveDocument.Attached.Placement.Base.Length<1e-7");cmd("Redo");
        cmd("SketchPlane Attached YZ 0 0 0");python("assert (App.ActiveDocument.Attached.Placement.Rotation.multVec(App.Vector(0,0,1))-App.Vector(1,0,0)).Length<1e-7");
        cmd("SketchPlacement Attached 1 2 3 90 0 0");python("s=App.ActiveDocument.Attached\nassert (s.Placement.Rotation.multVec(App.Vector(1,0,0))-App.Vector(0,1,0)).Length<1e-7");
        cmd("SketchAttach Attached SupportBox Face6");
        JSONObject attached=sketch(cmd("State"),"Attached");check(attached.getString("map_mode").equals("FlatFace"),"Native FlatFace mode");check(attached.getJSONArray("support").getJSONObject(0).getString("object").equals("SupportBox"),"Attachment dependency exposed");
        python("s=App.ActiveDocument.Attached\nassert s.AttachmentSupport[0][0]==App.ActiveDocument.SupportBox\nassert abs(s.Placement.Base.z-10)<1e-7");
        cmd("SketchOffset Attached 0 0 2 0 0 0");python("assert abs(App.ActiveDocument.Attached.Placement.Base.z-12)<1e-7");
        cmd("Set SupportBox.Height 20 mm");python("assert abs(App.ActiveDocument.Attached.Placement.Base.z-22)<1e-7");
        cmd("Undo");python("assert abs(App.ActiveDocument.Attached.Placement.Base.z-12)<1e-7");cmd("Redo");
        bad("SketchPlane Attached XY 0 0 0");bad("SketchPlacement Attached 0 0 0 0 0 0");
        cmd("External Attached SupportBox Edge9");
        attached=sketch(cmd("State"),"Attached");check(attached.getJSONArray("external").length()==1,"Native external reference recorded");check(attached.getJSONArray("external").getJSONObject(0).getInt("geometry_index")==-3,"Original external negative index");
        cmd("Constraint Attached Coincident 0 1 -3 1");cmd("Constraint Attached Coincident 0 2 -3 2");dof("Attached",0);
        cmd("Set SupportBox.Length 25 mm");python("s=App.ActiveDocument.Attached\nassert abs(s.Geometry[0].length()-25)<1e-6\nassert abs(s.getPoint(-3,2).x-25)<1e-6");
        cmd("Undo");python("assert abs(App.ActiveDocument.Attached.Geometry[0].length()-10)<1e-6");cmd("Redo");
        JSONObject externalPreview=cmd("SketchPreview Attached").getJSONObject("sketch_preview");check(externalPreview.getJSONArray("curves").length()==2,"Internal and external curves preview");check(externalPreview.getJSONArray("curves").getJSONObject(1).getBoolean("external"),"External preview style marked");check(externalPreview.getJSONArray("curves").getJSONObject(1).getInt("index")==-3,"Preview labels solver reference index");
        bad("External Attached SupportBox Edge9");bad("External Attached SupportBox Edge999");bad("External Attached Missing Edge1");bad("External Attached Attached Edge1");bad("External Attached SupportBox Face6");bad("External Attached SupportBox Edge1");
        bad("Constraint Attached Coincident 0 1 -99 1");bad("DeleteExternal Attached -1");bad("DeleteExternal Attached 99");
        cmd("Add RoundSupport Cylinder");bad("SketchAttach Attached RoundSupport Face1");bad("SketchAttach Attached Missing Face6");bad("SketchAttach Attached SupportBox Face999");bad("SketchAttach Attached Attached Face1");
        bad("SketchAttach Attached SupportBox Edge1");bad("SketchPlane Profile BAD 0 0 0");bad("SketchPlane Profile XY 1000001 0 0");bad("SketchOffset Profile 0 0 1 0 0 0");
        bad("Remove SupportBox");python("assert App.ActiveDocument.SupportBox is not None\nassert App.ActiveDocument.Attached.DoF==0\nassert abs(App.ActiveDocument.Attached.Placement.Base.z-22)<1e-7");
        cmd("Sketch Dependent");cmd("SketchLine Dependent 0 0 3 0");cmd("External Dependent Attached Edge1");bad("External Attached Dependent Edge1");
        cmd("DeleteExternal Dependent 0");cmd("Undo");check(sketch(cmd("State"),"Dependent").getJSONArray("external").length()==1,"Reference deletion Undo");cmd("Redo");
        cmd("Save Attachments.FCStd");cmd("Close");cmd("Open Attachments.FCStd");
        python("s=App.ActiveDocument.Attached\nassert s.MapMode=='FlatFace'\nassert s.AttachmentSupport[0][0]==App.ActiveDocument.SupportBox\nassert s.ExternalGeometry[0][0]==App.ActiveDocument.SupportBox\nassert abs(s.Placement.Base.z-22)<1e-7\nassert abs(s.Geometry[0].length()-25)<1e-6\nassert s.DoF==0");
        cmd("Set SupportBox.Length 32 mm");python("assert abs(App.ActiveDocument.Attached.Geometry[0].length()-32)<1e-6");cmd("Undo");cmd("Redo");
        cmd("SketchDetach Attached");python("s=App.ActiveDocument.Attached\nassert s.MapMode=='Deactivated' and not s.AttachmentSupport\nassert abs(s.Placement.Base.z-22)<1e-7");
        cmd("Undo");check(sketch(cmd("State"),"Attached").getString("map_mode").equals("FlatFace"),"Detach Undo restores support");cmd("Redo");
        cmd("DeleteExternal Attached 0");python("assert len(App.ActiveDocument.Attached.ExternalGeometry)==0\nassert App.ActiveDocument.Attached.ConstraintCount==0");
        cmd("Undo");dof("Attached",0);cmd("Redo");cmd("Remove SupportBox");cmd("Undo");cmd("Undo");cmd("Undo");
        dof("Attached",0);check(sketch(cmd("State"),"Attached").getString("map_mode").equals("FlatFace"),"Full dependency history restored");
        Path attachmentDestination=Paths.get(args[2],"../../../../..","samples","upstream-sketcher").normalize();Files.createDirectories(attachmentDestination);Files.copy(Paths.get(args[1],"documents","Attachments.FCStd"),attachmentDestination.resolve("Attachments.FCStd"),StandardCopyOption.REPLACE_EXISTING);
        Files.write(attachmentDestination.resolve("attachment-preview.json"),externalPreview.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        cmd("Set Profile.Label \"Türkçe Eskiz 💎\"");cmd("Save Sketch.FCStd");cmd("Close");state=cmd("Open Sketch.FCStd");dof("Profile",0);check(sketch(state,"Curves").getInt("geometry_count")==4,"FCStd native geometry restoration");
        python("s=App.ActiveDocument.Profile\nassert s.Label=='Türkçe Eskiz 💎'\nassert abs(s.Geometry[0].length()-40)<1e-7\ns=App.ActiveDocument.Curves\nassert s.getConstruction(3)\nassert s.Geometry[3].getWeights()==[1.0,2.0,2.0,1.0]");
        cmd("DeleteConstraint Profile 1");dof("Profile",1);cmd("Undo");dof("Profile",0);
        cmd("DeleteGeometry Curves 0");check(sketch(cmd("State"),"Curves").getInt("geometry_count")==3,"Delete native geometry");cmd("Undo");check(sketch(cmd("State"),"Curves").getInt("geometry_count")==4,"Geometry delete undo");
        int priorUndo=cmd("State").getJSONObject("document").getInt("undo");
        JSONArray attachmentEdits=new JSONArray().put(new JSONObject().put("op","sketch_offset").put("object","Attached").put("values",new JSONArray("[0,0,7,0,0,0]")))
            .put(new JSONObject().put("op","sketch_external").put("object","Attached").put("source","SupportBox").put("element","Edge999"));
        check(!new JSONObject(CoreNative.request(new JSONObject().put("op","batch").put("edits",attachmentEdits).toString())).getBoolean("ok"),"Atomic multi-edit attachment rollback");
        check(cmd("State").getJSONObject("document").getInt("undo")==priorUndo,"Invalid reference preserves history");python("assert abs(App.ActiveDocument.Attached.Placement.Base.z-22)<1e-7");
        bad("Set SupportBox.Length 0 mm");python("assert abs(App.ActiveDocument.SupportBox.Length.Value-32)<1e-7\nassert abs(App.ActiveDocument.Attached.Geometry[0].length()-32)<1e-6");
        String priorDocument=cmd("State").getJSONObject("document").getString("name");int priorDocuments=cmd("State").getJSONArray("documents").length();
        python("s=App.ActiveDocument.Attached\ns.MapMode='ObjectXY'\nApp.ActiveDocument.recompute()\nApp.ActiveDocument.saveAs("+JSONObject.quote(Paths.get(args[1],"documents","UnsupportedAttachment.FCStd").toString())+")\ns.MapMode='FlatFace'\nApp.ActiveDocument.recompute()\nApp.ActiveDocument.saveAs("+JSONObject.quote(Paths.get(args[1],"documents","SupportedAttachment.FCStd").toString())+")");
        bad("Open SupportedAttachment.FCStd");bad("Open UnsupportedAttachment.FCStd");check(cmd("State").getJSONObject("document").getString("name").equals(priorDocument),"Rejected FCStd keeps prior active document");check(cmd("State").getJSONArray("documents").length()==priorDocuments,"Rejected attachment FCStd does not leak a document");
        String activeName=cmd("State").getJSONObject("document").getString("name");
        cmd("NewDoc ReferenceBudget");cmd("Sketch Budget");
        for(int i=0;i<64;i++){cmd("Add Ref"+i+" Box");cmd("External Budget Ref"+i+" Edge9");}
        check(sketch(cmd("State"),"Budget").getJSONArray("external").length()==64,"External reference upper boundary accepted");
        cmd("Add RefOverflow Box");bad("External Budget RefOverflow Edge9");
        check(sketch(cmd("State"),"Budget").getJSONArray("external").length()==64,"Overflow rolls back without deleting references");
        JSONObject budgetPreview=cmd("SketchPreview Budget").getJSONObject("sketch_preview");check(budgetPreview.getJSONArray("curves").length()==64,"All bounded external lines preview");
        cmd("Close");cmd("Activate "+activeName);
        cmd("Api Sketcher.Constraint");check(cmd("State").getJSONObject("python").getJSONObject("api").getString("target").equals("Sketcher.Constraint"),"Original Sketcher API browser");
        Path destination=Paths.get(args[2],"../../../../..","samples","upstream-sketcher").normalize();Files.createDirectories(destination);Files.copy(Paths.get(args[1],"documents","Sketch.FCStd"),destination.resolve("Sketch.FCStd"),StandardCopyOption.REPLACE_EXISTING);
        Files.write(destination.resolve("preview.json"),cmd("SketchPreview Curves").getJSONObject("sketch_preview").toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        int objects=cmd("State").getJSONObject("document").getJSONArray("objects").length();for(int i=0;i<500;i++)cmd("State");check(cmd("State").getJSONObject("document").getJSONArray("objects").length()==objects,"Repeated JNI snapshots preserve the native document");check(SignalProbe.preserved(),"VM fault handler preserved after solver/restore/JIT stress");
        Files.deleteIfExists(Paths.get(args[2],"../../../../..","docs","sketcher-test-failure.txt").normalize());
        System.out.println("PASS: "+count+" genuine original Sketcher JNI/solver/entity/FCStd assertions; Android execution NOT_RUN");System.out.flush();System.exit(0);
    }
}
