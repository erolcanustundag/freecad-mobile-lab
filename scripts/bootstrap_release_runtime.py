#!/usr/bin/env python3
"""Restore only checksum-pinned runtime assets from a matching GitHub release."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path);args=p.parse_args()
release=json.loads((ROOT/'docs/RELEASE-ASSETS.json').read_text())
entry=next(x for x in release['assets'] if x['kind']=='native-runtime')
bundle=args.bundle.resolve()
if hashlib.sha256(bundle.read_bytes()).hexdigest()!=entry['sha256']:raise SystemExit('Runtime archive hash differs from the release lock')
expected={x['path']:x for x in entry['files']}
with zipfile.ZipFile(bundle) as archive:
    if archive.testzip() is not None or set(archive.namelist())!=set(expected):raise SystemExit('Invalid runtime archive entries')
    staged=[]
    for name,item in expected.items():
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:raise SystemExit('Invalid runtime path')
        destination=ROOT/relative
        if ROOT.resolve() not in destination.resolve().parents:raise SystemExit('Runtime path leaves the repository')
        data=archive.read(name)
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise SystemExit('Runtime file hash differs: '+name)
        if destination.exists() and destination.read_bytes()!=data:raise SystemExit('Refusing to overwrite modified runtime file: '+name)
        staged.append((destination,data))
    for destination,data in staged:
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
print('Restored',len(staged),'pinned runtime files; signing keys are not supplied')
