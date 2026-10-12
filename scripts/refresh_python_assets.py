#!/usr/bin/env python3
"""Refresh mobile Python modules without rebuilding the pinned native runtime."""
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
manifest_path=ROOT/'docs/core-apk-inputs.json'
manifest=json.loads(manifest_path.read_text())
assets=ROOT/'app/src/main/assets/core';path=assets/'python-home.zip'
expected={item['path']:item for item in manifest['python_assets']}
files={}
with zipfile.ZipFile(path) as archive:
    if archive.testzip() is not None:raise ValueError('Corrupt original runtime')
    if set(archive.namelist())!=set(expected):raise ValueError('Unexpected runtime entries')
    for name in archive.namelist():
        data=archive.read(name)
        if hashlib.sha256(data).hexdigest()!=expected[name]['sha256']:raise ValueError('Original runtime hash mismatch: '+name)
        if not name.startswith('scripts/mobile_'):files[name]=data
for source in assets.glob('mobile_*.py'):files['scripts/'+source.name]=source.read_bytes()
temporary=path.with_suffix('.tmp.zip')
try:
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,data in sorted(files.items()):archive.writestr(name,data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:raise ValueError('Refreshed runtime CRC mismatch')
    temporary.replace(path)
finally:temporary.unlink(missing_ok=True)
manifest['asset_zip_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
manifest['python_assets']=[{'path':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in sorted(files.items())]
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print('Refreshed embedded mobile modules; native libraries unchanged')
