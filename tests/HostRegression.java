// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Exercises the real JNI adapter with matching OCCT 7.9.2 on the host JVM. */
public final class HostRegression {
    interface Action { void run() throws Exception; }
    private static File root,cache;
    private static int checks;
    private static void check(boolean good,String reason) {if(!good)throw new AssertionError(reason);checks++;}
    private static void near(double actual,double expected,double tolerance) {check(Math.abs(actual-expected)<=tolerance,"Expected "+expected+", got "+actual);}
    private static void rejects(Action action)throws Exception {
        try{action.run();}catch(Exception expected){checks++;return;}
        throw new AssertionError("Invalid input was accepted");
    }
    private static void transaction(boolean undo,Action action)throws Exception {
        NativeCad.beginTransaction(undo);
        try{action.run();NativeCad.mesh(0);NativeCad.commitTransaction();}
        catch(Throwable error){NativeCad.rollbackTransaction();throw error;}
    }
    private static JSONArray objects()throws Exception{return new JSONArray(NativeCad.objects());}
    private static JSONObject object(int id)throws Exception {
        JSONArray all=objects();for(int i=0;i<all.length();i++)if(all.getJSONObject(i).getInt("id")==id)return all.getJSONObject(i);
        throw new AssertionError("Object is missing: "+id);
    }
    private static void empty()throws Exception{transaction(false,()->NativeCad.clear());}
    private static byte[] bytes(File f)throws Exception{return Files.readAllBytes(f.toPath());}
    private static byte[] utf(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static File zip(String name,Map<String,byte[]> entries)throws Exception {
        File file=new File(root,name);
        try(ZipOutputStream out=new ZipOutputStream(new FileOutputStream(file))){
            for(Map.Entry<String,byte[]> e:entries.entrySet()){out.putNextEntry(new ZipEntry(e.getKey()));out.write(e.getValue());out.closeEntry();}
        }
        return file;
    }
    private static JSONObject manifest(JSONArray all)throws Exception {
        return new JSONObject().put("format","FreeCADMobileLab").put("version",1).put("units","mm").put("objects",all);
    }
    private static File project(String name,JSONObject metadata,Map<String,byte[]> shapes)throws Exception {
        Map<String,byte[]> entries=new LinkedHashMap<>();entries.put("manifest.json",utf(metadata.toString()));entries.putAll(shapes);return zip(name,entries);
    }
    private static void noTemporaryFiles(){check(cache.list().length==0,"Extraction/staging files leaked: "+Arrays.toString(cache.list()));}
    private static void pass(String text){System.out.println("PASS: "+text);}

    public static void main(String[] args)throws Exception {
        root=Files.createTempDirectory("freecad-host-regression-").toFile();cache=new File(root,"cache");check(cache.mkdir(),"Cache directory creation failed");
        try {
            System.out.print(NativeCad.selfTest(root.getAbsolutePath()));
            empty();int ring=NativeCad.create("Ring",new double[]{18,1.6,3});
            JSONObject r=object(ring);near(r.getDouble("volume"),Math.PI*(10.6*10.6-81)*3,1e-6);
            near(r.getJSONArray("bounds").getDouble(0),21.2,1e-6);near(r.getJSONArray("bounds").getDouble(2),3,1e-6);
            float[] mesh=NativeCad.mesh(ring);check(mesh.length>3000&&mesh.length%30==0,"Ring display mesh is empty or malformed");
            for(float v:mesh)check(Float.isFinite(v),"Non-finite mesh attribute");
            for(int i=0;i<mesh.length;i+=10)near(Math.sqrt(mesh[i+3]*mesh[i+3]+mesh[i+4]*mesh[i+4]+mesh[i+5]*mesh[i+5]),1,1e-4);
            pass("default startup ring, exact dimensions, finite vertices and unit normals");

            String before=NativeCad.objects();
            rejects(()->NativeCad.create(null,new double[]{1}));rejects(()->NativeCad.create("Box",null));
            rejects(()->NativeCad.create("Box",new double[0]));rejects(()->NativeCad.create("Box",new double[]{1,2,Double.NaN}));
            rejects(()->NativeCad.edit(ring,new double[]{0,1,2}));rejects(()->NativeCad.move(ring,Double.POSITIVE_INFINITY,0,0));
            rejects(()->NativeCad.move(ring,1000001,0,0));rejects(()->NativeCad.restorePosition(ring,null));
            rejects(()->NativeCad.read(null,"brep"));rejects(()->NativeCad.remove(-1));
            check(NativeCad.objects().equals(before),"Rejected operation changed the workspace");
            pass("JNI null, NaN, invalid ID, dimension and position rejection without a VM crash");

            empty();int a=NativeCad.create("Box",new double[]{10,10,10}),b=NativeCad.create("Box",new double[]{10,10,10});NativeCad.move(b,5,0,0);
            int union=NativeCad.operation("Union",a,b,0);near(object(union).getDouble("volume"),1500,1e-6);check(NativeCad.undo(),"Union Undo failed");
            int cut=NativeCad.operation("Cut",a,b,0);near(object(cut).getDouble("volume"),500,1e-6);check(NativeCad.undo(),"Cut Undo failed");
            int common=NativeCad.operation("Intersect",a,b,0);near(object(common).getDouble("volume"),500,1e-6);check(NativeCad.undo(),"Intersection Undo failed");
            int rounded=NativeCad.operation("Fillet",a,0,0.2);check(object(rounded).getDouble("volume")<1000,"Fillet did not remove sharp corners");check(NativeCad.undo(),"Fillet Undo failed");
            pass("union, subtraction, intersection, unique-edge fillets and Undo");

            empty();a=NativeCad.create("Box",new double[]{9,7,3});NativeCad.move(a,4,-2,1);
            File solid=new File(root,"translated.brep");NativeCad.write(solid.getAbsolutePath(),"brep",a);
            int imported=NativeCad.read(solid.getAbsolutePath(),"brep");NativeCad.restorePosition(imported,new double[]{4,-2,1});NativeCad.move(imported,6,-2,1);
            NativeCad.visible(a,false);
            File stl=new File(root,"mesh.stl");NativeCad.write(stl.getAbsolutePath(),"stl",imported);int stlId=NativeCad.read(stl.getAbsolutePath(),"stl");NativeCad.visible(stlId,false);
            File good=new File(root,"roundtrip.fcml");ProjectStore.save(good,cache);JSONArray expected=objects();
            empty();transaction(true,()->ProjectStore.restore(good,cache));JSONArray actual=objects();check(actual.length()==expected.length(),"Project lost objects");
            for(int i=0;i<actual.length();i++){
                JSONObject x=actual.getJSONObject(i),y=expected.getJSONObject(i);check(x.getBoolean("visible")==y.getBoolean("visible"),"Visibility lost");
                check(x.getBoolean("mesh")==y.getBoolean("mesh"),"Mesh/solid kind changed");
                for(int j=0;j<3;j++){near(x.getJSONArray("xyz").getDouble(j),y.getJSONArray("xyz").getDouble(j),1e-8);near(x.getJSONArray("bounds").getDouble(j),y.getJSONArray("bounds").getDouble(j),1e-4);}
                if(!x.getBoolean("mesh"))near(x.getDouble("volume"),y.getDouble("volume"),1e-5);
            }
            int restored=actual.getJSONObject(1).getInt("id");NativeCad.move(restored,8,-2,1);
            File moved=new File(root,"moved.brep");NativeCad.write(moved.getAbsolutePath(),"brep",restored);
            String movedData=new String(bytes(moved),StandardCharsets.US_ASCII);check(!movedData.isEmpty(),"Moved BREP is empty");
            // Compare display bounds in world coordinates: a reopened BREP must move by 2, not 8.
            float[] placed=NativeCad.mesh(restored);float min=Float.MAX_VALUE,max=-min;
            for(int i=0;i<placed.length;i+=10){min=Math.min(min,placed[i]);max=Math.max(max,placed[i]);}
            near(min,3.5,1e-4);near(max,12.5,1e-4);noTemporaryFiles();
            pass("primitive, translated BREP and hidden STL project round-trip; movement after reopen");

            before=NativeCad.objects();final String baseline=before;
            JSONArray two=new JSONArray();JSONObject first=object(restored);first.put("id",101);two.put(first);
            JSONObject second=new JSONObject(first.toString()).put("id",102);two.put(second);
            Map<String,byte[]> shapes=new LinkedHashMap<>();shapes.put("part-101.brep",bytes(moved));shapes.put("part-102.brep",utf("corrupt BREP"));
            File bad=project("late-failure.fcml",manifest(two),shapes);
            rejects(()->transaction(true,()->ProjectStore.restore(bad,cache)));
            check(NativeCad.objects().equals(baseline),"Late import failure lost the original workspace");noTemporaryFiles();
            check(NativeCad.undo(),"Failure damaged the Undo history");near(object(restored).getJSONArray("xyz").getDouble(0),6,1e-8);
            final String undoBaseline=NativeCad.objects();transaction(true,()->ProjectStore.restore(good,cache));check(NativeCad.undo(),"Project import Undo failed");
            check(NativeCad.objects().equals(undoBaseline),"Project import required more than one Undo");
            pass("late project failure rolls back geometry, positions and Undo; whole import uses one Undo");

            rejects(()->ArchiveIO.unpackProject(zip("traversal.fcml",Collections.singletonMap("../escape",utf("bad"))),cache));
            rejects(()->ArchiveIO.unpackProject(zip("oversized.fcml",Collections.singletonMap("manifest.json",new byte[(int)ArchiveIO.MAX_MANIFEST+1])),cache));
            JSONObject unsupported=manifest(new JSONArray()).put("units","inch");File wrongUnits=project("units.fcml",unsupported,Collections.emptyMap());
            rejects(()->transaction(true,()->ProjectStore.restore(wrongUnits,cache)));
            ByteArrayOutputStream sink=new ByteArrayOutputStream();rejects(()->ArchiveIO.copy(new ByteArrayInputStream(new byte[200]),sink,128,null));check(sink.size()<=128,"Copy exceeded its limit");
            ArchiveIO.Budget budget=new ArchiveIO.Budget(128);ArchiveIO.copy(new ByteArrayInputStream(new byte[80]),sink,100,budget);rejects(()->ArchiveIO.copy(new ByteArrayInputStream(new byte[80]),sink,100,budget));
            rejects(()->ArchiveIO.copy(null,sink,100,null));noTemporaryFiles();
            pass("archive path, expanded-size, unit and cumulative IO limits; cleanup on failure");

            // A failed autosave must not truncate an existing destination. Force staging-temp creation to fail.
            File kept=new File(root,"kept.fcml");ProjectStore.save(kept,cache);byte[] keptBytes=bytes(kept);
            File absent=new File(root,"no-parent");rejects(()->ProjectStore.save(new File(absent,"save.fcml"),cache));
            check(Arrays.equals(keptBytes,bytes(kept)),"Failed save touched an existing project");noTemporaryFiles();
            rejects(()->ArchiveIO.replaceFile(new File(root,"missing-temp"),kept));check(Arrays.equals(keptBytes,bytes(kept)),"Failed replacement truncated the destination");
            pass("failed save cleans staging; project writes use sibling temp plus atomic replacement");

            String document="<?xml version=\"1.0\" encoding=\"UTF-8\"?><Document><Object name=\"Shown\"><Properties><Property name=\"Shape\"><Part file=\"shown.brp\"/></Property></Properties></Object><Object name=\"Hidden\"><Properties><Property name=\"Shape\"><Part file=\"hidden.brp\"/></Property></Properties></Object></Document>";
            String gui="<Document><ViewProvider name=\"Hidden\"><Property name=\"Visibility\"><Bool value=\"false\"/></Property></ViewProvider></Document>";
            Map<String,byte[]> fcEntries=new LinkedHashMap<>();fcEntries.put("Document.xml",utf(document));fcEntries.put("GuiDocument.xml",utf(gui));fcEntries.put("shown.brp",bytes(moved));fcEntries.put("hidden.brp",utf("hidden invalid shape must not be opened"));
            File fcstd=zip("visible.FCStd",fcEntries);int count=objects().length();transaction(true,()->FcstdImporter.read(fcstd,cache));check(objects().length()==count+1,"FCStd visibility filter failed");noTemporaryFiles();
            String fcBefore=NativeCad.objects();fcEntries.put("Document.xml",utf(document.replace("hidden.brp","missing.brp")));fcEntries.remove("GuiDocument.xml");
            File missing=zip("missing.FCStd",fcEntries);rejects(()->transaction(true,()->FcstdImporter.read(missing,cache)));check(NativeCad.objects().equals(fcBefore),"Missing FCStd part changed the workspace");
            fcEntries.put("Document.xml",utf("<!DOCTYPE Document [<!ENTITY x SYSTEM 'file:///should-not-read'>]><Document>&x;</Document>"));File dtd=zip("dtd.FCStd",fcEntries);
            rejects(()->transaction(true,()->FcstdImporter.read(dtd,cache)));noTemporaryFiles();
            pass("saved FCStd Part geometry, visibility, missing-part rollback and DTD rejection");

            empty();int meshId=NativeCad.read(stl.getAbsolutePath(),"stl");rejects(()->NativeCad.operation("Fillet",meshId,0,0.1));
            rejects(()->NativeCad.write(new File(root,"invalid.step").getAbsolutePath(),"step",meshId));rejects(()->NativeCad.write(new File(root,"invalid.brep").getAbsolutePath(),"brep",meshId));
            File tooMany=new File(root,"too-many.stl");try(RandomAccessFile file=new RandomAccessFile(tooMany,"rw")){int n=2000001;file.setLength(84L+50L*n);file.seek(80);for(int i=0;i<4;i++)file.write(n>>>(8*i));}
            String meshBefore=NativeCad.objects();rejects(()->NativeCad.read(tooMany.getAbsolutePath(),"stl"));check(NativeCad.objects().equals(meshBefore),"Oversized STL changed the workspace");
            pass("STL solid-operation/export rejection and 2,000,000-triangle preflight");
            LargeModelRegression.run(root,cache);
            System.out.println("PASS: host JNI regression suite completed ("+checks+" baseline assertions plus large-model checks)");
        }finally{ArchiveIO.deleteTree(root);}
    }
}
