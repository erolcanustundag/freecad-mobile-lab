package org.freecad.mobilelab;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Locale;
import org.json.*;

/** A4 overall-dimension sheet for a selected XY curve. Contours remain sampled SVG. */
final class DrawingSheet {
    static void write(File target,File cache,int id,String title,String notes)throws Exception {
        if(title==null||notes==null||title.length()>100||notes.length()>200||title.indexOf('\n')>=0||notes.indexOf('\n')>=0||title.indexOf('\r')>=0||notes.indexOf('\r')>=0)
            throw new IOException("Use a single-line title (100 characters) and notes (200 characters)");
        for(String value:new String[]{title,notes})for(int i=0;i<value.length();i++){char c=value.charAt(i);if(c<32||c==0xfffe||c==0xffff)throw new IOException("Drawing title/notes contain an invalid XML character");}
        JSONArray objects=new JSONArray(NativeCad.objects());JSONObject object=null;
        for(int i=0;i<objects.length();i++)if(objects.getJSONObject(i).getInt("id")==id)object=objects.getJSONObject(i);
        if(object==null||object.optBoolean("mesh")||!object.optBoolean("curve"))throw new IOException("Select an XY curve or Section result at Z=0");
        JSONArray b=object.getJSONArray("bbox");double xmin=b.getDouble(0),ymin=b.getDouble(1),xmax=b.getDouble(3),ymax=b.getDouble(4);
        double w=xmax-xmin,h=ymax-ymin;if(w<=.000001||h<=.000001)throw new IOException("Sheet needs a profile with positive width and height");
        double scale=Math.min(1,Math.min(148/w,190/h)),left=(210-w*scale)/2,top=40+(190-h*scale)/2;
        File part=File.createTempFile("sheet-",".svg",cache);String group;
        try{NativeCad.write(part.getAbsolutePath(),"svg",id);if(part.length()>8*1024*1024)throw new IOException("Drawing contour exceeds 8 MiB");String svg=new String(Files.readAllBytes(part.toPath()),StandardCharsets.UTF_8);int begin=svg.indexOf("<g "),end=svg.lastIndexOf("</svg>");if(begin<0||end<=begin)throw new IOException("Invalid contour export");group=svg.substring(begin,end).replace("stroke-width=\"0.05\"","stroke-width=\""+f(.25/scale)+"\"");}finally{part.delete();}
        StringBuilder s=new StringBuilder("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"210mm\" height=\"297mm\" viewBox=\"0 0 210 297\"><rect width=\"210\" height=\"297\" fill=\"white\"/><rect x=\"10\" y=\"10\" width=\"190\" height=\"277\" fill=\"none\" stroke=\"black\" stroke-width=\"0.25\"/>");
        wrapped(s,title,38,21,5,4.5);text(s,16,36,3,"Overall dimensions in mm · XY view");
        s.append("<g transform=\"translate(").append(f(left-xmin*scale)).append(' ').append(f(top+ymax*scale)).append(") scale(").append(f(scale)).append(")\">").append(group).append("</g>");
        double right=left+w*scale,bottom=top+h*scale,yd=bottom+12,xd=right+12;
        s.append("<g fill=\"none\" stroke=\"black\" stroke-width=\"0.25\">");
        line(s,left,bottom+2,left,yd+2);line(s,right,bottom+2,right,yd+2);line(s,left,yd,right,yd);tick(s,left,yd);tick(s,right,yd);
        line(s,right+2,top,xd+2,top);line(s,right+2,bottom,xd+2,bottom);line(s,xd,top,xd,bottom);tick(s,xd,top);tick(s,xd,bottom);s.append("</g>");
        text(s,(left+right)/2-7,yd-2,3,f3(w)+" mm");s.append("<text x=\"").append(f(xd-2)).append("\" y=\"").append(f((top+bottom)/2)).append("\" text-anchor=\"middle\" transform=\"rotate(-90 ").append(f(xd-2)).append(' ').append(f((top+bottom)/2)).append(")\" font-family=\"sans-serif\" font-size=\"3\" fill=\"black\">").append(escape(f3(h)+" mm")).append("</text>");
        text(s,16,254,3,"Scale "+(scale==1?"1:1":"1:"+f3(1/scale)));wrapped(s,notes,65,262,4,2.5);
        text(s,16,279,2.5,"Contours target 0.005 mm (capped) · print at 100%, no page fit");s.append("</svg>");
        try(FileOutputStream out=new FileOutputStream(target)){out.write(s.toString().getBytes(StandardCharsets.UTF_8));out.getFD().sync();}
    }
    private static String f(double x){return String.format(Locale.US,"%.9f",x);}
    private static String f3(double x){return String.format(Locale.US,"%.3f",x);}
    private static String escape(String x){return x.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\"","&quot;").replace("'","&apos;");}
    private static void text(StringBuilder s,double x,double y,double size,String value){s.append("<text x=\"").append(f(x)).append("\" y=\"").append(f(y)).append("\" font-family=\"sans-serif\" font-size=\"").append(f(size)).append("\" fill=\"black\">").append(escape(value)).append("</text>");}
    private static void wrapped(StringBuilder s,String value,int width,double y,double step,double size){for(int i=0;i<value.length();i+=width)text(s,16,y+(i/width)*step,size,value.substring(i,Math.min(value.length(),i+width)));}
    private static void line(StringBuilder s,double x1,double y1,double x2,double y2){s.append("<path d=\"M ").append(f(x1)).append(' ').append(f(y1)).append(" L ").append(f(x2)).append(' ').append(f(y2)).append("\"/>");}
    private static void tick(StringBuilder s,double x,double y){line(s,x-1,y+1,x+1,y-1);}
}
