package org.freecad.mobilelab;
import org.json.*;
/** Portable metadata checks that do not load the native kernel. */
public final class SchemaRegression {
    static int checks;interface Action{void run()throws Exception;}
    static void check(boolean b){if(!b)throw new AssertionError();checks++;}
    static void reject(Action a)throws Exception{try{a.run();}catch(Exception e){checks++;return;}throw new AssertionError("Invalid metadata accepted");}
    public static void main(String[] args)throws Exception {
        JSONObject legacy=new JSONObject().put("format","FreeCADMobileLab").put("version",1).put("units","mm").put("objects",new JSONArray());String original=legacy.toString();JSONObject migrated=ProjectSchema.read(original);
        check(legacy.getInt("version")==1);check(migrated.getInt("version")==2);check(migrated.getInt("minimumReader")==2);check(migrated.getJSONArray("features").length()==0);check(migrated.getString("writer").equals("migrated-from-v1"));check(original.equals(legacy.toString()));
        JSONObject current=ProjectSchema.fresh(new JSONArray()).put("features",new JSONArray());check(ProjectSchema.read(current.toString()).getString("writer").equals(ReleaseInfo.VERSION));
        for(String field:new String[]{"features","minimumReader","writer","geometryKernel","objects"}){JSONObject bad=new JSONObject(current.toString());bad.remove(field);reject(()->ProjectSchema.read(bad.toString()));}
        reject(()->ProjectSchema.read(current.toString().replace("OCCT-7.9.2","OCCT-9")));reject(()->ProjectSchema.read(new JSONObject(current.toString()).put("minimumReader",3).toString()));reject(()->ProjectSchema.read(new JSONObject(current.toString()).put("version",3).toString()));reject(()->ProjectSchema.read(new JSONObject(legacy.toString()).put("units","inch").toString()));reject(()->ProjectSchema.read(new JSONObject(legacy.toString()).put("version",0).toString()));reject(()->ProjectSchema.read("not json"));
        check(CommandLine.parse("Material").ui());check(CommandLine.parse("Revolve").ui());check(!CommandLine.parse("Revolve 0 0 0 0 1 0 360").ui());check(!CommandLine.parse("Material .25 .85").ui());check(CommandLine.parse("Guide").ui());check(CommandLine.parse("Samples").ui());check(CommandLine.parse("Drawing").ui());
        System.out.println("PASS: "+checks+" metadata compatibility/rejection and command dialog routing assertions; no native/runtime pass implied");
    }
}
