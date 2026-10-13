// SPDX-License-Identifier: LGPL-2.1-or-later
// Host-only check: importing embedded FreeCAD must preserve the JVM's handlers.
#include <jni.h>
#include <signal.h>
static struct sigaction previous;
extern "C" JNIEXPORT void JNICALL Java_org_freecad_mobilelab_SignalProbe_capture(JNIEnv*,jclass){sigaction(SIGSEGV,nullptr,&previous);}
extern "C" JNIEXPORT jboolean JNICALL Java_org_freecad_mobilelab_SignalProbe_preserved(JNIEnv*,jclass){
    struct sigaction current; if(sigaction(SIGSEGV,nullptr,&current)!=0)return JNI_FALSE;
    if(current.sa_sigaction!=previous.sa_sigaction || current.sa_flags!=previous.sa_flags)return JNI_FALSE;
    for(int i=1;i<NSIG;i++)if(sigismember(&current.sa_mask,i)!=sigismember(&previous.sa_mask,i))return JNI_FALSE;
    return JNI_TRUE;
}
