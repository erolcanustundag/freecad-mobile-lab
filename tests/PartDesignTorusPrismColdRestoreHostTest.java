// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignTorusPrismColdRestoreHostTest {
    static int checks;
    static JSONObject request(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));if(!r.getBoolean("ok"))throw new AssertionError(r.optString("error"));checks++;return r.getJSONObject("state");}
    public static void main(String[] a)throws Exception{
        System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);request(CoreCommandLine.parse("Open TorusPrism.FCStd"));
        JSONObject p=request(new JSONObject().put("op","python").put("code","import math\nd=App.ActiveDocument\nassert d.Boss.TypeId=='PartDesign::AdditivePrism' and d.Ring.TypeId=='PartDesign::AdditiveTorus'\nassert d.Notch.TypeId=='PartDesign::SubtractivePrism' and d.Channel.TypeId=='PartDesign::SubtractiveTorus'\nassert d.Boss.BaseFeature==d.Stock and d.Ring.BaseFeature==d.Boss and d.Notch.BaseFeature==d.Ring and d.Channel.BaseFeature==d.Notch\nassert d.Body.Tip==d.Channel and abs(d.Channel.Shape.Volume-8996-18*math.sqrt(3)-.25*math.pi**2)<1e-5\nassert d.LimitPrism.Polygon==32 and d.Triangle.Polygon==3\nassert (d.StandaloneRing.Angle1.Value,d.StandaloneRing.Angle2.Value,d.StandaloneRing.Angle3.Value)==(-180,180,360)")).getJSONObject("python").getJSONObject("console");if(!p.getString("error").isEmpty())throw new AssertionError(p.getString("error"));checks++;
        JSONObject shape=request(CoreCommandLine.parse("ShapeInfo Body")).getJSONObject("shape_inspection");if(!shape.getBoolean("valid")||shape.getInt("solids")!=1)throw new AssertionError("Restored original solid");checks++;
        request(CoreCommandLine.parse("Close"));System.out.println("PASS original torus/prism cold JVM checks: "+checks);
    }
}
