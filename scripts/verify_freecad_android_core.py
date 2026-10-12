#!/usr/bin/env python3
"""Check core dependency ELF architecture/alignment/loader closure.

Static checks are not proof of embedded Python initialisation or Android
document behaviour. No core dependency is added to the release APK here.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT.parent/'toolchains'
READELF=TOOLS/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
SYSTEM={'libc.so','libm.so','libdl.so','liblog.so','libandroid.so','libz.so'}

def main():
    python=ROOT.parent/'upstream/cpython-3.13.16/cross-build/aarch64-linux-android/prefix/lib'
    directories=[ROOT.parent/'freecad-core-android/lib',TOOLS/'freecad-android-prefix/lib',
        TOOLS/'qt/android-arm64-16k/lib',python]
    files=[]
    for directory in directories:files+=sorted(directory.glob('*.so'))
    files+=sorted((python/'python3.13/lib-dynload').glob('*.so'))
    files.append(ROOT/'app/src/main/jniLibs/arm64-v8a/libc++_shared.so')
    expected={'libFreeCADBase.so','libFreeCADApp.so','FreeCAD.so'}
    if not expected.issubset({p.name for p in files}):raise ValueError('The upstream core build has not completed')
    records=[];provided=set();failures=[];seen=set();exports=set();imports={}
    def symbols(file):
        output=subprocess.check_output([str(READELF),'--dyn-syms','--wide',str(file)],text=True)
        defined=set();required=set()
        for line in output.splitlines():
            columns=line.split(maxsplit=7)
            if len(columns)==8 and columns[0].rstrip(':').isdigit() and columns[4] in ('GLOBAL','WEAK'):
                name=columns[7].split()[0].split('@')[0]
                if columns[6]!='UND':defined.add(name)
                elif columns[4]!='WEAK':required.add(name)
        return defined,required
    for file in files:
        if file.resolve() in seen:continue
        seen.add(file.resolve())
        header=subprocess.check_output([str(READELF),'-h',str(file)],text=True)
        segments=subprocess.check_output([str(READELF),'-lW',str(file)],text=True)
        dynamic=subprocess.check_output([str(READELF),'-d',str(file)],text=True)
        alignment=min(int(line.split()[-1],16) for line in segments.splitlines() if line.strip().startswith('LOAD '))
        needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic)
        soname=re.findall(r'\(SONAME\).*?\[(.*?)\]',dynamic)
        name=soname[0] if soname else file.name
        if 'AArch64' not in header or alignment<16384:failures.append('Architecture/alignment: '+file.name)
        if not name.endswith('.so'):failures.append('Versioned loader name cannot be JNI packaged: '+name)
        provided.add(name)
        defined,required=symbols(file);exports.update(defined);imports[file.name]=required
        records.append({'filename':file.name,'soname':name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
            'minimum_load_alignment':alignment,'needed':needed})
    for record in records:
        for name in record['needed']:
            if name not in SYSTEM and name not in provided:failures.append(record['filename']+' missing '+name)
    # Check the linked ABI against API-26 stubs and the retained libc++, rather
    # than trusting only a matching SONAME or version string.
    sysroot=TOOLS/'android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/26'
    for name in SYSTEM:exports.update(symbols(sysroot/name)[0])
    missing_symbols={name:sorted(values-exports) for name,values in imports.items() if values-exports}
    if missing_symbols:failures.append('Unresolved strong symbols against provided libraries/API26: '+str(missing_symbols))
    report={'status':'STATIC_FAIL' if failures else 'STATIC_PASS_DEVICE_NOT_RUN',
        'android_execution':'NOT_RUN','jni_document_adapter':'NOT_IMPLEMENTED',
        'release_apk_contains_core':False,
        'python_entrypoint_packaging':'FreeCAD.so is a Python entrypoint; Android adapter must register/package it explicitly',
        'library_count':len(records),'strong_symbol_closure':not missing_symbols,
        'failures':failures,'libraries':records}
    (ROOT/'docs/freecad-core-android-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    if failures:raise ValueError('; '.join(failures))
    print('PASS:',len(records),'ARM64 core/dependency libraries, 16 KiB alignment and loader closure; Android execution NOT_RUN')

if __name__=='__main__':main()
