package org.freecad.mobilelab;

import android.content.Context;
import android.opengl.GLES30;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.Buffer;
import java.nio.FloatBuffer;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

final class CadView extends GLSurfaceView implements GLSurfaceView.Renderer,ModelViewport {
    interface ErrorListener { void onError(String message); }
    private MeshFrame mesh,scene;private RenderSettings options=RenderSettings.DEFAULT;
    @Override public void settings(RenderSettings settings){enqueue(()->{options=settings;if(mesh!=null&&wireVbo!=0&&options.style==RenderSettings.WIREFRAME)upload(wireVbo,mesh.wireBuffer());});}
    private FloatBuffer grid;
    private int gridCount,program,meshVbo,gridVbo,lineVbo,vao,mvpLocation,mvLocation,unlitLocation,materialVbo,wireVbo,styleLocation,clippingLocation,clipZLocation;
    private int width=1,height=1;
    // Camera and GPU state are confined to the GL thread.
    private float yaw=-32,pitch=-58,zoom=1,panX,panY,radius=15,cx,cy,cz,lastX,lastY;
    private int previousPointers;
    private boolean firstMesh=true,failed,orthographic;
    private boolean tapCandidate;private float downX,downY;private java.util.function.Consumer<double[]> pick;
    @Override public void setPickListener(java.util.function.Consumer<double[]> listener){pick=listener;}
    private volatile java.util.function.Consumer<float[]> orientation;
    @Override public void setOrientationListener(java.util.function.Consumer<float[]> listener){orientation=listener;enqueue(this::notifyOrientation);}
    private void notifyOrientation(){final float[] angles={yaw,pitch};post(()->{if(orientation!=null)orientation.accept(angles);});}
    private final ErrorListener errors;
    private final ScaleGestureDetector scale;
    private final float[] projection=new float[16],view=new float[16],model=new float[16],mv=new float[16],mvp=new float[16];

    CadView(Context context,ErrorListener errors) {
        super(context);this.errors=errors;
        setEGLContextClientVersion(3);
        // A 16-bit depth buffer is sufficient and supported by more GLES configurations.
        getHolder().setFormat(android.graphics.PixelFormat.RGBA_8888);
        setEGLConfigChooser(8,8,8,8,16,0);
        setPreserveEGLContextOnPause(true);setRenderer(this);setRenderMode(RENDERMODE_WHEN_DIRTY);
        scale=new ScaleGestureDetector(context,new ScaleGestureDetector.SimpleOnScaleGestureListener(){
            @Override public boolean onScale(ScaleGestureDetector detector) {
                float factor=detector.getScaleFactor();
                enqueue(()->zoom=Math.max(0.35f,Math.min(50,zoom/factor)));return true;
            }
        });
    }
    @Override public android.view.View view(){return this;}
    @Override public void close(){}
    private static FloatBuffer buffer(float[] values) {
        FloatBuffer b=ByteBuffer.allocateDirect(values.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();
        b.put(values);((Buffer)b).position(0);return b;
    }
    private void report(Throwable t) {
        android.util.Log.e("CAD_RENDERER","Rendering failed",t);
        if(failed)return;failed=true;
        String message=t.getMessage()==null?t.toString():t.getMessage();
        post(()->errors.onError(message));
    }
    private void enqueue(Runnable action) {
        queueEvent(()->{if(failed)return;try{action.run();}catch(Throwable t){report(t);}});requestRender();
    }
    @Override public void setMesh(MeshFrame values,boolean fit) {
        enqueue(()->{
            scene=mesh=values;cx=mesh.x;cy=mesh.y;cz=mesh.z;radius=mesh.radius;if(meshVbo!=0)upload(meshVbo,mesh.buffer());if(lineVbo!=0)upload(lineVbo,mesh.lineBuffer());if(materialVbo!=0)upload(materialVbo,mesh.materialBuffer());if(wireVbo!=0&&options.style==RenderSettings.WIREFRAME)upload(wireVbo,mesh.wireBuffer());
            if(fit||firstMesh){fitCamera();firstMesh=false;}makeGrid();
        });
    }
    private void fitCamera() {
        if(mesh!=null){cx=mesh.x;cy=mesh.y;cz=mesh.z;radius=mesh.radius;}
        zoom=1;panX=panY=0;
    }
    @Override public void fit(){enqueue(()->{mesh=scene;fitCamera();makeGrid();});}
    @Override public void focus(double[] bounds){enqueue(()->{mesh=MeshFrame.focus(mesh,bounds);fitCamera();makeGrid();});}
    @Override public void preset(String type) {
        enqueue(()->{float[] p=CameraMath.preset(type);yaw=p[0];pitch=p[1];orthographic=!type.equals("Isometric");notifyOrientation();});
    }
    private void makeGrid() {
        float spacing=(float)Math.pow(10,Math.floor(Math.log10(Math.max(1,radius/4))));
        float extent=Math.max(20,spacing*12);
        float[] lines=new float[1060];int p=0;
        for(int i=-12;i<=12;i++){
            float t=i*spacing;
            p=vertex(lines,p,-extent,t,0,0.17f,0.22f,0.28f);p=vertex(lines,p,extent,t,0,0.17f,0.22f,0.28f);
            p=vertex(lines,p,t,-extent,0,0.17f,0.22f,0.28f);p=vertex(lines,p,t,extent,0,0.17f,0.22f,0.28f);
        }
        float a=extent*0.6f;
        p=vertex(lines,p,0,0,0,0.95f,0.3f,0.3f);p=vertex(lines,p,a,0,0,0.95f,0.3f,0.3f);
        p=vertex(lines,p,0,0,0,0.3f,0.8f,0.4f);p=vertex(lines,p,0,a,0,0.3f,0.8f,0.4f);
        p=vertex(lines,p,0,0,0,0.35f,0.6f,1);p=vertex(lines,p,0,0,a,0.35f,0.6f,1);
        grid=buffer(lines);gridCount=p/10;if(gridVbo!=0)upload(gridVbo,grid);
    }
    private static int vertex(float[] v,int p,float x,float y,float z,float r,float g,float b) {
        float[] values={x,y,z,0,0,1,r,g,b,1};for(float f:values)v[p++]=f;return p;
    }
    @Override public void onSurfaceCreated(GL10 gl,EGLConfig config) {
        failed=false;program=meshVbo=gridVbo=lineVbo=materialVbo=wireVbo=vao=0;
        try {
            GLES30.glClearColor(0.067f,0.094f,0.125f,1);GLES30.glEnable(GLES30.GL_DEPTH_TEST);
            int vs=shader(GLES30.GL_VERTEX_SHADER,Shaders.VERTEX),fs=0;
            try {
                fs=shader(GLES30.GL_FRAGMENT_SHADER,Shaders.FRAGMENT);program=GLES30.glCreateProgram();
                GLES30.glAttachShader(program,vs);GLES30.glAttachShader(program,fs);GLES30.glLinkProgram(program);
                int[] ok=new int[1];GLES30.glGetProgramiv(program,GLES30.GL_LINK_STATUS,ok,0);
                if(ok[0]==0)throw new IllegalStateException("GLES program: "+GLES30.glGetProgramInfoLog(program));
            }finally{GLES30.glDeleteShader(vs);if(fs!=0)GLES30.glDeleteShader(fs);}
            mvpLocation=GLES30.glGetUniformLocation(program,"mvp");mvLocation=GLES30.glGetUniformLocation(program,"mv");unlitLocation=GLES30.glGetUniformLocation(program,"unlit");
            styleLocation=GLES30.glGetUniformLocation(program,"style");clippingLocation=GLES30.glGetUniformLocation(program,"clipping");clipZLocation=GLES30.glGetUniformLocation(program,"clipZ");
            int[] ids=new int[5];GLES30.glGenBuffers(5,ids,0);meshVbo=ids[0];gridVbo=ids[1];lineVbo=ids[2];materialVbo=ids[3];wireVbo=ids[4];
            int[] arrays=new int[1];GLES30.glGenVertexArrays(1,arrays,0);vao=arrays[0];GLES30.glBindVertexArray(vao);
            if(mesh!=null){upload(meshVbo,mesh.buffer());upload(lineVbo,mesh.lineBuffer());upload(materialVbo,mesh.materialBuffer());if(options.style==RenderSettings.WIREFRAME)upload(wireVbo,mesh.wireBuffer());}makeGrid();checkGl("Graphics setup");
            android.util.Log.i("CAD_RENDERER",GLES30.glGetString(GLES30.GL_RENDERER));
        }catch(Throwable t){report(t);}
    }
    private static int shader(int type,String source) {
        int s=GLES30.glCreateShader(type);GLES30.glShaderSource(s,source);GLES30.glCompileShader(s);
        int[] ok=new int[1];GLES30.glGetShaderiv(s,GLES30.GL_COMPILE_STATUS,ok,0);
        if(ok[0]==0){String log=GLES30.glGetShaderInfoLog(s);GLES30.glDeleteShader(s);throw new IllegalStateException(log);}
        return s;
    }
    private static void checkGl(String action) {
        int error=GLES30.glGetError();if(error!=GLES30.GL_NO_ERROR)throw new IllegalStateException(action+": GLES error 0x"+Integer.toHexString(error));
    }
    @Override public void onSurfaceChanged(GL10 gl,int w,int h) {
        width=Math.max(1,w);height=Math.max(1,h);GLES30.glViewport(0,0,w,h);
    }
    @Override public void onDrawFrame(GL10 gl) {
        if(failed)return;
        try {
            GLES30.glClear(GLES30.GL_COLOR_BUFFER_BIT|GLES30.GL_DEPTH_BUFFER_BIT);if(program==0)return;
            float aspect=(float)width/height,distance=radius*3.4f*zoom/Math.min(1,aspect);
            if(orthographic){float h=(float)(distance*Math.tan(Math.toRadians(21)));Matrix.orthoM(projection,0,-h*aspect,h*aspect,-h,h,Math.max(.001f,distance/1000),Math.max(100,distance+radius*10));}else Matrix.perspectiveM(projection,0,42,aspect,Math.max(0.001f,distance/1000),Math.max(100,distance+radius*10));
            Matrix.setLookAtM(view,0,panX,panY,distance,panX,panY,0,0,1,0);
            Matrix.setIdentityM(model,0);Matrix.rotateM(model,0,pitch,1,0,0);Matrix.rotateM(model,0,yaw,0,0,1);Matrix.translateM(model,0,-cx,-cy,-cz);
            Matrix.multiplyMM(mv,0,view,0,model,0);Matrix.multiplyMM(mvp,0,projection,0,mv,0);
            GLES30.glUseProgram(program);GLES30.glUniformMatrix4fv(mvpLocation,1,false,mvp,0);GLES30.glUniformMatrix4fv(mvLocation,1,false,mv,0);
            GLES30.glUniform1i(styleLocation,options.style);GLES30.glUniform1i(clippingLocation,options.clip?1:0);GLES30.glUniform1f(clipZLocation,(float)options.clipZ);
            GLES30.glBindVertexArray(vao);draw(gridVbo,gridCount,GLES30.GL_LINES,true);if(options.style==RenderSettings.WIREFRAME)draw(wireVbo,mesh==null?0:mesh.count*2,GLES30.GL_LINES,true);else draw(meshVbo,mesh==null?0:mesh.count,GLES30.GL_TRIANGLES,false);draw(lineVbo,mesh==null?0:mesh.lineCount,GLES30.GL_LINES,true);checkGl("Drawing");
        }catch(Throwable t){report(t);}
    }
    private void upload(int id,FloatBuffer b) {
        // The base Buffer method also stays compatible with Android 8 when built by Gradle/JDK 17.
        ((Buffer)b).position(0);GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER,id);GLES30.glBufferData(GLES30.GL_ARRAY_BUFFER,b.capacity()*4,b,GLES30.GL_STATIC_DRAW);GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER,0);checkGl("Mesh upload");
    }
    private void draw(int id,int vertices,int mode,boolean unlit) {
        if(id==0||vertices==0)return;GLES30.glUniform1i(unlitLocation,unlit?1:0);GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER,id);
        GLES30.glVertexAttribPointer(0,3,GLES30.GL_FLOAT,false,40,0);GLES30.glVertexAttribPointer(1,3,GLES30.GL_FLOAT,false,40,12);GLES30.glVertexAttribPointer(2,4,GLES30.GL_FLOAT,false,40,24);
        if(!unlit&&mesh!=null&&mesh.materials.length>0){GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER,materialVbo);GLES30.glVertexAttribPointer(3,2,GLES30.GL_FLOAT,false,8,0);GLES30.glEnableVertexAttribArray(3);}else{GLES30.glDisableVertexAttribArray(3);GLES30.glVertexAttrib2f(3,.45f,0);}
        for(int i=0;i<3;i++)GLES30.glEnableVertexAttribArray(i);GLES30.glDrawArrays(mode,0,vertices);GLES30.glBindBuffer(GLES30.GL_ARRAY_BUFFER,0);
    }
    @Override public boolean onTouchEvent(MotionEvent event) {
        scale.onTouchEvent(event);int n=event.getPointerCount();float x=event.getX(),y=event.getY();
        if(n>1){x=(x+event.getX(1))/2;y=(y+event.getY(1))/2;}
        if(event.getActionMasked()==MotionEvent.ACTION_DOWN){downX=x;downY=y;tapCandidate=true;}if(n>1||Math.hypot(x-downX,y-downY)>8*getResources().getDisplayMetrics().density)tapCandidate=false;
        if(event.getActionMasked()==MotionEvent.ACTION_UP&&tapCandidate&&pick!=null){final float sx=x,sy=y;enqueue(()->{if(mesh!=null){double[] ray=CameraMath.ray(mesh,width,height,yaw,pitch,zoom,panX,panY,orthographic,sx,sy);post(()->{if(pick!=null)pick.accept(ray);});}});}
        if(event.getActionMasked()==MotionEvent.ACTION_MOVE&&n==previousPointers) {
            float dx=x-lastX,dy=y-lastY;int pointers=n;
            enqueue(()->{if(pointers==1){yaw=(yaw+dx*0.45f)%360;pitch=(pitch+dy*0.45f)%360;notifyOrientation();}else{float factor=radius*zoom*2.8f/height;panX-=dx*factor;panY+=dy*factor;}});
        }
        lastX=x;lastY=y;previousPointers=n;return true;
    }
}
