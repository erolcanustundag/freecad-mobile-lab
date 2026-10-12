// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Native geometry, graph, drawing and persistence integration tests. */
public final class FreeformRegression {
    interface Task{void run()throws Exception;}
    static int checks;
    static void check(boolean value,String message){if(!value)throw new AssertionError(message);checks++;}
    static void near(double actual,double expected,double tolerance){check(Math.abs(actual-expected)<=tolerance,"Expected "+expected+", got "+actual);}
    static void rejects(Task t)throws Exception{try{t.run();}catch(Exception e){checks++;return;}throw new AssertionError("Invalid input accepted");}
    static void txn(Task t)throws Exception{NativeCad.beginTransaction(true);try{t.run();new MeshFrame(NativeCad.mesh(0),NativeCad.lines(0));NativeCad.commitTransaction();}catch(Throwable e){NativeCad.rollbackTransaction();throw e;}}
    static JSONObject object(int id)throws Exception{JSONArray a=new JSONArray(NativeCad.objects());for(int i=0;i<a.length();i++)if(a.getJSONObject(i).getInt("id")==id)return a.getJSONObject(i);throw new AssertionError("Missing object");}
    static JSONObject report(int id)throws Exception{return new JSONObject(NativeCad.analyze(id,3));}
    static double volume(int id)throws Exception{return object(id).getDouble("volume");}
    static int model(String kind,int id,double...p){return NativeCad.model(kind,new int[]{id},p);}
    static int create(String kind,double...p){return NativeCad.create(kind,p);}
    static String read(File f)throws Exception{return new String(Files.readAllBytes(f.toPath()),StandardCharsets.UTF_8);}
    static void pass(String s){System.out.println("PASS: "+s);}
    public static void main(String[] args)throws Exception{
        File root=Files.createTempDirectory("cad-freeform-").toFile(),cache=new File(root,"cache");cache.mkdir();
        try{
            NativeCad.clear();int circle=create("Circle",3),rectangle=create("Rectangle",10,6),ellipse=create("Ellipse",8,4);
            check(object(circle).getBoolean("curve"),"Circle not classified as a profile");check(NativeCad.lines(circle).length>100,"Profiles are invisible");
            MeshFrame frame=new MeshFrame(NativeCad.mesh(0),NativeCad.lines(0));check(frame.count==0&&frame.lineCount>0&&frame.radius>7,"Curve-only bounds are wrong");
            SoftwareRasterizer.Image image=SoftwareRasterizer.render(frame,360,360,0,0,1,0,0);int pixels=0;for(int x:image.pixels)if(x!=SoftwareRasterizer.BACKGROUND)pixels++;check(pixels>200,"Software curve rendering is empty");
            int pad=model("Extrude solid",rectangle,0,0,2);near(volume(pad),120,1e-5);int cylinder=model("Extrude solid",circle,0,0,4);near(volume(cylinder),36*Math.PI,1e-5);
            int wall=model("Extrude surface",circle,0,0,4);check(report(wall).getInt("solids")==0&&report(wall).getDouble("area")>70,"Surface extrusion became a solid or is empty");
            pass("curve-only software display, circle/ellipse/rectangle and exact solid/surface extrusions");

            int lower=create("Circle",5),upper=create("Circle",3);NativeCad.move(upper,0,0,10);
            int loft=NativeCad.model("Loft solid",new int[]{lower,upper},new double[]{0});near(volume(loft),Math.PI*10*(25+15+9)/3,.02);
            int loftSurface=NativeCad.model("Loft surface",new int[]{lower,upper},new double[]{1});check(report(loftSurface).getInt("solids")==0,"Surface loft closed unexpectedly");
            int profile=create("Rectangle",2,3);NativeCad.move(profile,3,0,0);int revolved=model("Revolve solid",profile,0,0,0,0,1,0,360);near(volume(revolved),Math.PI*12*3,1e-5);
            int rail=NativeCad.curve("Polyline",new double[]{0,0,0,1,0,0,10,1},false,0),section=create("Circle",1);
            int sweep=NativeCad.model("Sweep solid",new int[]{section,rail},new double[0]);near(volume(sweep),Math.PI*10,1e-5);
            int pipe=model("Pipe along curve",rail,.7);near(volume(pipe),Math.PI*.49*10,1e-5);
            int helix=create("Helix",5,3,2),helixPipe=model("Pipe along curve",helix,.3);check(volume(helixPipe)>15&&volume(helixPipe)<21,"Helical pipe volume wrong");
            pass("smooth/ruled lofts, exact revolutions, profile sweeps, straight and helical pipes");

            double[] poles={-8,0,0,1,-4,8,0,1,4,8,0,1,8,0,0,1};int nurbs=NativeCad.curve("NURBS curve",poles,false,0);
            JSONArray control=new JSONArray(NativeCad.curveData(nurbs));check(control.length()==16,"NURBS control points lost");near(control.getDouble(1),0,1e-10);NativeCad.move(nurbs,2,0,0);control=new JSONArray(NativeCad.curveData(nurbs));near(control.getDouble(0),-6,1e-10);
            double beforeHeight=object(nurbs).getJSONArray("bounds").getDouble(1);double[] weighted=poles.clone();weighted[7]=4;NativeCad.curve("NURBS curve",weighted,false,nurbs);check(object(nurbs).getJSONArray("bounds").getDouble(1)>beforeHeight+.1,"NURBS weights did not change the curve");
            int interpolated=NativeCad.curve("Interpolated curve",new double[]{0,0,0,1,4,0,0,1,4,4,0,1,0,4,0,1},true,0);int organicPad=model("Extrude solid",interpolated,0,0,2);check(volume(organicPad)>20,"Closed interpolated profile did not form solid");
            final int badNurbs=nurbs;String stable=NativeCad.objects();rejects(()->NativeCad.curve("NURBS curve",poles,true,badNurbs));rejects(()->NativeCad.curve("NURBS curve",new double[]{0,0,0,1,0,0,0,1},false,0));check(stable.equals(NativeCad.objects()),"Failed curve edit changed geometry");
            pass("rational NURBS weights, translated control points, in-place editing, closed splines and invalid-input preservation");

            int box=create("Box",10,8,6),cross=model("Section",box,0,0,3,0,0,1,1);JSONObject draw=report(cross);near(draw.getDouble("length"),36,1e-5);near(object(cross).getJSONArray("bounds").getDouble(2),0,1e-5);
            File svg=new File(root,"section.svg"),dxf=new File(root,"section.dxf");NativeCad.write(svg.toString(),"svg",cross);NativeCad.write(dxf.toString(),"dxf",cross);java.util.regex.Matcher width=java.util.regex.Pattern.compile("width=\"([0-9.eE+-]+)mm\"").matcher(read(svg));check(width.find()&&read(svg).contains("polyline"),"SVG drawing dimensions missing");near(Double.parseDouble(width.group(1)),10,1e-5);check(read(dxf).contains("$INSUNITS\n70\n4")&&read(dxf).endsWith("EOF\n"),"DXF units or terminator missing");
            int solidified=model("Solidify shell",box);near(volume(solidified),480,1e-5);
            int sides=model("Extrude surface",rectangle,0,0,2),bottom=create("NURBS patch",10,6,0),top=create("NURBS patch",10,6,0);NativeCad.move(top,0,0,2);int sewn=NativeCad.model("Sew surfaces",new int[]{sides,bottom,top},new double[]{.00001});int joined=model("Solidify shell",sewn);near(volume(joined),120,1e-4);
            int hollow=model("Hollow top",box,1);near(volume(hollow),480-8*6*5,1e-4);check(report(hollow).getBoolean("validCAD"),"Hollow body invalid");
            int chamfer=model("Chamfer",box,.2);check(volume(chamfer)<480&&volume(chamfer)>450,"Chamfer did not cut corners");int healed=model("Heal CAD",box,.001);near(volume(healed),480,1e-5);int offset=model("Offset shape",box,.1);check(volume(offset)>480,"Shape offset did not enlarge solid");
            int curveOffset=model("Offset curve",circle,.5);check(Math.abs(object(curveOffset).getJSONArray("bounds").getDouble(0)-6)>.9,"Planar curve offset did not change radius");
            int secondBox=create("Box",2,2,2);NativeCad.move(secondBox,20,0,0);near(NativeCad.distance(box,secondBox),14,1e-5);
            int patch=create("NURBS patch",20,16,8);check(report(patch).getInt("solids")==0&&report(patch).getDouble("area")>320,"NURBS surface patch is missing");
            pass("exact sections, millimetre SVG/DXF, hollowing, chamfer, healing, offsets, distance and NURBS surfaces");

            int bezel=create("Bezel setting",6,.6,3,1),prong=create("Prong setting",6,.6,4,2,4,.9),cutter=create("Gemstone cutter",6,2.5,2);
            check(report(bezel).getBoolean("validCAD")&&report(prong).getBoolean("validCAD")&&volume(cutter)>0,"Jewellery solids invalid");
            near(object(bezel).getJSONArray("bounds").getDouble(0),7.2,1e-5);check(report(prong).getInt("solids")==1,"Prong gallery is disconnected");
            int subdiv=create("Subdivision form",16,12,20,3,1,20);check(object(subdiv).getBoolean("mesh")&&object(subdiv).getLong("sourceTriangles")==768,"Catmull-Clark subdivision count wrong");check(report(subdiv).getBoolean("watertightMesh"),"Subdivision mesh is open");
            int repaired=model("Repair mesh",subdiv,.00001);check(report(repaired).getBoolean("watertightMesh"),"Mesh repair opened the surface");
            final int badSubdiv=subdiv;rejects(()->NativeCad.create("Subdivision form",new double[]{1,1,1,5,1,0}));rejects(()->NativeCad.model("Repair mesh",new int[]{badSubdiv},new double[]{0}));
            pass("connected bezel/prong settings, gemstone cutters, watertight Catmull-Clark meshes and repair");

            NativeCad.move(secondBox,10,0,0);int polar=NativeCad.array(secondBox,"Polar array",4,new double[]{0,0,0,360}),linear=NativeCad.array(secondBox,"Linear array",3,new double[]{4,0,0,0});near(volume(polar),32,1e-5);near(volume(linear),24,1e-5);int mirrored=NativeCad.mirror(secondBox,new double[]{0,0,0,1,0,0});near(volume(mirrored),8,1e-5);NativeCad.material(bezel,new double[]{.83,.64,.25});near(object(bezel).getJSONArray("color").getDouble(0),.83,1e-6);
            pass("linear/polar geometry arrays, mirror copies and saved object colours");

            File iges=new File(root,"model.igs"),obj=new File(root,"mesh.obj"),coarse=new File(root,"coarse.stl"),fine=new File(root,"fine.stl");NativeCad.write(iges.toString(),"iges",box);int roundIges=NativeCad.read(iges.toString(),"iges");near(volume(roundIges),480,.01);NativeCad.write(obj.toString(),"obj",bezel);int roundObj=NativeCad.read(obj.toString(),"obj");check(report(roundObj).getBoolean("watertightMesh"),"OBJ round trip opened mesh");
            int sphere=create("Sphere",4);NativeCad.writeWithTolerance(coarse.toString(),"stl",sphere,.5);NativeCad.writeWithTolerance(fine.toString(),"stl",sphere,.005);check(fine.length()>coarse.length()*1.2,"STL tolerance did not change triangle detail");
            File malformed=new File(root,"bad.obj");Files.write(malformed.toPath(),"v 0 0 0\nf 1 2 3\n".getBytes(StandardCharsets.UTF_8));rejects(()->NativeCad.read(malformed.toString(),"obj"));
            File concave=new File(root,"concave.obj");Files.write(concave.toPath(),"v 0 0 0\nv 4 0 0\nv 4 4 0\nv 2 2 0\nv 0 4 0\nf -5 -4 -3 -2 -1\n".getBytes(StandardCharsets.UTF_8));int concaveMesh=NativeCad.read(concave.toString(),"obj");near(report(concaveMesh).getDouble("area"),12,1e-6);check(object(concaveMesh).getLong("sourceTriangles")==3,"Concave OBJ polygon not triangulated");
            File badLine=new File(root,"long.obj");byte[] longLine=new byte[70000];java.util.Arrays.fill(longLine,(byte)'x');Files.write(badLine.toPath(),longLine);rejects(()->NativeCad.read(badLine.toString(),"obj"));
            pass("IGES CAD and OBJ mesh round trips, configurable STL tessellation and malformed OBJ rejection");

            final String graph=ParametricGraph.example();txn(()->{int id=ParametricGraph.evaluate(graph,new int[0]);ProjectStore.graphJson=graph;ProjectStore.graphOutputIds=ParametricGraph.lastOutputs.clone();near(volume(id),Math.PI*(10.6*10.6-81)*3,1e-5);});
            int count=new JSONArray(NativeCad.objects()).length();JSONObject changed=new JSONObject(graph);changed.getJSONArray("nodes").getJSONObject(0).put("value",20);String updated=changed.toString();txn(()->{int id=ParametricGraph.evaluate(updated,ProjectStore.graphOutputIds);ProjectStore.graphJson=updated;ProjectStore.graphOutputIds=ParametricGraph.lastOutputs.clone();near(volume(id),Math.PI*(11.6*11.6-100)*3,1e-5);});check(new JSONArray(NativeCad.objects()).length()==count,"Graph re-evaluation leaked old shapes");check(NativeCad.undo(),"Graph Undo failed");txn(()->{ParametricGraph.evaluate(updated,ProjectStore.graphOutputIds);ProjectStore.graphOutputIds=ParametricGraph.lastOutputs.clone();});check(new JSONArray(NativeCad.objects()).length()==count,"Graph regeneration after Undo leaked geometry");
            JSONObject cycle=new JSONObject(graph);cycle.getJSONArray("nodes").getJSONObject(0).put("kind","Add").put("inputs",new JSONArray("[1,2]"));rejects(()->ParametricGraph.validate(cycle.toString()));JSONObject wrong=new JSONObject(graph);wrong.getJSONArray("nodes").getJSONObject(3).put("inputs",new JSONArray("[4,2,3]"));rejects(()->ParametricGraph.validate(wrong.toString()));
            pass("typed parametric graph, slider-driven regeneration, no leaked shapes, cycle/type validation");

            File project=new File(root,"freeform.fcml");JSONArray expected=new JSONArray(NativeCad.objects());ProjectStore.save(project,cache);txn(()->ProjectStore.restore(project,cache));JSONArray actual=new JSONArray(NativeCad.objects());check(actual.length()==expected.length(),"New object types lost on reopen");for(int i=0;i<actual.length();i++){JSONObject a=actual.getJSONObject(i),b=expected.getJSONObject(i);check(a.getBoolean("curve")==b.getBoolean("curve"),"Curve kind lost");check(a.getBoolean("mesh")==b.getBoolean("mesh"),"Mesh kind lost");for(int j=0;j<3;j++){near(a.getJSONArray("bounds").getDouble(j),b.getJSONArray("bounds").getDouble(j),.001);near(a.getJSONArray("color").getDouble(j),b.getJSONArray("color").getDouble(j),1e-6);}}
            check(ProjectStore.graphJson.equals(updated)&&ProjectStore.graphOutputIds.length>0,"Graph lost on project reopen");txn(()->ParametricGraph.evaluate(updated,ProjectStore.graphOutputIds));
            int selected=new JSONArray(NativeCad.objects()).getJSONObject(0).getInt("id");String before=NativeCad.objects();rejects(()->txn(()->NativeCad.model("Extrude solid",new int[]{selected},new double[]{0,0,0})));check(NativeCad.objects().equals(before),"Failed modelling transaction changed project");check(cache.list().length==0,"Project temporary files leaked");
            pass("all new object types, colours and node graph project round trip; modelling failure rollback");
            System.out.println("PASS: "+checks+" freeform integration assertions");
        }finally{ArchiveIO.deleteTree(root);}
    }
}
