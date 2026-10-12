// SPDX-License-Identifier: LGPL-2.1-or-later
package org.qtproject.qt.android;
import android.app.Activity;

/** Use the official Qt Java classes for Core JNI; no Qt GUI is started. */
public final class MobileCoreBootstrap {
    private MobileCoreBootstrap(){}
    public static void prepare(Activity activity){
        QtNative.setClassLoader(activity.getClassLoader());
        QtNative.setActivity(activity);
        System.loadLibrary("Qt6Core_arm64-v8a");
        if(!QtNative.updateNativeActivity())throw new IllegalStateException("Qt document context could not be updated");
    }
}
