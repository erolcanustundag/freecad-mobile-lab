package org.freecad.mobilelab;
import android.content.Context;
import android.graphics.*;
import android.view.*;
/** Explicit world-axis drag control; 0.1 mm increments, one command on release. */
final class TransformHandles extends View {
    interface Result{void move(int axis,double delta);}
    final Result result;final Paint paint=new Paint(3);int active=-1;float down;double delta;boolean finished;
    TransformHandles(Context c,Result r){super(c);result=r;setContentDescription("World axis movement handles");}
    @Override protected void onDraw(Canvas c){c.drawColor(0xff111820);float cx=getWidth()/2f,cy=getHeight()/2f;int[] colors={0xffff6677,0xff66dd99,0xff66aaff};for(int i=0;i<3;i++){float x=cx+(i==0?85:i==2?-55:0),y=cy+(i==1?-70:i==2?55:0);paint.setColor(colors[i]);paint.setStrokeWidth(5);c.drawLine(cx,cy,x,y,paint);c.drawCircle(x,y,17,paint);paint.setTextSize(20);c.drawText(new String[]{"X","Y","Z"}[i],x+22,y+6,paint);}paint.setColor(Color.WHITE);paint.setTextSize(18);c.drawText(finished?"Move committed":active>=0?String.format(java.util.Locale.US,"%s: %+.1f mm",new String[]{"X","Y","Z"}[active],delta):"Drag an axis · 20 px = 1 mm",12,getHeight()-12,paint);}
    @Override public boolean onTouchEvent(MotionEvent e){if(finished)return true;float cx=getWidth()/2f,cy=getHeight()/2f;if(e.getActionMasked()==MotionEvent.ACTION_DOWN){active=-1;for(int i=0;i<3;i++){float x=cx+(i==0?85:i==2?-55:0),y=cy+(i==1?-70:i==2?55:0);if(Math.hypot(e.getX()-x,e.getY()-y)<30)active=i;}down=active==0?e.getX():-e.getY();delta=0;invalidate();return true;}if(active>=0){float position=active==0?e.getX():-e.getY();delta=Math.rint((position-down)/2)/10;invalidate();if(e.getActionMasked()==MotionEvent.ACTION_UP){finished=true;result.move(active,delta);}if(e.getActionMasked()==MotionEvent.ACTION_CANCEL){active=-1;delta=0;}}return true;}
}
