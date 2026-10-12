// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.io.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Fidelity, bounded preview, transforms and persistence through the real JNI kernel. */
final class LargeModelRegression {
    private static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    private static void near(double a,double b,double tolerance){check(Math.abs(a-b)<tolerance,"Expected "+b+", got "+a);}
    private interface Action{void run()throws Exception;}
    private static void rejects(Action a)throws Exception{try{a.run();}catch(Exception e){return;}throw new AssertionError("Invalid input accepted");}
    private static JSONObject object(int id)throws Exception{JSONArray a=new JSONArray(NativeCad.objects());for(int i=0;i<a.length();i++)if(a.getJSONObject(i).getInt("id")==id)return a.getJSONObject(i);throw new AssertionError("Missing object");}
    private static void transaction(Action action)throws Exception{NativeCad.beginTransaction(true);try{action.run();NativeCad.mesh(0);NativeCad.commitTransaction();}catch(Throwable e){NativeCad.rollbackTransaction();throw e;}}
    private static void bounds(JSONObject o,double x,double y,double z)throws Exception{JSONArray a=o.getJSONArray("bounds");near(a.getDouble(0),x,2e-5);near(a.getDouble(1),y,2e-5);near(a.getDouble(2),z,2e-5);}
    private static void word(byte[] data,int at,int n){for(int i=0;i<4;i++)data[at+i]=(byte)(n>>>(8*i));}
    private static float[] point(double u,double v){return new float[]{(float)((10+Math.cos(v))*Math.cos(u)),(float)((10+Math.cos(v))*Math.sin(u)),(float)Math.sin(v)};}
    private static void facet(OutputStream out,float[] a,float[] b,float[] c)throws Exception{byte[] record=new byte[50];int at=12;for(float[] p:new float[][]{a,b,c})for(float x:p){word(record,at,Float.floatToIntBits(x));at+=4;}out.write(record);}
    private static int torus(File file)throws Exception{
        final int nu=1024,nv=704,n=nu*nv*2;byte[] header=new byte[84];word(header,80,n);
        float[][] points=new float[nu*nv][];for(int u=0;u<nu;u++)for(int v=0;v<nv;v++)points[u*nv+v]=point(u*2*Math.PI/nu,v*2*Math.PI/nv);
        try(OutputStream out=new BufferedOutputStream(new FileOutputStream(file),1024*1024)){out.write(header);for(int u=0;u<nu;u++)for(int v=0;v<nv;v++){float[] a=points[u*nv+v],b=points[((u+1)%nu)*nv+v],c=points[((u+1)%nu)*nv+(v+1)%nv],d=points[u*nv+(v+1)%nv];facet(out,a,b,c);facet(out,a,c,d);}}
        return n;
    }
    private static long triangleHeader(File file)throws Exception{try(RandomAccessFile in=new RandomAccessFile(file,"r")){in.seek(80);long n=0;for(int i=0;i<4;i++)n|=(long)in.readUnsignedByte()<<(8*i);check(file.length()==84+50*n,"Truncated STL output");return n;}}
    static void run(File root,File cache)throws Exception {
        NativeCad.clear();int box=NativeCad.create("Box",new double[]{20,14,6});NativeCad.move(box,3,-5,2);
        String unchanged=NativeCad.objects();NativeCad.rotate(box,0,360,0);NativeCad.scale(box,1);check(unchanged.equals(NativeCad.objects()),"No-op transform lost editable primitive dimensions");
        final int initialBox=box;transaction(()->NativeCad.scale(initialBox,2));bounds(object(box),40,28,12);near(object(box).getDouble("volume"),13440,1e-5);
        File scaled=new File(root,"scaled.fcml");ProjectStore.save(scaled,cache);transaction(()->ProjectStore.restore(scaled,cache));box=new JSONArray(NativeCad.objects()).getJSONObject(0).getInt("id");bounds(object(box),40,28,12);
        final int solid=box;transaction(()->NativeCad.rotate(solid,0,0,90));bounds(object(solid),28,40,12);check(object(solid).getJSONArray("dims").length()==0,"Rotated solid has stale primitive dimensions");
        int copy=NativeCad.duplicate(solid,50,0,0);bounds(object(copy),28,40,12);near(object(copy).getDouble("volume"),13440,1e-5);
        File rotated=new File(root,"rotated.fcml");ProjectStore.save(rotated,cache);transaction(()->ProjectStore.restore(rotated,cache));JSONArray reopened=new JSONArray(NativeCad.objects());for(int i=0;i<reopened.length();i++){bounds(reopened.getJSONObject(i),28,40,12);near(reopened.getJSONObject(i).getDouble("volume"),13440,1e-4);}
        final int restored=reopened.getJSONObject(1).getInt("id");String before=NativeCad.objects();rejects(()->NativeCad.scale(restored,0));rejects(()->NativeCad.rotate(restored,Double.NaN,0,0));rejects(()->NativeCad.duplicate(restored,Double.POSITIVE_INFINITY,0,0));check(before.equals(NativeCad.objects()),"Rejected transform changed geometry");
        System.out.println("PASS: real solid resize, rotation, offset duplication and project fidelity; invalid transforms rejected");

        NativeCad.clear();File input=new File(root,"dense-torus.stl");int original=torus(input);check(input.length()>64L*1024*1024,"Fixture must exercise the old project-entry limit");
        int mesh=NativeCad.read(input.getAbsolutePath(),"stl");check(object(mesh).getLong("sourceTriangles")==original,"Import lost triangles");bounds(object(mesh),22,22,2);
        for(int budget:new int[]{10000,50000,150000}){float[] values=NativeCad.meshAtDetail(mesh,budget);check(values.length>0&&values.length/30<=budget,"Unbounded/empty preview");for(float v:values)if(!Float.isFinite(v))throw new AssertionError("Invalid preview values");check(object(mesh).getLong("sourceTriangles")==original,"Preview changed original geometry");System.out.println("PASS: "+original+" source triangles -> "+values.length/30+" preview triangles (budget "+budget+")");}
        MeshFrame frame=new MeshFrame(NativeCad.meshAtDetail(mesh,50000));SoftwareRasterizer.Image top=SoftwareRasterizer.render(frame,256,256,0,0,1,0,0);check(top.pixels[128*256+128]==SoftwareRasterizer.BACKGROUND,"Simplification closed the ring bore");int pixels=0;for(int p:top.pixels)if(p!=SoftwareRasterizer.BACKGROUND)pixels++;check(pixels>200,"Dense STL preview did not render");
        SoftwareRasterizer.Image image=SoftwareRasterizer.render(frame,480,480,-32,-58,1,0,0);try(OutputStream out=new FileOutputStream(new File(root,"dense-preview.ppm"))){out.write("P6\n480 480\n255\n".getBytes("US-ASCII"));for(int p:image.pixels){out.write(p>>>16&255);out.write(p>>>8&255);out.write(p&255);}}
        java.nio.file.Files.copy(new File(root,"dense-preview.ppm").toPath(),java.nio.file.Paths.get(System.getProperty("freecad.evidence.directory","."),"large-stl-preview.ppm"),java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        File output=new File(root,"dense-output.stl");NativeCad.write(output.getAbsolutePath(),"stl",mesh);check(triangleHeader(output)==original,"Export used the simplified preview");
        File project=new File(root,"dense.fcml");ProjectStore.save(project,cache);try(ZipFile zip=new ZipFile(project)){check(zip.getEntry("part-"+mesh+".stl").getSize()>64L*1024*1024,"Autosave did not keep the original mesh");}
        transaction(()->ProjectStore.restore(project,cache));mesh=new JSONArray(NativeCad.objects()).getJSONObject(0).getInt("id");check(object(mesh).getLong("sourceTriangles")==original,"Project reopen lost triangles");bounds(object(mesh),22,22,2);
        System.out.println("PASS: original "+original+"-triangle STL retained through export, >64 MiB project save, and reopen; bore preserved in software preview");
        final int source=mesh;final int[] duplicate={0};transaction(()->duplicate[0]=NativeCad.duplicate(source,30,0,0));check(NativeCad.meshAtDetail(duplicate[0],10000).length/30<=10000,"Multi-object preview exceeds its global budget");
        transaction(()->NativeCad.rotate(duplicate[0],0,90,0));bounds(object(duplicate[0]),2,22,22);transaction(()->NativeCad.scale(duplicate[0],.5));bounds(object(duplicate[0]),1,11,11);bounds(object(source),22,22,2);
        File transformed=new File(root,"transformed-mesh.stl");NativeCad.write(transformed.getAbsolutePath(),"stl",duplicate[0]);check(triangleHeader(transformed)==original,"Transformed mesh lost triangles");int reread=NativeCad.read(transformed.getAbsolutePath(),"stl");bounds(object(reread),1,11,11);
        check(NativeCad.undo(),"Large mesh Undo unavailable");
        check(NativeCad.undo(),"Large mesh scale Undo unavailable");bounds(object(duplicate[0]),2,22,22);
        rejects(()->NativeCad.meshAtDetail(source,200001));rejects(()->NativeCad.meshAtDetail(source,-1));
        File truncated=new File(root,"malformed.stl");try(RandomAccessFile f=new RandomAccessFile(truncated,"rw")){f.setLength(100);f.seek(80);f.write(new byte[]{1,0,0,0});}rejects(()->NativeCad.read(truncated.getAbsolutePath(),"stl"));
        File invalid=new File(root,"nan-coordinate.stl");byte[] invalidData=new byte[134];word(invalidData,80,1);word(invalidData,96,Float.floatToIntBits(Float.NaN));java.nio.file.Files.write(invalid.toPath(),invalidData);rejects(()->NativeCad.read(invalid.getAbsolutePath(),"stl"));
        File ascii=new File(root,"valid-ascii.stl");java.nio.file.Files.write(ascii.toPath(),("solid test\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid test\n").getBytes("US-ASCII"));int asciiId=NativeCad.read(ascii.getAbsolutePath(),"stl");check(object(asciiId).getLong("sourceTriangles")==1,"Valid ASCII STL rejected");
        System.out.println("PASS: dense STL transforms leave source unchanged, preserve exported detail, and support bounded multi-object previews/Undo; malformed STL rejected");
        check(cache.list().length==0,"Large-model staging files leaked");
    }
}
