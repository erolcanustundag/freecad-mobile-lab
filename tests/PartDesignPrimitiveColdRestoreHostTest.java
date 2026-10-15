// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignPrimitiveColdRestoreHostTest {
    static int checks;
    static JSONObject request(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));if(!r.getBoolean("ok"))throw new AssertionError(r.optString("error"));checks++;return r.getJSONObject("state");}
    public static void main(String[] a)throws Exception{
        System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);request(CoreCommandLine.parse("Open Primitives.FCStd"));
        JSONObject p=request(new JSONObject().put("op","python").put("code","import math\nd=App.ActiveDocument\nassert d.Block.TypeId=='PartDesign::AdditiveBox' and d.Boss.TypeId=='PartDesign::AdditiveCylinder'\nassert d.Notch.TypeId=='PartDesign::SubtractiveBox' and d.Bore.TypeId=='PartDesign::SubtractiveCylinder'\nassert d.Bore.BaseFeature==d.Notch and d.Notch.BaseFeature==d.Boss and d.Boss.BaseFeature==d.Block\nassert d.Body.Tip==d.Bore and abs(d.Bore.Shape.Volume-1180-10*math.pi)<1e-5\nassert d.WorkPlane.AttachmentSupport[0][0]==d.Block and d.Marker.AttachmentSupport[0][0]==d.WorkPlane")).getJSONObject("python").getJSONObject("console");if(!p.getString("error").isEmpty())throw new AssertionError(p.getString("error"));checks++;
        JSONObject shape=request(CoreCommandLine.parse("ShapeInfo Body")).getJSONObject("shape_inspection");if(!shape.getBoolean("valid")||shape.getInt("solids")!=1)throw new AssertionError("Restored original solid");checks++;
        request(CoreCommandLine.parse("Close"));System.out.println("PASS original primitive cold JVM checks: "+checks);
    }
}
