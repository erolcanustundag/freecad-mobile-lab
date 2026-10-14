#!/usr/bin/env python3
"""Stage a 16 KiB upstream App runtime for the isolated document activity.

Preserves the existing 31-library mobile renderer/kernel checkpoint. New
dependencies and Python assets have their own content manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
NDK=BASE/'toolchains/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin'
READELF=NDK/'llvm-readelf'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dynamic(path):return subprocess.check_output([str(READELF),'-d',str(path)],text=True)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--part',action='store_true',help='Stage the verified original Part/Materials runtime and its seven OCCT dependencies')
    parser.add_argument('--sketcher',action='store_true',help='Stage genuine Sketcher and solver; implies --part')
    parser.add_argument('--partdesign',action='store_true',help='Stage original PartDesign; implies Sketcher/Part')
    args=parser.parse_args()
    if args.partdesign:args.sketcher=True
    if args.sketcher:args.part=True
    libs=ROOT/'app/src/main/jniLibs/arm64-v8a'
    baseline=json.loads((ROOT/'versions-prebuilt.json').read_text())['libraries']
    for name,value in baseline.items():
        if digest(libs/name)!=value:raise ValueError('Retained mobile library changed: '+name)
    qt=BASE/'toolchains/qt/android-arm64-16k'
    prefix=BASE/'toolchains/freecad-android-prefix'
    python=BASE/'upstream/cpython-3.13.16/cross-build/aarch64-linux-android/prefix'
    core=BASE/('freecad-partdesign-android' if args.partdesign else 'freecad-part-android' if args.part else 'freecad-core-android')
    sources=list((core/'lib').glob('*.so'))
    if args.part:
        sources += [core/'Mod/Part/Part.so',core/'Mod/Material/Materials.so']
        sources += [BASE/'toolchains/occt-part-android/lib'/('lib'+name+'.so') for name in ('TKFeat','TKExpress','TKBin','TKBinL','TKMeshVS','TKRWMesh','TKDEGLTF')]
    renamed={'FreeCAD.so':'libFreeCADPython.so'}
    if args.part: renamed.update({'Part.so':'libFreeCADPart.so','Materials.so':'libFreeCADMaterials.so'})
    if args.sketcher:
        sources += [core/'Mod/Sketcher/Sketcher.so']
        renamed['Sketcher.so']='libFreeCADOriginalSketcher.so'
    if args.partdesign:
        sources += [core/'Mod/PartDesign/_PartDesign.so']
        renamed['_PartDesign.so']='libFreeCADOriginalPartDesign.so'
    sources+=list((prefix/'lib').glob('*.so'))+list((qt/'lib').glob('*.so'))
    sources+=list((python/'lib').glob('*.so'))
    sources+=[ROOT/'core-bridge-android/libfreecad_document_bridge.so']
    records={};originals={}
    for source in sorted(sources):
        sonames=re.findall(r'\(SONAME\).*?\[(.*?)\]',dynamic(source))
        name=sonames[0] if sonames else source.name
        name=renamed.get(name,name)
        if not name.startswith('lib') or not name.endswith('.so'):raise ValueError('Invalid APK library name: '+name)
        if name in baseline:raise ValueError('Core dependency collides with the retained kernel: '+name)
        if name in originals:
            if digest(source)!=originals[name]:raise ValueError('Conflicting dependency SONAME: '+name)
            continue
        originals[name]=digest(source)
        destination=libs/name;shutil.copyfile(source,destination)
        subprocess.run([str(NDK/'llvm-strip'),'--strip-unneeded',str(destination)],check=True)
        # Builtin modules are registered with AppendInittab. Normalize their
        # APK filenames, SONAMEs and every dependency edge together.
        if name in renamed.values():
            subprocess.run(['patchelf','--page-size','16384','--set-soname',name,str(destination)],check=True)
        needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic(destination))
        for original,replacement in renamed.items():
            if original in needed:
                subprocess.run(['patchelf','--page-size','16384','--replace-needed',original,replacement,str(destination)],check=True)
        if 'RUNPATH' in dynamic(destination) or 'RPATH' in dynamic(destination):
            subprocess.run(['patchelf','--page-size','16384','--remove-rpath',str(destination)],check=True)
        records[name]=digest(destination)
    required={'libFreeCADPython.so','libFreeCADApp.so','libFreeCADBase.so','libpython3.13.so',
        'libQt6Core_arm64-v8a.so','libfreecad_document_bridge.so'}
    if args.part: required.update({'libFreeCADPart.so','libFreeCADMaterials.so','libTKFeat.so','libTKExpress.so','libTKBin.so','libTKBinL.so','libTKMeshVS.so','libTKRWMesh.so','libTKDEGLTF.so'})
    if args.sketcher:required.add('libFreeCADOriginalSketcher.so')
    if not required.issubset(records):raise ValueError('Incomplete core dependency set')
    if args.partdesign:required.add('libFreeCADOriginalPartDesign.so')
    extras={p.name for p in libs.glob('*.so')}-set(baseline)-set(records)
    if extras:raise ValueError('Untracked native libraries: '+str(extras))
    assets=ROOT/'app/src/main/assets/core';assets.mkdir(parents=True,exist_ok=True)
    standard=python/'lib/python3.13'
    files=[p for p in standard.rglob('*') if p.is_file() and not {'__pycache__','test','tests','site-packages','ensurepip'}.intersection(p.relative_to(standard).parts) and p.suffix not in ('.pyc','.pyo')]
    out=assets/'python-home.zip';runtime=[]
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(files):
            name='lib/python3.13/'+str(path.relative_to(standard))
            z.write(path,name);runtime.append({'path':name,'size':path.stat().st_size,'sha256':digest(path)})
        for script in sorted(assets.glob('mobile_*.py')):
            name='scripts/'+script.name;z.write(script,name)
            runtime.append({'path':name,'size':script.stat().st_size,'sha256':digest(script)})
        if args.part:
            for resource in sorted((assets/'resources').rglob('*')):
                if resource.is_file() and not {'__pycache__'}.intersection(resource.parts) and resource.suffix not in ('.pyc','.pyo'):
                    name='scripts/'+str(resource.relative_to(assets));z.write(resource,name)
                    runtime.append({'path':name,'size':resource.stat().st_size,'sha256':digest(resource)})
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None:raise ValueError('Python asset CRC failure')
        for item in runtime:
            if hashlib.sha256(z.read(item['path'])).hexdigest()!=item['sha256']:raise ValueError('Python asset hash failure')
    jars=ROOT/'app/libs';jars.mkdir(exist_ok=True)
    shutil.copyfile(qt/'jar/Qt6Android.jar',jars/'Qt6Android.jar')
    licenses=assets/'licenses';licenses.mkdir(exist_ok=True)
    for path,name in ((BASE/'upstream/cpython-3.13.16/LICENSE','CPython-LICENSE.txt'),
        (BASE/'upstream/qtbase-everywhere-src-6.8.3/LICENSES/LGPL-3.0-only.txt','Qt-LGPL-3.0.txt'),
        (BASE/'upstream/FreeCAD-1.1.4/LICENSE','FreeCAD-LICENSE.txt')):
        if path.is_file():shutil.copyfile(path,licenses/name)
    (assets/'SOURCES.txt').write_text(('FreeCAD 1.1.4 Base/App/Part/Materials/Sketcher/PartDesign; ' if args.partdesign else 'FreeCAD 1.1.4 Base/App/Part/Materials/Sketcher; ' if args.sketcher else 'FreeCAD 1.1.4 Base/App/Part/Materials; ' if args.part else 'FreeCAD 1.1.4 Base/App; ')+ ' Qt 6.8.3 headless Core/XML/Network/Concurrent; CPython 3.13.16.\n'
        'Frozen sources, checksums, build scripts and patches: native-cad/docs/FREECAD-ANDROID-TOOLCHAINS.json and scripts.\n'
        'This isolated document lab is experimental. Only the documented bounded Part/Sketcher/Body/Pad/Pocket adapters are included; other workbenches and Android runtime parity remain pending.\n'
        'Source URLs and dependency notices: native-cad/docs/FREECAD-CORE-PORT.md and the dependency manifests.\n'+('Bundled original FreeCAD material/model resources retain their individual authors/licenses; default material data is GPL-2.0-or-later. Full GPL2 text is included in core/licenses/material-data-GPL-2.0.txt.\n' if args.part else ''))
    report={'scope':'opt-in upstream App/Part document lab; Android execution NOT_RUN' if args.part else 'opt-in upstream App document lab; Android execution NOT_RUN',
        'part':args.part,'sketcher':args.sketcher,'partdesign':args.partdesign,'builtin_modules':(['FreeCAD','Materials','Part'] if args.part else ['FreeCAD'])+(['Sketcher'] if args.sketcher else [])+(['_PartDesign'] if args.partdesign else []),
        'build_inputs':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'app/src/main/cpp/upstream-core/CoreBridge.cpp',ROOT/'app/src/main/cpp/upstream-core/CMakeLists.txt',ROOT/'scripts/build_freecad_android_core.py',ROOT/'scripts/build_part_occt.py',ROOT/'scripts/build_core_bridge.py',ROOT/'scripts/patch_embedded_runtime.py',ROOT/'scripts/patch_headless_sketcher.py']},
        'libraries':records,'original_library_hashes':originals,'python_assets':runtime,
        'asset_zip_sha256':digest(out),'java_jar_sha256':digest(jars/'Qt6Android.jar')}
    (ROOT/'docs/core-apk-inputs.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Staged',len(records),'additional ARM64 libraries,',len(runtime),'runtime files; retained 31 mobile libraries unchanged')
if __name__=='__main__':main()
