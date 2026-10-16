// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignWedgeSectorAdapterHostTest {
    static int checks;
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
    static JSONObject call(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject cmd(String s)throws Exception{return call(CoreCommandLine.parse(s));}
    static void bad(String s)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(s).toString()));check(!r.getBoolean("ok"),"Must reject "+s);}
    static void python(String code)throws Exception{JSONObject r=call(new JSONObject().put("op","python").put("code",code)).getJSONObject("python").getJSONObject("console");check(r.getString("error").isEmpty(),r.getString("error"));}
    static void volume(String n,double expected)throws Exception{JSONObject r=cmd("ShapeInfo "+n).getJSONObject("shape_inspection");check(r.getBoolean("valid")&&r.getInt("solids")==1,"Closed original solid");check(Math.abs(r.getDouble("volume")-expected)<1e-5,"Analytic volume "+n+": "+r);}
    public static void main(String[] a)throws Exception{
        System.load(a[3]);SignalProbe.capture();System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);check(SignalProbe.preserved(),"JVM signals retained");cmd("NewDoc WedgeSector");cmd("Body Body");
        bad("BodySubWedge Body Empty 0 2 0 3 0 2 0 1 0 2");
        for(String s:new String[]{"BodyAddWedge Body ZeroX 0 0 0 3 0 2 0 1 0 2","BodyAddWedge Body ReverseY 0 2 3 0 0 2 0 1 0 2","BodyAddWedge Body ZeroEndX 0 2 0 3 0 2 1 1 0 2","BodyAddWedge Body ReverseEndZ 0 2 0 3 0 2 0 1 2 0","BodyAddWedge Body Huge 0 1000001 0 3 0 2 0 1 0 2"})bad(s);
        cmd("BodyAddBox Body Stock 30 30 10");cmd("BodyAddWedge Body Wedge 0 4 0 3 0 2 0 2 0 2 5 5 10 0 0 0");volume("Body",9018);
        cmd("BodySubWedge Body WedgeCut 0 2 0 3 0 2 0 1 0 2 5 5 0 0 0 0");volume("Body",9009);
        cmd("BodyAddCone Body Cone 1 0 3 20 20 10 0 0 0");cmd("BodyConeAngle Body Cone 180");volume("Body",9009+0.5*Math.PI);
        cmd("BodyAddSphere Body Sphere 1 10 20 10 0 0 0");cmd("BodySphereAngles Body Sphere 0 90 180");volume("Body",9009+5*Math.PI/6);
        cmd("BodySubCone Body ConeCut 0.5 0 3 20 20 0 0 0 0");cmd("BodyConeAngle Body ConeCut 90");volume("Body",9009+37*Math.PI/48);
        cmd("BodySubSphere Body SphereCut 0.5 10 20 5 0 0 0");cmd("BodySphereAngles Body SphereCut -90 0 180");double original=9009+35*Math.PI/48;volume("Body",original);
        python("d=App.ActiveDocument\nassert d.Wedge.TypeId=='PartDesign::AdditiveWedge' and d.WedgeCut.TypeId=='PartDesign::SubtractiveWedge'\nassert d.Wedge.BaseFeature==d.Stock and d.WedgeCut.BaseFeature==d.Wedge and d.Cone.BaseFeature==d.WedgeCut and d.Sphere.BaseFeature==d.Cone\nassert d.ConeCut.BaseFeature==d.Sphere and d.SphereCut.BaseFeature==d.ConeCut and d.Body.Tip==d.SphereCut\nassert d.Cone.Angle.Value==180 and d.Sphere.Angle1.Value==0 and d.Sphere.Angle3.Value==180");
        for(String s:new String[]{"BodyConeAngle Body Cone 0","BodyConeAngle Body Cone 361","BodyConeAngle Body Wedge 90","BodyConeAngle Body Sphere 90","BodySphereAngles Body Cone 0 90 180","BodySphereAngles Body Sphere 30 30 180","BodySphereAngles Body Sphere 90 0 180","BodySphereAngles Body Sphere -91 90 180","BodySphereAngles Body Sphere 0 91 180","BodySphereAngles Body Sphere 0 90 0","BodySphereAngles Body Sphere 0 90 361","BodySphereAngles Body Sphere -90 0 180","Set Wedge.Xmax 0 mm","Set Wedge.Ymax 0 mm","Set Wedge.Z2max 0 mm","Set Wedge.X2min 2 mm","Set Wedge.Xmin -1000001 mm","Set Cone.Angle 90 deg","Set Sphere.Angle2 30 deg","Set Wedge.MapMode 1","Expression Wedge.Xmax 6","BodyAddWedge Body Inside 0 2 0 3 0 2 0 1 0 2 10 10 2 0 0 0","BodyAddWedge Body Detached 0 2 0 3 0 2 0 1 0 2 100 100 100 0 0 0","BodySubWedge Body Outside 0 2 0 3 0 2 0 1 0 2 100 100 100 0 0 0","BodySubWedge Body Wipe 0 100 0 100 0 100 0 100 0 100 -1 -1 -1 0 0 0","BodyPrimitivePose Body Wedge 999999 0 0 45 0 0"})bad(s);
        volume("Body",original);
        cmd("Set Stock.Height 10.2 mm");volume("Body",9187.2+(2164.0/3375-5.0/48)*Math.PI);cmd("Undo");bad("Set Stock.Height 12 mm");
        cmd("Set Wedge.Xmax 0.6 cm");volume("Body",original+6);cmd("Undo");cmd("Redo");cmd("Undo");
        cmd("Set Wedge.X2max 0.3 cm");volume("Body",original+3);cmd("Undo");
        cmd("Set WedgeCut.Xmax 3 mm");volume("Body",original-3);cmd("Undo");
        cmd("BodyConeAngle Body Cone 90");volume("Body",original-Math.PI/4);cmd("Undo");
        cmd("BodySphereAngles Body Sphere 0 30 180");volume("Body",9009+5*Math.PI/8);cmd("Undo");
        cmd("PartPlacement Body 1 2 3 30 20 10");volume("Body",original);cmd("Undo");
        cmd("Begin WedgeAtomic");cmd("Set Wedge.Xmax 6 mm");bad("BodySphereAngles Body Sphere -90 0 180");volume("Body",original);python("assert abs(App.ActiveDocument.Wedge.Xmax.Value-4)<1e-8");
        cmd("Body OtherBody");cmd("BodyAddCone OtherBody OtherCone 1 0 3");bad("BodyConeAngle Body OtherCone 180");
        cmd("Body SignedBody");cmd("BodyAddWedge SignedBody Signed -2 2 -1 2 -1 1 3 5 2 3");volume("SignedBody",14);cmd("Set Signed.Xmin -0.3 cm");volume("SignedBody",16.5);cmd("Undo");
        cmd("RemoveBodyFeature Body SphereCut");volume("Body",original+Math.PI/24);cmd("Undo");
        cmd("Save WedgeSector.FCStd");Process cold=new ProcessBuilder(System.getProperty("java.home")+"/bin/java","-cp",System.getProperty("java.class.path"),"org.freecad.mobilelab.PartDesignWedgeSectorColdRestoreHostTest",a[0],a[1],a[2]).inheritIO().start();check(cold.waitFor()==0,"Original wedge/sector cold restoration");
        python("import zipfile,xml.etree.ElementTree as ET,mobile_core\nroot=mobile_core._root\nwith zipfile.ZipFile(root/'WedgeSector.FCStd') as z:saved={n:z.read(n) for n in z.namelist()}\ndef wedge_sector_fixture(filename,obj,prop,tag,key,value):\n    tree=ET.fromstring(saved['Document.xml'])\n    node=tree.find(\"./ObjectData/Object[@name='\"+obj+\"']/Properties/Property[@name='\"+prop+\"']/\"+tag)\n    assert node is not None\n    node.set(key,value)\n    xml=ET.tostring(tree)\n    with zipfile.ZipFile(root/('BadWedgeSector'+filename+'.FCStd'),'w') as z:\n        for n,b in saved.items():z.writestr(n,xml if n=='Document.xml' else b)");
        String[] changes={"'ZeroX','Wedge','Xmax','Float','value','0'","'EndX','Wedge','X2min','Float','value','2'","'SignedNan','Signed','Xmin','Float','value','nan'","'Y','Wedge','Ymax','Float','value','0'","'Z','WedgeCut','Z2max','Float','value','0'","'ConeZero','Cone','Angle','Float','value','0'","'ConeMax','Cone','Angle','Float','value','361'","'SphereLatLow','Sphere','Angle1','Float','value','-91'","'SphereLatHigh','Sphere','Angle2','Float','value','91'","'SphereOrder','Sphere','Angle2','Float','value','0'","'SphereZero','Sphere','Angle3','Float','value','0'","'SphereMax','Sphere','Angle3','Float','value','361'","'Offset','Wedge','AttachmentOffset','PropertyPlacement','Px','1'","'WedgeBounds','Wedge','Placement','PropertyPlacement','Px','1000000'","'BodyBounds','Body','Placement','PropertyPlacement','Px','999999'","'History','WedgeCut','BaseFeature','Link','value','Cone'","'Foreign','WedgeCut','BaseFeature','Link','value','OtherCone'"};
        for(String mutation:changes)python("wedge_sector_fixture("+mutation+")");
        for(String n:new String[]{"ZeroX","EndX","SignedNan","Y","Z","ConeZero","ConeMax","SphereLatLow","SphereLatHigh","SphereOrder","SphereZero","SphereMax","Offset","WedgeBounds","BodyBounds","History","Foreign"})bad("Open BadWedgeSector"+n+".FCStd");
        volume("Body",original);cmd("ExportStep Body WedgeSector.step");cmd("ImportStep Copy WedgeSector.step");volume("Copy",original);
        cmd("Close");cmd("Open WedgeSector.FCStd");volume("Body",original);volume("SignedBody",14);
        System.out.println("PASS original wedge/sector JNI checks: "+checks);
    }
}
