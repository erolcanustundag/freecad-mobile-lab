// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;
import android.app.*;
import android.content.Context;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import org.json.*;

final class NativeWirePreview {
    static Dialog show(Activity activity,JSONObject data) throws JSONException {
        Dialog dialog=new Dialog(activity);LinearLayout root=new LinearLayout(activity);root.setOrientation(LinearLayout.VERTICAL);
        TextView title=new TextView(activity);title.setText(data.getString("object")+" · "+L10n.text(activity,"3D native wire preview"));title.setPadding(20,20,20,12);root.addView(title);
        Preview view=new Preview(activity,new WireFrame(data));root.addView(view,new LinearLayout.LayoutParams(-1,0,1));
        TextView hint=new TextView(activity);hint.setText(L10n.text(activity,"Drag to orbit · pinch to zoom · two fingers to pan"));hint.setPadding(20,12,20,12);root.addView(hint);
        LinearLayout buttons=new LinearLayout(activity);Button fit=new Button(activity);fit.setText(L10n.text(activity,"Fit"));fit.setOnClickListener(v->view.fit());buttons.addView(fit,new LinearLayout.LayoutParams(0,-2,1));
        Button close=new Button(activity);close.setText(L10n.text(activity,"Close"));close.setOnClickListener(v->dialog.dismiss());buttons.addView(close,new LinearLayout.LayoutParams(0,-2,1));root.addView(buttons);
        dialog.setContentView(root);dialog.show();dialog.getWindow().setLayout(-1,-1);return dialog;
    }
    private static final class Preview extends View {
        final WireFrame frame;final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        float yaw=-45,pitch=35.264f,zoom=1,panX=0,panY=0,lastX,lastY,lastSpan;boolean touching;
        Preview(Context context,WireFrame frame){super(context);this.frame=frame;setBackgroundColor(0xff101820);setContentDescription(L10n.text(context,"3D native wire preview"));}
        void fit(){yaw=-45;pitch=35.264f;zoom=1;panX=panY=0;invalidate();}
        float[] project(double[] curve,int i){return frame.project(curve[i],curve[i+1],curve[i+2],getWidth(),getHeight(),yaw,pitch,zoom,panX,panY);}
        @Override protected void onDraw(Canvas canvas){
            super.onDraw(canvas);if(getWidth()==0||getHeight()==0)return;
            paint.setColor(0xffffcd72);paint.setStrokeWidth(2);paint.setTextSize(20);
            for(int n=0;n<frame.curves.length;n++){
                double[] curve=frame.curves[n];Path path=new Path();float[] first=project(curve,0);path.moveTo(first[0],first[1]);
                for(int i=3;i<curve.length;i+=3){float[] p=project(curve,i);path.lineTo(p[0],p[1]);}
                paint.setStyle(Paint.Style.STROKE);canvas.drawPath(path,paint);paint.setStyle(Paint.Style.FILL);canvas.drawText(Integer.toString(frame.indices[n]),first[0]+5,first[1]-5,paint);
            }
        }
        @Override public boolean onTouchEvent(MotionEvent event){
            int action=event.getActionMasked();
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){touching=false;lastSpan=0;performClick();return true;}
            if(action==MotionEvent.ACTION_POINTER_UP){int remaining=event.getActionIndex()==0?1:0;lastX=event.getX(remaining);lastY=event.getY(remaining);lastSpan=0;return true;}
            float x=event.getX(),y=event.getY(),span=0;
            if(event.getPointerCount()>=2){x=(x+event.getX(1))/2;y=(y+event.getY(1))/2;span=(float)Math.hypot(event.getX(1)-event.getX(0),event.getY(1)-event.getY(0));}
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN||!touching){touching=true;lastX=x;lastY=y;lastSpan=span;return true;}
            if(action==MotionEvent.ACTION_MOVE){
                if(event.getPointerCount()>=2){
                    panX=Math.max(-getWidth()*100f,Math.min(getWidth()*100f,panX+x-lastX));panY=Math.max(-getHeight()*100f,Math.min(getHeight()*100f,panY+y-lastY));
                    if(lastSpan>0&&span>0)zoom=Math.max(.05f,Math.min(100,zoom*span/lastSpan));
                }else{yaw=(yaw+(x-lastX)*.4f)%360;pitch=Math.max(-89,Math.min(89,pitch+(y-lastY)*.4f));}
                lastX=x;lastY=y;lastSpan=span;invalidate();
            }
            return true;
        }
        @Override public boolean performClick(){super.performClick();return true;}
    }
}
