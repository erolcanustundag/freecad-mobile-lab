// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignPathAdapterHostTest {
    static int checks;
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
    static JSONObject call(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject cmd(String s)throws Exception{return call(CoreCommandLine.parse(s));}
    static void bad(String s)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(s).toString()));check(!r.getBoolean("ok"),"Must reject "+s);}
    static void python(String s)throws Exception{JSONObject c=call(new JSONObject().put("op","python").put("code",s)).getJSONObject("python").getJSONObject("console");check(c.getString("error").isEmpty(),c.getString("error"));}
    static void volume(String n,double v)throws Exception{JSONObject r=cmd("ShapeInfo "+n).getJSONObject("shape_inspection");check(r.getBoolean("valid")&&r.getInt("solids")==1,"Closed single solid "+n);check(Math.abs(r.getDouble("volume")-v)<0.001,"Analytic volume "+n+": "+r);}
    static void circle(String b,String s,double x,double y,double r,String plane,double z)throws Exception{cmd("BodySketch "+b+" "+s);cmd("SketchCircle "+s+" "+x+" "+y+" "+r);cmd("Constraint "+s+" Block 0");cmd("SketchPlane "+s+" "+plane+" 0 0 "+z);}
    static void pipe(String b,String n,boolean cut,boolean arc)throws Exception{
        cmd("Body "+b);
        if(cut){circle(b,b+"Base",0,0,6,"XY",0);cmd("Pad "+b+" "+b+"Base "+b+"Pad 10");}
        circle(b,b+"Profile",0,0,arc&&cut?0.5:1,"XY",cut?2:0);
        cmd("BodySketch "+b+" "+b+"Path");
        if(arc)cmd("SketchArc "+b+"Path "+(cut?-2:-5)+" 0 "+(cut?2:5)+" 0 90");
        else cmd("SketchLine "+b+"Path 0 0 0 6");
        cmd("Constraint "+b+"Path Block 0");cmd("SketchPlane "+b+"Path XZ 0 0 "+(cut?2:0));
        cmd((cut?"BodySubPipe ":"BodyAddPipe ")+b+" "+b+"Profile "+b+"Path Edge1 "+n);
    }
    public static void main(String[] a)throws Exception{
        System.load(a[3]);SignalProbe.capture();System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);check(SignalProbe.preserved(),"JVM signals retained");cmd("NewDoc Paths");
        double stock=360*Math.PI,helix=5*Math.PI*Math.PI;
        pipe("StraightBody","Straight",false,false);volume("StraightBody",6*Math.PI);
        pipe("ArcBody","Arc",false,true);volume("ArcBody",2.5*Math.PI*Math.PI);
        pipe("CutBody","Cut",true,false);volume("CutBody",stock-6*Math.PI);
        pipe("ArcCutBody","ArcCut",true,true);volume("ArcCutBody",stock-0.25*Math.PI*Math.PI);
        for(boolean cut:new boolean[]{false,true}){
            String b=cut?"HelixCutBody":"HelixBody",n=cut?"HelixCut":"Helix";cmd("Body "+b);
            if(cut){circle(b,b+"Base",0,0,6,"XY",0);cmd("Pad "+b+" "+b+"Base "+b+"Pad 10");}
            circle(b,b+"Profile",5,0,0.5,"XZ",cut?2:0);
            cmd((cut?"BodySubHelix ":"BodyAddHelix ")+b+" "+b+"Profile "+n+" 3 6");volume(b,cut?stock-helix:helix);
        }
        python("d=App.ActiveDocument\nassert d.Straight.TypeId=='PartDesign::AdditivePipe' and d.Cut.TypeId=='PartDesign::SubtractivePipe'\nassert d.Straight.Spine==(d.StraightBodyPath,['Edge1'])\nassert d.Helix.TypeId=='PartDesign::AdditiveHelix' and d.HelixCut.TypeId=='PartDesign::SubtractiveHelix'\nassert d.Helix.ReferenceAxis[0] in d.HelixBody.Origin.OriginFeatures\nassert d.Helix.ReferenceAxis[0].Role=='Z_Axis' and abs(d.Helix.Turns-2)<1e-8\nassert d.HelixCut.BaseFeature==d.HelixCutBodyPad and d.HelixCutBody.Tip==d.HelixCut");
        cmd("Set Helix.Pitch 4 mm");volume("HelixBody",3.75*Math.PI*Math.PI);cmd("Undo");volume("HelixBody",helix);cmd("Redo");volume("HelixBody",3.75*Math.PI*Math.PI);cmd("Undo");
        cmd("Set Helix.Height 0.9 cm");volume("HelixBody",7.5*Math.PI*Math.PI);cmd("Undo");
        cmd("Set HelixCut.Pitch 4 mm");volume("HelixCutBody",stock-3.75*Math.PI*Math.PI);cmd("Undo");
        cmd("Set HelixCut.Height 3 mm");volume("HelixCutBody",stock-2.5*Math.PI*Math.PI);cmd("Undo");
        bad("SketchPlane StraightBodyProfile XY 0 0 1");volume("StraightBody",6*Math.PI);
        cmd("DeleteConstraint StraightBodyProfile 0");cmd("Constraint StraightBodyProfile Radius 0 1");cmd("Datum StraightBodyProfile 0 0.5 mm");volume("StraightBody",1.5*Math.PI);cmd("Undo");volume("StraightBody",6*Math.PI);
        cmd("DeleteConstraint HelixBodyProfile 0");cmd("Constraint HelixBodyProfile Radius 0 0.5");cmd("Datum HelixBodyProfile 0 0.6 mm");volume("HelixBody",7.2*Math.PI*Math.PI);cmd("Undo");volume("HelixBody",helix);
        bad("Datum HelixBodyProfile 0 1.6 mm");volume("HelixBody",helix);
        bad("Expression HelixBodyProfile.Constraints[0] 100");
        cmd("PartPlacement HelixBody 1 2 3 20 30 40");volume("HelixBody",helix);cmd("Undo");
        cmd("Set HelixCutBodyPad.Length 12 mm");volume("HelixCutBody",432*Math.PI-helix);cmd("Undo");
        bad("SketchPlane HelixCutBodyProfile XZ 0 0 12");volume("HelixCutBody",stock-helix);
        for(String s:new String[]{"Set Helix.Pitch 0 mm","Set Helix.Pitch 1 mm","Set Helix.Pitch 0.000001 mm","Set Helix.Height 0 mm","Set Helix.Height 49 mm","Set Helix.Height 1000001 mm","Set Helix.Angle 2 deg","Set Helix.Mode 1","Set Helix.LeftHanded true","Set Helix.ReferenceAxis Z_Axis","Set Straight.Mode 1","Set Straight.Transition 1","Set Straight.SpineTangent true","Set Straight.Sections HelixBodyProfile","Remove HelixBodyProfile","Remove StraightBodyPath","Set Straight.Placement 0"})bad(s);
        volume("HelixBody",helix);volume("StraightBody",6*Math.PI);
        cmd("Body EmptyBody");circle("EmptyBody","EmptyProfile",5,0,0.5,"XZ",0);bad("BodySubHelix EmptyBody EmptyProfile NoStock 3 6");
        bad("BodyAddHelix EmptyBody HelixBodyProfile Foreign 3 6");bad("BodyAddHelix HelixBody HelixBodyProfile Reused 3 6");
        cmd("BodySketch EmptyBody BadCircle");cmd("SketchLine BadCircle 0 0 1 0");bad("BodyAddHelix EmptyBody BadCircle OpenHelix 3 6");
        circle("EmptyBody","WrongPlane",5,0,0.5,"XY",0);bad("BodyAddHelix EmptyBody WrongPlane WrongHelix 3 6");
        circle("EmptyBody","CrossAxis",0,0,0.5,"XZ",0);bad("BodyAddHelix EmptyBody CrossAxis AxisHelix 3 6");
        circle("EmptyBody","UnusedProfile",0,0,1,"XY",0);
        bad("BodyAddPipe EmptyBody UnusedProfile StraightBodyPath Edge1 ForeignPath");bad("BodyAddPipe StraightBody StraightBodyProfile StraightBodyPath Edge2 MissingEdge");
        cmd("Begin AtomicPaths");cmd("Set Helix.Pitch 4 mm");bad("Set HelixCut.Height 100 mm");volume("HelixBody",helix);
        cmd("Save Paths.FCStd");
        python("import zipfile,xml.etree.ElementTree as ET,mobile_core\nroot=mobile_core._root\nwith zipfile.ZipFile(root/'Paths.FCStd') as z:saved={n:z.read(n) for n in z.namelist()}\ndef path_fixture(filename,obj,prop,tag,value):\n    tree=ET.fromstring(saved['Document.xml'])\n    node=tree.find(\"./ObjectData/Object[@name='\"+obj+\"']/Properties/Property[@name='\"+prop+\"']/\"+tag)\n    assert node is not None\n    node.set('value',value)\n    xml=ET.tostring(tree)\n    with zipfile.ZipFile(root/('BadPath'+filename+'.FCStd'),'w') as z:\n        for n,b in saved.items():z.writestr(n,xml if n=='Document.xml' else b)");
        String[] changes={"'Pitch','Helix','Pitch','Float','0.000001'","'Height','Helix','Height','Float','1000001'","'Turns','Helix','Turns','Float','1000000'","'HelixMode','Helix','Mode','Integer','1'","'Cone','Helix','Angle','Float','2'","'Edited','Helix','HasBeenEdited','Bool','false'","'Handed','Helix','LeftHanded','Bool','true'","'Axis','Helix','ReferenceAxis','LinkSub','X_Axis'","'PipeMode','Straight','Mode','Integer','2'","'Transition','Straight','Transition','Integer','1'","'Transform','Straight','Transformation','Integer','1'","'ForeignPath','Straight','Spine','LinkSub','CutBodyPath'","'CyclePath','Straight','Spine','LinkSub','Straight'","'History','HelixCut','BaseFeature','Link','CutBodyPad'","'Profile','Helix','Profile','LinkSub','HelixCutBodyProfile'","'Suppressed','Straight','Suppressed','Bool','true'"};
        for(String mutation:changes)python("path_fixture("+mutation+")");
        String[] names={"Pitch","Height","Turns","HelixMode","Cone","Edited","Handed","Axis","PipeMode","Transition","Transform","ForeignPath","CyclePath","History","Profile","Suppressed"};
        for(String n:names)bad("Open BadPath"+n+".FCStd");volume("HelixBody",helix);
        cmd("ExportStep HelixCutBody HelixCut.step");cmd("ImportStep HelixCopy HelixCut.step");volume("HelixCopy",stock-helix);
        cmd("ExportStep ArcBody Arc.step");cmd("ImportStep ArcCopy Arc.step");volume("ArcCopy",2.5*Math.PI*Math.PI);
        cmd("RemoveBodyFeature HelixCutBody HelixCut");volume("HelixCutBody",stock);cmd("Undo");volume("HelixCutBody",stock-helix);
        cmd("BodyTip HelixCutBody HelixCutBodyPad");volume("HelixCutBody",stock);bad("BodySubHelix HelixCutBody EmptyProfile Branched 3 6");cmd("BodyTip HelixCutBody HelixCut");
        cmd("Close");cmd("Open Paths.FCStd");volume("HelixBody",helix);volume("HelixCutBody",stock-helix);volume("ArcBody",2.5*Math.PI*Math.PI);volume("ArcCutBody",stock-0.25*Math.PI*Math.PI);
        python("d=App.ActiveDocument\nassert d.Helix.ReferenceAxis[0].Role=='Z_Axis'\nassert d.HelixCutBody.Tip==d.HelixCut\nassert d.Arc.Spine==(d.ArcBodyPath,['Edge1'])");
        System.out.println("PASS original path JNI checks: "+checks);
    }
}
