#!/usr/bin/env python3
"""Build ICU host generators and ARM64 Android uc/i18n dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/unicode-org/icu/releases/download/release-74-2/icu4c-74_2-src.tgz'
SHA512='e6c7876c0f3d756f3a6969cad9a8909e535eeaac352f3a721338b9cbd56864bf7414469d29ec843462997815d2ca9d0dab06d38c37cdd4d8feb28ad04d8781b0'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--prefix',type=Path,default=ROOT.parent/'toolchains/freecad-android-prefix')
    p.add_argument('--jobs',type=int,default=3)
    args=p.parse_args()
    if not 1<=args.jobs<=16:p.error('--jobs must be 1 to 16')
    archive=ROOT.parent/'toolchains/icu4c-74_2-src.tgz'
    if not archive.exists():
        temp=archive.with_suffix('.partial')
        with urllib.request.urlopen(URL,timeout=60) as src,temp.open('wb') as stream:
            while data:=src.read(1024*1024):stream.write(data)
        if hashlib.sha512(temp.read_bytes()).hexdigest()!=SHA512:raise ValueError('ICU checksum mismatch')
        temp.replace(archive)
    if hashlib.sha512(archive.read_bytes()).hexdigest()!=SHA512:raise ValueError('ICU checksum mismatch')
    dest=ROOT.parent/'upstream/icu-74.2';source=dest/'icu/source'
    if not source.exists():
        dest.mkdir(parents=True,exist_ok=True)
        with tarfile.open(archive) as tar:tar.extractall(dest,filter='data')
    host=ROOT.parent/'icu-host-build';cross=ROOT.parent/'icu-android-build'
    host.mkdir(exist_ok=True);cross.mkdir(exist_ok=True)
    host=host.resolve();cross=cross.resolve();source=source.resolve();prefix=args.prefix.resolve()
    env=dict(os.environ)
    def run(command,directory,environment):subprocess.run(command,cwd=directory,env=environment,check=True)
    options=['--disable-tests','--disable-samples','--disable-extras','--disable-icuio']
    if not (host/'Makefile').exists():run([str(source/'configure'),'--disable-shared','--enable-static',*options],host,env)
    run(['make','-j'+str(args.jobs)],host,env)
    tools=args.ndk.resolve()/'toolchains/llvm/prebuilt/linux-x86_64/bin'
    targetenv=dict(env,CC=str(tools/'aarch64-linux-android26-clang'),CXX=str(tools/'aarch64-linux-android26-clang++'),
        AR=str(tools/'llvm-ar'),RANLIB=str(tools/'llvm-ranlib'),CFLAGS='-O2 -fPIC',CXXFLAGS='-O2 -fPIC',
        LDFLAGS='-Wl,-z,max-page-size=16384')
    if not (cross/'Makefile').exists():run([str(source/'configure'),'--host=aarch64-linux-android',
        '--with-cross-build='+str(host),'--prefix='+str(prefix),'--enable-shared','--disable-static',
        '--disable-tools',*options],cross,targetenv)
    run(['make','-j'+str(args.jobs)],cross,targetenv)
    run(['make','install'],cross,targetenv)
    manifest_path=ROOT/'docs/FREECAD-ANDROID-TOOLCHAINS.json';d=json.loads(manifest_path.read_text())
    d['icu']={'version':'74.2','url':URL,'sha512':SHA512,'status':'CROSS_BUILT_STATIC_CHECK_PENDING_DEVICE_NOT_RUN'}
    manifest_path.write_text(json.dumps(d,indent=2)+'\n')
    print('ICU Android dependencies installed:',prefix,'(Android execution NOT_RUN)')

if __name__=='__main__':main()
