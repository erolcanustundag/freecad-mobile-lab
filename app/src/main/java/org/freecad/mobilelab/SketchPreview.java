// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.*;
import android.content.Context;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;

/** Bounded XY display of sampled original Sketcher geometry, with pan/pinch. */
final class SketchPreview {
    static Dialog show(Activity activity,JSONObject sketch)throws Exception{
        Dialog dialog=new Dialog(activity);LinearLayout root=new LinearLayout(activity);root.setOrientation(1);
        TextView title=new TextView(activity);title.setTextColor(0xffedf3f8);title.setPadding(20,16,20,8);
        title.setText(sketch.getString("object")+" · "+L10n.text(activity,"Degrees of freedom")+": "+sketch.getInt("dof"));root.addView(title);
        Preview view=new Preview(activity,sketch.getJSONArray("curves"));root.addView(view,new LinearLayout.LayoutParams(-1,0,1));
        TextView hint=new TextView(activity);L10n.setText(hint,"Sketch-local XY · drag to pan · pinch to zoom · cyan construction curves");hint.setTextColor(0xffa5b4c5);root.addView(hint);
        LinearLayout row=new LinearLayout(activity);Button fit=new Button(activity),close=new Button(activity);L10n.setText(fit,"Fit");L10n.setText(close,"Close");fit.setOnClickListener(v->view.fit());close.setOnClickListener(v->dialog.dismiss());row.addView(fit,new LinearLayout.LayoutParams(0,-2,1));row.addView(close,new LinearLayout.LayoutParams(0,-2,1));root.addView(row);
        dialog.setContentView(root);dialog.show();dialog.getWindow().setLayout(-1,-1);return dialog;
    }
    private static final class Curve{final float[] points;final boolean construction;final int index;Curve(float[] p,boolean c,int i){points=p;construction=c;index=i;}}
    private static final class Preview extends View{
        final ArrayList<Curve> curves=new ArrayList<>();final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        float minX=Float.POSITIVE_INFINITY,minY=minX,maxX=Float.NEGATIVE_INFINITY,maxY=maxX,centerX,centerY,scale=1,fitScale=1,lastX,lastY,lastSpan;
        Preview(Context context,JSONArray entries)throws Exception{
            super(context);if(entries.length()>256)throw new IllegalArgumentException("Too many sketch curves");int total=0;
            for(int i=0;i<entries.length();i++){JSONObject item=entries.getJSONObject(i);JSONArray points=item.getJSONArray("points");total+=points.length();if(total>8192)throw new IllegalArgumentException("Too many sketch preview points");float[] p=new float[points.length()*2];
                for(int j=0;j<points.length();j++){JSONArray pair=points.getJSONArray(j);if(pair.length()!=2)throw new IllegalArgumentException("Invalid XY point");for(int k=0;k<2;k++){double n=pair.getDouble(k);if(!Double.isFinite(n)||Math.abs(n)>1000000)throw new IllegalArgumentException("Invalid sketch coordinate");p[j*2+k]=(float)n;}minX=Math.min(minX,p[j*2]);maxX=Math.max(maxX,p[j*2]);minY=Math.min(minY,p[j*2+1]);maxY=Math.max(maxY,p[j*2+1]);}
                curves.add(new Curve(p,item.getBoolean("construction"),item.getInt("index")));
            }
            if(total==0){minX=minY=-10;maxX=maxY=10;}setBackgroundColor(0xff101820);
        }
        void fit(){centerX=(minX+maxX)/2;centerY=(minY+maxY)/2;fitScale=Math.max(.00001f,Math.min(Math.max(1,getWidth()-64)/Math.max(1,maxX-minX),Math.max(1,getHeight()-64)/Math.max(1,maxY-minY)));scale=fitScale;invalidate();}
        @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){fit();}
        float x(float n){return getWidth()/2f+(n-centerX)*scale;}float y(float n){return getHeight()/2f-(n-centerY)*scale;}
        @Override protected void onDraw(Canvas canvas){super.onDraw(canvas);paint.setStrokeWidth(1);paint.setColor(0xff42505f);canvas.drawLine(0,y(0),getWidth(),y(0),paint);canvas.drawLine(x(0),0,x(0),getHeight(),paint);
            for(Curve c:curves){paint.setColor(c.construction?0xff55dce4:0xffffcd72);paint.setStrokeWidth(c.construction?2:3);paint.setStyle(Paint.Style.STROKE);Path path=new Path();for(int i=0;i<c.points.length;i+=2){float px=x(c.points[i]),py=y(c.points[i+1]);if(i==0)path.moveTo(px,py);else path.lineTo(px,py);}canvas.drawPath(path,paint);paint.setStyle(Paint.Style.FILL);paint.setTextSize(24);if(c.points.length>0)canvas.drawText(Integer.toString(c.index),x(c.points[0])+8,y(c.points[1])-8,paint);}
        }
        @Override public boolean onTouchEvent(MotionEvent event){int action=event.getActionMasked();if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){lastSpan=0;return true;}float cx=event.getX(),cy=event.getY(),span=0;if(event.getPointerCount()>1){cx=(event.getX(0)+event.getX(1))/2;cy=(event.getY(0)+event.getY(1))/2;span=(float)Math.hypot(event.getX(1)-event.getX(0),event.getY(1)-event.getY(0));}
            if(action==MotionEvent.ACTION_MOVE){if(span>0&&lastSpan>0){float before=scale;scale=Math.max(fitScale*.05f,Math.min(fitScale*100,scale*span/lastSpan));centerX+=(cx-getWidth()/2f)*(1/before-1/scale);centerY-=(cy-getHeight()/2f)*(1/before-1/scale);}centerX-=(cx-lastX)/scale;centerY+=(cy-lastY)/scale;invalidate();}
            lastX=cx;lastY=cy;lastSpan=span;return true;
        }
    }
}
