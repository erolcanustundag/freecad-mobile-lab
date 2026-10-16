// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignWedgeSectorColdRestoreHostTest {
    static int checks;
    static JSONObject request(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));if(!r.getBoolean("ok"))throw new AssertionError(r.optString("error"));checks++;return r.getJSONObject("state");}
    public static void main(String[] a)throws Exception{
        System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);request(CoreCommandLine.parse("Open WedgeSector.FCStd"));
        JSONObject p=request(new JSONObject().put("op","python").put("code","import math\nd=App.ActiveDocument\nassert d.Wedge.TypeId=='PartDesign::AdditiveWedge' and d.WedgeCut.TypeId=='PartDesign::SubtractiveWedge'\nassert d.WedgeCut.BaseFeature==d.Wedge and d.Cone.BaseFeature==d.WedgeCut and d.Sphere.BaseFeature==d.Cone\nassert d.ConeCut.BaseFeature==d.Sphere and d.SphereCut.BaseFeature==d.ConeCut and d.Body.Tip==d.SphereCut\nassert abs(d.SphereCut.Shape.Volume-9009-35*math.pi/48)<1e-5\nassert d.Cone.Angle.Value==180 and d.ConeCut.Angle.Value==90\nassert (d.Sphere.Angle1.Value,d.Sphere.Angle2.Value,d.Sphere.Angle3.Value)==(0,90,180)\nassert abs(d.Signed.Shape.Volume-14)<1e-6 and d.Signed.Xmin.Value==-2")).getJSONObject("python").getJSONObject("console");if(!p.getString("error").isEmpty())throw new AssertionError(p.getString("error"));checks++;
        JSONObject shape=request(CoreCommandLine.parse("ShapeInfo Body")).getJSONObject("shape_inspection");if(!shape.getBoolean("valid")||shape.getInt("solids")!=1)throw new AssertionError("Restored original solid");checks++;
        request(CoreCommandLine.parse("Close"));System.out.println("PASS original wedge/sector cold JVM checks: "+checks);
    }
}
