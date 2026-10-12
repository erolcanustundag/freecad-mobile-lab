// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import android.app.Application;

public final class CrashApplication extends Application {
    interface GraphicsFailure { void failed(Throwable failure); }
    static volatile GraphicsFailure graphicsFailure;
    @Override public void onCreate() {
        super.onCreate();Diagnostics.initialize(this);
        Thread.UncaughtExceptionHandler previous=Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread,error)->{
            Diagnostics.error(this,"Uncaught error on "+thread.getName(),error);
            GraphicsFailure listener=graphicsFailure;
            // GLSurfaceView has already run GLThread's finally/cleanup before this callback.
            if(thread.getName().startsWith("GLThread")&&listener!=null){listener.failed(error);return;}
            if(previous!=null)previous.uncaughtException(thread,error);
            else{android.os.Process.killProcess(android.os.Process.myPid());System.exit(10);}
        });
    }
}
