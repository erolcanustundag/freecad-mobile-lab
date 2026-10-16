// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignRoundPrimitiveColdRestoreHostTest {
    static int checks;
    static JSONObject request(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));if(!r.getBoolean("ok"))throw new AssertionError(r.optString("error"));checks++;return r.getJSONObject("state");}
    public static void main(String[] a)throws Exception{
        System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);request(CoreCommandLine.parse("Open RoundPrimitives.FCStd"));
        JSONObject p=request(new JSONObject().put("op","python").put("code","import math\nd=App.ActiveDocument\nassert d.Dome.TypeId=='PartDesign::AdditiveSphere' and d.Cone.TypeId=='PartDesign::AdditiveCone'\nassert d.SphereCut.TypeId=='PartDesign::SubtractiveSphere' and d.ConeCut.TypeId=='PartDesign::SubtractiveCone'\nassert d.Dome.BaseFeature==d.Stock and d.Cone.BaseFeature==d.Dome and d.SphereCut.BaseFeature==d.Cone and d.ConeCut.BaseFeature==d.SphereCut\nassert d.Body.Tip==d.ConeCut and abs(d.ConeCut.Shape.Volume-1100-53*math.pi/108)<1e-5\nassert d.Equal.TypeId=='PartDesign::AdditiveCone' and d.Apex.Radius1.Value==0\nassert abs(d.Apex.Shape.Volume-4*math.pi)<1e-5 and abs(d.Equal.Shape.Volume-3*math.pi)<1e-5")).getJSONObject("python").getJSONObject("console");if(!p.getString("error").isEmpty())throw new AssertionError(p.getString("error"));checks++;
        JSONObject shape=request(CoreCommandLine.parse("ShapeInfo Body")).getJSONObject("shape_inspection");if(!shape.getBoolean("valid")||shape.getInt("solids")!=1)throw new AssertionError("Restored original solid");checks++;
        request(CoreCommandLine.parse("Close"));System.out.println("PASS original round primitive cold JVM checks: "+checks);
    }
}
