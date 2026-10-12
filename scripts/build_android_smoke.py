#!/usr/bin/env python3
"""Build a separate instrumentation APK for the Android runtime smoke checks."""
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SDK=Path(os.environ.get('ANDROID_SDK_ROOT',ROOT.parent/'toolchains/android-sdk'))
JDK=Path(os.environ.get('JAVA_HOME',ROOT.parent/'toolchains/jdk-17.0.16+8'))
TOOLS=SDK/'build-tools/35.0.0';JAR=SDK/'platforms/android-35/android.jar';OUT=ROOT.parent/'android-qa/smoke'
def run(*args):subprocess.run([str(x) for x in args],check=True)
OUT.mkdir(parents=True,exist_ok=True);(OUT/'classes').mkdir(exist_ok=True);(OUT/'dex').mkdir(exist_ok=True)
(OUT/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.freecad.mobilelab.test"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="35"/><application android:label="FreeCAD startup checks" android:debuggable="true"/><instrumentation android:name="org.freecad.mobilelab.test.StartupSmokeInstrumentation" android:targetPackage="org.freecad.mobilelab"/></manifest>''')
run(TOOLS/'aapt2','link','-I',JAR,'--manifest',OUT/'AndroidManifest.xml','-o',OUT/'resources.apk')
run(JDK/'bin/javac','--release','8','-classpath',JAR,'-d',OUT/'classes',ROOT/'tests/StartupSmokeInstrumentation.java')
run(JDK/'bin/java','-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',JAR,'--output',OUT/'dex',*sorted((OUT/'classes').rglob('*.class')))
import shutil,zipfile
shutil.copy2(OUT/'resources.apk',OUT/'unsigned.apk')
with zipfile.ZipFile(OUT/'unsigned.apk','a',compression=zipfile.ZIP_DEFLATED) as apk:apk.write(OUT/'dex/classes.dex','classes.dex')
run(TOOLS/'zipalign','-f','4',OUT/'unsigned.apk',OUT/'aligned.apk')
run(JDK/'bin/java','-jar',TOOLS/'lib/apksigner.jar','sign','--ks',ROOT/'apk-build/development.keystore','--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',OUT/'startup-smoke.apk',OUT/'aligned.apk')
print('Instrumentation APK:',OUT/'startup-smoke.apk')
