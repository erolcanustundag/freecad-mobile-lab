#!/usr/bin/env python3
"""Restore frozen Boost/Eigen sources from the matching public source asset."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True,type=Path)
    args=parser.parse_args()
    lock=json.loads((ROOT/'versions-prebuilt.json').read_text())['native_sources']
    selected={name:sha for name,sha in lock.items() if name.startswith(('vendor/boost/','vendor/eigen/'))}
    if selected and all((ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha for name,sha in selected.items()):
        print('PASS: frozen vendor sources already present;',len(selected),'native source hashes match')
        return
    release=json.loads((ROOT/'docs/RELEASE-ASSETS.json').read_text())
    item=next(a for a in release['assets'] if a['kind']=='application-source')
    with args.bundle.open('rb') as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=item['sha256']:
            raise ValueError('Source archive differs from the release lock')
    prefix='FreeCADMobileLab/native-cad/'
    with zipfile.ZipFile(args.bundle) as archive:
        if archive.testzip() is not None:raise ValueError('Source archive CRC failure')
        for name,sha in selected.items():
            data=archive.read(prefix+name)
            if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Source hash differs: '+name)
            destination=ROOT/name
            if destination.exists() and destination.read_bytes()!=data:
                raise ValueError('Refusing to overwrite edited source: '+name)
        for name in sorted(archive.namelist()):
            if not name.startswith((prefix+'vendor/boost/',prefix+'vendor/eigen/')) or name.endswith('/'):continue
            relative=Path(name[len(prefix):])
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('Invalid vendor source path')
            destination=ROOT/relative
            if ROOT.resolve() not in destination.resolve().parents:raise ValueError('Vendor path leaves repository')
            data=archive.read(name)
            if destination.exists() and destination.read_bytes()!=data:
                raise ValueError('Refusing to overwrite edited source: '+str(relative))
        for name in sorted(archive.namelist()):
            if not name.startswith((prefix+'vendor/boost/',prefix+'vendor/eigen/')) or name.endswith('/'):continue
            destination=ROOT/name[len(prefix):]
            if destination.exists():continue
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(archive.read(name))
    print('PASS: restored frozen vendor sources;',len(selected),'native source hashes match')

if __name__=='__main__':main()
