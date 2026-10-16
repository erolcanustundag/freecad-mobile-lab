// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignPrimitiveAdapterHostTest {
    static int checks;
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
    static JSONObject call(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject cmd(String s)throws Exception{return call(CoreCommandLine.parse(s));}
    static void bad(String s)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(s).toString()));check(!r.getBoolean("ok"),"Must reject "+s);}
    static void python(String code)throws Exception{JSONObject r=call(new JSONObject().put("op","python").put("code",code)).getJSONObject("python").getJSONObject("console");check(r.getString("error").isEmpty(),r.getString("error"));}
    static void volume(String n,double expected)throws Exception{JSONObject r=cmd("ShapeInfo "+n).getJSONObject("shape_inspection");check(r.getBoolean("valid")&&r.getInt("solids")==1,"Closed original solid");check(Math.abs(r.getDouble("volume")-expected)<1e-5,"Analytic volume "+n+": "+r);}
    public static void main(String[] a)throws Exception{
        System.load(a[3]);SignalProbe.capture();System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);check(SignalProbe.preserved(),"JVM signals retained");cmd("NewDoc Primitives");cmd("Body Body");
        bad("BodySubBox Body NoStock 1 1 1");bad("BodySubCylinder Body NoCylinderStock 1 1");bad("BodyAddBox Body ZeroBox 0 1 1");bad("BodyAddCylinder Body NegativeCylinder -1 2");
        cmd("BodyAddBox Body Block 10 10 10");volume("Body",1000);
        cmd("BodyAddCylinder Body Boss 2 4 5 5 10 0 0 0");volume("Body",1000+16*Math.PI);
        cmd("BodySubBox Body Notch 2 2 5 1 1 0 0 0 0");volume("Body",980+16*Math.PI);
        cmd("BodySubCylinder Body Bore 1 6 5 5 0 0 0 0");volume("Body",980+10*Math.PI);
        python("d=App.ActiveDocument\nassert d.Block.TypeId=='PartDesign::AdditiveBox' and d.Boss.TypeId=='PartDesign::AdditiveCylinder'\nassert d.Notch.TypeId=='PartDesign::SubtractiveBox' and d.Bore.TypeId=='PartDesign::SubtractiveCylinder'\nassert d.Block.BaseFeature is None and d.Boss.BaseFeature==d.Block and d.Notch.BaseFeature==d.Boss and d.Bore.BaseFeature==d.Notch\nassert d.Body.Tip==d.Bore\nfor o in (d.Block,d.Boss,d.Notch,d.Bore):assert o.MapMode=='Deactivated' and not o.AttachmentSupport and o.AttacherType=='Attacher::AttachEngine3D'");
        check(cmd("BodyInfo Body").getJSONObject("body_inspection").getJSONArray("solid_history").length()==4,"Original primitive solid history");
        for(String s:new String[]{"BodyAddBox Body Inside 1 1 1 7 7 2 0 0 0","BodySubCylinder Body Outside 1 2 100 100 100 0 0 0","BodySubBox Body Wipe 100 100 100 -1 -1 -1 0 0 0","BodyAddBox Body Far 10 10 10 100 100 100 0 0 0","BodyAddBox Body Budget 10 10 10 999999 0 0 45 0 0","BodyPrimitivePose Body Boss 5 5 20 0 0 0","BodyPrimitivePose Body Bore 1000001 0 0 0 0 0","BodyPrimitivePose Body Body 0 0 0 0 0 0","Set Boss.Angle 180 deg","Set Boss.FirstAngle 1 deg","Set Boss.SecondAngle 1 deg","Set Boss.MapMode 1","Set Boss.MapReversed true","Set Boss.Suppressed true","Set Boss.FuzzyTolerance 0","Set Block.Length 0 mm","Set Bore.Radius 1000001 mm","Set Block.Height -1 mm","Expression Block.Length 10","PartPlacement Boss 5 5 10 0 0 0","RemoveBodyFeature Body Block"})bad(s);
        volume("Body",980+10*Math.PI);cmd("BodyTip Body Block");bad("BodyAddBox Body Branched 2 2 2 10 0 0 0 0 0");cmd("BodyTip Body Bore");
        cmd("Set Block.Height 12 mm");volume("Body",1180+2*Math.PI);cmd("Set Boss.Height 6 mm");volume("Body",1180+10*Math.PI);
        cmd("Set Bore.Radius 0.15 cm");volume("Body",1180+2.5*Math.PI);cmd("Undo");volume("Body",1180+10*Math.PI);cmd("Redo");cmd("Undo");
        cmd("Set Block.Length 1.2 cm");volume("Body",1420+10*Math.PI);cmd("Undo");
        cmd("BodyPrimitivePose Body Notch 2 2 0 30 0 0");volume("Body",1180+10*Math.PI);python("assert (App.ActiveDocument.Notch.Placement.Base-App.Vector(2,2,0)).Length<1e-8");cmd("Undo");
        cmd("Set Boss.Refine false");volume("Body",1180+10*Math.PI);cmd("Set Boss.Refine true");
        cmd("Begin AtomicPrimitive");cmd("Set Block.Height 13 mm");bad("BodyPrimitivePose Body Boss 5 5 100 0 0 0");volume("Body",1180+10*Math.PI);python("assert abs(App.ActiveDocument.Block.Height.Value-12)<1e-8");
        cmd("PartPlacement Body 1 2 3 30 20 10");volume("Body",1180+10*Math.PI);cmd("Undo");bad("PartPlacement Body 999999 0 0 0 0 0");
        cmd("BodyPlane Body WorkPlane 20 20");cmd("DatumAttach Body WorkPlane Block Face6");cmd("BodySketchDatum Body WorkPlane Marker");cmd("SketchCircle Marker 2 3 1");cmd("Constraint Marker Block 0");cmd("SketchOffset Marker 1 1 0 20 0 0");
        cmd("Set Block.Height 13 mm");volume("Body",1280+6*Math.PI);python("assert abs(App.ActiveDocument.WorkPlane.Placement.Base.z-13)<1e-8 and App.ActiveDocument.WorkPlane.AttachmentSupport[0][0]==App.ActiveDocument.Block");cmd("Undo");
        cmd("Body OtherBody");cmd("BodyAddBox OtherBody OtherStock 5 5 5");bad("BodyPrimitivePose Body OtherStock 0 0 0 0 0 0");bad("DatumAttach OtherBody WorkPlane OtherStock Face6");
        cmd("RemoveBodyFeature Body Bore");volume("Body",1180+16*Math.PI);cmd("Undo");cmd("Redo");cmd("Undo");volume("Body",1180+10*Math.PI);
        cmd("Save Primitives.FCStd");Process cold=new ProcessBuilder(System.getProperty("java.home")+"/bin/java","-cp",System.getProperty("java.class.path"),"org.freecad.mobilelab.PartDesignPrimitiveColdRestoreHostTest",a[0],a[1],a[2]).inheritIO().start();check(cold.waitFor()==0,"Original primitive cold restoration");
        python("import zipfile,xml.etree.ElementTree as ET,mobile_core\nroot=mobile_core._root\nwith zipfile.ZipFile(root/'Primitives.FCStd') as z:saved={n:z.read(n) for n in z.namelist()}\ndef primitive_fixture(filename,obj,prop,tag,key,value):\n    tree=ET.fromstring(saved['Document.xml'])\n    node=tree.find(\"./ObjectData/Object[@name='\"+obj+\"']/Properties/Property[@name='\"+prop+\"']/\"+tag)\n    assert node is not None\n    node.set(key,value)\n    xml=ET.tostring(tree)\n    with zipfile.ZipFile(root/('BadPrimitive'+filename+'.FCStd'),'w') as z:\n        for n,b in saved.items():z.writestr(n,xml if n=='Document.xml' else b)");
        String[] changes={"'Length','Block','Length','Float','value','0'","'Radius','Bore','Radius','Float','value','nan'","'Height','Boss','Height','Float','value','1000001'","'Angle','Boss','Angle','Float','value','180'","'FirstAngle','Boss','FirstAngle','Float','value','1'","'SecondAngle','Bore','SecondAngle','Float','value','1'","'Mode','Boss','MapMode','Integer','value','2'","'Engine','Boss','AttacherType','String','value','Attacher::AttachEnginePlane'","'Offset','Boss','AttachmentOffset','PropertyPlacement','Px','1'","'Reverse','Boss','MapReversed','Bool','value','true'","'PathParameter','Boss','MapPathParameter','Float','value','0.5'","'Suppressed','Bore','Suppressed','Bool','value','true'","'Tolerance','Boss','FuzzyTolerance','Float','value','0'","'PoseNan','Notch','Placement','PropertyPlacement','Py','nan'","'Quaternion','Notch','Placement','PropertyPlacement','Q3','2'","'PoseBudget','Block','Placement','PropertyPlacement','Px','999999'","'BodyBudget','Body','Placement','PropertyPlacement','Px','999999'","'History','Bore','BaseFeature','Link','value','Block'","'Foreign','Bore','BaseFeature','Link','value','OtherStock'"};
        for(String mutation:changes)python("primitive_fixture("+mutation+")");
        for(String n:new String[]{"Length","Radius","Height","Angle","FirstAngle","SecondAngle","Mode","Engine","Offset","Reverse","PathParameter","Suppressed","Tolerance","PoseNan","Quaternion","PoseBudget","BodyBudget","History","Foreign"})bad("Open BadPrimitive"+n+".FCStd");
        volume("Body",1180+10*Math.PI);cmd("ExportStep Body Primitives.step");cmd("ImportStep Copy Primitives.step");volume("Copy",1180+10*Math.PI);
        cmd("Close");cmd("Open Primitives.FCStd");volume("Body",1180+10*Math.PI);python("d=App.ActiveDocument\nassert d.Bore.BaseFeature==d.Notch and d.Notch.BaseFeature==d.Boss and d.Boss.BaseFeature==d.Block and d.Body.Tip==d.Bore\nassert d.WorkPlane.AttachmentSupport[0][0]==d.Block and d.Marker.AttachmentSupport[0][0]==d.WorkPlane");
        cmd("NewDoc PrimitiveBudget");cmd("Body BudgetBody");
        for(int i=0;i<64;i++)cmd("BodyAddBox BudgetBody Block"+i+" 1 1 1 "+i+" 0 0 0 0 0");
        volume("BudgetBody",64);bad("BodyAddSphere BudgetBody TooManySphere 1 64 0 0 0 0 0");bad("BodyAddCone BudgetBody TooManyCone 1 0 2 64 0 0 0 0 0");bad("BodyAddBox BudgetBody TooMany 1 1 1 64 0 0 0 0 0");check(cmd("BodyInfo BudgetBody").getJSONObject("body_inspection").getJSONArray("solid_history").length()==64,"Native primitive budget rollback");
        System.out.println("PASS original primitive JNI checks: "+checks);
    }
}
