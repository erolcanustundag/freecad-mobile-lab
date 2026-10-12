package org.freecad.mobilelab;
import android.graphics.*;
import java.util.*;
/** Bounded system-font outlines sampled to polygons at approximately 0.05 mm. */
final class TextOutlines {
    static int create(String text,double height,double depth){
        if(text==null||text.trim().isEmpty()||text.length()>40||!Double.isFinite(height)||height<.1||height>100||!Double.isFinite(depth)||depth<.001||depth>100)throw new IllegalArgumentException("Text: 1–40 characters, height 0.1–100 mm and depth 0.001–100 mm");
        Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);paint.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));paint.setTextSize(100);Path path=new Path();paint.getTextPath(text,0,text.length(),0,0,path);RectF bounds=new RectF();path.computeBounds(bounds,true);if(bounds.height()<=0)throw new IllegalArgumentException("Text has no visible outlines");double scale=height/bounds.height();PathMeasure measure=new PathMeasure(path,true);ArrayList<Double> xy=new ArrayList<>();ArrayList<Integer> counts=new ArrayList<>();float[] position=new float[2];
        do{float length=measure.getLength();if(length<=1e-5)continue;int n=Math.max(8,(int)Math.ceil(length*scale/.05));if(n>1024||counts.size()>=256||xy.size()+n*2>32768)throw new IllegalArgumentException("Text outline is too detailed; shorten it or reduce height");for(int i=0;i<n;i++){if(!measure.getPosTan(length*i/n,position,null))throw new IllegalArgumentException("Font contour could not be sampled");xy.add((position[0]-bounds.left)*scale);xy.add((bounds.bottom-position[1])*scale);}counts.add(n);}while(measure.nextContour());
        double[] points=new double[xy.size()];for(int i=0;i<points.length;i++)points[i]=xy.get(i);int[] loops=new int[counts.size()];for(int i=0;i<loops.length;i++)loops[i]=counts.get(i);return NativeCad.textSolid(points,loops,depth);
    }
}
