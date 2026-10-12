// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.JSONArray;
/** Bounded conversion of genuine Part triangles into the existing renderer format. */
final class PartMesh {
    static MeshFrame frame(JSONArray coordinates)throws Exception{
        if(coordinates.length()%9!=0||coordinates.length()>270000)throw new IllegalArgumentException("Invalid or oversized Part preview");
        float[] result=new float[coordinates.length()/9*30];int out=0;
        for(int start=0;start<coordinates.length();start+=9){double[] xyz=new double[9];for(int i=0;i<9;i++){xyz[i]=coordinates.getDouble(start+i);if(!Double.isFinite(xyz[i])||Math.abs(xyz[i])>1000000)throw new IllegalArgumentException("Part preview coordinates out of range");}double ax=xyz[3]-xyz[0],ay=xyz[4]-xyz[1],az=xyz[5]-xyz[2],bx=xyz[6]-xyz[0],by=xyz[7]-xyz[1],bz=xyz[8]-xyz[2];double nx=ay*bz-az*by,ny=az*bx-ax*bz,nz=ax*by-ay*bx,length=Math.sqrt(nx*nx+ny*ny+nz*nz);if(length==0){nx=0;ny=0;nz=1;length=1;}for(int vertex=0;vertex<3;vertex++){for(int i=0;i<3;i++)result[out++]=(float)xyz[vertex*3+i];result[out++]=(float)(nx/length);result[out++]=(float)(ny/length);result[out++]=(float)(nz/length);result[out++]=.75f;result[out++]=.7f;result[out++]=.4f;result[out++]=1;}}
        return new MeshFrame(result);
    }
}
