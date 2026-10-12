#!/usr/bin/env python3
"""Build genuine missing OCCT7.9.2 Part dependencies against retained ARM64 libraries.

Existing toolkit bytes are imported, never rebuilt or replaced. No geometry
implementations are stubbed: selected toolkits compile their upstream FILES.
"""
import argparse,json,subprocess,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=['TKFillet','TKMesh','TKernel','TKG2d','TKG3d','TKMath','TKShHealing','TKXSBase','TKBool','TKBO','TKBRep','TKTopAlgo','TKGeomAlgo','TKGeomBase','TKOffset','TKPrim','TKHLR','TKFeat','TKExpress','TKBin','TKBinL','TKCAF','TKXCAF','TKLCAF','TKVCAF','TKCDF','TKMeshVS','TKService','TKV3d','TKRWMesh','TKDESTEP','TKDEIGES','TKDEGLTF','TKDESTL']
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jobs',type=int,default=4);p.add_argument('--configure-only',action='store_true');p.add_argument('--host',action='store_true',help='Build Linux reference dependencies separately from Android');args=p.parse_args()
    base=ROOT.parent;source=base/'occt-source';headers=base/'occt-host/include/opencascade';ndk=base/'toolchains/android-ndk-r27c'
    platform='host' if args.host else 'android'
    work=base/('occt-part-'+platform);project=work/'project';prefix=base/'toolchains'/('occt-part-'+platform);project.mkdir(parents=True,exist_ok=True);(prefix/'lib').mkdir(parents=True,exist_ok=True)
    existing_dir=base/'occt-host/lib' if args.host else ROOT/'app/src/main/jniLibs/arm64-v8a'
    existing={x.stem[3:]:x for x in existing_dir.glob('libTK*.so')};missing=[x for x in REQUIRED if x not in existing]
    include=prefix/'include/opencascade';include.parent.mkdir(parents=True,exist_ok=True)
    # The retained minimal OCCT install lacks headers from unbuilt toolkits.
    # Keep generated headers, then add genuine upstream headers/inline files.
    if include.is_symlink():include.unlink()
    include.mkdir(exist_ok=True)
    for path in headers.iterdir():
        if path.is_file() and not (include/path.name).exists():(include/path.name).symlink_to(path)
    for path in sorted((source/'src').glob('*/*')):
        if path.suffix in ('.h','.hxx','.lxx','.gxx','.pxx') and not (include/path.name).exists():(include/path.name).symlink_to(path)
    lines=['cmake_minimum_required(VERSION 3.21)','project(FreeCADPartOCCT LANGUAGES C CXX)','set(CMAKE_CXX_STANDARD 17)','set(CMAKE_POSITION_INDEPENDENT_CODE ON)','set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG")',f'set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "{prefix}/lib")','set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -Wl,-z,max-page-size=16384")',f'include_directories(SYSTEM "{include}")']
    for name,path in sorted(existing.items()):
        destination=prefix/'lib'/path.name
        if not destination.exists():destination.symlink_to(path)
        lines += [f'add_library({name} SHARED IMPORTED GLOBAL)',f'set_target_properties({name} PROPERTIES IMPORTED_LOCATION "{path}")']
    records=[]
    for toolkit in missing:
        packages=(source/'src'/toolkit/'PACKAGES').read_text().split();files=[]
        for package in packages:
            folder=source/'src'/package
            for entry in (folder/'FILES').read_text().splitlines():
                name=entry.strip()
                if name.endswith(('.cxx','.cpp','.c')) and (folder/name).is_file():files.append(folder/name)
        if not files:raise ValueError('Missing upstream toolkit source: '+toolkit)
        dependencies=(source/'src'/toolkit/'EXTERNLIB').read_text().split()
        toolkit_deps=[x for x in dependencies if x.startswith('TK') or x=='TKernel']
        external=[x for x in dependencies if x not in toolkit_deps and not x.startswith('CSF_')]
        if external:raise ValueError('Review external toolkit dependencies: '+str(external))
        lines += [f'add_library({toolkit} SHARED '+' '.join('"'+str(x)+'"' for x in files)+')',f'target_compile_definitions({toolkit} PRIVATE __{toolkit}_DLL)',f'target_link_libraries({toolkit} PRIVATE '+' '.join(toolkit_deps)+')']
        records.append({'toolkit':toolkit,'sources':len(files),'dependencies':dependencies})
    (project/'CMakeLists.txt').write_text('\n'.join(lines)+'\n');(work/'toolkits.json').write_text(json.dumps(records,indent=2)+'\n')
    command=['cmake','-S',str(project),'-B',str(work/'build'),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release']
    if not args.host:command+=['-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),'-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-26','-DANDROID_STL=c++_shared']
    subprocess.run(command,check=True)
    if not args.configure_only:subprocess.run(['cmake','--build',str(work/'build'),'--parallel',str(args.jobs)],check=True)
    print('Part OCCT prerequisite', 'configured' if args.configure_only else 'built',missing,'at',prefix,'(not staged into an APK)')
if __name__=='__main__':main()
