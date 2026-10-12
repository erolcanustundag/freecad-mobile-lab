// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.io.*;
import java.util.*;

/** Real native startup mesh plus numerical depth-buffer checks, without Android APIs. */
public final class SoftwareRendererTest {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static int colored(SoftwareRasterizer.Image image){int n=0;for(int p:image.pixels)if(p!=SoftwareRasterizer.BACKGROUND)n++;return n;}
    private static void ppm(SoftwareRasterizer.Image image,File file)throws Exception {
        try(OutputStream out=new BufferedOutputStream(new FileOutputStream(file))){out.write(("P6\n"+image.width+" "+image.height+"\n255\n").getBytes("US-ASCII"));for(int pixel:image.pixels){out.write(pixel>>>16&255);out.write(pixel>>>8&255);out.write(pixel&255);}}
    }
    private static float[] triangle(float z,float r,float g,float b) {
        return new float[]{-1,-1,z,0,0,1,r,g,b,1,1,-1,z,0,0,1,r,g,b,1,0,1,z,0,0,1,r,g,b,1};
    }
    public static void main(String[] args)throws Exception {
        NativeCad.clear();int ring=NativeCad.create("Ring",new double[]{18,1.6,3});MeshFrame nativeRing=new MeshFrame(NativeCad.mesh(ring));
        SoftwareRasterizer.Image top=SoftwareRasterizer.render(nativeRing,256,256,0,0,1,0,0);
        int count=colored(top);check(count>200&&count<15000,"Native ring pixels missing or overfilled: "+count);check(top.pixels[128*256+128]==SoftwareRasterizer.BACKGROUND,"Ring bore was filled");
        SoftwareRasterizer.Image orbit=SoftwareRasterizer.render(nativeRing,480,480,-32,-58,1,0,0);check(colored(orbit)>500,"Isometric ring rendering failed");
        check(!Arrays.equals(top.pixels,SoftwareRasterizer.render(nativeRing,256,256,15,-60,1,0,0).pixels),"Orbit did not change the view");
        check(!Arrays.equals(top.pixels,SoftwareRasterizer.render(nativeRing,256,256,0,0,1,2,0).pixels),"Pan did not change the view");
        check(colored(SoftwareRasterizer.render(nativeRing,256,256,0,0,.6f,0,0))>count,"Zoom did not enlarge the native mesh");
        if(args.length>0)ppm(orbit,new File(args[0]));System.out.println("PASS: actual native ring rendered in software; bore, orbit, pan and zoom preserved ("+count+" top-view pixels)");
        float[] near=triangle(1,1,0,0),far=triangle(0,0,1,0),first=new float[60],second=new float[60];
        System.arraycopy(far,0,first,0,30);System.arraycopy(near,0,first,30,30);System.arraycopy(near,0,second,0,30);System.arraycopy(far,0,second,30,30);
        SoftwareRasterizer.Image a=SoftwareRasterizer.render(new MeshFrame(first),128,128,0,0,1,0,0),b=SoftwareRasterizer.render(new MeshFrame(second),128,128,0,0,1,0,0);
        check(Arrays.equals(a.pixels,b.pixels),"Depth buffer depends on triangle order");int center=a.pixels[64*128+64];check((center>>>16&255)>100&&(center>>>8&255)==0,"Far triangle occluded the near triangle");System.out.println("PASS: depth-buffer occlusion is correct and independent of triangle order");
        MeshFrame empty=new MeshFrame(new float[0]);check(colored(SoftwareRasterizer.render(empty,32,32,0,0,1,0,0))==0,"Empty workspace was not empty");
        try{new MeshFrame(new float[]{Float.NaN});throw new AssertionError("Malformed mesh accepted");}catch(IllegalArgumentException expected){}
        try{SoftwareRasterizer.render(empty,0,32,0,0,1,0,0);throw new AssertionError("Invalid viewport accepted");}catch(IllegalArgumentException expected){}
        NativeCad.move(ring,100000,-100000,1000);MeshFrame shifted=new MeshFrame(NativeCad.mesh(ring));check(colored(SoftwareRasterizer.render(shifted,256,256,0,0,1,0,0))>200,"Translated geometry did not fit the camera");
        System.out.println("PASS: empty workspace, invalid input and camera fit for translated CAD geometry");
    }
}
