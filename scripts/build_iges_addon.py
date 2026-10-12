#!/usr/bin/env python3
"""Build the matching OCCT IGES toolkit against the supplied pinned native libraries."""
from pathlib import Path
import subprocess,os,shutil
root=Path(__file__).resolve().parents[1];workspace=root.parent
source=Path(os.environ.get('OCCT_SOURCE',workspace/'occt-source'))
ndk=Path(os.environ.get('ANDROID_NDK_ROOT',workspace/'toolchains/android-ndk-r27c'))
prefix=root/'vendor/occt/arm64-v8a';build=root/'iges-build';project=build/'project';project.mkdir(parents=True,exist_ok=True)
sources=[]
for package in (source/'src/TKDEIGES/PACKAGES').read_text().split():
 folder=source/'src'/package;sources+=sorted(folder.glob('*.cxx'))+sorted(folder.glob('*.c'))
 for file in folder.iterdir():
  if file.suffix in ('.hxx','.lxx','.gxx'):shutil.copy2(file,prefix/'include/opencascade'/file.name)
libs=(source/'src/TKDEIGES/EXTERNLIB').read_text().split()
text='cmake_minimum_required(VERSION 3.22)\nproject(OCCTIgesAddon LANGUAGES C CXX)\nset(CMAKE_CXX_STANDARD 11)\n'
for lib in libs:text+=f'add_library({lib} SHARED IMPORTED)\nset_target_properties({lib} PROPERTIES IMPORTED_LOCATION "{prefix}/lib/lib{lib}.so")\n'
text+='add_library(TKDEIGES SHARED\n'+''.join(f'"{p}"\n' for p in sources)+')\n'
text+=f'target_include_directories(TKDEIGES PRIVATE "{prefix}/include/opencascade")\ntarget_link_libraries(TKDEIGES PRIVATE '+ ' '.join(libs)+')\ntarget_link_options(TKDEIGES PRIVATE -Wl,-z,max-page-size=16384)\n'
(project/'CMakeLists.txt').write_text(text)
subprocess.run(['cmake','-S',str(project),'-B',str(build/'build'),'-G','Ninja',f'-DCMAKE_TOOLCHAIN_FILE={ndk}/build/cmake/android.toolchain.cmake','-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-26','-DANDROID_STL=c++_shared','-DCMAKE_BUILD_TYPE=Release'],check=True)
subprocess.run(['cmake','--build',str(build/'build'),'--parallel',os.environ.get('BUILD_JOBS','4')],check=True)
shutil.copy2(build/'build/libTKDEIGES.so',prefix/'lib/libTKDEIGES.so')
print('Built IGES addon from pinned OCCT source:',len(sources),'translation units',flush=True)
