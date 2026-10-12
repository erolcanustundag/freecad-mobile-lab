#!/usr/bin/env python3
"""Build pinned CPython for ARM64 Android using its upstream Android tooling.

This produces a dependency prefix, not an APK or a device runtime test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
HOST='aarch64-linux-android'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT.parent/'upstream/cpython-3.13.16')
    p.add_argument('--sdk',type=Path,default=ROOT.parent/'toolchains/android-sdk')
    p.add_argument('--ndk',type=Path,default=ROOT.parent/'toolchains/android-ndk-r27c')
    p.add_argument('--jobs',type=int,default=2)
    args=p.parse_args()
    source,sdk,ndk=(v.resolve() for v in (args.source,args.sdk,args.ndk))
    if not 1<=args.jobs<=32:p.error('--jobs must be 1 to 32')
    if not (source/'Android/android.py').is_file():p.error('Extract the pinned CPython source first')
    script=source/'Android/android-env.sh';text=script.read_text()
    old='ndk=$ANDROID_HOME/ndk/$ndk_version\nif ! [ -e "$ndk/package.xml" ]; then'
    new=('# Allow a verified standalone toolchain; do not impersonate another SDK version.\n'
         'ndk=${ANDROID_NDK_ROOT:-$ANDROID_HOME/ndk/$ndk_version}\n'
         'if [ -n "${ANDROID_NDK_ROOT:-}" ] && ! [ -d "$ndk/toolchains/llvm/prebuilt" ]; then\n'
         '    fail "ANDROID_NDK_ROOT is not a valid standalone NDK"\n'
         'fi\n'
         'if [ -z "${ANDROID_NDK_ROOT:-}" ] && ! [ -e "$ndk/package.xml" ]; then')
    if old in text:script.write_text(text.replace(old,new,1))
    elif new not in text:p.error('Unexpected android-env.sh; review the pinned NDK override patch')
    env=dict(os.environ,ANDROID_HOME=str(sdk),ANDROID_NDK_ROOT=str(ndk),ANDROID_API_LEVEL='26')
    # The upstream downloader caches archives without checking their hashes.
    # Populate that cache with the checkpoint's verified artifacts first.
    manifest_path=ROOT/'docs/FREECAD-ANDROID-TOOLCHAINS.json'
    manifest=json.loads(manifest_path.read_text())
    cache=source/'cross-build/downloads';cache.mkdir(parents=True,exist_ok=True)
    for item in manifest['cpython_dependency_archives']:
        filename=item['filename']
        if Path(filename).name!=filename:raise ValueError('Invalid dependency archive name')
        destination=cache/filename
        def valid(path):return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        if not valid(destination):
            tag=filename.removesuffix('-'+HOST+'.tar.gz')
            url='https://github.com/beeware/cpython-android-source-deps/releases/download/'+tag+'/'+filename
            temp=destination.with_suffix('.partial')
            try:
                with urllib.request.urlopen(url,timeout=60) as src,temp.open('wb') as out:
                    while data:=src.read(1024*1024):
                        out.write(data)
                        if out.tell()>32*1024*1024:raise ValueError('Oversized Python dependency')
                if not valid(temp):raise ValueError('Python dependency checksum mismatch: '+filename)
                temp.replace(destination)
            finally:temp.unlink(missing_ok=True)
    def run(command):subprocess.run(command,cwd=source,env=env,check=True)
    helper=[sys.executable,'Android/android.py']
    build=source/'cross-build/build'
    if not (build/'Makefile').exists():run(helper+['configure-build','--','--without-ensurepip'])
    run(['make','-C',str(build),'-j'+str(args.jobs)])
    run(helper+['configure-host',HOST])
    cross=source/'cross-build'/HOST
    run(['make','-C',str(cross),'-j'+str(args.jobs)])
    run(['make','-C',str(cross),'install','prefix='+str(cross/'prefix')])
    manifest['cpython_source']['status']='ARM64_CROSS_BUILT_DEVICE_NOT_RUN'
    manifest['cpython_dependency_archives']=[{'filename':v.name,'size':v.stat().st_size,
        'sha256':hashlib.sha256(v.read_bytes()).hexdigest()}
        for v in sorted((source/'cross-build/downloads').glob('*.tar.gz'))]
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('CPython Android prefix:',cross/'prefix','(Android execution NOT_RUN)')

if __name__=='__main__':main()
