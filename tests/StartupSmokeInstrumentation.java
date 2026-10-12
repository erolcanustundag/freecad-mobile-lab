// SPDX-License-Identifier: LGPL-2.1-or-later
package org.freecad.mobilelab.test;

import android.app.Instrumentation;
import android.content.Intent;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.*;
import java.lang.reflect.Method;

/** Android runtime checks, packaged separately; never part of the delivered application. */
public final class StartupSmokeInstrumentation extends Instrumentation {
    private final StringBuilder report=new StringBuilder();
    @Override public void onCreate(Bundle args){super.onCreate(args);start();}
    private void pass(String message){report.append("PASS: ").append(message).append('\n');Bundle status=new Bundle();status.putString("stream",message+"\n");sendStatus(0,status);}
    private Object nativeCall(String method,Class<?>[] parameters,Object... args)throws Exception {
        Class<?> c=Class.forName("org.freecad.mobilelab.NativeCad",true,getTargetContext().getClassLoader());Method m=c.getDeclaredMethod(method,parameters);m.setAccessible(true);return m.invoke(null,args);
    }
    private AccessibilityNodeInfo find(String text) {
        AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();if(root==null)return null;
        for(AccessibilityNodeInfo node:root.findAccessibilityNodeInfosByText(text))if(node.getText()!=null&&node.getText().toString().contains(text))return node;return null;
    }
    private AccessibilityNodeInfo await(String text,long timeout)throws Exception {
        long end=SystemClock.elapsedRealtime()+timeout;
        while(SystemClock.elapsedRealtime()<end){AccessibilityNodeInfo node=find(text);if(node!=null)return node;SystemClock.sleep(300);}throw new AssertionError("UI text not found: "+text);
    }
    private void click(String text)throws Exception {if(!await(text,30000).performAction(AccessibilityNodeInfo.ACTION_CLICK))throw new AssertionError("Click failed: "+text);}
    private AccessibilityNodeInfo input(AccessibilityNodeInfo root){if(root==null)return null;if("android.widget.AutoCompleteTextView".contentEquals(root.getClassName())||"android.widget.EditText".contentEquals(root.getClassName()))return root;for(int i=0;i<root.getChildCount();i++){AccessibilityNodeInfo result=input(root.getChild(i));if(result!=null)return result;}return null;}
    private void command(String text)throws Exception{AccessibilityNodeInfo field=input(getUiAutomation().getRootInActiveWindow());if(field==null)throw new AssertionError("Command field missing");Bundle args=new Bundle();args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,text);if(!field.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,args))throw new AssertionError("Command input failed");click("Run");}
    private void awaitAbsent(String text)throws Exception{long end=SystemClock.elapsedRealtime()+30000;while(SystemClock.elapsedRealtime()<end){if(find(text)==null)return;SystemClock.sleep(300);}throw new AssertionError("UI text still present: "+text);}
    private String shell(String command)throws Exception{try(android.os.ParcelFileDescriptor fd=getUiAutomation().executeShellCommand(command);InputStream in=new FileInputStream(fd.getFileDescriptor());ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] bytes=new byte[1024];int count;while((count=in.read(bytes))!=-1)out.write(bytes,0,count);return out.toString("UTF-8");}}
    @Override public void onStart() {
        Bundle result=new Bundle();
        try {
            String tests=(String)nativeCall("selfTest",new Class<?>[]{String.class},getTargetContext().getFilesDir().getAbsolutePath());report.append(tests);pass("Android JNI kernel diagnostics completed");
            Intent start=new Intent().setClassName("org.freecad.mobilelab","org.freecad.mobilelab.StartupActivity").putExtra("diagnostics_only",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TASK);
            getTargetContext().startActivity(start);await("FREECAD",30000);await("Copy crash report",30000);pass("Android recovery launcher opens");
            click("Start empty workspace");await("Empty workspace",30000);pass("separate CAD process opens empty software-rendered workspace");
            click("+ Create");click("Basic solids");click("Box");click("Apply");await("1680.00 mm³",30000);SystemClock.sleep(1000);
            android.graphics.Bitmap screenshot=getUiAutomation().takeScreenshot();
            if(screenshot==null)throw new AssertionError("Android screenshot unavailable");
            try(OutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),"android-software-box.png"))){screenshot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}finally{screenshot.recycle();}
            pass("native Box creation and Android software viewer update; screenshot recorded");
            command("Box 20 10 4");await("800.00 mm³",30000);command("Rename \"QA command box\"");await("QA command box",30000);command("Undo");awaitAbsent("QA command box");command("Redo");await("QA command box",30000);pass("command bar exact Box, Rename, Undo and Redo");
            command("Guide");click("Getting started");await("GETTING STARTED",30000);click("Close");pass("offline guide opens");
            String pid=shell("pidof org.freecad.mobilelab:cad").trim();if(!pid.matches("[0-9]+"))throw new AssertionError("CAD PID not found: "+pid);shell("am crash "+pid);
            SystemClock.sleep(1500);getTargetContext().startActivity(new Intent().setClassName("org.freecad.mobilelab","org.freecad.mobilelab.StartupActivity").putExtra("diagnostics_only",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP));
            await("Copy crash report",30000);pass("recovery process survives a forced CAD-process crash");
            click("FreeCAD document lab");await("Ready",90000);command("NewDoc AndroidCoreSmoke");await("AndroidCoreSmoke",30000);
            command("Add Source Feature");await("Source",30000);command("AddProperty Source Width Length");await("Width",30000);command("Set Source.Width 2 cm");await("20.0 mm",30000);
            command("Add Driven Feature");await("Driven",30000);command("AddProperty Driven Width Length");SystemClock.sleep(500);command("Expression Driven.Width Source.Width * 2");await("40.0 mm",30000);
            command("Set Source.Width 32 mm");await("64.0 mm",30000);command("Undo");await("40.0 mm",30000);command("Redo");await("64.0 mm",30000);pass("upstream document lab commands, units, expression recompute and native Undo/Redo");
            command("Save AndroidCoreSmoke.FCStd");await("Ready",30000);SystemClock.sleep(500);command("Close");await("Create a document",30000);command("Open AndroidCoreSmoke.FCStd");await("64.0 mm",30000);pass("upstream App metadata native FCStd restored in isolated Android process");
            command("Python print('PYTHON_ANDROID_OK')");await("PYTHON_ANDROID_OK",30000);command("Api App.Vector");await("API: App.Vector",30000);
            command("Proxy Scaled Source.Width 3");await("96.0 mm",30000);command("Save AndroidProxySmoke.FCStd");await("Ready",30000);SystemClock.sleep(500);command("Close");await("Create a document",30000);command("Open AndroidProxySmoke.FCStd");await("96.0 mm",30000);pass("Android embedded Python, native API browser and scripted proxy FCStd restore");
            result.putString("stream",report.toString());finish(-1,result);
        }catch(Throwable error){StringWriter stack=new StringWriter();error.printStackTrace(new PrintWriter(stack));result.putString("stream",report+"FAIL: "+stack);finish(0,result);}
    }
}
