// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.content.Context;
import android.graphics.*;
import android.view.*;

/** Tappable faces choose orthographic views; the lower ISO target restores perspective. */
final class ViewCube extends View {
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final java.util.function.Consumer<String> choose;
    private float yaw=-32,pitch=-58,downX,downY;
    ViewCube(Context context,java.util.function.Consumer<String> choose){super(context);this.choose=choose;setContentDescription("Navigation cube. Tap a visible face for its view, or ISO for perspective.");setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);setFocusable(true);}
    void angles(float[] value){yaw=value[0];pitch=value[1];invalidate();}
    private float scale(){return Math.min(getWidth(),getHeight())*.24f;}
    @Override protected void onDraw(Canvas canvas){float scale=scale(),cx=getWidth()/2f,cy=getHeight()*.42f;paint.setTextAlign(Paint.Align.CENTER);paint.setTypeface(Typeface.DEFAULT_BOLD);
        for(int face:ViewCubeMath.visible(yaw,pitch)){double[][] p=ViewCubeMath.polygon(face,yaw,pitch);Path path=new Path();path.moveTo(cx+(float)p[0][0]*scale,cy-(float)p[0][1]*scale);for(int i=1;i<4;i++)path.lineTo(cx+(float)p[i][0]*scale,cy-(float)p[i][1]*scale);path.close();paint.setStyle(Paint.Style.FILL);paint.setColor(face>=4?0xff306353:face<2?0xff28485c:0xff344253);canvas.drawPath(path,paint);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(getResources().getDisplayMetrics().density);paint.setColor(0xff79b8aa);canvas.drawPath(path,paint);double[] n=ViewCubeMath.project(ViewCubeMath.NORMALS[face],yaw,pitch);paint.setStyle(Paint.Style.FILL);paint.setColor(0xffedf3f8);paint.setTextSize(getWidth()*.087f);canvas.drawText(ViewCubeMath.NAMES[face],cx+(float)n[0]*scale,cy-(float)n[1]*scale+paint.getTextSize()*.35f,paint);}
        paint.setStyle(Paint.Style.FILL);paint.setColor(0xdd1b2633);canvas.drawRoundRect(getWidth()*.26f,getHeight()*.78f,getWidth()*.74f,getHeight()*.98f,6,6,paint);paint.setColor(0xff59dfc4);paint.setTextSize(getWidth()*.1f);canvas.drawText("ISO",cx,getHeight()*.92f,paint);
    }
    @Override public boolean onTouchEvent(MotionEvent e){if(e.getActionMasked()==MotionEvent.ACTION_DOWN){downX=e.getX();downY=e.getY();return true;}if(e.getActionMasked()==MotionEvent.ACTION_UP){if(Math.hypot(e.getX()-downX,e.getY()-downY)<8*getResources().getDisplayMetrics().density){if(e.getY()>getHeight()*.76f){choose.accept("Isometric");performClick();}else{int face=ViewCubeMath.hit(yaw,pitch,(e.getX()-getWidth()/2f)/scale(),-(e.getY()-getHeight()*.42f)/scale());if(face>=0){choose.accept(ViewCubeMath.NAMES[face]);performClick();}}}return true;}return true;}
    @Override public boolean performClick(){super.performClick();return true;}
}
