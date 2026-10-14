// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignAdapterHostTest {
    static int checks;
    static void check(boolean b,String why){if(!b)throw new AssertionError(why);checks++;}
    static JSONObject call(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));check(r.getBoolean("ok"),r.optString("error"));return r.getJSONObject("state");}
    static JSONObject cmd(String s)throws Exception{return call(CoreCommandLine.parse(s));}
    static void bad(String s)throws Exception{JSONObject r=new JSONObject(CoreNative.request(CoreCommandLine.parse(s).toString()));check(!r.getBoolean("ok"),"Must reject "+s);}
    static void python(String s)throws Exception{JSONObject c=call(new JSONObject().put("op","python").put("code",s)).getJSONObject("python").getJSONObject("console");check(c.getString("error").isEmpty(),c.getString("error"));}
    static void volume(String name,double expected)throws Exception{JSONObject v=cmd("ShapeInfo "+name).getJSONObject("shape_inspection");check(v.getBoolean("valid"),"Valid "+name);check(v.getInt("solids")==1,"One solid "+name);check(Math.abs(v.getDouble("volume")-expected)<1e-5,"Volume "+name+": "+v);}
    public static void main(String[] args)throws Exception{
        System.load(args[3]);SignalProbe.capture();System.load(args[0]);CoreNative.initialize(args[1],args[2],args[1]);check(SignalProbe.preserved(),"JVM signal handler preserved with original PartDesign");
        java.util.Locale previous=java.util.Locale.getDefault();try{for(java.util.Locale l:new java.util.Locale[]{java.util.Locale.US,new java.util.Locale("tr","TR"),java.util.Locale.GERMANY}){java.util.Locale.setDefault(l);for(String alias:new String[]{"Body","GÖVDE","Körper"})check(CoreCommandLine.parse(alias+" Body").getJSONArray("edits").getJSONObject(0).getString("op").equals("body_create"),"Localized Body alias");}}finally{java.util.Locale.setDefault(previous);}
        check(cmd("NewDoc BodyWorkflows").getBoolean("partdesign"),"Original PartDesign builtin loaded");cmd("Body Body");JSONObject b=cmd("BodyInfo Body").getJSONObject("body_inspection");check(b.getJSONArray("origin_features").length()==7,"Original origin frames");check(b.getBoolean("single_solid"),"Bounded single solid policy");
        python("b=App.ActiveDocument.Body\nassert b.TypeId=='PartDesign::Body'\nassert b.Origin.TypeId=='App::Origin'\nassert b.Tip is None\nassert len(App.ActiveDocument.Objects)==9");
        bad("Body Body");bad("Set Body.AllowCompound true");bad("Set Body.Tip Body");bad("Remove Body");bad("Remove Origin");bad("Set X_Axis.Placement 0");
        cmd("BodySketch Body Profile");cmd("SketchCircle Profile 0 0 10");cmd("Constraint Profile Block 0");cmd("Pad Body Profile Pad 10");volume("Pad",1000*Math.PI);volume("Body",1000*Math.PI);
        python("d=App.ActiveDocument\nassert d.Body.Tip==d.Pad\nassert d.Pad.Profile[0]==d.Profile\nassert d.Profile in d.Body.Group\nassert d.Pad.Type=='Length'\nassert d.Pad.SideType=='One side'");
        cmd("Set Pad.Length 2 cm");volume("Body",2000*Math.PI);cmd("Undo");volume("Body",1000*Math.PI);cmd("Redo");volume("Body",2000*Math.PI);cmd("Undo");
        for(String s:new String[]{"Set Pad.Length 0","Set Pad.Length -1","Set Pad.Length 1000001","Set Pad.BaseFeature Body","Expression Pad.Length 1000001","Remove Profile","Remove Pad","Pad Body Profile Duplicate 5","Pocket Body Profile BadPocket 2"})bad(s);
        cmd("BodySketch Body CutProfile");cmd("SketchCircle CutProfile 0 0 2");cmd("SketchPlane CutProfile XY 0 0 10");cmd("Constraint CutProfile Block 0");cmd("Pocket Body CutProfile Pocket 2");volume("Pocket",Math.PI*(1000-8));volume("Body",Math.PI*(1000-8));
        python("d=App.ActiveDocument\nassert d.Pocket.BaseFeature==d.Pad\nassert d.Body.Tip==d.Pocket");
        cmd("Set Pocket.Length 3 mm");volume("Body",Math.PI*(1000-12));cmd("Undo");volume("Body",Math.PI*(1000-8));cmd("Redo");cmd("Undo");
        cmd("BodyTip Body Pad");volume("Body",1000*Math.PI);cmd("BodySketch Body Later");cmd("SketchCircle Later 0 0 1");bad("Pad Body Later Branch 2");bad("RemoveBodyFeature Body Pocket");cmd("BodyTip Body Pocket");
        cmd("Body Other");cmd("BodySketch Other Foreign");cmd("SketchCircle Foreign 0 0 1");bad("Pad Body Foreign ForeignPad 2");bad("BodyTip Other Pad");bad("BodySketch Other Profile");bad("Pocket Other Foreign EmptyPocket 1");
        cmd("Sketch Loose");cmd("SketchCircle Loose 20 0 1");cmd("BodySketch Body Loose");cmd("SketchPlane Loose XY 0 0 10");bad("Pocket Body Loose NoCut 2");python("assert App.ActiveDocument.getObject('NoCut') is None\nassert App.ActiveDocument.Body.Tip==App.ActiveDocument.Pocket");
        cmd("Sketch Unowned");cmd("SketchCircle Unowned 0 0 1");bad("Pad Body Unowned UnownedPad 2");
        cmd("Add Solid Box");cmd("BodyFrom Solid ImportedBody");volume("ImportedBody",1000);JSONObject from=cmd("BodyInfo ImportedBody").getJSONObject("body_inspection");check(from.getString("base_source").equals("Solid"),"Linked original base source");check(from.getJSONArray("solid_history").length()==1,"Autogenerated FeatureBase");cmd("Set Solid.Length 15 mm");volume("ImportedBody",1500);bad("Remove Solid");bad("BodyFrom Body NestedBody");
        cmd("Add Round Cylinder");bad("BodyTip Body Round");
        cmd("Save Body.FCStd");cmd("ExportStep Body Body.step");cmd("ImportStep Roundtrip Body.step");volume("Roundtrip",Math.PI*(1000-8));
        cmd("RemoveBodyFeature Body Pocket");volume("Body",1000*Math.PI);cmd("Undo");volume("Body",Math.PI*(1000-8));cmd("Redo");cmd("Undo");
        cmd("Begin \"Atomic native edit\"");cmd("Set Pocket.Length 4 mm");cmd("Abort");volume("Body",Math.PI*(1000-8));
        int count=cmd("State").getJSONObject("document").getJSONArray("objects").length();JSONArray edits=new JSONArray().put(CoreCommandLine.parse("Body Temporary").getJSONArray("edits").getJSONObject(0)).put(CoreCommandLine.parse("Set Pad.Length 0").getJSONArray("edits").getJSONObject(0));JSONObject r=new JSONObject(CoreNative.request(new JSONObject().put("op","batch").put("edits",edits).toString()));check(!r.getBoolean("ok"),"Atomic rollback rejected");check(cmd("State").getJSONObject("document").getJSONArray("objects").length()==count,"Rollback removes autogenerated origin children");
        cmd("Close");cmd("Open Body.FCStd");volume("Body",Math.PI*(1000-8));volume("ImportedBody",1500);python("d=App.ActiveDocument\nassert d.Body.Tip==d.Pocket\nassert d.Pocket.Profile[0]==d.CutProfile\nassert d.ImportedBody.BaseFeature==d.Solid\nassert d.Pocket in d.Body.Group");
        check(SignalProbe.preserved(),"JVM signals preserved after full workflow");System.out.println("PASS: "+checks+" original PartDesign JNI workflow checks");
    }
}
