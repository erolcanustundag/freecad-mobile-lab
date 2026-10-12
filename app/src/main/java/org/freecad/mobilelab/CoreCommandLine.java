// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import org.json.*;
import java.util.*;

/** Human command syntax for the upstream document adapter. */
final class CoreCommandLine {
    static final String HELP="NewDoc MobileDocument\nAdd Source Feature\nAddProperty Source Width Length\nSet Source.Width 2 cm\nAdd Driven Feature\nAddProperty Driven Width Length\nExpression Driven.Width Source.Width * 2\n\nUndo · Redo · Recompute · State\nBegin \"Edit dimensions\" · Commit · Abort\nGroup GroupName ObjectName\nLink InstanceName TargetName\nSave Model.FCStd · Open Model.FCStd\nActivate DocumentName · Close\n\nObject kinds: Feature, Group, Link, VarSet. Property kinds: Length, Angle, Area, Volume, Float, Integer, String, Bool, Link. Quotes preserve spaces. Save before closing the app.";
    static JSONObject parse(String text)throws Exception{
        if(text==null||text.length()>4096)throw new IllegalArgumentException("Command exceeds 4,096 characters");
        String trimmed=text.trim();if(trimmed.length()>6&&trimmed.regionMatches(true,0,"Python",0,6)&&Character.isWhitespace(trimmed.charAt(6)))return new JSONObject().put("op","python").put("code",trimmed.substring(6).trim());
        List<String> a=tokens(text);if(a.isEmpty())throw new IllegalArgumentException("Enter a command");
        String command=a.get(0).toLowerCase(Locale.ROOT);JSONObject request=new JSONObject(),edit=new JSONObject();
        switch(command){
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
                if(a.size()!=2&&a.size()!=3)throw new IllegalArgumentException("Add NAME [Feature|Group|Link|VarSet]");
                String kind=a.size()==3?a.get(2).toLowerCase(Locale.ROOT):"feature";
                String type=kind.equals("feature")?"App::FeaturePython":kind.equals("group")?"App::DocumentObjectGroup":kind.equals("link")?"App::Link":kind.equals("varset")?"App::VarSet":null;
                if(type==null)throw new IllegalArgumentException("Unknown object kind");
                edit.put("op","add").put("name",a.get(1)).put("type",type);break;
            case "remove":arity(a,2);edit.put("op","remove").put("object",a.get(1));break;
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
    private static void arity(List<String> values,int count){if(values.size()!=count)throw new IllegalArgumentException("Wrong number of command arguments");}
    private static List<String> tokens(String text){
        List<String> out=new ArrayList<>();StringBuilder token=new StringBuilder();boolean quote=false,started=false,escape=false;
        for(int i=0;i<text.length();i++){char c=text.charAt(i);if(escape){if(c!='"'&&c!='\\')token.append('\\');token.append(c);escape=false;started=true;}else if(c=='\\'&&quote)escape=true;else if(c=='"'){quote=!quote;started=true;}else if(Character.isWhitespace(c)&&!quote){if(started){out.add(token.toString());token.setLength(0);started=false;}}else{token.append(c);started=true;}}
        if(quote||escape)throw new IllegalArgumentException("Unclosed quote or escape");if(started)out.add(token.toString());if(out.size()>128)throw new IllegalArgumentException("Too many command arguments");return out;
    }
}
