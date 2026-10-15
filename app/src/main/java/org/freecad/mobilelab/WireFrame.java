// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;

/** Bounded world-space native edge data; only projected screen pixels use floats. */
final class WireFrame {
    final String[] labels; final double[][] curves; final int[] indices; final double cx,cy,cz,span; final int pointCount;
    WireFrame(JSONObject data) throws JSONException {
        JSONArray input=data.getJSONArray("curves");
        if(input.length()<1||input.length()>128)throw new IllegalArgumentException("Use1–128 native edges");
        labels=new String[input.length()];curves=new double[input.length()][];indices=new int[input.length()];
        double[] lo={Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY};
        double[] hi={Double.NEGATIVE_INFINITY,Double.NEGATIVE_INFINITY,Double.NEGATIVE_INFINITY};int total=0;
        for(int i=0;i<input.length();i++){
            JSONObject edge=input.getJSONObject(i);JSONArray points=edge.getJSONArray("points");
            indices[i]=edge.getInt("index");labels[i]=edge.optString("label",Integer.toString(indices[i]));
            if(indices[i]<1||points.length()<2||points.length()>8192-total)throw new IllegalArgumentException("Wire preview exceeds its edge/point limits");
            total+=points.length();curves[i]=new double[points.length()*3];
            for(int j=0;j<points.length();j++){
                JSONArray point=points.getJSONArray(j);if(point.length()!=3)throw new IllegalArgumentException("Use world XYZ points");
                for(int k=0;k<3;k++){
                    double value=point.getDouble(k);
                    if(!Double.isFinite(value)||Math.abs(value)>1000000)throw new IllegalArgumentException("Wire preview must stay within±1,000,000mm");
                    curves[i][j*3+k]=value;lo[k]=Math.min(lo[k],value);hi[k]=Math.max(hi[k],value);
                }
            }
        }
        pointCount=total;cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2;cz=(lo[2]+hi[2])/2;
        span=Math.max(1e-7,Math.max(hi[0]-lo[0],Math.max(hi[1]-lo[1],hi[2]-lo[2])));
    }
    float[] project(double x,double y,double z,int width,int height,float yaw,float pitch,float zoom,float panX,float panY){
        if(width<=0||height<=0||!Float.isFinite(yaw)||!Float.isFinite(pitch)||!Float.isFinite(zoom)||zoom<=0||!Float.isFinite(panX)||!Float.isFinite(panY))throw new IllegalArgumentException("Use a finite camera and positive viewport");
        double a=Math.toRadians(yaw),b=Math.toRadians(pitch),dx=x-cx,dy=y-cy,dz=z-cz;
        double right=Math.cos(a)*dx-Math.sin(a)*dy,forward=Math.sin(a)*dx+Math.cos(a)*dy;
        double up=Math.cos(b)*dz-Math.sin(b)*forward;
        double scale=Math.max(1,Math.min(width-64,height-64))*.5/span*zoom;
        return new float[]{(float)(width*.5+right*scale+panX),(float)(height*.5-up*scale+panY)};
    }
}
