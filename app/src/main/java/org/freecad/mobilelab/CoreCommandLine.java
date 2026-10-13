// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.util.*;

/** Human command syntax for the upstream document adapter. */
final class CoreCommandLine {
    static final String SKETCH_HELP="Sketch Profile\nSketchLine Profile 0 0 30 0\nSketchCircle Profile 10 10 5\nSketchArc Profile 0 0 10 0 180\nSketchEllipse Profile 0 0 20 10\nSketchSpline Profile 3 0,0;10,20;20,20;30,0 [1,2,2,1]\nConstruction Profile 0 true\nConstraint Profile Horizontal 0\nConstraint Profile Coincident 0 1 -1 1\nConstraint Profile Distance 0 30\nDatum Profile 2 40 mm\nMovePoint Profile 0 2 40 0\nDeleteGeometry Profile 0\nDeleteConstraint Profile 0\nSketchPreview Profile\nSketchPlane Profile XZ 0 0 10\nSketchPlacement Profile 0 0 0 0 0 0\nSketchAttach Profile Solid Face6\nSketchOffset Profile 0 0 2 0 0 0\nSketchDetach Profile\nExternal Profile Solid Edge9\nConstraint Profile Coincident 0 1 -3 1\nDeleteExternal Profile 0\nSketchTrim Profile 0 5 0\nSketchExtend Profile 0 5 2\nSketchFillet Profile 0 1 8 0 10 2 2\nSketchSplit Profile 0 5 0\nSketchMirror Profile 0,1 Y\nSketchArray Profile 0 3 2 10 0 1 false\nConstraint Profile Symmetric 0 1 0 2 -2\nConstraint Profile Symmetric 0 1 1 2 -1 1\nDriving Profile 0 false\nConstraint Profile PointOnObject 0 1 -1\nConstraint Profile DistanceX 0 20\nConstraint Profile DistanceY 0 1 -5\nConstraint Profile DistanceX 0 1 1 2 30\nConstraint Profile Block 0\nActive Profile 0 false\n\nGeometry/constraint indices start at 0. Constraint angles use degrees; dimensions use mm. Datum accepts units. Preview uses sketch-local XY coordinates. External projected edges use -3, -4, etc.; DeleteExternal uses reference indices 0, 1, etc. Placement/offset rotations use yaw pitch roll degrees. Detach preserves current world placement. Native solver edits, Undo/Redo and FCStd save/open are supported.";
    static final String HELP="NewDoc MobileDocument\nAdd Source Feature\nAddProperty Source Width Length\nSet Source.Width 2 cm\nAdd Driven Feature\nAddProperty Driven Width Length\nExpression Driven.Width Source.Width * 2\n\nUndo · Redo · Recompute · State\nBegin \"Edit dimensions\" · Commit · Abort\nGroup GroupName ObjectName\nLink InstanceName TargetName\nSave Model.FCStd · Open Model.FCStd\nActivate DocumentName · Close\n\nAdd Solid Box · Set Solid.Length 25 mm\nPreview Solid 0.2 · ExportStep Solid Model.step\nImportStep Imported Model.step\nCut Result Solid Tool · Fuse Result Solid Tool · Common Result Solid Tool\n\nObject kinds: Feature, Group, Link, VarSet; native Part runtime: Box, Cylinder, Sphere, Cone, Torus, PartFeature. Property kinds: Length, Angle, Area, Volume, Float, Integer, String, Bool, Link. Quotes preserve spaces. Save before closing the app.";
    static JSONObject parse(String text)throws Exception{
        if(text==null||text.length()>4096)throw new IllegalArgumentException("Command exceeds 4,096 characters");
        String trimmed=text.trim();if(trimmed.length()>6&&trimmed.regionMatches(true,0,"Python",0,6)&&Character.isWhitespace(trimmed.charAt(6)))return new JSONObject().put("op","python").put("code",trimmed.substring(6).trim());
        List<String> a=tokens(text);if(a.isEmpty())throw new IllegalArgumentException("Enter a command");
        String command=a.get(0).toLowerCase(Locale.ROOT).replace("\u0307","");JSONObject request=new JSONObject(),edit=new JSONObject();
        switch(command){
            case "sketchmirror":
                arity(a,4);String axis=a.get(3);edit.put("op","sketch_mirror").put("object",a.get(1)).put("indices",indices(a.get(2))).put("axis",axis.equalsIgnoreCase("X")?-1:axis.equalsIgnoreCase("Y")?-2:Integer.parseInt(axis));break;
            case "sketcharray":
                if(a.size()!=8&&a.size()!=9)throw new IllegalArgumentException("SketchArray SKETCH INDICES COLUMNS ROWS DX DY PERPSCALE [true|false]");
                edit.put("op","sketch_array").put("object",a.get(1)).put("indices",indices(a.get(2))).put("columns",Integer.parseInt(a.get(3))).put("rows",Integer.parseInt(a.get(4))).put("step",xy(a.get(5),a.get(6))).put("ratio",Double.parseDouble(a.get(7))).put("constrain_spacing",a.size()==9?booleanValue(a.get(8)):false);break;
            case "active":case "driving":
                arity(a,4);edit.put("op",command.equals("active")?"sketch_active":"sketch_driving").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2))).put("value",booleanValue(a.get(3)));break;
            case "sketchtrim":case "sketchsplit":
                arity(a,5);edit.put("op",command.equals("sketchtrim")?"sketch_trim":"sketch_split").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2))).put("point",xy(a.get(3),a.get(4)));break;
            case "sketchextend":
                arity(a,5);edit.put("op","sketch_extend").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2))).put("amount",Double.parseDouble(a.get(3))).put("position",Integer.parseInt(a.get(4)));break;
            case "sketchfillet":
                arity(a,9);edit.put("op","sketch_fillet").put("object",a.get(1)).put("first",Integer.parseInt(a.get(2))).put("second",Integer.parseInt(a.get(3))).put("first_point",xy(a.get(4),a.get(5))).put("second_point",xy(a.get(6),a.get(7))).put("radius",Double.parseDouble(a.get(8)));break;
            case "sketchplane":
                arity(a,6);edit.put("op","sketch_plane").put("object",a.get(1)).put("plane",a.get(2).toUpperCase(Locale.ROOT)).put("origin",numbers(a,3));break;
            case "sketchplacement":case "sketchoffset":
                arity(a,8);edit.put("op",command.equals("sketchplacement")?"sketch_placement":"sketch_offset").put("object",a.get(1)).put("values",numbers(a,2));break;
            case "sketchattach":case "external":
                arity(a,4);edit.put("op",command.equals("sketchattach")?"sketch_attach":"sketch_external").put("object",a.get(1)).put("source",a.get(2)).put("element",a.get(3));break;
            case "sketchdetach":
                arity(a,2);edit.put("op","sketch_detach").put("object",a.get(1));break;
            case "deleteexternal":
                arity(a,3);edit.put("op","sketch_delete_external").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2)));break;
            case "sketch":case "eskiz":case "skizze":
                arity(a,2);edit.put("op","add").put("name",a.get(1)).put("type","Sketcher::SketchObject");break;
            case "sketchline":case "sketchcircle":case "sketcharc":case "sketchellipse":case "sketchspline":
                edit=geometryRequest(command,a);break;
            case "construction":
                arity(a,4);if(!a.get(3).equalsIgnoreCase("true")&&!a.get(3).equalsIgnoreCase("false"))throw new IllegalArgumentException("Construction SKETCH INDEX true|false");
                edit.put("op","sketch_construction").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2))).put("value",Boolean.parseBoolean(a.get(3)));break;
            case "deletegeometry":case "deleteconstraint":
                arity(a,3);edit.put("op",command.equals("deletegeometry")?"sketch_delete_geometry":"sketch_delete_constraint").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2)));break;
            case "movepoint":
                arity(a,6);edit.put("op","sketch_move").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2))).put("position",Integer.parseInt(a.get(3))).put("point",xy(a.get(4),a.get(5)));break;
            case "constraint":
                if(a.size()<4)throw new IllegalArgumentException("Constraint SKETCH KIND ARGUMENTS");
                String constraint=null;for(String allowed:new String[]{"Horizontal","Vertical","Coincident","Parallel","Perpendicular","Tangent","Equal","Distance","Radius","Diameter","Angle","Symmetric","PointOnObject","Block","DistanceX","DistanceY"})if(allowed.equalsIgnoreCase(a.get(2)))constraint=allowed;
                if(constraint==null)throw new IllegalArgumentException("Unsupported native constraint kind");
                JSONArray arguments=new JSONArray();boolean dimension=constraint.equals("DistanceX")||constraint.equals("DistanceY")||constraint.equals("Distance")||constraint.equals("Radius")||constraint.equals("Diameter")||constraint.equals("Angle");
                int expected=constraint.equals("Coincident")?4:constraint.equals("PointOnObject")?3:constraint.equals("Horizontal")||constraint.equals("Vertical")||constraint.equals("Block")?1:2;
                if(constraint.equals("Symmetric")){if(a.size()!=8&&a.size()!=9)throw new IllegalArgumentException("Symmetric uses two point pairs and an axis, or three point pairs");}else if(constraint.equals("DistanceX")||constraint.equals("DistanceY")){if(a.size()!=5&&a.size()!=6&&a.size()!=8)throw new IllegalArgumentException("DistanceX/Y uses LINE VALUE, ENTITY POINT VALUE or two point pairs VALUE");}else arity(a,expected+3);
                for(int i=3;i<a.size();i++){if(dimension&&i==a.size()-1)arguments.put(Double.parseDouble(a.get(i)));else arguments.put(Integer.parseInt(a.get(i)));}
                edit.put("op","sketch_constraint").put("object",a.get(1)).put("kind",constraint).put("args",arguments);break;
            case "datum":
                if(a.size()<4)throw new IllegalArgumentException("Datum SKETCH INDEX VALUE [UNIT]");
                StringBuilder datum=new StringBuilder(a.get(3));for(int i=4;i<a.size();i++)datum.append(' ').append(a.get(i));
                edit.put("op","sketch_datum").put("object",a.get(1)).put("index",Integer.parseInt(a.get(2))).put("value",datum.toString());break;
            case "sketchpreview":arity(a,2);return request.put("op","sketch_preview").put("object",a.get(1));
            case "record":arity(a,1);return request.put("op","record_start");
            case "stoprecord":arity(a,2);return request.put("op","record_stop").put("name",a.get(1));
            case "api":arity(a,2);return request.put("op","api").put("target",a.get(1));
            case "runmacro":arity(a,2);return request.put("op","macro_run").put("name",a.get(1));
            case "proxy":
                if(a.size()!=3&&a.size()!=4)throw new IllegalArgumentException("Proxy NAME SOURCE.PROPERTY [FACTOR]");
                String[] source=a.get(2).split("\\.",-1);if(source.length!=2)throw new IllegalArgumentException("Use Source.Property");
                double factor=a.size()==4?Double.parseDouble(a.get(3)):1;
                edit.put("op","proxy").put("name",a.get(1)).put("source",source[0]).put("property",source[1]).put("factor",factor);break;
            case "newdoc":arity(a,2);return request.put("op","new").put("name",a.get(1));
            case "activate":arity(a,2);return request.put("op","activate").put("name",a.get(1));
            case "open":case "save":arity(a,2);return request.put("op",command).put("file",a.get(1));
            case "begin":if(a.size()>2)throw new IllegalArgumentException("Begin [\"Edit label\"]");return request.put("op","begin").put("label",a.size()==2?a.get(1):"Mobile edit");
            case "commit":case "abort":case "undo":case "redo":case "recompute":case "state":case "close":arity(a,1);return request.put("op",command);
            case "add":
                if(a.size()!=2&&a.size()!=3)throw new IllegalArgumentException("Add NAME [Feature|Group|Link|VarSet|Box|Cylinder|Sphere|Cone|Torus|PartFeature]");
                String kind=a.size()==3?a.get(2).toLowerCase(Locale.ROOT):"feature";
                String type=kind.equals("feature")?"App::FeaturePython":kind.equals("group")?"App::DocumentObjectGroup":kind.equals("link")?"App::Link":kind.equals("varset")?"App::VarSet":kind.equals("box")?"Part::Box":kind.equals("cylinder")?"Part::Cylinder":kind.equals("sphere")?"Part::Sphere":kind.equals("cone")?"Part::Cone":kind.equals("torus")?"Part::Torus":kind.equals("partfeature")?"Part::Feature":kind.equals("sketch")?"Sketcher::SketchObject":null;
                if(type==null)throw new IllegalArgumentException("Unknown object kind");
                edit.put("op","add").put("name",a.get(1)).put("type",type);break;
            case "cut":case "fuse":case "common":
                arity(a,4);return booleanRequest(command.equals("cut")?"Part::Cut":command.equals("fuse")?"Part::Fuse":"Part::Common",a.get(1),a.get(2),a.get(3));
            case "remove":arity(a,2);edit.put("op","remove").put("object",a.get(1));break;
            case "preview":
                if(a.size()!=2&&a.size()!=3)throw new IllegalArgumentException("Preview OBJECT [TOLERANCE_MM]");
                return request.put("op","part_preview").put("object",a.get(1)).put("tolerance",a.size()==3?Double.parseDouble(a.get(2)):0.2);
            case "importstep":arity(a,3);return request.put("op","part_import").put("name",a.get(1)).put("file",a.get(2));
            case "exportstep":arity(a,3);return request.put("op","part_export").put("object",a.get(1)).put("file",a.get(2));
            case "addproperty":
                arity(a,4);String propertyType=null;
                for(String allowed:new String[]{"Length","Angle","Area","Volume","Float","Integer","String","Bool","Link"})if(allowed.equalsIgnoreCase(a.get(3)))propertyType=allowed;
                if(propertyType==null)throw new IllegalArgumentException("Unknown property kind");
                edit.put("op","property").put("object",a.get(1)).put("name",a.get(2)).put("type","App::Property"+propertyType);break;
            case "set":case "expression":
                if(a.size()<3)throw new IllegalArgumentException("Set OBJECT.PROPERTY VALUE / Expression OBJECT.PROPERTY FORMULA");
                String[] address=a.get(1).split("\\.",-1);if(address.length!=2||address[0].isEmpty()||address[1].isEmpty())throw new IllegalArgumentException("Use Object.Property");
                StringBuilder value=new StringBuilder(a.get(2));for(int i=3;i<a.size();i++)value.append(' ').append(a.get(i));
                edit.put("op",command).put("object",address[0]).put("property",address[1]).put(command.equals("set")?"value":"expression",value.toString());break;
            case "group":arity(a,3);edit.put("op","group").put("group",a.get(1)).put("object",a.get(2));break;
            case "link":arity(a,3);edit.put("op","link").put("object",a.get(1)).put("target",a.get(2));break;
            default:throw new IllegalArgumentException("Unknown document command. Open Help for the command list.");
        }
        return request.put("op","batch").put("label",text.substring(0,Math.min(128,text.length()))).put("edits",new JSONArray().put(edit));
    }
    static JSONObject booleanRequest(String type,String name,String base,String tool)throws Exception{
        if(!type.equals("Part::Cut")&&!type.equals("Part::Fuse")&&!type.equals("Part::Common"))throw new IllegalArgumentException("Unsupported Part boolean");
        JSONArray edits=new JSONArray().put(new JSONObject().put("op","add").put("type",type).put("name",name))
            .put(new JSONObject().put("op","set").put("object",name).put("property","Base").put("value",base))
            .put(new JSONObject().put("op","set").put("object",name).put("property","Tool").put("value",tool));
        return new JSONObject().put("op","batch").put("label","Part boolean").put("edits",edits);
    }
    private static JSONArray xy(String x,String y)throws Exception{return new JSONArray().put(Double.parseDouble(x)).put(Double.parseDouble(y));}
    private static JSONObject geometryRequest(String command,List<String> a)throws Exception{
        JSONObject geometry=new JSONObject();
        if(command.equals("sketchline")){arity(a,6);geometry.put("kind","Line").put("start",xy(a.get(2),a.get(3))).put("end",xy(a.get(4),a.get(5)));}
        else if(command.equals("sketchspline")){
            if(a.size()!=4&&a.size()!=5)throw new IllegalArgumentException("SketchSpline SKETCH DEGREE x,y;x,y;... [w,w,...]");
            JSONArray poles=new JSONArray();String[] pairs=a.get(3).split(";",-1);if(pairs.length>64)throw new IllegalArgumentException("At most 64 spline poles");
            for(String pair:pairs){String[] values=pair.split(",",-1);if(values.length!=2)throw new IllegalArgumentException("Use x,y pole pairs");poles.put(xy(values[0],values[1]));}
            geometry.put("kind","BSpline").put("degree",Integer.parseInt(a.get(2))).put("poles",poles);
            if(a.size()==5){JSONArray weights=new JSONArray();for(String weight:a.get(4).split(",",-1))weights.put(Double.parseDouble(weight));geometry.put("weights",weights);}
        }else{
            arity(a,command.equals("sketchcircle")?5:command.equals("sketcharc")?7:6);
            geometry.put("center",xy(a.get(2),a.get(3)));
            if(command.equals("sketchellipse"))geometry.put("kind","Ellipse").put("major",Double.parseDouble(a.get(4))).put("minor",Double.parseDouble(a.get(5)));
            else{geometry.put("kind",command.equals("sketchcircle")?"Circle":"Arc").put("radius",Double.parseDouble(a.get(4)));if(command.equals("sketcharc"))geometry.put("start_angle",Double.parseDouble(a.get(5))).put("end_angle",Double.parseDouble(a.get(6)));}
        }
        return new JSONObject().put("op","sketch_geometry").put("object",a.get(1)).put("geometry",geometry);
    }
    private static void arity(List<String> values,int count){if(values.size()!=count)throw new IllegalArgumentException("Wrong number of command arguments");}
    private static JSONArray indices(String text)throws Exception{String[] values=text.split(",",-1);if(values.length>32)throw new IllegalArgumentException("At most32 source indices");JSONArray result=new JSONArray();for(String v:values)result.put(Integer.parseInt(v));return result;}
    private static boolean booleanValue(String text){if(!text.equalsIgnoreCase("true")&&!text.equalsIgnoreCase("false"))throw new IllegalArgumentException("Use true or false");return Boolean.parseBoolean(text);}
    private static JSONArray numbers(List<String> values,int start)throws Exception{JSONArray result=new JSONArray();for(int i=start;i<values.size();i++)result.put(Double.parseDouble(values.get(i)));return result;}
    private static List<String> tokens(String text){
        List<String> out=new ArrayList<>();StringBuilder token=new StringBuilder();boolean quote=false,started=false,escape=false;
        for(int i=0;i<text.length();i++){char c=text.charAt(i);if(escape){if(c!='"'&&c!='\\')token.append('\\');token.append(c);escape=false;started=true;}else if(c=='\\'&&quote)escape=true;else if(c=='"'){quote=!quote;started=true;}else if(Character.isWhitespace(c)&&!quote){if(started){out.add(token.toString());token.setLength(0);started=false;}}else{token.append(c);started=true;}}
        if(quote||escape)throw new IllegalArgumentException("Unclosed quote or escape");if(started)out.add(token.toString());if(out.size()>128)throw new IllegalArgumentException("Too many command arguments");return out;
    }
}
