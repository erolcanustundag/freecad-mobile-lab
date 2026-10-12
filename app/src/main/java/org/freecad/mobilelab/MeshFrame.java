// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.nio.*;

/** Immutable, bounded native mesh shared by GPU and software viewers. */
final class MeshFrame {
    final float[] values;
    final float[] lines,materials;
    final int count;
    final int lineCount;
    final float x,y,z,radius;
    private FloatBuffer buffer;
    private FloatBuffer lineBuffer,materialBuffer,wireBuffer;
    MeshFrame(float[] values) {this(values,new float[0]);}
    MeshFrame(float[] values,float[] lines) {this(values,lines,new float[0]);}
    MeshFrame(float[] values,float[] lines,float[] materials) {
        if(values==null||values.length%30!=0||values.length>6000000)
            throw new IllegalArgumentException("Invalid or oversized display mesh");
        if(lines==null||lines.length%20!=0||lines.length>400000)throw new IllegalArgumentException("Invalid or oversized curve display");
        if(materials==null||(materials.length!=0&&materials.length!=values.length/5))throw new IllegalArgumentException("Material buffer length mismatch");for(float m:materials)if(!Float.isFinite(m)||m<0||m>1)throw new IllegalArgumentException("Invalid display material");this.materials=materials;
        float x0=Float.MAX_VALUE,y0=x0,z0=x0,x1=-x0,y1=x1,z1=x1;
        for(float[] source:new float[][]{values,lines})for(int i=0;i<source.length;i++) {
            if(!Float.isFinite(source[i]))throw new IllegalArgumentException("Invalid display coordinates");
            if(i%10==0){x0=Math.min(x0,source[i]);x1=Math.max(x1,source[i]);}
            if(i%10==1){y0=Math.min(y0,source[i]);y1=Math.max(y1,source[i]);}
            if(i%10==2){z0=Math.min(z0,source[i]);z1=Math.max(z1,source[i]);}
        }
        this.values=values;this.lines=lines;count=values.length/10;lineCount=lines.length/10;
        x=count+lineCount==0?0:(float)(((double)x0+x1)/2);y=count+lineCount==0?0:(float)(((double)y0+y1)/2);z=count+lineCount==0?0:(float)(((double)z0+z1)/2);
        double dx=(double)x1-x0,dy=(double)y1-y0,dz=(double)z1-z0;
        radius=count+lineCount==0?15:Math.max(1,(float)(Math.sqrt(dx*dx+dy*dy+dz*dz)/2));
        if(!Float.isFinite(radius))throw new IllegalArgumentException("Display bounds are too large");
    }
    static MeshFrame focus(MeshFrame source,double[] bounds){return new MeshFrame(source,bounds);}
    private MeshFrame(MeshFrame source,double[] b){if(source==null||b==null||b.length!=6)throw new IllegalArgumentException("Select geometry to frame");for(double v:b)if(!Double.isFinite(v)||Math.abs(v)>1000000)throw new IllegalArgumentException("Invalid focus bounds");for(int i=0;i<3;i++)if(b[i]>b[i+3])throw new IllegalArgumentException("Invalid focus bounds");values=source.values;lines=source.lines;materials=source.materials;count=source.count;lineCount=source.lineCount;buffer=source.buffer;lineBuffer=source.lineBuffer;materialBuffer=source.materialBuffer;wireBuffer=source.wireBuffer;x=(float)((b[0]+b[3])/2);y=(float)((b[1]+b[4])/2);z=(float)((b[2]+b[5])/2);radius=Math.max(1,(float)(Math.sqrt(Math.pow(b[3]-b[0],2)+Math.pow(b[4]-b[1],2)+Math.pow(b[5]-b[2],2))/2));}
    FloatBuffer buffer() {
        if(buffer==null){buffer=ByteBuffer.allocateDirect(values.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();buffer.put(values);((Buffer)buffer).position(0);}
        return buffer;
    }
    FloatBuffer lineBuffer(){if(lineBuffer==null){lineBuffer=ByteBuffer.allocateDirect(lines.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();lineBuffer.put(lines);((Buffer)lineBuffer).position(0);}return lineBuffer;}
    FloatBuffer materialBuffer(){if(materialBuffer==null){materialBuffer=ByteBuffer.allocateDirect(materials.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();materialBuffer.put(materials);((Buffer)materialBuffer).position(0);}return materialBuffer;}
    FloatBuffer wireBuffer(){if(wireBuffer==null){wireBuffer=ByteBuffer.allocateDirect(values.length*8).order(ByteOrder.nativeOrder()).asFloatBuffer();for(int base=0;base<values.length;base+=30)for(int j:new int[]{0,1,1,2,2,0})wireBuffer.put(values,base+j*10,10);((Buffer)wireBuffer).position(0);}return wireBuffer;}
}
