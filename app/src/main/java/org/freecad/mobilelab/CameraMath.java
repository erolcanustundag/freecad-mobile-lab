package org.freecad.mobilelab;
/** Camera math shared by touch picking and software projections. */
final class CameraMath {
    static float[] preset(String type){switch(type){case "Top":return new float[]{0,0};case "Bottom":return new float[]{0,180};case "Front":return new float[]{0,-90};case "Back":return new float[]{180,-90};case "Right":return new float[]{-90,-90};case "Left":return new float[]{90,-90};default:return new float[]{-32,-58};}}
    static double[] ray(MeshFrame mesh,int width,int height,float yaw,float pitch,float zoom,float panX,float panY,boolean ortho,float sx,float sy){
        if(mesh==null||width<1||height<1)throw new IllegalArgumentException("Empty view");double aspect=(double)width/height,d=mesh.radius*3.4*Math.max(.35,zoom)/Math.min(1,aspect),scale=height/(2*Math.tan(Math.toRadians(21))),px=(sx-width*.5)/scale*d,py=(height*.5-sy)/scale*d;
        double[] o=inverse(yaw,pitch,panX+(ortho?px:0),panY+(ortho?py:0),d),v=inverse(yaw,pitch,ortho?0:px,ortho?0:py,-d);double length=Math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);return new double[]{o[0]+mesh.x,o[1]+mesh.y,o[2]+mesh.z,v[0]/length,v[1]/length,v[2]/length,6*d/scale};
    }
    static double[] inverse(float yaw,float pitch,double x,double y,double z){double a=Math.toRadians(yaw),b=Math.toRadians(pitch),ry=Math.cos(b)*y+Math.sin(b)*z,rz=-Math.sin(b)*y+Math.cos(b)*z;return new double[]{Math.cos(a)*x+Math.sin(a)*ry,-Math.sin(a)*x+Math.cos(a)*ry,rz};}
}
