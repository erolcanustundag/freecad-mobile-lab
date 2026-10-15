// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
public final class PartDesignAttachmentColdRestoreHostTest {
    static int checks;
    static JSONObject request(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));if(!r.getBoolean("ok"))throw new AssertionError(r.optString("error"));checks++;return r.getJSONObject("state");}
    public static void main(String[] a)throws Exception{
        System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);request(CoreCommandLine.parse("Open Attachments.FCStd"));
        String code="import math\nd=App.ActiveDocument\nassert d.Plane.MapMode=='FlatFace' and d.Axis.MapMode=='Tangent' and d.Point.MapMode=='Vertex'\nfor o in (d.Plane,d.Axis,d.Point):assert o.AttachmentSupport[0][0]==d.Stock\nassert len(d.Axis.Shape.Edges)==1 and not d.Axis.Shape.Vertexes and 'Transient' in d.Axis.getPropertyStatus('Shape')\nassert d.Profile.AttachmentSupport[0][0]==d.Plane and abs(d.Profile.AttachmentOffset.Base.x-2)<1e-8\nassert abs(d.Boss.Shape.Volume-1200-4*math.pi)<1e-5 and d.Body.Tip==d.Boss";
        JSONObject r=request(new JSONObject().put("op","python").put("code",code)).getJSONObject("python").getJSONObject("console");if(!r.getString("error").isEmpty())throw new AssertionError(r.getString("error"));checks++;
        for(String n:new String[]{"Plane","Axis","Point"}){new WireFrame(request(CoreCommandLine.parse("DatumPreview "+n)).getJSONObject("wire_preview"));checks++;}
        request(CoreCommandLine.parse("Close"));System.out.println("PASS original attachment cold JVM checks: "+checks);
    }
}
