#!/usr/bin/env python3
"""Rebuild Qt's headless Android dependencies with 16 KiB ELF alignment.

The official Qt 6.8.3 ARM64 binaries checked in this session use 4 KiB LOAD
alignment and are deliberately excluded from APK inputs.
"""
import argparse
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT.parent/'upstream/qtbase-everywhere-src-6.8.3')
    p.add_argument('--build',type=Path,default=ROOT.parent/'qt-core-android-build')
    p.add_argument('--prefix',type=Path,default=ROOT.parent/'toolchains/qt/android-arm64-16k')
    p.add_argument('--host',type=Path,default=ROOT.parent/'toolchains/qt/linux-x86_64')
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--sdk',type=Path,default=ROOT.parent/'toolchains/android-sdk')
    p.add_argument('--jobs',type=int,default=3)
    args=p.parse_args()
    if not 1<=args.jobs<=16:p.error('--jobs must be 1 to 16')
    source,build,prefix,host,ndk,sdk=(v.resolve() for v in (args.source,args.build,args.prefix,args.host,args.ndk,args.sdk))
    env=dict(os.environ,ANDROID_SDK_ROOT=str(sdk),ANDROID_NDK_ROOT=str(ndk))
    command=['cmake','-S',str(source),'-B',str(build),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),
        '-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-26','-DANDROID_STL=c++_shared',
        '-DANDROID_SDK_ROOT='+str(sdk),'-DANDROID_NDK_ROOT='+str(ndk),
        '-DCMAKE_INSTALL_PREFIX='+str(prefix),'-DQT_HOST_PATH='+str(host),
        '-DQT_BUILD_TESTS=OFF','-DQT_BUILD_EXAMPLES=OFF',
        '-DFEATURE_gui=OFF','-DFEATURE_widgets=OFF','-DFEATURE_opengl=OFF',
        '-DFEATURE_dbus=OFF','-DFEATURE_sql=OFF','-DFEATURE_testlib=OFF','-DFEATURE_printsupport=OFF',
        '-DFEATURE_network=ON','-DFEATURE_concurrent=ON','-DFEATURE_xml=ON',
        '-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384']
    subprocess.run(command,check=True,env=env)
    subprocess.run(['cmake','--build',str(build),'--parallel',str(args.jobs)],check=True,env=env)
    subprocess.run(['cmake','--install',str(build)],check=True,env=env)
    print('Headless Qt Android build installed:',prefix,'(Android execution NOT_RUN)')

if __name__=='__main__':main()
