// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

import android.view.View;

interface ModelViewport {
    View view();
    void setMesh(MeshFrame mesh,boolean fit);
    default void setFrameListener(java.util.function.LongConsumer listener){}
    default void settings(RenderSettings settings){}
    void fit();
    void preset(String type);
    default void focus(double[] bounds){}
    default void setOrientationListener(java.util.function.Consumer<float[]> listener){}
    default void setPickListener(java.util.function.Consumer<double[]> listener){}
    void onPause();
    void onResume();
    void close();
}
