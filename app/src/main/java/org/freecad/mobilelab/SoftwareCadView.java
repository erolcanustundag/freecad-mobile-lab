// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import android.content.Context;
import android.graphics.*;
import android.view.*;
import java.util.concurrent.*;

/** Software bitmap viewer of the actual native CAD mesh, rendered off the UI thread. */
final class SoftwareCadView extends View implements ModelViewport {
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final CadView.ErrorListener errors;
    private final ScaleGestureDetector scale;
    private final Paint paint=new Paint(Paint.FILTER_BITMAP_FLAG);
    private java.util.function.LongConsumer frameListener;
    @Override public void setFrameListener(java.util.function.LongConsumer listener){frameListener=listener;}
    private MeshFrame mesh,scene;private RenderSettings options=RenderSettings.DEFAULT;
    @Override public void settings(RenderSettings s){options=s;changed();}
    private Bitmap bitmap;
    private float yaw=-32,pitch=-58,zoom=1,panX,panY,lastX,lastY;
    private int previousPointers,generation;
    private boolean rendering,paused,closed;
    private boolean orthographic,tapCandidate;
    private float downX,downY;
    private java.util.function.Consumer<double[]> pick;
    private java.util.function.Consumer<float[]> orientation;
    @Override public void setOrientationListener(java.util.function.Consumer<float[]> listener){orientation=listener;if(listener!=null)listener.accept(new float[]{yaw,pitch});}
    @Override public void setPickListener(java.util.function.Consumer<double[]> listener){pick=listener;}
    SoftwareCadView(Context context,CadView.ErrorListener errors) {
        super(context);this.errors=errors;setLayerType(View.LAYER_TYPE_SOFTWARE,null);
        scale=new ScaleGestureDetector(context,new ScaleGestureDetector.SimpleOnScaleGestureListener(){
            @Override public boolean onScale(ScaleGestureDetector detector){zoom=Math.max(.35f,Math.min(50,zoom/detector.getScaleFactor()));changed();return true;}
        });
    }
    @Override public View view(){return this;}
    @Override public void setMesh(MeshFrame value,boolean fit){boolean first=mesh==null;scene=mesh=value;if(fit||first){zoom=1;panX=panY=0;}changed();}
    @Override public void focus(double[] bounds){mesh=MeshFrame.focus(mesh,bounds);zoom=1;panX=panY=0;changed();}
    @Override public void fit(){mesh=scene;zoom=1;panX=panY=0;changed();}
    @Override public void preset(String type){float[] p=CameraMath.preset(type);yaw=p[0];pitch=p[1];orthographic=!type.equals("Isometric");changed();}
    private void changed(){generation++;if(orientation!=null)orientation.accept(new float[]{yaw,pitch});schedule();}
    private void schedule() {
        if(rendering||paused||closed||getWidth()<1||getHeight()<1)return;
        float factor=Math.min(1,640f/Math.max(getWidth(),getHeight()));int w=Math.max(1,Math.round(getWidth()*factor)),h=Math.max(1,Math.round(getHeight()*factor));
        final int ticket=generation;final MeshFrame scene=mesh;final float a=yaw,b=pitch,z=zoom,px=panX,py=panY;final boolean ortho=orthographic;final RenderSettings settings=options;rendering=true;
        worker.execute(()->{
            try {
                long start=System.nanoTime();SoftwareRasterizer.Image frame=SoftwareRasterizer.render(scene,w,h,a,b,z,px,py,ortho,settings);
                if(frame==null){post(()->{rendering=false;if(!closed&&ticket!=generation)schedule();});return;}final long elapsed=(System.nanoTime()-start)/1000000;Bitmap next=Bitmap.createBitmap(frame.pixels,w,h,Bitmap.Config.ARGB_8888);
                post(()->{rendering=false;if(closed){next.recycle();return;}if(ticket==generation&&!paused){Bitmap old=bitmap;bitmap=next;if(old!=null)old.recycle();invalidate();if(frameListener!=null)frameListener.accept(elapsed);}else next.recycle();if(ticket!=generation)schedule();});
            }catch(Throwable t){post(()->{rendering=false;if(!closed){Diagnostics.error(getContext(),"Software 3D",t);errors.onError(t.toString());}});}
        });
    }
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){changed();}
    @Override protected void onDraw(Canvas canvas){canvas.drawColor(SoftwareRasterizer.BACKGROUND);if(bitmap!=null)canvas.drawBitmap(bitmap,null,new Rect(0,0,getWidth(),getHeight()),paint);}
    @Override public boolean onTouchEvent(MotionEvent event) {
        scale.onTouchEvent(event);int n=event.getPointerCount();float x=event.getX(),y=event.getY();if(n>1){x=(x+event.getX(1))/2;y=(y+event.getY(1))/2;}
        if(event.getActionMasked()==MotionEvent.ACTION_DOWN){downX=x;downY=y;tapCandidate=true;}
        if(n>1||Math.hypot(x-downX,y-downY)>8*getResources().getDisplayMetrics().density)tapCandidate=false;
        if(event.getActionMasked()==MotionEvent.ACTION_UP&&tapCandidate&&pick!=null&&mesh!=null)pick.accept(CameraMath.ray(mesh,getWidth(),getHeight(),yaw,pitch,zoom,panX,panY,orthographic,x,y));
        if(event.getActionMasked()==MotionEvent.ACTION_MOVE&&n==previousPointers){float dx=x-lastX,dy=y-lastY;if(n==1){yaw=(yaw+dx*.45f)%360;pitch=(pitch+dy*.45f)%360;}else{float factor=(mesh==null?15:mesh.radius)*zoom*2.8f/Math.max(1,getHeight());panX-=dx*factor;panY+=dy*factor;}changed();}
        lastX=x;lastY=y;previousPointers=n;return true;
    }
    @Override public void onPause(){paused=true;generation++;}
    @Override public void onResume(){paused=false;changed();}
    @Override public void close(){closed=true;worker.shutdownNow();if(bitmap!=null){bitmap.recycle();bitmap=null;}}
}
