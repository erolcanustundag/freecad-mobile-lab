package org.freecad.mobilelab;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Project persistence. Call restore inside an engine transaction. */
final class ProjectStore {
    private static final Set<String> TYPES=new HashSet<>(Arrays.asList("Ring","Box","Cylinder","Sphere","Torus","Sketch pad","Union","Cut","Intersect","Fillet","STEP solid","IGES solid","BREP solid","BREP curve","STL mesh","Circle","Ellipse","Rectangle","Helix","Bezel setting","Prong setting","Subdivision form","NURBS curve","Interpolated curve","Polyline","Extrude solid","Extrude surface","Revolve solid","Revolve surface","Loft solid","Loft surface","Sweep solid","Sweep surface","Pipe along curve","Section","Offset curve","Offset shape","Chamfer","Heal CAD","Sew surfaces","Linear array","Polar array","Hollow top","NURBS patch","Gemstone cutter","Solidify shell","Text solid","Curve array","Oval bezel","Rectangle bezel","Cushion bezel","Oval prongs","Comfort ring","Signet ring","Pendant frame","Bangle","Join curves","Planar region","Trim curve","Extend line","Project curve","Selected fillet","Selected chamfer","Selected shell","Trim patch","Untrim patch"));
    static String graphJson;
    static int[] graphOutputIds=new int[0];
    static JSONArray castingRecords=new JSONArray();
    static void reset(){Worksheet.reset();Expressions.reset();FeatureModel.recipes=new JSONArray();graphJson=null;graphOutputIds=new int[0];castingRecords=new JSONArray();}
    static String workspace()throws Exception{JSONObject o=new JSONObject();o.put("features",FeatureModel.recipes);o.put("variables",Expressions.json());o.put("worksheet",Worksheet.json());if(graphJson!=null)o.put("graph",new JSONObject(graphJson));JSONArray ids=new JSONArray();for(int id:graphOutputIds)ids.put(id);o.put("graphObjectIds",ids);if(castingRecords.length()>0)o.put("casting",castingRecords);return o.toString();}
    static void applyWorkspace(String text)throws Exception{JSONObject o=text==null||text.isEmpty()?new JSONObject():new JSONObject(text);Worksheet.load(o.optJSONObject("worksheet"));Expressions.load(o.optJSONObject("variables"));FeatureModel.load(o.optJSONArray("features"));graphJson=o.has("graph")?o.getJSONObject("graph").toString():null;JSONArray ids=o.optJSONArray("graphObjectIds");graphOutputIds=new int[ids==null?0:ids.length()];for(int i=0;i<graphOutputIds.length;i++)graphOutputIds[i]=ids.getInt(i);castingRecords=o.optJSONArray("casting");if(castingRecords==null)castingRecords=new JSONArray();}
    static double[] numbers(JSONArray values,int count,double low,double high)throws Exception {
        if(values.length()!=count)throw new IOException("Invalid project dimensions or position");
        double[] result=new double[count];
        for(int i=0;i<count;i++) {
            result[i]=values.getDouble(i);
            if(!Double.isFinite(result[i])||result[i]<low||result[i]>high)throw new IOException("Invalid project measurements");
        }
        return result;
    }
    private static int dimensionCount(String type) {
        if(JewelleryCatalog.dimensions(type)>0)return JewelleryCatalog.dimensions(type);
        if(type.equals("Ring")||type.equals("Box")||type.equals("Sketch pad"))return 3;
        if(type.equals("Cylinder")||type.equals("Torus"))return 2;
        if(type.equals("Sphere")||type.equals("Circle"))return 1;
        if(type.equals("Ellipse")||type.equals("Rectangle"))return 2;
        if(type.equals("Helix")||type.equals("NURBS patch")||type.equals("Gemstone cutter"))return 3;
        if(type.equals("Bezel setting"))return 4;
        if(type.equals("Prong setting")||type.equals("Subdivision form"))return 6;return 0;
    }
    static void save(File destination,File cache)throws Exception {
        JSONArray objects=new JSONArray(NativeCad.objects());
        if(objects.length()>250)throw new IOException("Project exceeds 250 objects");
        File staging=Files.createTempDirectory(cache.toPath(),"save-").toFile();
        File temp=null;
        try {
            temp=File.createTempFile(destination.getName()+"-",".tmp",destination.getParentFile());
            JSONObject manifest=ProjectSchema.fresh(objects);manifest.put("variables",Expressions.json());manifest.put("worksheet",Worksheet.json());
            if(graphJson!=null){ParametricGraph.validate(graphJson);manifest.put("graph",new JSONObject(graphJson));Set<Integer> alive=new HashSet<>();for(int i=0;i<objects.length();i++)alive.add(objects.getJSONObject(i).getInt("id"));JSONArray outputs=new JSONArray();for(int id:graphOutputIds)if(alive.contains(id))outputs.put(id);manifest.put("graphObjectIds",outputs);}
            Set<Integer> live=new HashSet<>();for(int i=0;i<objects.length();i++)live.add(objects.getJSONObject(i).getInt("id"));JSONArray casting=new JSONArray();for(int i=0;i<castingRecords.length();i++){JSONObject c=castingRecords.getJSONObject(i);if(live.contains(c.getInt("source"))&&live.contains(c.getInt("output")))casting.put(c);}if(casting.length()>0)manifest.put("casting",casting);
            FeatureModel.validate(FeatureModel.recipes,live);manifest.put("features",FeatureModel.recipes);
            byte[] metadata=manifest.toString().getBytes(StandardCharsets.UTF_8);
            if(metadata.length>ArchiveIO.MAX_MANIFEST)throw new IOException("Project metadata is too large");
            ArchiveIO.Budget budget=new ArchiveIO.Budget(ArchiveIO.MAX_TOTAL);budget.add(metadata.length);
            try(ZipOutputStream zip=new ZipOutputStream(new FileOutputStream(temp))) {
                zip.putNextEntry(new ZipEntry("manifest.json"));zip.write(metadata);zip.closeEntry();
                for(int i=0;i<objects.length();i++) {
                    JSONObject o=objects.getJSONObject(i);int id=o.getInt("id");String ext=o.getBoolean("mesh")?"stl":"brep";
                    File shape=new File(staging,"part-"+id+"."+ext);NativeCad.write(shape.getAbsolutePath(),ext,id);
                    if(shape.length()>ArchiveIO.MAX_SHAPE)throw new IOException("Project shape is too large");
                    zip.putNextEntry(new ZipEntry(shape.getName()));
                    try(InputStream in=new FileInputStream(shape)){ArchiveIO.copy(in,zip,ArchiveIO.MAX_SHAPE,budget);}
                    zip.closeEntry();shape.delete();
                }
            }
            try(RandomAccessFile f=new RandomAccessFile(temp,"rw")){f.getFD().sync();}
            ArchiveIO.replaceFile(temp,destination);
        }finally{if(temp!=null)temp.delete();ArchiveIO.deleteTree(staging);}
    }
    static int schemaVersion(File source)throws Exception {
        try(ZipFile z=new ZipFile(source)){ZipEntry e=z.getEntry("manifest.json");if(e==null)throw new IOException("Missing project manifest");try(InputStream in=z.getInputStream(e);ByteArrayOutputStream out=new ByteArrayOutputStream()){ArchiveIO.copy(in,out,ArchiveIO.MAX_MANIFEST,null);return new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8)).optInt("version");}}
    }
    static int restore(File source,File cache)throws Exception{return restore(source,cache,null);}
    static int restore(File source,File cache,Map<Integer,Integer> restoredIds)throws Exception {
        File dir=ArchiveIO.unpackProject(source,cache);
        try {
            JSONObject manifest=ProjectSchema.read(new String(Files.readAllBytes(new File(dir,"manifest.json").toPath()),StandardCharsets.UTF_8));
            JSONArray objects=manifest.getJSONArray("objects");if(objects.length()>250)throw new IOException("Project exceeds 250 objects");
            Set<Integer> ids=new HashSet<>();
            // Validate all records before clearing the live workspace.
            for(int i=0;i<objects.length();i++) {
                JSONObject o=objects.getJSONObject(i);int id=o.getInt("id");String type=o.getString("type");boolean mesh=o.getBoolean("mesh");
                if(id<=0||!ids.add(id)||!TYPES.contains(type))throw new IOException("Invalid project object");
                int expected=dimensionCount(type);numbers(o.getJSONArray("dims"),expected,type.equals("Subdivision form")||type.equals("NURBS patch")?-10000:0.001,10000);
                numbers(o.getJSONArray("xyz"),3,-1000000,1000000);o.getBoolean("visible");if(o.has("color"))numbers(o.getJSONArray("color"),3,0,1);if(o.has("surfaceMaterial")){double[] m=numbers(o.getJSONArray("surfaceMaterial"),2,0,1);if(m[0]<.04)throw new IOException("Invalid material roughness");}
                if(o.optString("name","").length()>256||o.optString("layer","Default").isEmpty()||o.optString("layer","Default").length()>128)throw new IOException("Invalid object name or layer");
                if(mesh&&expected>0&&!type.equals("Subdivision form"))throw new IOException("Invalid mesh object");
                String ext=mesh?"stl":"brep";
                if(!new File(dir,"part-"+id+"."+ext).isFile())throw new IOException("Saved project shape is missing");
            }
            String loadedGraph=manifest.has("graph")?manifest.getJSONObject("graph").toString():null;if(loadedGraph!=null)ParametricGraph.validate(loadedGraph);
            JSONArray loadedCasting=manifest.optJSONArray("casting");if(loadedCasting!=null){if(loadedCasting.length()>250)throw new IOException("Too many casting records");for(int i=0;i<loadedCasting.length();i++){JSONObject c=loadedCasting.getJSONObject(i);if(!ids.contains(c.getInt("source"))||!ids.contains(c.getInt("output"))||c.getInt("source")==c.getInt("output"))throw new IOException("Invalid casting references");numbers(new JSONArray().put(c.getDouble("percent")),1,0,20);numbers(c.getJSONArray("originalBounds"),3,0,1000000);}}
            JSONArray loadedFeatures=manifest.optJSONArray("features");if(loadedFeatures!=null)FeatureModel.validate(loadedFeatures,ids);
            Worksheet.validate(manifest.optJSONObject("worksheet"));Expressions.validateJson(manifest.optJSONObject("variables"));
            Map<Integer,Integer> remap=new HashMap<>();NativeCad.clear();int selected=0;
            for(int i=0;i<objects.length();i++) {
                JSONObject o=objects.getJSONObject(i);double[] xyz=numbers(o.getJSONArray("xyz"),3,-1000000,1000000);
                String type=o.getString("type");int n=dimensionCount(type),id;
                if(n>0){id=NativeCad.create(type,numbers(o.getJSONArray("dims"),n,type.equals("Subdivision form")||type.equals("NURBS patch")?-10000:0.001,10000));NativeCad.move(id,xyz[0],xyz[1],xyz[2]);}
                else {String ext=o.getBoolean("mesh")?"stl":"brep";id=NativeCad.read(new File(dir,"part-"+o.getInt("id")+"."+ext).getAbsolutePath(),ext);NativeCad.restorePosition(id,xyz);}
                NativeCad.visible(id,o.getBoolean("visible"));if(o.has("color"))NativeCad.material(id,numbers(o.getJSONArray("color"),3,0,1));if(o.has("surfaceMaterial"))NativeCad.surfaceMaterial(id,numbers(o.getJSONArray("surfaceMaterial"),2,0,1));if(o.optBoolean("graphOwned"))NativeCad.markGraphOwned(id,true);NativeCad.properties(id,o.optString("name",""),o.optString("layer","Default"),o.optBoolean("locked"));remap.put(o.getInt("id"),id);selected=id;
            }
            JSONArray graphIds=manifest.optJSONArray("graphObjectIds");ArrayList<Integer> mapped=new ArrayList<>();for(int i=0;graphIds!=null&&i<graphIds.length();i++){Integer id=remap.get(graphIds.getInt(i));if(id==null)throw new IOException("Missing graph object");mapped.add(id);}graphOutputIds=new int[mapped.size()];for(int i=0;i<graphOutputIds.length;i++)graphOutputIds[i]=mapped.get(i);graphJson=loadedGraph;castingRecords=new JSONArray();for(int i=0;loadedCasting!=null&&i<loadedCasting.length();i++){JSONObject c=new JSONObject(loadedCasting.getJSONObject(i).toString());c.put("source",remap.get(c.getInt("source")));c.put("output",remap.get(c.getInt("output")));castingRecords.put(c);}
            FeatureModel.load(FeatureModel.remap(loadedFeatures,remap));Expressions.load(manifest.optJSONObject("variables"));Worksheet.load(manifest.optJSONObject("worksheet"));
            NativeCad.setWorkspace(workspace());
            if(restoredIds!=null){restoredIds.clear();restoredIds.putAll(remap);}
            return selected;
        }finally{ArchiveIO.deleteTree(dir);}
    }
}
