// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.util.*;
import org.json.*;

/** A bounded CAD command language. No shell, reflection, script or file execution. */
final class CommandLine {
    static final LinkedHashMap<String,String> HELP=new LinkedHashMap<>();
    static final Map<String,String> ALIASES=new HashMap<>(),CREATE=new HashMap<>();
    static {
        add("Help","Help [command] · show commands","?");
        add("History","History · recent command input");
        primitive("Box","Box", "width depth height");primitive("Ring","Ring","innerDiameter wall bandWidth");
        primitive("Cylinder","Cylinder","radius height");primitive("Sphere","Sphere","radius");primitive("Torus","Torus","majorRadius tubeRadius");
        primitive("Circle","Circle","radius");primitive("Ellipse","Ellipse","xRadius yRadius");primitive("Rectangle","Rectangle","width depth");
        primitive("Helix","Helix","radius pitch turns");primitive("SketchPad","Sketch pad","width depth height");
        primitive("Bezel","Bezel setting","stoneDiameter wall height seatDepth");primitive("Prongs","Prong setting","stoneDiameter wall height seatDepth count prongDiameter");
        primitive("Patch","NURBS patch","width depth bulge");primitive("GemCutter","Gemstone cutter","diameter pavilionDepth clearanceHeight");
        primitive("SubD","Subdivision form","width depth height levels topScale twistDegrees");
        for(String type:JewelleryCatalog.LABELS.keySet()){String command=type.replace(" ","");primitive(command,type,"dimensions; Help / template dialog shows fields");}
        add("Text","Text \"text\" height depth · system font outline solid");add("Mass","Mass densityGramsPerCubicCentimetre · estimated mass");add("Templates","Templates · jewellery and saved presets");add("PresetSave","PresetSave \"name\" · save selected primitive parameters");add("ArrayCurve","ArrayCurve · distribute copies on a curve");add("Allowance","Allowance · casting percentage and original geometry");
        add("Line","Line x1 y1 z1 x2 y2 z2");add("Arc","Arc centreX centreY centreZ radius startDegrees endDegrees · XY");add("Polyline","Polyline XYZ triples · 2 to 16 points");add("NURBSCurve","NURBSCurve XYZW poles · 2 to 16 poles");add("InterpCurve","InterpCurve XYZ through-points · 2 to 16 points");add("Revolve","Revolve axisX axisY axisZ directionX directionY directionZ angleDegrees");add("Samples","Samples · editable reference models");add("Guide","Guide · offline tutorials");add("Drawing","Drawing · A4 dimensioned SVG sheet");
        add("Spreadsheet","Spreadsheet · mobile A1:H32 grid and CSV");add("Cell","Cell address value · formula starts with =");add("SheetClear","SheetClear · remove worksheet cells; Undo restores");add("SheetImport","SheetImport · UTF-8 CSV file picker");add("SheetExport","SheetExport · UTF-8 CSV file picker");add("Align","Align targetId axis sourceAnchor [targetAnchor] · axis X/Y/Z, anchor Min/Centre/Max");add("FitSelected","FitSelected · frame selected geometry");add("Layers","Layers · visibility and lock controls");for(String n:new String[]{"LayerShow","LayerHide","LayerLock","LayerUnlock"})add(n,n+" layerName");
        add("Set","Set name expression · document variable");add("Unset","Unset name · remove unused variable");add("Variables","Variables · saved scalar expressions");add("Calc","Calc expression · scalar calculator");add("Measure","Measure [id1 id2] · object report / exact CAD distance");add("Distance","Distance XYZ XYZ · point distance in mm");add("Angle","Angle XYZ XYZ XYZ · middle point is vertex");add("RotateAround","RotateAround pivotXYZ axisXYZ angleDegrees");add("ScaleAround","ScaleAround pivotXYZ factor");add("ViewCube","ViewCube · choose an orthographic or ISO view");add("Left","Left · orthographic view");add("Select","Select objectId","sel");add("Move","Move x y z · absolute position");add("Rotate","Rotate xDegrees yDegrees zDegrees");add("Scale","Scale factor");
        add("Duplicate","Duplicate dx dy dz","copy");add("Delete","Delete · selected object","erase");add("Hide","Hide · selected object");add("Show","Show objectId");add("ShowAll","ShowAll");
        add("Undo","Undo","u");add("Redo","Redo");add("Rename","Rename \"name\"");add("Layer","Layer \"layerName\"");add("Lock","Lock · selected object");add("Unlock","Unlock · selected object");add("Clear","Clear · empty workspace; Undo restores it");
        add("Extrude","Extrude height OR Extrude dx dy dz · selected closed profile","extrudecrv");add("ExtrudeSurface","ExtrudeSurface height OR dx dy dz");
        add("Loft","Loft id1 id2 [id3 ...] · smooth solid");add("LoftSurface","LoftSurface id1 id2 [id3 ...]");
        add("Sweep","Sweep profileId railId");add("Pipe","Pipe radius");add("OffsetCurve","OffsetCurve distance");add("Offset","Offset distance · CAD shape");
        add("Union","Union firstId secondId","booleanunion","fuse");add("Cut","Cut bodyId toolId","booleandifference");add("Intersect","Intersect firstId secondId","booleanintersection");
        add("Fillet","Fillet radius","filletedge");add("Chamfer","Chamfer distance");add("Hollow","Hollow wall");add("Heal","Heal tolerance");add("Solidify","Solidify · selected closed shell");
        add("Section","Section z · flatten horizontal section to XY");add("Mirror","Mirror pointX pointY pointZ normalX normalY normalZ");
        add("Array","Array count stepX stepY stepZ");add("PolarArray","PolarArray count centreX centreY centreZ angle");
        for(String name:new String[]{"Render","Material","PNGOptions","Performance","Clip","ClipOff","Shaded","Studio","Zebra","Wireframe"})add(name,name+" · rendering option");add("Thickness","Thickness · approximate CAD wall ray samples");add("PrintPrep","PrintPrep · bed fit, placement and orientation");add("GraphFiles","GraphFiles · save/open recipes and batch variants");add("FillHoles","FillHoles · bounded planar mesh boundary repair");add("Selection","Selection · object / topology filters and multiple objects");add("FeatureHistory","FeatureHistory · saved operations and parameters");add("FeatureSet","FeatureSet numericParameters · rebuild selected recipe");add("Detach","Detach · keep selected geometry as a snapshot");add("Topology","Topology · indexed edges/faces");add("SurfacePoints","SurfacePoints · edit NURBS surface poles");add("Curvature","Curvature · sample selected single curve");
        add("Join","Join id1 id2 [id3 ...] · connected curves");add("Region","Region · one closed planar profile");add("TrimCurve","TrimCurve startFraction endFraction");add("ExtendLine","ExtendLine startLength endLength");add("ProjectCurve","ProjectCurve targetZ");add("FilletSelected","FilletSelected radius edgeIndex [edgeIndex ...]");add("ChamferSelected","ChamferSelected distance edgeIndex [edgeIndex ...]");add("ShellSelected","ShellSelected wall faceIndex [faceIndex ...]");add("TrimPatch","TrimPatch uStart uEnd vStart vEnd");add("UntrimPatch","UntrimPatch · restore full UV patch");
        add("Material","Material roughness metallic · no arguments opens editor");
        add("Color","Color red green blue · each 0 to 1","colour");
        for(String n:new String[]{"Fit","Top","Front","Right","Back","Bottom","Isometric","View","Create","Edit","Tools","Graph","Sketch","Open","Save","Export","Info","Analyze","Quality","Recovery","Tests","Objects","Gizmo"})add(n,n+" · open tool or view");
        ALIASES.put("ze","Fit");ALIASES.put("zoomextents","Fit");ALIASES.put("iso","Isometric");ALIASES.put("properties","Info");ALIASES.put("bezelsetting","Bezel");ALIASES.put("prongsetting","Prongs");
    }
    static void add(String name,String usage,String...aliases){HELP.put(name,usage);ALIASES.put(name.toLowerCase(Locale.US),name);for(String a:aliases)ALIASES.put(a,name);}
    static void primitive(String name,String type,String usage){CREATE.put(name,type);add(name,name+" "+usage+" · no arguments opens dimensions");}
    static final class Request {
        final String name;final List<String> args;
        Request(String name,List<String> args){this.name=name;this.args=Collections.unmodifiableList(args);}
        double[] values(){double[] p=new double[args.size()];for(int i=0;i<p.length;i++){try{p[i]=args.get(i).startsWith("=")?Worksheet.formula(args.get(i)):Expressions.evaluate(args.get(i));}catch(Exception e){throw new IllegalArgumentException("Expected a number: "+args.get(i));}if(!Double.isFinite(p[i]))throw new IllegalArgumentException("Numbers must be finite");}return p;}
        boolean ui(){return name.equals("Help")||name.equals("History")||(!engine(name))||(args.isEmpty()&&(CREATE.containsKey(name)||Arrays.asList("Move","Rotate","Scale","Duplicate","Extrude","ExtrudeSurface","Loft","LoftSurface","Sweep","Pipe","Union","Cut","Intersect","Fillet","Chamfer","Hollow","Offset","OffsetCurve","Section","Mirror","Array","PolarArray","Color","Heal","Material","Revolve","RotateAround","ScaleAround","Align").contains(name)));}
        boolean recordUndo(){return !name.equals("Undo")&&!name.equals("Redo")&&!name.equals("Select");}
    }
    static boolean engine(String n){return CREATE.containsKey(n)||Arrays.asList("Cell","SheetClear","Align","LayerShow","LayerHide","LayerLock","LayerUnlock","Set","Unset","RotateAround","ScaleAround","Line","Arc","Polyline","NURBSCurve","InterpCurve","Revolve","Material","Select","Move","Rotate","Scale","Duplicate","Delete","Hide","Show","ShowAll","Undo","Redo","Rename","Layer","Lock","Unlock","Clear","Extrude","ExtrudeSurface","Loft","LoftSurface","Sweep","Pipe","OffsetCurve","Offset","Union","Cut","Intersect","Fillet","Chamfer","Hollow","Heal","Solidify","Section","Mirror","Array","PolarArray","Color","FeatureSet","Detach","Join","Region","TrimCurve","ExtendLine","ProjectCurve","FilletSelected","ChamferSelected","ShellSelected","TrimPatch","UntrimPatch").contains(n);}
    static Request parse(String input){
        if(input==null||input.length()>4096)throw new IllegalArgumentException("Command is missing or too long");
        ArrayList<String> tokens=new ArrayList<>();StringBuilder token=new StringBuilder();boolean quoted=false,escape=false,started=false;
        for(char c:input.toCharArray()){if(c=='\n'||c=='\r'||c==';'||c==0)throw new IllegalArgumentException("Enter one command at a time");if(escape){token.append(c);started=true;escape=false;continue;}if(c=='\\'&&quoted){escape=true;continue;}if(c=='\"'){quoted=!quoted;started=true;continue;}if(!quoted&&(Character.isWhitespace(c)||c==',')){if(started){tokens.add(token.toString());token.setLength(0);started=false;}}else{token.append(c);started=true;}}
        if(quoted||escape)throw new IllegalArgumentException("Close the quoted value");if(started)tokens.add(token.toString());if(tokens.isEmpty())throw new IllegalArgumentException("Enter a command, or Help");if(tokens.size()>65)throw new IllegalArgumentException("Too many command arguments");
        String raw=tokens.remove(0);if(raw.startsWith("_"))raw=raw.substring(1);String name=ALIASES.get(raw.toLowerCase(Locale.US));if(name==null)throw new IllegalArgumentException("Unknown command: "+raw+". Type Help.");return new Request(name,tokens);
    }
    static void count(Request r,int...allowed){for(int n:allowed)if(r.args.size()==n)return;throw new IllegalArgumentException(HELP.get(r.name));}
    static int integer(double x){if(x<1||x>Integer.MAX_VALUE||x!=Math.rint(x))throw new IllegalArgumentException("Expected a positive integer");return (int)x;}
    static int execute(Request r,int selected)throws Exception{
        if(r.ui())throw new IllegalArgumentException("This command opens a UI tool");String n=r.name;
        if(n.equals("Cell")){count(r,2);Worksheet.set(r.args.get(0),r.args.get(1));return selected;}
        if(n.equals("SheetClear")){count(r,0);Worksheet.reset();return selected;}
        if(n.equals("Align")){count(r,3,4);PrecisionTools.align(selected,PrecisionTools.identifier(r.args.get(0)),r.args.get(1),r.args.get(2),r.args.size()==4?r.args.get(3):r.args.get(2));return selected;}
        if(n.equals("LayerShow")||n.equals("LayerHide")||n.equals("LayerLock")||n.equals("LayerUnlock")){count(r,1);LayerTools.apply(r.args.get(0),n.equals("LayerShow")?Boolean.TRUE:n.equals("LayerHide")?Boolean.FALSE:null,n.equals("LayerLock")?Boolean.TRUE:n.equals("LayerUnlock")?Boolean.FALSE:null);return selected;}
        if(n.equals("Set")){count(r,2);Expressions.set(r.args.get(0),r.args.get(1));return selected;}
        if(n.equals("Unset")){count(r,1);Expressions.remove(r.args.get(0));return selected;}
        if(Arrays.asList("Rename","Layer","Lock","Unlock").contains(n)){count(r,n.equals("Rename")||n.equals("Layer")?1:0);JSONArray list=new JSONArray(NativeCad.objects());JSONObject o=null;for(int i=0;i<list.length();i++)if(list.getJSONObject(i).getInt("id")==selected)o=list.getJSONObject(i);if(o==null)throw new IllegalArgumentException("Select an object");NativeCad.properties(selected,n.equals("Rename")?r.args.get(0):o.optString("name",""),n.equals("Layer")?r.args.get(0):o.optString("layer","Default"),n.equals("Lock")||(!n.equals("Unlock")&&o.optBoolean("locked")));return selected;}double[] p=r.values();
        if(CREATE.containsKey(n))return NativeCad.create(CREATE.get(n),p);
        if(n.equals("RotateAround")){count(r,7);PrecisionTools.rotateAround(selected,p);return selected;}
        if(n.equals("ScaleAround")){count(r,4);PrecisionTools.scaleAround(selected,p);return selected;}
        if(n.equals("Material")){count(r,2);NativeCad.surfaceMaterial(selected,p);return selected;}
        if(n.equals("Arc")){count(r,6);return NativeCad.drawing(p,new int[]{2});}
        if(n.equals("Line")){count(r,6);return FeatureModel.curve("Polyline",new double[]{p[0],p[1],p[2],1,p[3],p[4],p[5],1},false,0);}
        if(n.equals("Polyline")||n.equals("NURBSCurve")||n.equals("InterpCurve")){int stride=n.equals("NURBSCurve")?4:3;if(p.length%stride!=0||p.length/stride<2||p.length/stride>16)throw new IllegalArgumentException(HELP.get(n));double[] poles=new double[p.length/stride*4];for(int i=0;i<poles.length/4;i++){System.arraycopy(p,i*stride,poles,i*4,3);poles[i*4+3]=stride==4?p[i*stride+3]:1;}return FeatureModel.curve(n.equals("NURBSCurve")?"NURBS curve":n.equals("InterpCurve")?"Interpolated curve":"Polyline",poles,false,0);}
        if(n.equals("Select")){count(r,1);int id=integer(p[0]);JSONArray a=new JSONArray(NativeCad.objects());for(int i=0;i<a.length();i++)if(a.getJSONObject(i).getInt("id")==id)return id;throw new IllegalArgumentException("Object does not exist");}
        if(n.equals("Clear")){count(r,0);NativeCad.clear();ProjectStore.reset();return 0;}
        if(n.equals("Undo")){count(r,0);if(!NativeCad.undo())throw new IllegalArgumentException("Nothing to undo");ProjectStore.applyWorkspace(NativeCad.getWorkspace());return selected;}
        if(n.equals("Redo")){count(r,0);if(!NativeCad.redo())throw new IllegalArgumentException("Nothing to redo");ProjectStore.applyWorkspace(NativeCad.getWorkspace());return selected;}
        if(n.equals("ShowAll")){count(r,0);JSONArray a=new JSONArray(NativeCad.objects());for(int i=0;i<a.length();i++)NativeCad.visible(a.getJSONObject(i).getInt("id"),true);return selected;}
        if(n.equals("Show")){count(r,1);NativeCad.visible(integer(p[0]),true);return selected;}
        if(n.equals("Move")){count(r,3);FeatureModel.move(selected,p[0],p[1],p[2]);return selected;}
        if(n.equals("Rotate")){count(r,3);FeatureModel.rotate(selected,p[0],p[1],p[2]);return selected;}
        if(n.equals("Scale")){count(r,1);FeatureModel.scale(selected,p[0]);return selected;}
        if(n.equals("Duplicate")){count(r,3);return NativeCad.duplicate(selected,p[0],p[1],p[2]);}
        if(n.equals("Delete")){count(r,0);FeatureModel.remove(selected);return 0;}
        if(n.equals("Hide")){count(r,0);NativeCad.visible(selected,false);return selected;}
        if(n.equals("Union")||n.equals("Cut")||n.equals("Intersect")){count(r,2);return FeatureModel.operation(n,integer(p[0]),integer(p[1]),0);}
        if(n.equals("Fillet")){count(r,1);return FeatureModel.operation(n,selected,0,p[0]);}
        if(n.equals("Mirror")){count(r,6);return NativeCad.mirror(selected,p);}
        if(n.equals("Array")){count(r,4);return NativeCad.array(selected,"Linear array",integer(p[0]),new double[]{p[1],p[2],p[3],0});}
        if(n.equals("PolarArray")){count(r,5);return NativeCad.array(selected,"Polar array",integer(p[0]),new double[]{p[1],p[2],p[3],p[4]});}
        if(n.equals("Color")){count(r,3);NativeCad.material(selected,p);return selected;}
        if(n.equals("Detach")){count(r,0);FeatureModel.detach(selected);return selected;}
        if(n.equals("FeatureSet")){FeatureModel.parameters(selected,p);return selected;}
        String kind=n;int[] ids={selected};
        if(n.equals("Revolve")){count(r,7);kind="Revolve solid";}
        else if(n.equals("Join")){if(p.length<2||p.length>8)throw new IllegalArgumentException("Join needs 2 to 8 IDs");ids=new int[p.length];for(int i=0;i<p.length;i++)ids[i]=integer(p[i]);p=new double[0];kind="Join curves";}
        else if(n.equals("Region")){count(r,0);kind="Planar region";}
        else if(n.equals("TrimCurve")){count(r,2);kind="Trim curve";}
        else if(n.equals("ExtendLine")){count(r,2);kind="Extend line";}
        else if(n.equals("ProjectCurve")){count(r,1);kind="Project curve";}
        else if(n.equals("TrimPatch")){count(r,4);kind="Trim patch";}
        else if(n.equals("UntrimPatch")){count(r,0);kind="Untrim patch";}
        else if(n.endsWith("Selected")){if(p.length<2||p.length>16)throw new IllegalArgumentException("Enter radius/wall plus 1 to 15 indices");kind=n.equals("FilletSelected")?"Selected fillet":n.equals("ChamferSelected")?"Selected chamfer":"Selected shell";}
        else 
        if(n.equals("Extrude")||n.equals("ExtrudeSurface")){count(r,1,3);kind=n.equals("Extrude")?"Extrude solid":"Extrude surface";if(p.length==1)p=new double[]{0,0,p[0]};}
        else if(n.equals("Loft")||n.equals("LoftSurface")){if(p.length<2||p.length>8)throw new IllegalArgumentException("Loft needs 2 to 8 profile IDs");ids=new int[p.length];for(int i=0;i<p.length;i++)ids[i]=integer(p[i]);p=new double[]{0};kind=n.equals("Loft")?"Loft solid":"Loft surface";}
        else if(n.equals("Sweep")){count(r,2);ids=new int[]{integer(p[0]),integer(p[1])};p=new double[0];kind="Sweep solid";}
        else if(n.equals("Section")){count(r,1);p=new double[]{0,0,p[0],0,0,1,1};}
        else if(n.equals("Solidify")){count(r,0);kind="Solidify shell";}
        else {count(r,1);kind=n.equals("Pipe")?"Pipe along curve":n.equals("OffsetCurve")?"Offset curve":n.equals("Offset")?"Offset shape":n.equals("Hollow")?"Hollow top":n.equals("Heal")?"Heal CAD":n;}
        int result=FeatureModel.model(kind,ids,p);for(int id:ids)NativeCad.visible(id,false);return result;
    }
    static String help(String name){if(name!=null&&!name.isEmpty()){String canonical=ALIASES.get(name.toLowerCase(Locale.US));if(canonical==null)throw new IllegalArgumentException("Unknown command");return HELP.get(canonical);}StringBuilder b=new StringBuilder("Dimensions in mm. Select an object before editing. IDs appear on object chips.\nEnter repeats the previous command. Commands are local CAD actions.\n\n");for(String s:HELP.values())b.append(s).append('\n');return b.toString();}
}
