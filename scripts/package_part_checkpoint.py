#!/usr/bin/env python3
"""Preserve costly verified Part/reference binaries and complete OCCT headers.
Restore the existing core dependency prefixes separately; no signing key is included.
"""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--platform',choices=('host','android','all'),default='all');parser.add_argument('--sketcher',action='store_true');args=parser.parse_args()
for platform in (('host','android') if args.platform=='all' else (args.platform,)):
    files=[]
    prefix=BASE/'toolchains'/('occt-part-'+platform)
    files += [p for p in (prefix/'include').rglob('*') if p.is_file()]
    files += [prefix/'lib'/('lib'+name+'.so') for name in ('TKFeat','TKExpress','TKBin','TKBinL','TKMeshVS','TKRWMesh','TKDEGLTF')]
    core=BASE/('freecad-part-'+platform)
    files += [p for p in (core/'lib').glob('*.so') if p.is_file()]
    files += [core/'Mod/Part/Part.so',core/'Mod/Material/Materials.so']
    if args.sketcher:files.append(core/'Mod/Sketcher/Sketcher.so')
    files += [p for p in (core/'src').rglob('*') if p.is_file() and p.suffix in ('.h','.hpp','.hxx')]
    for name in ('core-apk-inputs.json','core-apk-verification.json','native-part-results.json'):
        if (ROOT/'docs'/name).is_file():files.append(ROOT/'docs'/name)
    if any(not p.is_file() for p in files):raise ValueError('Complete the original '+platform+' Part build first')
    out=ROOT/'dist'/('FreeCAD-Mobile-Lab-'+('sketcher' if args.sketcher else 'part')+'-build-'+platform+'.zip');out.parent.mkdir(exist_ok=True);temporary=out.with_suffix('.tmp.zip');records=[]
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for path in sorted(set(files)):
            name='FreeCADMobileLab/'+str(path.relative_to(BASE));data=path.read_bytes();info=zipfile.ZipInfo(name);info.create_system=3;info.external_attr=(0o100000|(path.stat().st_mode&0o777))<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data);records.append(dict(path=name,size=len(data),sha256=hashlib.sha256(data).hexdigest()))
        z.writestr('PART-CHECKPOINT.json',json.dumps(dict(platform=platform,scope='Genuine original Part build dependencies/output, not an Android installer',android_execution='NOT_RUN',files=records),indent=2))
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        for item in records:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
    temporary.replace(out);print(out.name,out.stat().st_size,hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
