#!/usr/bin/env python3
"""Preserve costly core build outputs and dependency prefixes for continuation.

Source archives/NDK/JDK are fetched separately using pinned manifests.
Symlinked regular files are stored as bytes so standard ZIP extraction is safe.
"""
from pathlib import Path
import hashlib
import json
import zipfile
import os

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
PREFIXES=['occt-host','toolchains/freecad-host-prefix','toolchains/freecad-android-prefix',
    'toolchains/qt/linux-x86_64','toolchains/qt/android-arm64-16k',
    'upstream/cpython-3.13.16/cross-build/aarch64-linux-android/prefix']
paths=[]
for name in PREFIXES:
    folder=BASE/name
    if not folder.is_dir():raise ValueError('Missing checkpoint prefix: '+name)
    paths += [p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
for name in ('freecad-core-host','freecad-core-android'):
    folder=BASE/name
    paths += [p for p in (folder/'lib').glob('*') if p.is_file()]
    paths += [p for p in (folder/'src').rglob('*') if p.is_file() and p.suffix in ('.h','.hpp','.hxx')]
paths += [p for p in (ROOT/'docs').glob('*') if p.is_file() and any(s in p.name for s in ('CORE','DEPENDENCIES','TOOLCHAINS','core-','android-loader','qt-core'))]
paths += [p for p in (ROOT/'samples/upstream-core').glob('*') if p.is_file()]
paths=sorted(set(paths))

def is_host(path):
    name=str(path.relative_to(BASE))
    return any(name.startswith(prefix+'/') for prefix in ('occt-host','toolchains/freecad-host-prefix',
        'toolchains/qt/linux-x86_64','freecad-core-host'))

def write_part(label,selected):
    OUT=ROOT/'dist'/('FreeCAD-Mobile-Lab-core-build-'+label+'.zip')
    records=[]
    temp=OUT.with_suffix('.tmp.zip')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
        for path in selected:
            name='FreeCADMobileLab/'+str(path.relative_to(BASE))
            data=path.read_bytes()
            info=zipfile.ZipInfo(name)
            info.create_system=3
            info.external_attr=(0o100000 | (path.stat().st_mode & 0o777)) << 16
            info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
            records.append({'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        archive.writestr('CHECKPOINT-'+label+'.json',json.dumps({'scope':'development build outputs, not an APK',
            'host':'Linux x86_64','android':'ARM64 API26/NDK27c','android_runtime':'NOT_RUN',
            'jni_adapter':'build separately from the matching source bundle','files':records},indent=2)+'\n')
        archive.writestr('README-'+label+'.txt','This is a reusable build checkpoint, not an Android installer.\n'
            'Extract BOTH core-build-host.zip and core-build-android.zip under the project parent; preserve ZIP executable modes.\n'
            'Fetch frozen upstream source/NDK/JDK separately; read native-cad/docs/FREECAD-CORE-PORT.md.\n'
            'Rebuild the small JNI adapter from the source bundle. Device execution remains unverified.\n')
    with zipfile.ZipFile(temp) as archive:
        assert archive.testzip() is None,'Core checkpoint CRC failure'
        for entry in records:
            assert hashlib.sha256(archive.read(entry['path'])).hexdigest()==entry['sha256'],entry['path']
    os.replace(temp,OUT)
    print('PASS:',len(records),'checkpoint files, CRC/SHA256 verified; size',round(OUT.stat().st_size/2**20,1),'MiB')
    print(OUT)

for label in ('host','android'):
    write_part(label,[p for p in paths if is_host(p)==(label=='host')])
