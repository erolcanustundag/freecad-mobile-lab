// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.nio.file.*;

public final class PythonToolsHostTest {
    private static int count;
    private static void check(boolean condition,String reason){if(!condition)throw new AssertionError(reason);count++;}
    private static JSONObject call(JSONObject request)throws Exception{
        JSONObject result=new JSONObject(CoreNative.request(request.toString()));check(result.getBoolean("ok"),result.optString("error"));return result.getJSONObject("state");
    }
    private static JSONObject command(String line)throws Exception{return call(CoreCommandLine.parse(line));}
    private static JSONObject op(String name)throws Exception{return call(new JSONObject().put("op",name));}
    private static JSONObject script(String code)throws Exception{return call(new JSONObject().put("op","python").put("code",code));}
    private static JSONObject console(JSONObject state)throws Exception{return state.getJSONObject("python").getJSONObject("console");}
    private static void bad(JSONObject request)throws Exception{JSONObject r=new JSONObject(CoreNative.request(request.toString()));check(!r.getBoolean("ok"),"Expected a rejected operation");}
    private static double quantity(JSONObject state,String name,String property)throws Exception{
        JSONArray objects=state.getJSONObject("document").getJSONArray("objects");
        for(int i=0;i<objects.length();i++){JSONObject o=objects.getJSONObject(i);if(o.getString("name").equals(name)){JSONArray p=o.getJSONArray("properties");for(int j=0;j<p.length();j++)if(p.getJSONObject(j).getString("name").equals(property))return p.getJSONObject(j).getJSONObject("value").getDouble("value");}}
        throw new AssertionError("Missing property "+name+"."+property);
    }
    public static void main(String[] args)throws Exception{
        System.load(args[0]);CoreNative.initialize(args[1],args[2],args[1]);
        JSONObject s=command("Python print(App.Version()[:3])");check(console(s).getString("output").contains("'4'"),"Upstream Python bindings available");
        s=script("value = 7\nprint('Ölçü 💎')");check(console(s).getString("output").contains("Ölçü 💎"),"Console Unicode output");
        s=script("print(value * 6)");check(console(s).getString("output").contains("42"),"Persistent console namespace");
        s=script("1/0");check(console(s).getString("error").contains("ZeroDivisionError"),"Python traceback");
        s=script("while True: pass");check(console(s).getString("error").contains("tracing budget"),"Loop deadline");
        s=script("print('x' * 100000)");check(console(s).getString("output").length()==65536,"Bounded output");
        s=command("Api App.Vector");check(s.getJSONObject("python").getJSONObject("api").getJSONArray("members").length()>4,"Native API browser");
        bad(new JSONObject().put("op","api").put("target","App.__dict__"));
        op("record_start");command("NewDoc MacroSource");command("Add Source Feature");command("AddProperty Source Width Length");command("Set Source.Width 2 cm");
        command("AddProperty Source Enabled Bool");command("Set Source.Enabled true");command("AddProperty Source Count Integer");command("Set Source.Count 17");
        command("AddProperty Source Factor Float");command("Set Source.Factor 2.5");
        call(new JSONObject().put("op","record_stop").put("name","Recorded.py"));
        s=call(new JSONObject().put("op","macro_read").put("name","Recorded.py"));String recorded=s.getString("macro_source");
        check(recorded.contains("openTransaction"),"Recorder includes native edit transactions");
        check(recorded.contains("Enabled = True")&&recorded.contains("Count = 17")&&recorded.contains("Factor = 2.5"),"Recorder preserves typed values");
        command("Close");s=command("RunMacro Recorded.py");check(console(s).getString("error").isEmpty(),"Recorded native macro replay");check(Math.abs(quantity(s,"Source","Width")-20)<1e-9,"Recorded unit value");
        call(new JSONObject().put("op","macro_save").put("name","Edit.py").put("code","App.ActiveDocument.getObject('Source').Width = '32 mm'\nprint('changed')\n"));
        s=command("RunMacro Edit.py");check(Math.abs(quantity(s,"Source","Width")-32)<1e-9,"Saved macro edits upstream App");
        check(console(s).getString("output").contains("changed"),"Macro output");
        bad(new JSONObject().put("op","macro_save").put("name","../Bad.py").put("code","pass"));
        bad(new JSONObject().put("op","macro_save").put("name","Edit.py").put("code","if :"));
        s=call(new JSONObject().put("op","macro_read").put("name","Edit.py"));check(s.getString("macro_source").contains("32 mm"),"Bad macro edit preserves previous file");
        s=command("Proxy Scaled Source.Width 2");check(Math.abs(quantity(s,"Scaled","Output")-64)<1e-9,"Real FeaturePython execute");
        s=command("Set Source.Width 25 mm");check(Math.abs(quantity(s,"Scaled","Output")-50)<1e-9,"Proxy dependency recompute");
        s=command("Undo");check(Math.abs(quantity(s,"Scaled","Output")-64)<1e-9,"Proxy dependent Undo");s=command("Redo");check(Math.abs(quantity(s,"Scaled","Output")-50)<1e-9,"Proxy dependent Redo");
        command("Save Proxy.FCStd");check(Files.isRegularFile(Paths.get(args[1],"documents","Proxy.FCStd")),"Proxy native FCStd saved");command("Close");s=command("Open Proxy.FCStd");
        check(Math.abs(quantity(s,"Scaled","Output")-50)<1e-9,"Proxy FCStd output restored");
        s=command("Set Source.Width 21 mm");check(Math.abs(quantity(s,"Scaled","Output")-42)<1e-9,"Proxy class/state restored and recomputes");
        s=script("print(type(App.ActiveDocument.getObject('Scaled').Proxy).__module__)");check(console(s).getString("output").contains("mobile_features"),"Native proxy restoration module identity");
        bad(new JSONObject().put("op","batch").put("edits",new JSONArray().put(new JSONObject().put("op","proxy").put("name","Bad").put("source","Source").put("property","Factor").put("factor",2))));
        s=op("state");check(s.getJSONObject("document").getJSONArray("objects").length()==2,"Bad proxy creation rolls back");
        System.out.println("PASS: "+count+" upstream Python tooling assertions; Android runtime NOT_RUN");System.out.flush();System.exit(0);
    }
}
