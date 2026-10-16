// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignTorusPrismAdapterHostTest {
    static int checks;
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
    static JSONObject call(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject cmd(String s)throws Exception{return call(CoreCommandLine.parse(s));}
    static void bad(String s)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(s).toString()));check(!r.getBoolean("ok"),"Must reject "+s);}
    static void python(String code)throws Exception{JSONObject r=call(new JSONObject().put("op","python").put("code",code)).getJSONObject("python").getJSONObject("console");check(r.getString("error").isEmpty(),r.getString("error"));}
    static void volume(String n,double expected)throws Exception{JSONObject r=cmd("ShapeInfo "+n).getJSONObject("shape_inspection");check(r.getBoolean("valid")&&r.getInt("solids")==1,"Closed original solid");check(Math.abs(r.getDouble("volume")-expected)<1e-5,"Analytic volume "+n+": "+r);}
    public static void main(String[] a)throws Exception{
        System.load(a[3]);SignalProbe.capture();System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);check(SignalProbe.preserved(),"JVM signals retained");cmd("NewDoc TorusPrism");cmd("Body Body");
        for(String s:new String[]{"BodySubPrism Body EmptyPrism 6 2 3","BodySubTorus Body EmptyTorus 2 0.5","BodyAddTorus Body Horn 1 1","BodyAddTorus Body Spindle 0.5 1","BodyAddTorus Body ZeroTube 2 0","BodyAddTorus Body NegativeTube 2 -1","BodyAddPrism Body FewSides 2 2 3","BodyAddPrism Body TooManySides 33 2 3","BodyAddPrism Body ZeroRadius 3 0 3","BodyAddPrism Body ZeroHeight 3 1 0"})bad(s);
        double original=8996+18*Math.sqrt(3)+0.25*Math.PI*Math.PI;
        cmd("BodyAddBox Body Stock 30 30 10");cmd("BodyAddPrism Body Boss 6 2 3 5 5 10 0 0 0");volume("Body",9000+18*Math.sqrt(3));
        cmd("BodyAddTorus Body Ring 2 0.5 20 20 10 0 0 0");volume("Body",9000+18*Math.sqrt(3)+0.5*Math.PI*Math.PI);
        cmd("BodySubPrism Body Notch 4 1 2 5 5 0 0 0 0");volume("Body",8996+18*Math.sqrt(3)+0.5*Math.PI*Math.PI);
        cmd("BodySubTorus Body Channel 2 0.25 20 20 5 0 0 0");volume("Body",original);
        python("d=App.ActiveDocument\nassert [o.TypeId for o in (d.Boss,d.Ring,d.Notch,d.Channel)]==['PartDesign::AdditivePrism','PartDesign::AdditiveTorus','PartDesign::SubtractivePrism','PartDesign::SubtractiveTorus']\nassert d.Boss.BaseFeature==d.Stock and d.Ring.BaseFeature==d.Boss and d.Notch.BaseFeature==d.Ring and d.Channel.BaseFeature==d.Notch and d.Body.Tip==d.Channel\nassert (d.Ring.Angle1.Value,d.Ring.Angle2.Value,d.Ring.Angle3.Value)==(-180,180,360) and d.Boss.FirstAngle.Value==0 and d.Boss.SecondAngle.Value==0");
        for(String s:new String[]{"BodyAddTorus Body InsideRing 2 0.5 10 10 5 0 0 0","BodyAddPrism Body InsidePrism 6 1 2 10 10 5 0 0 0","BodyAddTorus Body DetachedRing 2 0.5 100 100 100 0 0 0","BodyAddPrism Body DetachedPrism 6 1 2 100 100 100 0 0 0","BodySubTorus Body OutsideRing 2 0.5 100 100 100 0 0 0","BodySubPrism Body OutsidePrism 6 1 2 100 100 100 0 0 0","BodySubPrism Body WipePrism 4 100 100 5 5 -1 0 0 0","BodyPrimitivePose Body Ring 999999 0 0 0 0 0","BodyPrimitivePose Body Boss 999999 0 0 45 0 0","BodyPrimitivePose Body Channel 20 20 -1000000 0 0 0","Set Ring.Radius1 0.5 mm","Set Ring.Radius2 2 mm","Set Channel.Radius2 0 mm","Set Ring.Angle1 -90 deg","Set Ring.Angle2 90 deg","Set Channel.Angle3 180 deg","Set Boss.FirstAngle 1 deg","Set Notch.SecondAngle 1 deg","Set Boss.Polygon 2","Set Boss.Polygon 33","Set Boss.Polygon 4.5","Set Boss.Polygon 4 mm","Set Boss.Circumradius 0 mm","Set Boss.Height 0 mm","Set Boss.MapMode 1","Set Ring.Suppressed true","Set Channel.FuzzyTolerance 0","Expression Boss.Polygon 5","Expression Ring.Radius1 3","PartPlacement Ring 20 20 10 0 0 0"})bad(s);
        volume("Body",original);
        cmd("Set Ring.Radius1 0.3 cm");volume("Body",8996+18*Math.sqrt(3)+0.5*Math.PI*Math.PI);cmd("Undo");cmd("Redo");cmd("Undo");
        cmd("Set Ring.Radius2 0.1 cm");volume("Body",8996+18*Math.sqrt(3)+1.75*Math.PI*Math.PI);cmd("Undo");
        cmd("Set Boss.Polygon 4");volume("Body",9020+0.25*Math.PI*Math.PI);cmd("Undo");
        cmd("Set Boss.Circumradius 0.3 cm");volume("Body",8996+40.5*Math.sqrt(3)+0.25*Math.PI*Math.PI);cmd("Undo");
        cmd("Set Notch.Polygon 3");volume("Body",9000+16.5*Math.sqrt(3)+0.25*Math.PI*Math.PI);cmd("Undo");
        cmd("Set Stock.Length 31 mm");volume("Body",original+300);cmd("Undo");
        cmd("BodyPrimitivePose Body Boss 5 5 10 30 0 0");volume("Body",original);cmd("Undo");
        cmd("PartPlacement Body 1 2 3 30 20 10");volume("Body",original);cmd("Undo");bad("PartPlacement Body 999999 0 0 0 0 0");
        cmd("BodyTip Body Stock");bad("BodyAddPrism Body Branched 6 2 3 5 5 10 0 0 0");cmd("BodyTip Body Channel");
        cmd("Begin TorusAtomic");cmd("Set Stock.Length 31 mm");bad("BodyPrimitivePose Body Ring 20 20 100 0 0 0");volume("Body",original);python("assert abs(App.ActiveDocument.Stock.Length.Value-30)<1e-8");
        cmd("Body BoundaryBody");cmd("BodyAddPrism BoundaryBody LimitPrism 32 2 3");volume("BoundaryBody",192*Math.sin(Math.PI/16));
        cmd("Body TriangleBody");cmd("BodyAddPrism TriangleBody Triangle 3 2 3");volume("TriangleBody",9*Math.sqrt(3));
        cmd("Body RingBody");cmd("BodyAddTorus RingBody StandaloneRing 2 0.5");volume("RingBody",Math.PI*Math.PI);bad("BodyPrimitivePose Body StandaloneRing 20 20 10 0 0 0");
        cmd("RemoveBodyFeature Body Channel");volume("Body",original+0.25*Math.PI*Math.PI);cmd("Undo");volume("Body",original);
        cmd("Save TorusPrism.FCStd");Process cold=new ProcessBuilder(System.getProperty("java.home")+"/bin/java","-cp",System.getProperty("java.class.path"),"org.freecad.mobilelab.PartDesignTorusPrismColdRestoreHostTest",a[0],a[1],a[2]).inheritIO().start();check(cold.waitFor()==0,"Original torus/prism cold restoration");
        python("import zipfile,xml.etree.ElementTree as ET,mobile_core\nroot=mobile_core._root\nwith zipfile.ZipFile(root/'TorusPrism.FCStd') as z:saved={n:z.read(n) for n in z.namelist()}\ndef torus_prism_fixture(filename,obj,prop,tag,key,value):\n    tree=ET.fromstring(saved['Document.xml'])\n    node=tree.find(\"./ObjectData/Object[@name='\"+obj+\"']/Properties/Property[@name='\"+prop+\"']/\"+tag)\n    assert node is not None\n    node.set(key,value)\n    xml=ET.tostring(tree)\n    with zipfile.ZipFile(root/('BadTorusPrism'+filename+'.FCStd'),'w') as z:\n        for n,b in saved.items():z.writestr(n,xml if n=='Document.xml' else b)");
        String[] changes={"'PolygonLow','Boss','Polygon','Integer','value','2'","'PolygonHigh','Notch','Polygon','Integer','value','33'","'PolygonFraction','Boss','Polygon','Integer','value','4.5'","'PolygonExponent','Boss','Polygon','Integer','value','3e1'","'Horn','Ring','Radius1','Float','value','0.5'","'TubeZero','Channel','Radius2','Float','value','0'","'TubeNan','Channel','Radius2','Float','value','nan'","'Radius','Boss','Circumradius','Float','value','0'","'Height','Boss','Height','Float','value','1000001'","'Angle1','Ring','Angle1','Float','value','-90'","'Angle2','Ring','Angle2','Float','value','90'","'Angle3','Channel','Angle3','Float','value','180'","'FirstAngle','Boss','FirstAngle','Float','value','1'","'SecondAngle','Notch','SecondAngle','Float','value','1'","'Mode','Ring','MapMode','Integer','value','2'","'Offset','Boss','AttachmentOffset','PropertyPlacement','Px','1'","'Tolerance','Channel','FuzzyTolerance','Float','value','0'","'RingBounds','Ring','Placement','PropertyPlacement','Px','1000000'","'PrismBounds','Boss','Placement','PropertyPlacement','Px','1000000'","'BodyBounds','Body','Placement','PropertyPlacement','Px','999999'","'History','Channel','BaseFeature','Link','value','Stock'","'Foreign','Channel','BaseFeature','Link','value','StandaloneRing'"};
        for(String mutation:changes)python("torus_prism_fixture("+mutation+")");
        for(String n:new String[]{"PolygonLow","PolygonHigh","PolygonFraction","PolygonExponent","Horn","TubeZero","TubeNan","Radius","Height","Angle1","Angle2","Angle3","FirstAngle","SecondAngle","Mode","Offset","Tolerance","RingBounds","PrismBounds","BodyBounds","History","Foreign"})bad("Open BadTorusPrism"+n+".FCStd");
        volume("Body",original);cmd("ExportStep Body TorusPrism.step");cmd("ImportStep Copy TorusPrism.step");volume("Copy",original);
        cmd("Close");cmd("Open TorusPrism.FCStd");volume("Body",original);volume("BoundaryBody",192*Math.sin(Math.PI/16));
        System.out.println("PASS original torus/prism JNI checks: "+checks);
    }
}
