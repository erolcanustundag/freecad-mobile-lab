#!/usr/bin/env python3
"""Reject stale embedded Python and changed core binaries before APK packaging."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def digest(data):return hashlib.sha256(data).hexdigest()
def check(root=ROOT):
    manifest=json.loads((root/'docs/core-apk-inputs.json').read_text())
    assets=root/'app/src/main/assets/core'
    if manifest.get('sketcher'):
        if not manifest.get('part') or manifest.get('builtin_modules')!=['FreeCAD','Materials','Part','Sketcher'] or 'libFreeCADOriginalSketcher.so' not in manifest['libraries']:
            raise ValueError('Original Sketcher runtime registration/library is incomplete')
    data=(assets/'python-home.zip').read_bytes()
    if digest(data)!=manifest['asset_zip_sha256']:raise ValueError('Embedded Python archive changed; refresh the runtime manifest')
    entries={item['path']:item for item in manifest['python_assets']}
    with zipfile.ZipFile(assets/'python-home.zip') as archive:
        if archive.testzip() is not None or set(archive.namelist())!=set(entries):raise ValueError('Embedded Python archive entries differ')
        for name,item in entries.items():
            if digest(archive.read(name))!=item['sha256']:raise ValueError('Embedded Python file differs: '+name)
        local={p.name for p in assets.glob('mobile_*.py')}
        embedded={Path(n).name for n in entries if n.startswith('scripts/mobile_') and n.endswith('.py')}
        if local!=embedded:raise ValueError('Embedded mobile module list is stale; run refresh_python_assets.py')
        for name in sorted(local):
            if (assets/name).read_bytes()!=archive.read('scripts/'+name):
                raise ValueError('Embedded mobile module is stale: '+name+'; run refresh_python_assets.py')
        if manifest.get('part'):
            base='scripts/resources/Mod/Material/Resources/'
            required={base+name for name in ('Materials/Standard/Default.FCMat','Materials/Appearance/Default.FCMat','Models/Rendering/BasicRendering.yml','Models/Mechanical/Density.yml')}
            if not required.issubset(entries):raise ValueError('Bundled Part material resources are missing; restage the complete Part runtime')
            resources={str(p.relative_to(assets)) for p in (assets/'resources').rglob('*') if p.is_file()}
            packaged={n[len('scripts/'):] for n in entries if n.startswith('scripts/resources/')}
            if resources!=packaged:raise ValueError('Bundled Part material resource list is stale')
            for name in resources:
                if (assets/name).read_bytes()!=archive.read('scripts/'+name):raise ValueError('Bundled Part material resource differs: '+name)
    if digest((root/'app/libs/Qt6Android.jar').read_bytes())!=manifest['java_jar_sha256']:
        raise ValueError('Qt Java archive differs from the pinned runtime')
    for name,value in manifest['libraries'].items():
        if digest((root/'app/src/main/jniLibs/arm64-v8a'/name).read_bytes())!=value:
            raise ValueError('Upstream core library changed: '+name)
    return len(entries)
if __name__=='__main__':print('PASS:',check(),'embedded Python files and all core/JAR inputs match the source manifest')
