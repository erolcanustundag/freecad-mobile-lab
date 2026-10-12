#!/usr/bin/env python3
"""Build the four upstream FreeCAD Boost components for ARM64 Android."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
URL='https://archives.boost.io/release/1.87.0/source/boost_1_87_0.tar.bz2'
SHA256='af57be25cb4c4f4b413ed692fe378affb4352ea50fbe294a11ef548f4d527d89'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--prefix',type=Path,default=ROOT.parent/'toolchains/freecad-android-prefix')
    p.add_argument('--jobs',type=int,default=2)
    args=p.parse_args()
    if not 1<=args.jobs<=16:p.error('--jobs must be 1 to 16')
    archive=ROOT.parent/'toolchains/boost_1_87_0.tar.bz2'
    if not archive.exists():
        temp=archive.with_suffix('.partial')
        with urllib.request.urlopen(URL,timeout=60) as src,temp.open('wb') as output:
            while data:=src.read(1024*1024):output.write(data)
        if hashlib.sha256(temp.read_bytes()).hexdigest()!=SHA256:raise ValueError('Boost source checksum mismatch')
        temp.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA256:raise ValueError('Boost source checksum mismatch')
    source=ROOT.parent/'upstream/boost_1_87_0'
    if not source.exists():
        with tarfile.open(archive) as tar:tar.extractall(ROOT.parent/'upstream',filter='data')
    prefix=args.prefix.resolve();prefix.mkdir(parents=True,exist_ok=True)
    toolchain=args.ndk.resolve()/'toolchains/llvm/prebuilt/linux-x86_64/bin'
    config=source/'freecad-android.jam'
    config.write_text('using clang : android : '+str(toolchain/'aarch64-linux-android26-clang++')+
        ' : <archiver>'+str(toolchain/'llvm-ar')+' <ranlib>'+str(toolchain/'llvm-ranlib')+
        ' <compileflags>-fPIC <linkflags>-Wl,-z,max-page-size=16384 ;\n')
    env=dict(os.environ)
    def run(command):subprocess.run(command,cwd=source,env=env,check=True)
    if not (source/'b2').is_file():run(['./bootstrap.sh','--with-toolset=gcc','--with-libraries=program_options,regex,thread,date_time'])
    run(['./b2','-j'+str(args.jobs),'--user-config='+str(config),'toolset=clang-android',
        'target-os=android','architecture=arm','address-model=64','threading=multi',
        'variant=release','link=shared','runtime-link=shared','--layout=system',
        '--with-program_options','--with-regex','--with-thread','--with-date_time',
        '--prefix='+str(prefix),'install'])
    print('Boost Android dependency prefix:',prefix,'(Android execution NOT_RUN)')

if __name__=='__main__':main()
