// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import java.io.*;
import java.nio.charset.*;
import java.nio.file.*;
import java.util.*;
import org.json.*;

/** A bounded mobile worksheet, independent of native FreeCAD Spreadsheet objects. */
final class Worksheet {
    static final int ROWS=32,COLS=8,MAX_CSV=65536;
    private static LinkedHashMap<String,String> cells=new LinkedHashMap<>();
    static String address(String name){String n=name.toUpperCase(Locale.US);if(!n.matches("[A-H]([1-9]|[12][0-9]|3[0-2])"))throw new IllegalArgumentException("Cell must be A1 to H32");return n;}
    static String source(String name){return cells.getOrDefault(address(name),"");}
    static void checkValue(String value){if(value==null||value.length()>256)throw new IllegalArgumentException("Cell text is limited to 256 characters");for(char c:value.toCharArray())if(c==0||(Character.isISOControl(c)&&c!='\n'&&c!='\r'&&c!='\t'))throw new IllegalArgumentException("Invalid cell control character");}
    static void set(String name,String value){checkValue(value);String n=address(name);LinkedHashMap<String,String> next=new LinkedHashMap<>(cells);if(value.isEmpty())next.remove(n);else next.put(n,value);cells=next;}
    static void reset(){cells=new LinkedHashMap<>();}
    static JSONObject json()throws Exception{JSONObject o=new JSONObject();for(Map.Entry<String,String> c:cells.entrySet())o.put(c.getKey(),c.getValue());return o;}
    static LinkedHashMap<String,String> decoded(JSONObject o)throws Exception{LinkedHashMap<String,String> next=new LinkedHashMap<>();if(o!=null){Iterator<String> it=o.keys();while(it.hasNext()){String key=it.next(),n=address(key),value=o.getString(key);checkValue(value);if(!key.equals(n))throw new IllegalArgumentException("Worksheet addresses must be uppercase");if(!value.isEmpty())next.put(n,value);}}if(next.size()>ROWS*COLS)throw new IllegalArgumentException("Too many cells");return next;}
    static void load(JSONObject o)throws Exception{cells=decoded(o);}
    static void validate(JSONObject o)throws Exception{decoded(o);}
    static boolean numeric(String value){return value.trim().matches("[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?(?:mm|cm|m|in|deg)?");}
    static double value(String name){String cell=address(name),raw=source(cell);if(!raw.startsWith("=")&&!numeric(raw))throw new IllegalArgumentException("Cell "+cell+" is empty or text");LinkedHashMap<String,String> definitions=new LinkedHashMap<>();for(int row=1;row<=ROWS;row++)for(int col=0;col<COLS;col++){String id=""+(char)('A'+col)+row,s=cells.getOrDefault(id,"");if(s.startsWith("="))definitions.put(id,s.substring(1));else if(numeric(s))definitions.put(id,s);}return Expressions.evaluateIn(cell,normalise(definitions));}
    static String display(String name){String raw=source(name);if(raw.startsWith("=")||numeric(raw))try{return String.format(Locale.US,"%.10g",value(name));}catch(Exception e){return "#ERR: "+e.getMessage();}return raw;}
    static double formula(String expression){LinkedHashMap<String,String> definitions=new LinkedHashMap<>();for(Map.Entry<String,String> c:cells.entrySet()){String raw=c.getValue();if(raw.startsWith("="))definitions.put(c.getKey(),raw.substring(1));else if(numeric(raw))definitions.put(c.getKey(),raw);}return Expressions.evaluateIn(normalise(expression.startsWith("=")?expression.substring(1):expression),normalise(definitions));}
    static Map<String,String> normalise(Map<String,String> source){Map<String,String> result=new LinkedHashMap<>();for(Map.Entry<String,String> e:source.entrySet())result.put(e.getKey(),normalise(e.getValue()));return result;}
    static String normalise(String source){java.util.regex.Matcher m=java.util.regex.Pattern.compile("(?i)\\b([a-h](?:[1-9]|[12][0-9]|3[0-2]))\\b").matcher(source);StringBuffer out=new StringBuffer();while(m.find())m.appendReplacement(out,m.group(1).toUpperCase(Locale.US));m.appendTail(out);return out.toString();}
    static JSONObject displayJson()throws Exception{JSONObject o=new JSONObject();for(String key:cells.keySet())o.put(key,display(key));return o;}
    static String report(){StringBuilder b=new StringBuilder("Mobile worksheet A1:H32. Formula cells start with =. Cells can reference other cells and document variables. Existing solids are not automatically bound to cells.\n\n");for(String key:cells.keySet())b.append(key).append(" | ").append(cells.get(key)).append(" | ").append(display(key)).append('\n');if(cells.isEmpty())b.append("No cells. Try Cell A1 18, Cell A2 =A1+2, then Ring =A1 1.6 3.\n");return b.toString();}
    static void writeCsv(File file)throws Exception{StringBuilder out=new StringBuilder();int maxRow=0,maxCol=0;for(String key:cells.keySet()){maxRow=Math.max(maxRow,Integer.parseInt(key.substring(1)));maxCol=Math.max(maxCol,key.charAt(0)-'A'+1);}for(int row=1;row<=Math.max(1,maxRow);row++){for(int col=0;col<Math.max(1,maxCol);col++){if(col>0)out.append(',');String v=cells.getOrDefault(""+(char)('A'+col)+row,"");if(v.contains(",")||v.contains("\"")||v.contains("\n")||v.contains("\r"))out.append('"').append(v.replace("\"","\"\"")).append('"');else out.append(v);}out.append("\r\n");}byte[] bytes=out.toString().getBytes(StandardCharsets.UTF_8);if(bytes.length>MAX_CSV)throw new IOException("CSV exceeds 64 KiB");Files.write(file.toPath(),bytes);}
    static void readCsv(File file)throws Exception{if(file.length()>MAX_CSV)throw new IOException("CSV exceeds 64 KiB");String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(Files.readAllBytes(file.toPath()))).toString();if(text.startsWith("\ufeff"))text=text.substring(1);LinkedHashMap<String,String> next=new LinkedHashMap<>();StringBuilder value=new StringBuilder();int row=1,col=0;boolean quoted=false,closed=false,started=false;
        for(int i=0;i<text.length();i++){char c=text.charAt(i);if(quoted){if(c=='"'){if(i+1<text.length()&&text.charAt(i+1)=='"'){value.append('"');i++;}else{quoted=false;closed=true;}}else value.append(c);if(value.length()>256)throw new IOException("CSV cell exceeds 256 characters");continue;}
            if(c=='"'){if(started||closed)throw new IOException("Unexpected CSV quote");quoted=true;started=true;continue;}if(c==','||c=='\n'||c=='\r'){put(next,row,col,value.toString());value.setLength(0);started=closed=false;if(c==',')col++;else{if(c=='\r'&&i+1<text.length()&&text.charAt(i+1)=='\n')i++;row++;col=0;}if(col>=COLS||row>ROWS+1||(row==ROWS+1&&i+1<text.length()))throw new IOException("CSV exceeds 32 rows / 8 columns");continue;}if(closed)throw new IOException("Unexpected text after CSV quote");value.append(c);started=true;if(value.length()>256)throw new IOException("CSV cell exceeds 256 characters");}
        if(quoted)throw new IOException("Unclosed CSV quote");if(started||value.length()>0||col>0)put(next,row,col,value.toString());cells=next;
    }
    private static void put(Map<String,String> next,int row,int col,String value)throws Exception{if(row>ROWS||col>=COLS)throw new IOException("CSV exceeds 32 rows / 8 columns");checkValue(value);if(!value.isEmpty())next.put(""+(char)('A'+col)+row,value);}
}
