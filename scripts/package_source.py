#!/usr/bin/env python3
"""Package the app, pinned dependencies and OCCT rebuild sources, excluding builds."""
from pathlib import Path
import argparse
import os
import json
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--private-checkpoint', action='store_true', help='Include the local development keystore and private continuation for private checkpoint storage only')
args = parser.parse_args()
OCCT = Path(os.environ.get('OCCT_SOURCE', ROOT.parent/'occt-source'))
OUT = ROOT/'dist/FreeCAD-Mobile-Lab-source.zip'
RELEASE = json.loads((ROOT/'release.json').read_text())
record=json.loads((ROOT/'docs/apk-inputs.json').read_text())
assert record['sha256']==__import__('hashlib').sha256((ROOT/'dist'/record['apk']).read_bytes()).hexdigest()
for name,value in record['inputs'].items():assert __import__('hashlib').sha256((ROOT/name).read_bytes()).hexdigest()==value,('Source drift',name)
files = []
for name in ('app','vendor','scripts','docs','samples','.github'):
    files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.rsync-tmp' not in p.parts and p.name!='package-results-'+RELEASE['version']+'.txt')
for p in (ROOT/'tests').iterdir():
    if p.suffix in ('.cpp','.java','.py','.sh'):files.append(p)
for name in ('README.md','LICENSE','build.gradle','settings.gradle','gradle.properties','versions.lock','versions-prebuilt.json','release.json','.gitignore'):
    files.append(ROOT/name)
if args.private_checkpoint:
    files.append(ROOT/'apk-build/development.keystore')
else:
    files=[p for p in files if p.name!='CONTINUE.md' and p.name!='RELEASE-PREPARATION-PRIVATE.json' and p.suffix not in ('.keystore','.jks','.pem','.key')]
occt_files = []
for name in ('src','adm'):
    occt_files.extend(p for p in (OCCT/name).rglob('*') if p.is_file() and '.rsync-tmp' not in p.parts)
occt_files.extend(p for p in OCCT.iterdir() if p.is_file() and '.rsync-tmp' not in p.parts)
assert files and occt_files and all(p.is_file() for p in files)
app_files=set(files)
snapshots={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in set(files+occt_files)}
OUT.parent.mkdir(parents=True,exist_ok=True)
temp = OUT.with_suffix('.tmp.zip')
try:
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(files)):
            z.write(p,Path('FreeCADMobileLab/native-cad')/p.relative_to(ROOT))
        for p in sorted(set(occt_files)):
            z.write(p,Path('FreeCADMobileLab/occt-source')/p.relative_to(OCCT))
    with zipfile.ZipFile(temp) as z:
        assert len(z.namelist())==len(set(z.namelist())), 'Duplicate source entries'
        assert z.testzip() is None, 'Corrupt source archive'
        for path,checksum in snapshots.items():
            base=ROOT if path in app_files else OCCT
            prefix='FreeCADMobileLab/native-cad/' if base==ROOT else 'FreeCADMobileLab/occt-source/'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==checksum,('Source changed during packaging',path)
            assert hashlib.sha256(z.read(prefix+str(path.relative_to(base)))).hexdigest()==checksum,('Archive differs',path)
        prefix='FreeCADMobileLab/native-cad/'
        for name in ('Shaders','CadView','MainActivity','NativeCad','ArchiveIO','ProjectStore','FcstdImporter','Diagnostics','CrashApplication','StartupActivity','MeshFrame','ModelViewport','SoftwareRasterizer','SoftwareCadView','NativeTombstone','ParametricGraph','GraphEditor','SketchCanvas','CommandLine','ReleaseInfo'):
            relative=f'app/src/main/java/org/freecad/mobilelab/{name}.java'
            assert z.read(prefix+relative)==(ROOT/relative).read_bytes(), relative
        for relative in ('app/src/main/cpp/cad.cpp','app/src/main/cpp/AdvancedTools.cpp','app/src/main/cpp/AdvancedTools.hpp','app/src/main/cpp/MeshPreview.cpp','app/src/main/cpp/MeshPreview.hpp','vendor/meshoptimizer/src/simplifier.cpp','vendor/meshoptimizer/LICENSE.md'):
            assert z.read(prefix+relative)==(ROOT/relative).read_bytes(), relative
        with zipfile.ZipFile(ROOT/'dist'/('FreeCAD-Mobile-Lab-'+RELEASE['version']+'-arm64.apk')) as apk:
            for n in apk.namelist():
                if n.startswith('lib/') and n.endswith('.so'):
                    assert z.read(prefix+'app/src/main/jniLibs/'+n[4:])==apk.read(n), n
    os.replace(temp,OUT)
    print(f'PASS: {len(files)+len(occt_files)} source entries, CRC checks, current Java and matching APK libraries')
    print(f'Source bundle: {OUT} ({OUT.stat().st_size/1024/1024:.1f} MiB)')
finally:
    temp.unlink(missing_ok=True)
