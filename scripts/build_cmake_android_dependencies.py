#!/usr/bin/env python3
"""Build pinned fmt/yaml-cpp/pybind11 and optionally Xerces for ARM64 core."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--prefix',type=Path,default=ROOT.parent/'toolchains/freecad-android-prefix')
    p.add_argument('--jobs',type=int,default=2)
    p.add_argument('--xerces',action='store_true',help='Requires the ICU cross-build prefix')
    args=p.parse_args()
    if not 1<=args.jobs<=16:p.error('--jobs must be 1 to 16')
    prefix=args.prefix.resolve();ndk=args.ndk.resolve()
    specs=[('fmt-11.1.4',['-DFMT_TEST=OFF','-DFMT_DOC=OFF','-DFMT_INSTALL=ON']),
        ('yaml-cpp-0.8.0',['-DYAML_CPP_BUILD_TESTS=OFF','-DYAML_CPP_BUILD_TOOLS=OFF','-DYAML_BUILD_SHARED_LIBS=ON']),
        ('pybind11-2.13.6',['-DPYBIND11_TEST=OFF','-DPYBIND11_INSTALL=ON','-DPYBIND11_NOPYTHON=ON'])]
    if args.xerces:specs=[('xerces-c-3.2.5',['-Dtranscoder=icu','-Dnetwork=OFF',
        '-Dthreads=posix','-DBUILD_TESTING=OFF','-DBUILD_SAMPLES=OFF','-DBUILD_DOC=OFF','-DICU_ROOT='+str(prefix)])]
    for name,options in specs:
        source=(ROOT.parent/'upstream'/name).resolve()
        if not (source/'CMakeLists.txt').is_file():p.error('Extract pinned source first: '+name)
        build=(ROOT.parent/(name+'-android-build')).resolve()
        command=['cmake','-S',str(source),'-B',str(build),'-G','Ninja',
            '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
            '-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),
            '-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-26','-DANDROID_STL=c++_shared',
            '-DCMAKE_INSTALL_PREFIX='+str(prefix),'-DCMAKE_PREFIX_PATH='+str(prefix),
            '-DCMAKE_FIND_ROOT_PATH='+str(prefix),'-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY',
            '-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY','-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY',
            '-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER','-DBUILD_SHARED_LIBS=ON',
            '-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384',*options]
        subprocess.run(command,check=True)
        subprocess.run(['cmake','--build',str(build),'--parallel',str(args.jobs)],check=True)
        subprocess.run(['cmake','--install',str(build)],check=True)
        print('Built Android dependency',name,flush=True)

if __name__=='__main__':main()
