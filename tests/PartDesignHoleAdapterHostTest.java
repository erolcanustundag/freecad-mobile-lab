// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignHoleAdapterHostTest {
    static int checks;
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
    static JSONObject call(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject cmd(String s)throws Exception{return call(CoreCommandLine.parse(s));}
    static void bad(String s)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(s).toString()));check(!r.getBoolean("ok"),"Must reject "+s);}
    static void python(String s)throws Exception{JSONObject c=call(new JSONObject().put("op","python").put("code",s)).getJSONObject("python").getJSONObject("console");check(c.getString("error").isEmpty(),c.getString("error"));}
    static void volume(String n,double v)throws Exception{JSONObject r=cmd("ShapeInfo "+n).getJSONObject("shape_inspection");check(r.getBoolean("valid")&&r.getInt("solids")==1,"Closed single solid "+n);check(Math.abs(r.getDouble("volume")-v)<0.00001,"Analytic volume "+n+": "+r);}
    static void circle(String b,String s,double x,double y,double r,String plane,double z)throws Exception{cmd("BodySketch "+b+" "+s);cmd("SketchCircle "+s+" "+x+" "+y+" "+r);cmd("Constraint "+s+" Block 0");cmd("SketchPlane "+s+" "+plane+" 0 0 "+z);}
    public static void main(String[] a)throws Exception{
        System.load(a[3]);SignalProbe.capture();System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);check(SignalProbe.preserved(),"JVM signals retained");cmd("NewDoc Holes");
        for(String n:new String[]{"Blind","Through","Bore","Sink"}){
            cmd("Body "+n+"Body");circle(n+"Body",n+"Base",0,0,6,"XY",0);cmd("Pad "+n+"Body "+n+"Base "+n+"Pad 10");circle(n+"Body",n+"Profile",0,0,1,"XY",10);
        }
        double stock=360*Math.PI;
        cmd("BodyHole BlindBody BlindProfile Blind 2 4");volume("BlindBody",stock-4*Math.PI);
        cmd("BodyHoleThrough ThroughBody ThroughProfile Through 2");volume("ThroughBody",stock-10*Math.PI);
        cmd("BodyCounterbore BoreBody BoreProfile Bore 2 4 4 1");volume("BoreBody",stock-7*Math.PI);
        cmd("BodyCountersink SinkBody SinkProfile Sink 2 4 4");volume("SinkBody",stock-16*Math.PI/3);
        python("d=App.ActiveDocument\nassert all(getattr(d,n).TypeId=='PartDesign::Hole' for n in ['Blind','Through','Bore','Sink'])\nassert d.Blind.Profile[0]==d.BlindProfile and d.Blind.BaseFeature==d.BlindPad\nassert d.Bore.HoleCutType=='Counterbore' and d.Sink.HoleCutType=='Countersink'\nassert d.Through.DepthType=='ThroughAll' and d.Blind.DrillPoint=='Flat'\nassert not d.Blind.Threaded and not d.Blind.ModelThread");
        cmd("Set Blind.Diameter 3 mm");volume("BlindBody",stock-9*Math.PI);cmd("Undo");volume("BlindBody",stock-4*Math.PI);cmd("Redo");volume("BlindBody",stock-9*Math.PI);cmd("Undo");
        cmd("Set Blind.Depth 0.5 cm");volume("BlindBody",stock-5*Math.PI);cmd("Undo");
        cmd("Set Through.Diameter 3 mm");volume("ThroughBody",stock-22.5*Math.PI);cmd("Undo");bad("Set Through.Depth 5 mm");
        cmd("Set Bore.HoleCutDiameter 6 mm");volume("BoreBody",stock-12*Math.PI);cmd("Undo");
        cmd("Set Bore.HoleCutDepth 2 mm");volume("BoreBody",stock-10*Math.PI);cmd("Undo");
        cmd("Set Bore.Diameter 3 mm");volume("BoreBody",stock-10.75*Math.PI);cmd("Undo");
        cmd("Set Sink.Diameter 3 mm");volume("SinkBody",stock-113*Math.PI/12);cmd("Undo");
        cmd("Set Sink.HoleCutDiameter 6 mm");volume("SinkBody",stock-32*Math.PI/3);cmd("Undo");
        cmd("Set Sink.Depth 6 mm");volume("SinkBody",stock-22*Math.PI/3);cmd("Undo");
        cmd("PartPlacement BoreBody 1 2 3 20 30 40");volume("BoreBody",stock-7*Math.PI);cmd("Undo");
        cmd("SketchPlane BlindProfile XY 0 0 8");volume("BlindBody",stock-4*Math.PI);cmd("Undo");bad("SketchPlane BlindProfile XY 0 0 0");volume("BlindBody",stock-4*Math.PI);
        bad("SketchPlane BlindProfile XZ 0 0 10");volume("BlindBody",stock-4*Math.PI);
        cmd("Set ThroughPad.Length 20 mm");volume("ThroughBody",720*Math.PI-10*Math.PI);cmd("SketchPlane ThroughProfile XY 0 0 20");volume("ThroughBody",720*Math.PI-20*Math.PI);cmd("Undo");cmd("Undo");
        cmd("DeleteConstraint BlindProfile 0");cmd("Constraint BlindProfile Radius 0 1");cmd("Datum BlindProfile 0 2 mm");volume("BlindBody",stock-4*Math.PI);cmd("Undo");
        for(String s:new String[]{"Set Blind.Diameter 0 mm","Set Blind.Depth 0 mm","Set Blind.Depth 1000001 mm","Set Bore.HoleCutDiameter 1 mm","Set Bore.Diameter 5 mm","Set Bore.HoleCutDepth 4 mm","Set Bore.Depth 0.5 mm","Set Sink.HoleCutDiameter 10 mm","Set Sink.HoleCutDepth 2 mm","Set Blind.Threaded true","Set Blind.ModelThread true","Set Blind.Reversed true","Set Blind.DrillPoint 1","Set Blind.HoleCutType 1","Set Blind.DepthType 1","Set Blind.Tapered true","Set Blind.DrillPointAngle 120 deg","Set Blind.ThreadDepth 100 mm","Remove BlindProfile","Set Blind.Placement 0"})bad(s);
        cmd("Body EmptyBody");circle("EmptyBody","EmptyProfile",0,0,1,"XY",10);bad("BodyHole EmptyBody EmptyProfile EmptyHole 2 4");bad("BodyHole BoreBody EmptyProfile ForeignHole 2 4");bad("BodyHole BlindBody BlindProfile ReusedHole 2 4");
        circle("BlindBody","OutsideProfile",20,0,1,"XY",10);bad("BodyHole BlindBody OutsideProfile NoCut 2 4");
        circle("ThroughBody","AllProfile",0,0,1,"XY",10);bad("BodyHoleThrough ThroughBody AllProfile EmptyResult 20");
        cmd("BodyTip BoreBody BorePad");circle("BoreBody","UnusedProfile",0,0,1,"XY",10);bad("BodyHole BoreBody UnusedProfile Branched 2 4");cmd("BodyTip BoreBody Bore");
        cmd("Begin AtomicHoles");cmd("Set Blind.Depth 6 mm");bad("Set Bore.HoleCutDepth 4 mm");volume("BlindBody",stock-4*Math.PI);
        cmd("Save Holes.FCStd");
        python("import zipfile,xml.etree.ElementTree as ET,mobile_core\nroot=mobile_core._root\nwith zipfile.ZipFile(root/'Holes.FCStd') as z:saved={n:z.read(n) for n in z.namelist()}\ndef hole_fixture(filename,obj,prop,tag,value):\n    tree=ET.fromstring(saved['Document.xml'])\n    node=tree.find(\"./ObjectData/Object[@name='\"+obj+\"']/Properties/Property[@name='\"+prop+\"']/\"+tag)\n    assert node is not None\n    node.set('value',value)\n    xml=ET.tostring(tree)\n    with zipfile.ZipFile(root/('BadHole'+filename+'.FCStd'),'w') as z:\n        for n,b in saved.items():z.writestr(n,xml if n=='Document.xml' else b)");
        String[] changes={"'Diameter','Blind','Diameter','Float','0'","'Depth','Blind','Depth','Float','1000001'","'Head','Bore','HoleCutDiameter','Float','1'","'HeadDepth','Bore','HoleCutDepth','Float','4'","'SinkDepth','Sink','Depth','Float','0.5'","'Threaded','Blind','Threaded','Bool','true'","'Model','Blind','ModelThread','Bool','true'","'ThreadType','Blind','ThreadType','Integer','1'","'ThreadDepth','Blind','ThreadDepth','Float','1000001'","'Taper','Blind','Tapered','Bool','true'","'Point','Blind','DrillPoint','Integer','1'","'Reverse','Blind','Reversed','Bool','true'","'Cut','Blind','HoleCutType','Integer','3'","'Mode','Blind','DepthType','Integer','2'","'Cone','Sink','HoleCutCountersinkAngle','Float','5'","'Custom','Bore','HoleCutCustomValues','Bool','false'","'History','Blind','BaseFeature','Link','BorePad'","'Profile','Blind','Profile','LinkSub','BoreProfile'","'Cycle','Blind','Profile','LinkSub','Blind'"};
        for(String mutation:changes)python("hole_fixture("+mutation+")");
        for(String n:new String[]{"Diameter","Depth","Head","HeadDepth","SinkDepth","Threaded","Model","ThreadType","ThreadDepth","Taper","Point","Reverse","Cut","Mode","Cone","Custom","History","Profile","Cycle"})bad("Open BadHole"+n+".FCStd");volume("BlindBody",stock-4*Math.PI);
        cmd("ExportStep BoreBody Bore.step");cmd("ImportStep BoreCopy Bore.step");volume("BoreCopy",stock-7*Math.PI);
        cmd("ExportStep SinkBody Sink.step");cmd("ImportStep SinkCopy Sink.step");volume("SinkCopy",stock-16*Math.PI/3);
        cmd("RemoveBodyFeature BlindBody Blind");volume("BlindBody",stock);cmd("Undo");volume("BlindBody",stock-4*Math.PI);cmd("Redo");volume("BlindBody",stock);cmd("Undo");
        cmd("Close");cmd("Open Holes.FCStd");volume("BlindBody",stock-4*Math.PI);volume("ThroughBody",stock-10*Math.PI);volume("BoreBody",stock-7*Math.PI);volume("SinkBody",stock-16*Math.PI/3);
        python("d=App.ActiveDocument\nassert d.BoreBody.Tip==d.Bore and d.Bore.BaseFeature==d.BorePad\nassert d.Sink.Profile[0]==d.SinkProfile and d.Sink.HoleCutCountersinkAngle.Value==90");
        System.out.println("PASS original Hole JNI checks: "+checks);
    }
}
