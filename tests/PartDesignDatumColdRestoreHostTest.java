// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
/** Fresh JVM/interpreter: constructor caches and references cannot survive from the saver. */
public final class PartDesignDatumColdRestoreHostTest {
    static int checks;
    static JSONObject request(JSONObject q)throws Exception{JSONObject r=new JSONObject(CoreNative.request(q.toString()));if(!r.getBoolean("ok"))throw new AssertionError(r.optString("error"));checks++;return r.getJSONObject("state");}
    public static void main(String[] a)throws Exception{
        System.load(a[0]);CoreNative.initialize(a[1],a[2],a[1]);
        request(CoreCommandLine.parse("Open Datums.FCStd"));
        String code="d=App.ActiveDocument\nassert not d.WorkAxis.Shape.isNull() and d.WorkAxis.Shape.isValid()\nassert d.WorkAxis.TypeId=='PartDesign::Line'\nassert 'Transient' in d.WorkAxis.getPropertyStatus('Shape')\nassert d.WorkAxis.Shape.Edges[0].Curve.Direction.dot(d.WorkAxis.Placement.Rotation.multVec(App.Vector(0,0,1)))>1-1e-9\nassert (d.WorkAxis.Shape.Edges[0].Curve.Location-d.WorkAxis.Placement.Base).Length<1e-9\nassert d.Profile.AttachmentSupport[0][0]==d.WorkPlane\nassert d.FrameProfile.AttachmentSupport[0][0]==d.Frame\nassert d.Body.Tip==d.Pad and d.FrameBody.Tip==d.FramePad";
        JSONObject py=request(new JSONObject().put("op","python").put("code",code)).getJSONObject("python").getJSONObject("console");if(!py.getString("error").isEmpty())throw new AssertionError(py.getString("error"));checks+=8;
        JSONObject frame=request(CoreCommandLine.parse("DatumPreview WorkAxis")).getJSONObject("wire_preview");new WireFrame(frame);checks++;
        request(CoreCommandLine.parse("Close"));
        System.out.println("PASS original Datum cold JVM restoration checks: "+checks);
    }
}
