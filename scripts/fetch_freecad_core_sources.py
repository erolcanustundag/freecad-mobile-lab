#!/usr/bin/env python3
"""Fetch checksum-pinned upstream core sources from the checkpoint manifest."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--only',nargs='+',choices=['freecad','cpython','qtbase','boost','icu','fmt','yaml-cpp','pybind11','xerces'])
    args=p.parse_args();manifest=json.loads((ROOT/'docs/FREECAD-ANDROID-TOOLCHAINS.json').read_text())
    specs=[]
    def add(name,key,archive,subdirectory=''):
        if key in manifest:specs.append(dict(manifest[key],name=name,archive=archive,subdirectory=subdirectory))
    add('freecad','freecad_source','FreeCAD-1.1.4.tar.gz')
    add('cpython','cpython_source','cpython-v3.13.16.tar.gz')
    add('qtbase','qtbase_source','qtbase-everywhere-src-6.8.3.tar.xz')
    add('boost','boost','boost_1_87_0.tar.bz2')
    add('icu','icu','icu4c-74_2-src.tgz','icu-74.2')
    add('xerces','xerces','xerces-c-3.2.5.tar.gz')
    specs += [dict(e,subdirectory='') for e in manifest.get('cmake_dependencies',[])]
    if args.only:specs=[e for e in specs if e['name'] in args.only]
    if args.only and set(args.only)-{e['name'] for e in specs}:p.error('Requested source is not pinned in the manifest')
    def fetch(entry):
        algorithm='sha256' if 'sha256' in entry else 'sha512'
        path=ROOT.parent/'toolchains'/entry['archive'];path.parent.mkdir(parents=True,exist_ok=True)
        def valid(file):return file.is_file() and hashlib.new(algorithm,file.read_bytes()).hexdigest()==entry[algorithm]
        if not valid(path):
            temp=path.with_suffix('.partial')
            try:
                with urllib.request.urlopen(entry['url'],timeout=60) as src,temp.open('wb') as out:
                    while data:=src.read(1024*1024):
                        out.write(data)
                        if out.tell()>256*1024*1024:raise ValueError('Source archive exceeds 256 MiB')
                if not valid(temp):raise ValueError('Source checksum mismatch: '+entry['name'])
                temp.replace(path)
            finally:temp.unlink(missing_ok=True)
        return entry,path
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:archives=list(pool.map(fetch,specs))
    for entry,path in archives:
        destination=ROOT.parent/'upstream'/entry['subdirectory'];destination.mkdir(parents=True,exist_ok=True)
        if path.suffix=='.zip':
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Invalid source ZIP path')
                archive.extractall(destination)
        else:
            with tarfile.open(path) as archive:archive.extractall(destination,filter='data')
        print('Verified and extracted',entry['name'],flush=True)

if __name__=='__main__':main()
