#!/usr/bin/env python3
"""Check the packaged APK, native dependency closure and 16 KiB ELF alignment."""
import argparse
import shutil
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('ANDROID_SDK_ROOT', ROOT.parent/'toolchains/android-sdk'))
NDK = Path(os.environ.get('ANDROID_NDK_ROOT', ROOT.parent/'toolchains/android-ndk-r27c'))
JDK = Path(os.environ.get('JAVA_HOME', ROOT.parent/'toolchains/jdk-17.0.16+8'))
RELEASE = json.loads((ROOT/'release.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--reproduce',action='store_true');args=parser.parse_args()
suffix='-reproduced' if args.reproduce else ''
APK = ROOT/'dist'/('FreeCAD-Mobile-Lab-'+RELEASE['version']+suffix+'-arm64.apk')
TOOLS = SDK/'build-tools/35.0.0'
READELF = NDK/'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-readelf'
if not READELF.exists():READELF=Path(shutil.which('readelf') or '/missing-readelf')
record=ROOT/'docs'/('apk-inputs'+suffix+'.json')
if record.exists():
    r=json.loads(record.read_text());assert r['sha256']==hashlib.sha256(APK.read_bytes()).hexdigest(),'APK bytes differ from input record'
    for name,value in r['inputs'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,('Input drift',name)
ANDROID_LIBS = {'libc.so','libm.so','libdl.so','liblog.so','libandroid.so',
                'libEGL.so','libGLESv2.so','libGLESv3.so','libjnigraphics.so','libz.so'}

def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True)

badging = run(TOOLS/'aapt2','dump','badging',APK)
assert f"versionCode='{RELEASE['version_code']}'" in badging and f"versionName='{RELEASE['version_name']}'" in badging
assert "minSdkVersion:'26'" in badging and "targetSdkVersion:'35'" in badging
assert "native-code: 'arm64-v8a'" in badging
tree = run(TOOLS/'aapt2','dump','xmltree',APK,'--file','AndroidManifest.xml')
if RELEASE.get('channel')=='release':
    assert not re.search(r'debuggable\([^)]*\)=true',tree), 'Public release must not be debuggable'
assert 'StartupActivity' in tree and ':cad' in tree and 'CrashApplication' in tree
assert re.search(r'extractNativeLibs\([^)]*\)=true',tree), 'Native extraction must be enabled'
assert re.search(r'hardwareAccelerated\([^)]*\)=false',tree), 'Recovery UI must not require hardware acceleration'
assert re.search(r'required\([^)]*\)=false',tree), 'GLES must be optional'
assert 'uses-permission:' not in badging
signatures = run(JDK/'bin/java','-jar',TOOLS/'lib/apksigner.jar','verify','--verbose','--print-certs',APK)
assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in signatures
assert 'Verified using v3 scheme (APK Signature Scheme v3): true' in signatures
certificate = subprocess.check_output([str(JDK/'bin/keytool'),'-exportcert','-keystore',str(ROOT/'apk-build/development.keystore'),'-storepass','android','-alias','androiddebugkey'])
assert hashlib.sha256(certificate).hexdigest() in signatures, 'APK signing identity differs from the retained development key'
run(TOOLS/'zipalign','-c','-P','16','4',APK)
with zipfile.ZipFile(APK) as z, tempfile.TemporaryDirectory(prefix='cad-apk-check-') as tmp:
    assert z.testzip() is None
    assert not any('__pycache__' in Path(n).parts or n.endswith(('.pyc','.pyo')) for n in z.namelist()), 'Generated Python caches must not be packaged'
    names = [n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')]
    core='CoreDocumentActivity' in tree
    core_inputs=json.loads((ROOT/'docs/core-apk-inputs.json').read_text()) if core else None
    assert len(names)==31+(len(core_inputs['libraries']) if core else 0), names
    packaged = {Path(n).name for n in names}
    for name in names:
        data = z.read(name)
        if core and Path(name).name in core_inputs['libraries']:
            assert hashlib.sha256(data).hexdigest()==core_inputs['libraries'][Path(name).name],name
        if Path(name).name=='libcad_mobile.so':
            assert b'STL exceeds 2,000,000 triangles' in data, 'Old STL limit packaged'
            for method in re.findall(r'static native [\w\[\]]+ (\w+)\(', (ROOT/'app/src/main/java/org/freecad/mobilelab/NativeCad.java').read_text()):
                assert ('Java_org_freecad_mobilelab_NativeCad_'+method).encode() in data, method
        assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==183, name
        path = Path(tmp)/Path(name).name; path.write_bytes(data)
        elf = run(READELF,'-l','-d','--wide',path)
        loads = [line.split() for line in elf.splitlines() if line.strip().startswith('LOAD ')]
        assert loads and all(int(line[-1],16)>=16384 for line in loads), name
        needed = set(re.findall(r'Shared library: \[([^]]+)\]',elf))
        assert not (needed-packaged-ANDROID_LIBS), (name,needed-packaged-ANDROID_LIBS)
    dex = z.read('classes.dex')
    assert b'CommandLine' in dex and b'zoomextents' in dex.lower(), 'Command input missing'
    assert b'uniform bool unlit' in dex and b'uniform bool flat' not in dex, 'Wrong fragment shader packaged'

print(f"PASS: version {RELEASE['version_name']} / code {RELEASE['version_code']}, ARM64, API 26–35, recovery launcher and separate CAD process, no network permission")
print('PASS: APK v2/v3 signatures, retained development signing identity and 16 KiB ZIP alignment')
print('PASS:',len(names),'native ARM64 libraries, dependency closure and 16 KiB ELF LOAD alignment')
print('PASS: corrected fragment shader is present in the APK DEX')
print('PASS: larger STL import limit and native transforms/freeform/analysis/curve-rendering JNI methods are packaged')
print('APK SHA256:',hashlib.sha256(APK.read_bytes()).hexdigest())

