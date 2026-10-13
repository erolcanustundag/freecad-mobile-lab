#!/usr/bin/env python3
"""Build the real document JNI adapter for host reference or ARM64 Android."""
import argparse
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--android',action='store_true')
p.add_argument('--part',action='store_true',help='Link verified original Part/Materials from the isolated Part build')
p.add_argument('--sketcher',action='store_true',help='Register the real original Sketcher builtin; implies --part')
args=p.parse_args()
if args.sketcher: args.part=True
env=dict(os.environ)
command=['cmake','-S',str(ROOT/'app/src/main/cpp/upstream-core'),'-G','Ninja',
    '-DCMAKE_BUILD_TYPE=Release','-DFREECAD_SKETCHER_LIBRARY=']
if args.android:
    ndk=Path(env.get('ANDROID_NDK_ROOT',BASE/'toolchains/android-ndk-r27c')).resolve()
    qt=BASE/'toolchains/qt/android-arm64-16k'
    qthost=BASE/'toolchains/qt/linux-x86_64'
    python=BASE/'upstream/cpython-3.13.16/cross-build/aarch64-linux-android/prefix'
    build=ROOT/'core-bridge-android'
    command+=['-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),
        '-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-26','-DANDROID_STL=c++_shared',
        '-DCMAKE_PREFIX_PATH='+str(qt),'-DCMAKE_FIND_ROOT_PATH='+str(qt),
        '-DQT_HOST_PATH='+str(qthost),'-DQt6CoreTools_DIR='+str(qthost/'lib/cmake/Qt6CoreTools'),
        '-DPython3_INCLUDE_DIR='+str(python/'include/python3.13'),
        '-DPython3_LIBRARY='+str(python/'lib/libpython3.13.so'),
        '-DFREECAD_CORE_LIBRARY='+str(BASE/'freecad-core-android/lib/FreeCAD.so')]
    if args.part:
        command+=['-DFREECAD_CORE_LIBRARY='+str(BASE/'freecad-part-android/lib/FreeCAD.so'),'-DFREECAD_PART_LIBRARY='+str(BASE/'freecad-part-android/Mod/Part/Part.so'),'-DFREECAD_MATERIALS_LIBRARY='+str(BASE/'freecad-part-android/Mod/Material/Materials.so')]
    env['LD_LIBRARY_PATH']=str(qthost/'lib')
else:
    prefix=BASE/'toolchains/freecad-host-prefix/usr'
    python=Path(env.get('CODEX_PRIMARY_RUNTIME_PYTHON','/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3')).resolve().parents[1]
    build=ROOT/'core-bridge-host'
    command+=['-DCMAKE_PREFIX_PATH='+str(prefix),
        '-DPython3_INCLUDE_DIR='+str(python/'include/python3.12'),
        '-DPython3_LIBRARY='+str(python/'lib/libpython3.12.so.1.0'),
        '-DFREECAD_CORE_LIBRARY='+str(BASE/'freecad-core-host/lib/FreeCAD.so'),
        '-DJDK_ROOT='+str(Path(env.get('JAVA_HOME',BASE/'toolchains/jdk-system17')).resolve())]
    if args.part:
        command+=['-DFREECAD_CORE_LIBRARY='+str(BASE/'freecad-part-host/lib/FreeCAD.so'),'-DFREECAD_PART_LIBRARY='+str(BASE/'freecad-part-host/Mod/Part/Part.so'),'-DFREECAD_MATERIALS_LIBRARY='+str(BASE/'freecad-part-host/Mod/Material/Materials.so')]
command+=['-B',str(build)]
if args.sketcher:
    platform='android' if args.android else 'host'
    command+=['-DFREECAD_SKETCHER_LIBRARY='+str(BASE/('freecad-part-'+platform)/'Mod/Sketcher/Sketcher.so')]
subprocess.run(command,check=True,env=env)
subprocess.run(['cmake','--build',str(build),'--parallel','2'],check=True,env=env)
print('Built document bridge:',build)
