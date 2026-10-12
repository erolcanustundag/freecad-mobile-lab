#!/usr/bin/env python3
"""Cross-build upstream Base/App and Python entrypoint; no APK is produced."""
import argparse
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT.parent/'upstream/FreeCAD-1.1.4')
    p.add_argument('--build',type=Path,default=ROOT.parent/'freecad-core-android')
    p.add_argument('--prefix',type=Path,default=ROOT.parent/'toolchains/freecad-android-prefix')
    p.add_argument('--qt',type=Path,default=ROOT.parent/'toolchains/qt/android-arm64-16k')
    p.add_argument('--qt-host',type=Path,default=ROOT.parent/'toolchains/qt/linux-x86_64')
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--cpython',type=Path,default=ROOT.parent/'upstream/cpython-3.13.16')
    p.add_argument('--occt-headers',type=Path,default=ROOT.parent/'occt-host/include/opencascade')
    p.add_argument('--jobs',type=int,default=3)
    p.add_argument('--configure-only',action='store_true')
    p.add_argument('--part',action='store_true',help='Build original Part/Materials after missing OCCT dependencies are available; does not stage an APK')
    p.add_argument('--occt-prefix',type=Path,default=ROOT.parent/'toolchains/occt-part-android')
    args=p.parse_args()
    if not 1<=args.jobs<=16:p.error('--jobs must be 1 to 16')
    source,build,prefix,qt,qthost,ndk,cpython,occt=(v.resolve() for v in (args.source,args.build,args.prefix,args.qt,args.qt_host,args.ndk,args.cpython,args.occt_headers))
    py=cpython/'cross-build/aarch64-linux-android/prefix'
    if not (py/'lib/libpython3.13.so').is_file():p.error('Build the CPython Android prefix first')
    if 'Xml LinguistTools)' not in (source/'cMake/FreeCAD_Helpers/SetupQt.cmake').read_text():p.error('Apply the headless translation patch first')
    boost_file=source/'cMake/FreeCAD_Helpers/SetupBoost.cmake';text=boost_file.read_text()
    old='    if(UNIX AND NOT APPLE)'
    new=('    # Android provides pthread functions in libc, without a libpthread DSO.\n'
         '    # Keep the Boost/Threads compiler flags, but do not append -lpthread.\n'
         '    if(UNIX AND NOT APPLE AND NOT ANDROID)')
    if old in text:boost_file.write_text(text.replace(old,new,1))
    elif new not in text:p.error('Unexpected SetupBoost.cmake; review the Android pthread patch')
    init=(source/'cMake/FreeCAD_Helpers/InitializeFreeCADBuildOptions.cmake').read_text()
    modules=re.findall(r'option\((BUILD_[A-Z_]+) "Build the FreeCAD',init)
    command=['cmake','-S',str(source),'-B',str(build),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
        '-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),
        '-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-26','-DANDROID_STL=c++_shared',
        '-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384',
        '-DCMAKE_PREFIX_PATH='+str(prefix)+';'+str(qt)+';'+str(py),
        '-DCMAKE_FIND_ROOT_PATH='+str(prefix)+';'+str(qt)+';'+str(py),
        '-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER','-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY',
        '-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY','-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY',
        '-DFREECAD_QT_VERSION=6','-DQT_HOST_PATH='+str(qthost),
        '-DQt6_DIR='+str(qt/'lib/cmake/Qt6'),
        '-DQt6LinguistTools_DIR='+str(qthost/'lib/cmake/Qt6LinguistTools'),
        '-DQt6CoreTools_DIR='+str(qthost/'lib/cmake/Qt6CoreTools'),
        '-DBUILD_GUI=OFF','-DENABLE_DEVELOPER_TESTS=OFF','-DBUILD_FEM_VTK=OFF',
        '-DFREECAD_USE_SMESH=OFF','-DBUILD_SMESH=OFF','-DFREECAD_USE_FREETYPE=OFF',
        '-DFREECAD_USE_EXTERNAL_E57FORMAT=ON','-DFREECAD_USE_EXTERNAL_FMT=ON',
        '-DBOOST_ROOT='+str(prefix),'-DBoost_NO_BOOST_CMAKE=ON',
        '-DPython3_EXECUTABLE='+str(cpython/'cross-build/build/python'),
        '-DPython3_INCLUDE_DIR='+str(py/'include/python3.13'),
        '-DPython3_LIBRARY='+str(py/'lib/libpython3.13.so'),
        '-DOCCT_CMAKE_FALLBACK=ON','-DOCC_INCLUDE_DIR='+str(occt),
        '-DOCC_LIBRARY='+str(ROOT/'app/src/main/jniLibs/arm64-v8a/libTKernel.so'),
        '-DEIGEN3_INCLUDE_DIR='+str(ROOT/'vendor/eigen'),
        '-DICU_ROOT='+str(prefix)]
    command+=['-D'+name+'=OFF' for name in sorted(set(modules))]
    if args.part:
        occ=args.occt_prefix.resolve()
        if not (occ/'lib/libTKFeat.so').is_file() or not (occ/'lib/libTKDEGLTF.so').is_file():p.error('Build the missing Part OCCT dependencies first')
        command += ['-DBUILD_PART=ON','-DBUILD_MATERIAL=ON','-DOCC_LIBRARY='+str(occ/'lib/libTKernel.so'),'-DOCC_LIBRARY_DIR='+str(occ/'lib'),'-DCMAKE_MODULE_LINKER_FLAGS=-Wl,-z,max-page-size=16384']
    env=dict(os.environ)
    env['LD_LIBRARY_PATH']=str(qthost/'lib')+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    subprocess.run(command,check=True,env=env)
    if not args.configure_only:
        subprocess.run(['cmake','--build',str(build),'--target','FreeCADBase','FreeCADApp','FreeCADMainPy',*(['Materials','Part'] if args.part else []),
            '--parallel',str(args.jobs)],check=True,env=env)
    print('Upstream Android core', 'configured' if args.configure_only else 'cross-built',
        'at',build,'(JNI/Android runtime verification NOT_RUN)')

if __name__=='__main__':main()
