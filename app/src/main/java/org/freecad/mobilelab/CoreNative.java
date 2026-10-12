// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab;

/** Loaded only by the isolated document lab, never by the recovery launcher. */
final class CoreNative {
    static native void initialize(String pythonHome,String scriptRoot,String documentRoot);
    static native String request(String json);
}
