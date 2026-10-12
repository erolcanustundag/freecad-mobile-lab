#!/usr/bin/env python3
"""Use APK-compatible ICU SONAMEs while retaining 16 KiB LOAD alignment.

ICU's Unix makefiles produce .so.74 names. Android JNI packaging expects
lib*.so. This changes loader names, not the versioned ICU function ABI.
Only the separate cross-build prefix is touched, never sealed APK inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix',type=Path,default=ROOT.parent/'toolchains/freecad-android-prefix')
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--patchelf',default='patchelf')
    args=p.parse_args();lib=(args.prefix/'lib').resolve()
    if lib.is_relative_to((ROOT/'app').resolve()):p.error('Refusing to modify APK application inputs')
    readelf=args.ndk.resolve()/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
    files=sorted(lib.glob('libicu*.so'));names={};records=[]
    if len(files)<3:p.error('Build ICU first')
    for file in files:
        target=file.resolve()
        if not target.is_relative_to(lib):p.error('ICU library resolves outside the dependency prefix')
        header=subprocess.check_output([str(readelf),'-h',str(target)],text=True)
        if 'AArch64' not in header:p.error('Non-ARM64 library: '+str(file))
        old=subprocess.check_output([args.patchelf,'--print-soname',str(target)],text=True).strip()
        names[old]=file.name
    for file in files:
        target=file.resolve();before=hashlib.sha256(target.read_bytes()).hexdigest()
        command=[args.patchelf,'--page-size','16384','--set-soname',file.name]
        needed=subprocess.check_output([args.patchelf,'--print-needed',str(target)],text=True).splitlines()
        for name in needed:
            if name in names and name!=names[name]:command+=['--replace-needed',name,names[name]]
        subprocess.run(command+[str(target)],check=True)
        text=subprocess.check_output([str(readelf),'-lW',str(target)],text=True)
        alignment=min(int(line.split()[-1],16) for line in text.splitlines() if line.strip().startswith('LOAD '))
        if alignment<16384:raise ValueError('ICU alignment regressed: '+file.name)
        records.append({'filename':file.name,'source_sha256':before,
            'apk_loader_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'minimum_load_alignment':alignment,'device_runtime':'NOT_RUN'})
    (ROOT/'docs/icu-android-loader-verification.json').write_text(json.dumps(records,indent=2)+'\n')
    print('ICU APK loader names and 16 KiB alignment verified:',len(records),'libraries')

if __name__=='__main__':main()
