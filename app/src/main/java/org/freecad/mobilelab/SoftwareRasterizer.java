// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.util.Arrays;

/** Perspective triangle rasterizer with a depth buffer. No Android/GPU/native calls. */
final class SoftwareRasterizer {
    static final int BACKGROUND=0xff111820;
    static final class Image {
        final int width,height;
        final int[] pixels;
        Image(int w,int h){this(w,h,false);}
        Image(int w,int h,boolean transparent){width=w;height=h;pixels=new int[w*h];Arrays.fill(pixels,transparent?0:BACKGROUND);}
    }
    static Image render(MeshFrame mesh,int width,int height,float yaw,float pitch,float zoom,float panX,float panY) {
        return render(mesh,width,height,yaw,pitch,zoom,panX,panY,false);
    }
    static Image render(MeshFrame mesh,int width,int height,float yaw,float pitch,float zoom,float panX,float panY,boolean orthographic) {
        return render(mesh,width,height,yaw,pitch,zoom,panX,panY,orthographic,RenderSettings.DEFAULT);
    }
    static Image render(MeshFrame mesh,int width,int height,float yaw,float pitch,float zoom,float panX,float panY,boolean orthographic,RenderSettings options) {
        if(width<1||height<1||width>2048||height>2048)throw new IllegalArgumentException("Invalid software viewport size");
        Image image=new Image(width,height,options.transparent);if(mesh==null||mesh.count+mesh.lineCount==0)return image;
        float[] depth=new float[width*height];
        double az=Math.toRadians(yaw),ax=Math.toRadians(pitch),ca=Math.cos(az),sa=Math.sin(az),cb=Math.cos(ax),sb=Math.sin(ax);
        double aspect=(double)width/height,distance=mesh.radius*3.4*Math.max(.35,zoom)/Math.min(1,aspect),scale=height/(2*Math.tan(Math.toRadians(21)));
        float[] xs=new float[3],ys=new float[3],invz=new float[3],shade=new float[3],rgb=new float[9],normals=new float[9];float[] v=mesh.values;
        for(int base=0;base<v.length;base+=30) {
            if((base%3840)==0&&Thread.currentThread().isInterrupted())return null;
            boolean clipped=false;
            for(int j=0;j<3;j++) {
                int i=base+j*10;double x=(double)v[i]-mesh.x,y=(double)v[i+1]-mesh.y,z=(double)v[i+2]-mesh.z;
                double rx=ca*x-sa*y,ry=sa*x+ca*y,py=cb*ry-sb*z,pz=sb*ry+cb*z,cz=distance-pz;
                if(cz<=1e-6){clipped=true;break;}
                double projectionDepth=orthographic?distance:cz;xs[j]=(float)(width*.5+(rx-panX)*scale/projectionDepth);ys[j]=(float)(height*.5-(py-panY)*scale/projectionDepth);invz[j]=(float)(1/cz);
                double nx=ca*v[i+3]-sa*v[i+4],ny=sa*v[i+3]+ca*v[i+4],nz=v[i+5];
                double ty=cb*ny-sb*nz,tz=sb*ny+cb*nz;
                if(nx*(-rx+panX)+ty*(-py+panY)+tz*cz<0){nx=-nx;ty=-ty;tz=-tz;}
                double length=Math.sqrt(nx*nx+ty*ty+tz*tz);if(length>1e-8){nx/=length;ty/=length;tz/=length;}
                double light=Math.max(0,(nx*.3+ty*.7+tz)/Math.sqrt(1.58));
                normals[j*3]=(float)nx;normals[j*3+1]=(float)ty;normals[j*3+2]=(float)tz;
                if(options.style==RenderSettings.STUDIO){int m=i/5;float[] color=StudioLighting.color(nx,ty,tz,-rx+panX,-py+panY,cz,new float[]{v[i+6],v[i+7],v[i+8]},mesh.materials.length==0?.45:mesh.materials[m],mesh.materials.length==0?0:mesh.materials[m+1]);System.arraycopy(color,0,rgb,j*3,3);}
                double fill=Math.max(0,(-nx*.8-ty*.2+tz*.6)/Math.sqrt(1.04));shade[j]=(float)Math.min(1.15,.28+.64*light+.18*fill);
            }
            if(clipped)continue;
            double area=(xs[1]-xs[0])*(ys[2]-ys[0])-(ys[1]-ys[0])*(xs[2]-xs[0]);if(Math.abs(area)<1e-9)continue;
            if(options.style==RenderSettings.WIREFRAME){for(int j=0;j<3;j++)edge(image,depth,xs[j],ys[j],invz[j],v[base+j*10+2],xs[(j+1)%3],ys[(j+1)%3],invz[(j+1)%3],v[base+(j+1)%3*10+2],pixel(v[base+6],v[base+7],v[base+8]),options);continue;}
            int x0=Math.max(0,(int)Math.floor(Math.min(xs[0],Math.min(xs[1],xs[2])))),x1=Math.min(width-1,(int)Math.ceil(Math.max(xs[0],Math.max(xs[1],xs[2]))));
            int y0=Math.max(0,(int)Math.floor(Math.min(ys[0],Math.min(ys[1],ys[2])))),y1=Math.min(height-1,(int)Math.ceil(Math.max(ys[0],Math.max(ys[1],ys[2]))));
            for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++) {
                double px=x+.5,py=y+.5;
                double w1=((px-xs[0])*(ys[2]-ys[0])-(py-ys[0])*(xs[2]-xs[0]))/area;
                double w2=((xs[1]-xs[0])*(py-ys[0])-(ys[1]-ys[0])*(px-xs[0]))/area,w0=1-w1-w2;
                if(w0<-.000001||w1<-.000001||w2<-.000001)continue;
                float reciprocal=(float)(w0*invz[0]+w1*invz[1]+w2*invz[2]);int index=y*width+x;
                if(options.clip&&(w0*v[base+2]*invz[0]+w1*v[base+12]*invz[1]+w2*v[base+22]*invz[2])/reciprocal>options.clipZ)continue;
                if(reciprocal<=depth[index])continue;depth[index]=reciprocal;
                float light=(float)((w0*shade[0]*invz[0]+w1*shade[1]*invz[1]+w2*shade[2]*invz[2])/reciprocal);
                int r=Math.min(255,Math.max(0,Math.round(v[base+6]*light*255))),g=Math.min(255,Math.max(0,Math.round(v[base+7]*light*255))),b=Math.min(255,Math.max(0,Math.round(v[base+8]*light*255)));
                if(options.style==RenderSettings.STUDIO){float rr=(float)((w0*rgb[0]*invz[0]+w1*rgb[3]*invz[1]+w2*rgb[6]*invz[2])/reciprocal),gg=(float)((w0*rgb[1]*invz[0]+w1*rgb[4]*invz[1]+w2*rgb[7]*invz[2])/reciprocal),bb=(float)((w0*rgb[2]*invz[0]+w1*rgb[5]*invz[1]+w2*rgb[8]*invz[2])/reciprocal);image.pixels[index]=pixel(rr,gg,bb);}
                else if(options.style==RenderSettings.ZEBRA){double nx=(w0*normals[0]*invz[0]+w1*normals[3]*invz[1]+w2*normals[6]*invz[2])/reciprocal,ny=(w0*normals[1]*invz[0]+w1*normals[4]*invz[1]+w2*normals[7]*invz[2])/reciprocal,nz=(w0*normals[2]*invz[0]+w1*normals[5]*invz[1]+w2*normals[8]*invz[2])/reciprocal,len=Math.sqrt(nx*nx+ny*ny+nz*nz);float color=Math.sin(Math.atan2(nx,nz)*18+(len>1e-8?ny/len:0)*10)>0?.94f:.06f;image.pixels[index]=pixel(color,color,color);}
                else image.pixels[index]=0xff000000|(r<<16)|(g<<8)|b;
            }
        }
        float[] lines=mesh.lines;
        for(int base=0;base<lines.length;base+=20){
            if((base%2000)==0&&Thread.currentThread().isInterrupted())return null;
            boolean clipped=false;
            for(int j=0;j<2;j++){int i=base+j*10;double x=lines[i]-mesh.x,y=lines[i+1]-mesh.y,z=lines[i+2]-mesh.z,rx=ca*x-sa*y,ry=sa*x+ca*y,py=cb*ry-sb*z,pz=sb*ry+cb*z,cz=distance-pz;if(cz<=1e-6){clipped=true;break;}double projectionDepth=orthographic?distance:cz;xs[j]=(float)(width*.5+(rx-panX)*scale/projectionDepth);ys[j]=(float)(height*.5-(py-panY)*scale/projectionDepth);invz[j]=(float)(1/cz);}
            if(clipped)continue;edge(image,depth,xs[0],ys[0],invz[0],lines[base+2],xs[1],ys[1],invz[1],lines[base+12],pixel(lines[base+6],lines[base+7],lines[base+8]),options);
        }
        return image;
    }
    private static int pixel(float r,float g,float b){return 0xff000000|(Math.min(255,Math.max(0,Math.round(r*255)))<<16)|(Math.min(255,Math.max(0,Math.round(g*255)))<<8)|Math.min(255,Math.max(0,Math.round(b*255)));}
    private static void edge(Image image,float[] depth,float x0,float y0,float z0,float world0,float x1,float y1,float z1,float world1,int color,RenderSettings options){int steps=Math.max(1,Math.min(8192,(int)Math.ceil(Math.max(Math.abs(x1-x0),Math.abs(y1-y0)))));for(int k=0;k<=steps;k++){float t=(float)k/steps,z=(1-t)*z0+t*z1;int x=Math.round(x0+t*(x1-x0)),y=Math.round(y0+t*(y1-y0));if(options.clip&&((1-t)*world0*z0+t*world1*z1)/z>options.clipZ)continue;for(int dx=0;dx<2;dx++)if(x+dx>=0&&x+dx<image.width&&y>=0&&y<image.height){int index=y*image.width+x+dx;if(z*1.0001f>=depth[index]){depth[index]=z*1.0001f;image.pixels[index]=color;}}}}
}
