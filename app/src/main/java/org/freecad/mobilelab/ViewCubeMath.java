// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.util.*;

/** Shared projection and hit testing for the native mobile navigation cube. */
final class ViewCubeMath {
    static final String[] NAMES={"Right","Left","Back","Front","Top","Bottom"};
    static final double[][] NORMALS={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
    static final double[][][] FACES={{{1,-1,-1},{1,1,-1},{1,1,1},{1,-1,1}},{{-1,1,-1},{-1,-1,-1},{-1,-1,1},{-1,1,1}},{{1,1,-1},{-1,1,-1},{-1,1,1},{1,1,1}},{{-1,-1,-1},{1,-1,-1},{1,-1,1},{-1,-1,1}},{{-1,-1,1},{1,-1,1},{1,1,1},{-1,1,1}},{{-1,1,-1},{1,1,-1},{1,-1,-1},{-1,-1,-1}}};
    static double[] project(double[] v,float yaw,float pitch){double a=Math.toRadians(yaw),b=Math.toRadians(pitch),x=Math.cos(a)*v[0]-Math.sin(a)*v[1],y=Math.sin(a)*v[0]+Math.cos(a)*v[1];return new double[]{x,Math.cos(b)*y-Math.sin(b)*v[2],Math.sin(b)*y+Math.cos(b)*v[2]};}
    static int[] visible(float yaw,float pitch){ArrayList<Integer> faces=new ArrayList<>();for(int i=0;i<6;i++)if(project(NORMALS[i],yaw,pitch)[2]>1e-7)faces.add(i);faces.sort((a,b)->Double.compare(project(NORMALS[a],yaw,pitch)[2],project(NORMALS[b],yaw,pitch)[2]));int[] out=new int[faces.size()];for(int i=0;i<out.length;i++)out[i]=faces.get(i);return out;}
    static double[][] polygon(int face,float yaw,float pitch){double[][] points=new double[4][];for(int i=0;i<4;i++)points[i]=project(FACES[face][i],yaw,pitch);return points;}
    static boolean contains(double[][] points,double x,double y){boolean in=false;for(int i=0,j=3;i<4;j=i++){double[] a=points[i],b=points[j];if((a[1]>y)!=(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])in=!in;}return in;}
    static int hit(float yaw,float pitch,double x,double y){int found=-1;for(int i:visible(yaw,pitch))if(contains(polygon(i,yaw,pitch),x,y))found=i;return found;}
}
