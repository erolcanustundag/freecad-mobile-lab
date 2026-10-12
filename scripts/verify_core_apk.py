#!/usr/bin/env python3
"""Check actual packaged App/Python bytes and ABI closure, without claiming execution."""
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
NDK=ROOT.parent/'toolchains/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64'
READELF=NDK/'bin/llvm-readelf'
SYSTEM={'libc.so','libm.so','libdl.so','liblog.so','libandroid.so','libz.so',
    'libEGL.so','libGLESv2.so','libGLESv3.so','libjnigraphics.so'}
def symbols(path):
    defined=set();required=set()
    output=subprocess.check_output([str(READELF),'--dyn-syms','--wide',str(path)],text=True)
    for line in output.splitlines():
        c=line.split(maxsplit=7)
        if len(c)==8 and c[0].rstrip(':').isdigit() and c[4] in ('GLOBAL','WEAK'):
            name=c[7].split()[0].split('@')[0]
            if c[6]!='UND':defined.add(name)
            elif c[4]=='GLOBAL':required.add(name)
    return defined,required
def main():
    release=json.loads((ROOT/'release.json').read_text())
    apk=ROOT/'dist'/('FreeCAD-Mobile-Lab-'+release['version']+'-arm64.apk')
    manifest=json.loads((ROOT/'docs/core-apk-inputs.json').read_text())
    with zipfile.ZipFile(apk) as z,tempfile.TemporaryDirectory(prefix='core-apk-static-') as temp:
        raw=z.read('assets/core/python-home.zip')
        assert hashlib.sha256(raw).hexdigest()==manifest['asset_zip_sha256']
        with zipfile.ZipFile(io.BytesIO(raw)) as runtime:
            assert runtime.testzip() is None
            assert set(runtime.namelist())=={i['path'] for i in manifest['python_assets']}
            for item in manifest['python_assets']:
                assert hashlib.sha256(runtime.read(item['path'])).hexdigest()==item['sha256']
            entries=[(name,z.read(name)) for name in z.namelist() if name.startswith('lib/') and name.endswith('.so')]
            entries += [(name,runtime.read(name)) for name in runtime.namelist() if name.endswith('.so')]
        records=[];exports=set();required={};provided=set()
        for index,(name,data) in enumerate(entries):
            path=Path(temp)/str(index);path.write_bytes(data)
            header=subprocess.check_output([str(READELF),'-h',str(path)],text=True)
            segments=subprocess.check_output([str(READELF),'-lW',str(path)],text=True)
            dynamic=subprocess.check_output([str(READELF),'-d',str(path)],text=True)
            assert 'AArch64' in header,name
            alignment=min(int(line.split()[-1],16) for line in segments.splitlines() if line.strip().startswith('LOAD '))
            assert alignment>=16384,(name,alignment)
            sonames=re.findall(r'\(SONAME\).*?\[(.*?)\]',dynamic)
            provided.add(sonames[0] if sonames else Path(name).name)
            needs=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic)
            defined,undefined=symbols(path);exports.update(defined);required[name]=undefined
            records.append({'path':name,'alignment':alignment,'needed':needs})
        for name in SYSTEM:exports.update(symbols(NDK/'sysroot/usr/lib/aarch64-linux-android/26'/name)[0])
        for record in records:
            assert not (set(record['needed'])-provided-SYSTEM),record
        if manifest.get('part'):
            assert manifest['builtin_modules']==['FreeCAD','Materials','Part']
            expected={'libFreeCADPart.so','libFreeCADMaterials.so'}
            assert expected.issubset(provided)
            assert {'PyInit_Part','PyInit_Materials'}.issubset(exports),'Genuine builtin entrypoints are missing'
            bridge=next(x for x in records if x['path']=='lib/arm64-v8a/libfreecad_document_bridge.so')
            assert expected.issubset(set(bridge['needed'])),'Part/Materials must be linked by the bridge'
            assert {'PyInit_Part','PyInit_Materials'}.issubset(required[bridge['path']]),'Builtin registration must reference the real entrypoints'
            assert 'scripts/mobile_part.py' in {x['path'] for x in manifest['python_assets']}
        missing={name:sorted(values-exports) for name,values in required.items() if values-exports}
        assert not missing,missing
        dex=z.read('classes.dex')
        for name in (b'CoreDocumentActivity',b'MobileCoreBootstrap',b'QtNative',b'CoreAssets',b'CoreNative'):
            assert name in dex,name
        assert b'Java_org_freecad_mobilelab_CoreNative_initialize' in z.read('lib/arm64-v8a/libfreecad_document_bridge.so')
        assert b'Java_org_freecad_mobilelab_CoreNative_request' in z.read('lib/arm64-v8a/libfreecad_document_bridge.so')
    report={'version':release['version'],'apk_sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),
        'status':'STATIC_PASS','android_execution':'NOT_RUN','libraries_and_python_extensions':len(records),
        'strong_symbol_closure':True,'native_loader_closure':True,'minimum_alignment':16384,
        'python_asset_files':len(manifest['python_assets']),'original_part_builtin_entrypoints':bool(manifest.get('part')),'libraries':records}
    (ROOT/'docs/core-apk-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(records),'packaged ARM64 libraries/extensions, 16 KiB alignment, API26 strong-symbol/loader closure;',len(manifest['python_assets']),'Python files verified. Android execution NOT_RUN')
if __name__=='__main__':main()
