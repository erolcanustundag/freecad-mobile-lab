package org.freecad.mobilelab;
import org.json.*;

/** Small editable examples added to the current workspace. */
final class SampleCatalog {
    static final String[] LABELS={"18 mm comfort ring","Signet with circular seat","Pendant frame","Editable plate with hole","Loft and weighted curve"};
    static final String[] GRAPHS={"Graph · parametric ring","Graph · bezel pattern"};
    private static int finish(int id,String name){NativeCad.properties(id,name,"Examples",false);NativeCad.material(id,new double[]{.83,.64,.25});NativeCad.surfaceMaterial(id,new double[]{.25,.85});return id;}
    static int add(int choice)throws Exception {
        if(choice==0)return finish(NativeCad.create("Comfort ring",new double[]{18,1.6,3,.4}),LABELS[0]);
        if(choice==1){int body=NativeCad.create("Signet ring",JewelleryCatalog.DEFAULTS.get("Signet ring").clone());int tool=NativeCad.create("Cylinder",new double[]{1.2,3});NativeCad.move(tool,0,11,2);int result=FeatureModel.operation("Cut",body,tool,0);NativeCad.visible(body,false);NativeCad.visible(tool,false);return finish(result,LABELS[1]);}
        if(choice==2)return finish(NativeCad.create("Pendant frame",JewelleryCatalog.DEFAULTS.get("Pendant frame").clone()),LABELS[2]);
        if(choice==3){int root=NativeCad.create("Rectangle",new double[]{20,12});int pad=FeatureModel.model("Extrude solid",new int[]{root},new double[]{0,0,3});int tool=NativeCad.create("Cylinder",new double[]{2,5});NativeCad.move(tool,0,0,-1);int result=FeatureModel.operation("Cut",pad,tool,0);NativeCad.visible(root,false);NativeCad.visible(pad,false);NativeCad.visible(tool,false);return finish(result,"Plate · edit hidden Rectangle root");}
        if(choice==4){int a=NativeCad.create("Circle",new double[]{4}),b=NativeCad.create("Circle",new double[]{7});NativeCad.move(b,0,0,12);int result=FeatureModel.model("Loft solid",new int[]{a,b},new double[]{0});NativeCad.visible(a,false);NativeCad.visible(b,false);int curve=FeatureModel.curve("NURBS curve",new double[]{12,-8,0,1,18,-4,4,2,12,4,8,1,18,8,12,1},false,0);NativeCad.properties(curve,"Weighted freeform curve","Examples",false);return finish(result,"Editable circular loft");}
        throw new IllegalArgumentException("Unknown sample");
    }
    static String graph(int choice)throws Exception {
        if(choice==0)return ParametricGraph.example();
        if(choice!=1)throw new IllegalArgumentException("Unknown graph sample");
        JSONArray nodes=new JSONArray();double[] values={5,.5,3,1,8,8,0,0};
        for(int i=0;i<values.length;i++)nodes.put(new JSONObject().put("id",i+1).put("kind","Number").put("value",values[i]).put("inputs",new JSONArray()).put("group",i<4?"Setting":"Pattern"));
        nodes.put(new JSONObject().put("id",9).put("kind","Bezel").put("inputs",new JSONArray(new int[]{1,2,3,4})).put("group","Setting"));
        nodes.put(new JSONObject().put("id",10).put("kind","Linear array").put("inputs",new JSONArray(new int[]{9,5,6,7,8})).put("group","Pattern"));
        String json=new JSONObject().put("version",1).put("nodes",nodes).put("outputs",new JSONArray(new int[]{10})).toString();ParametricGraph.validate(json);return json;
    }
}
