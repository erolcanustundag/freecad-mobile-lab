#!/usr/bin/env python3
"""Build a signed native APK using official Android SDK tools, without Maven.

The debug certificate is a public development identity, not a production key.
Build the CAD libraries first; see scripts/build_occt.sh and README.md.
"""
import os
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SDK = Path(os.environ.get('ANDROID_SDK_ROOT', WORKSPACE / 'toolchains/android-sdk'))
JDK = Path(os.environ.get('JAVA_HOME', WORKSPACE / 'toolchains/jdk-17.0.16+8'))
TOOLS = SDK / 'build-tools/35.0.0'
ANDROID_JAR = SDK / 'platforms/android-35/android.jar'
NDK = Path(os.environ.get('ANDROID_NDK_ROOT', WORKSPACE / 'toolchains/android-ndk-r27c'))
BUILD = ROOT / 'apk-build'
OUT = ROOT / 'dist'
RELEASE = json.loads((ROOT/'release.json').read_text())

def run(*args):
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT)

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source_input(path):return path.is_file() and '.rsync-tmp' not in path.parts and '__pycache__' not in path.parts and path.suffix not in ('.pyc','.pyo')
def stage_assets(source,destination):
    shutil.rmtree(destination,ignore_errors=True)
    destination.mkdir(parents=True,exist_ok=True)
    for path in sorted(source.rglob('*')):
        if source_input(path):
            target=destination/path.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
def input_snapshot():
    paths=[ROOT/'release.json',ROOT/'app/src/main/AndroidManifest.xml']
    for folder in ('java','res','assets','jniLibs'):
        paths.extend(p for p in (ROOT/'app/src/main'/folder).rglob('*') if source_input(p))
    paths.extend((ROOT/'app/libs').glob('*.jar'))
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prebuilt',action='store_true',help='Reuse the verified packaged ARM64 libraries without an NDK build');parser.add_argument('--reproduce',action='store_true');parser.add_argument('--production',action='store_true');parser.add_argument('--upstream-core',action='store_true',help='Include the separately verified upstream document runtime');parser.add_argument('--unsigned',action='store_true',help='Produce an aligned APK without creating or accessing a signing key');args=parser.parse_args()
    if args.unsigned and (args.production or args.reproduce):raise SystemExit('Unsigned mode cannot be combined with production or reproduce')
    if args.production and args.reproduce:raise SystemExit('Select production or reproduce, not both')
    if args.upstream_core:
        from check_core_runtime_inputs import check
        check(ROOT)
    key=BUILD/'development.keystore';alias='androiddebugkey';storepass='pass:android';keypass='pass:android'
    if args.production:
        required=('CAD_SIGNING_KEYSTORE','CAD_SIGNING_ALIAS','CAD_STORE_PASSWORD','CAD_KEY_PASSWORD')
        if any(not os.environ.get(n) for n in required):raise SystemExit('Production signing requires external keystore, alias and password environment variables')
        key=Path(os.environ['CAD_SIGNING_KEYSTORE']).resolve();alias=os.environ['CAD_SIGNING_ALIAS']
        if not key.is_file() or ROOT in key.parents or digest(key)==digest(BUILD/'development.keystore'):raise SystemExit('Use a private signing key outside the project')
        def cert(path,a,option,value):return subprocess.check_output([str(JDK/'bin/keytool'),'-exportcert','-keystore',str(path),'-alias',a,option,value],stderr=subprocess.DEVNULL)
        if hashlib.sha256(cert(key,alias,'-storepass:env','CAD_STORE_PASSWORD')).digest()==hashlib.sha256(cert(BUILD/'development.keystore','androiddebugkey','-storepass','android')).digest():raise SystemExit('The public development certificate cannot be used for production')
        storepass='env:CAD_STORE_PASSWORD';keypass='env:CAD_KEY_PASSWORD'

    records_path=ROOT/'docs/CHECKPOINTS.json'
    sealed=records_path.exists() and any(x['version']==RELEASE['version'] for x in json.loads(records_path.read_text()))
    if args.reproduce and not sealed:raise SystemExit('Reproduce requires a recorded checkpoint')
    if sealed and not args.reproduce and not args.production and not args.unsigned:
        raise SystemExit('This APK version is a recorded checkpoint. Select a new version before building.')
    # Keep the signing identity, but never package classes/resources from an old build.
    for name in ('compiled', 'classes', 'gen', 'dex'):
        shutil.rmtree(BUILD/name, ignore_errors=True)
    for path in (BUILD, OUT, BUILD/'compiled', BUILD/'classes', BUILD/'gen', BUILD/'dex'):
        path.mkdir(parents=True, exist_ok=True)
    libs = ROOT / 'app/src/main/jniLibs/arm64-v8a'
    libs.mkdir(parents=True,exist_ok=True)
    if args.prebuilt:
        pinned=json.loads((ROOT/'versions-prebuilt.json').read_text())
        actual={p.name:digest(p) for p in libs.glob('*.so')}
        if {n:actual.get(n) for n in pinned['libraries']}!=pinned['libraries']:raise SystemExit('Prebuilt libraries differ from the retained verified checkpoint')
        extra={n:v for n,v in actual.items() if n not in pinned['libraries']}
        expected=json.loads((ROOT/'docs/core-apk-inputs.json').read_text())['libraries'] if args.upstream_core else {}
        if extra!=expected:raise SystemExit('Upstream core library manifest differs; stage and verify it before packaging')
        for name,value in pinned['native_sources'].items():
            if digest(ROOT/name)!=value:raise SystemExit('Native source changed: rebuild with the NDK instead of --prebuilt')
    else:
        strip = NDK / 'toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip'
        for source in sorted((ROOT/'vendor/occt/arm64-v8a/lib').glob('*.so')):
            shutil.copy2(source, libs/source.name)
        for name in ('cad_mobile','freecad_sketcher'):
            shutil.copy2(ROOT/'sketcher-build'/f'lib{name}.so', libs/f'lib{name}.so')
        shutil.copy2(NDK/'toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/libc++_shared.so', libs/'libc++_shared.so')
        for lib in libs.glob('*.so'):
            run(strip, '--strip-unneeded', lib)
    frozen=input_snapshot()
    stage_assets(ROOT/'app/src/main/assets',BUILD/'assets')
    if args.reproduce or args.production and sealed:
        record=json.loads((ROOT/'docs/apk-inputs.json').read_text())
        if frozen!=record['inputs']:raise SystemExit('Recorded checkpoint inputs changed; select a new version')
    run(TOOLS/'aapt2','compile','--dir',ROOT/'app/src/main/res','-o',BUILD/'compiled')
    flats=sorted((BUILD/'compiled').glob('*.flat'))
    ET.register_namespace('android','http://schemas.android.com/apk/res/android')
    manifest=ET.parse(ROOT/'app/src/main/AndroidManifest.xml')
    manifest.getroot().set('package','org.freecad.mobilelab')
    manifest.write(BUILD/'AndroidManifest.xml',encoding='utf-8',xml_declaration=True)
    command=[TOOLS/'aapt2','link','-I',ANDROID_JAR,'--manifest',BUILD/'AndroidManifest.xml',
             '--min-sdk-version','26','--target-sdk-version','35','--version-code',str(RELEASE['version_code']),
             '--version-name',RELEASE['version_name'],'--java',BUILD/'gen',
             '-A',BUILD/'assets','-o',BUILD/'resources.apk']
    # Release packaging and signing identity are separate decisions. Retain the
    # prototype certificate for upgrades without exposing a debuggable release.
    debuggable=not (args.production or args.unsigned) and RELEASE.get('channel','candidate')!='release'
    if debuggable:command.append('--debug-mode')
    command.extend(flats)
    run(*command)
    sources=[p for p in sorted((ROOT/'app/src/main/java').rglob('*.java'))+sorted((BUILD/'gen').rglob('*.java')) if '.rsync-tmp' not in p.parts]
    # Android 8 has Java 8 core APIs; --release avoids accidental JDK 17 calls
    # (for example the newer covariant FloatBuffer.position return type).
    java_jars=sorted((ROOT/'app/libs').glob('*.jar'))
    run(JDK/'bin/javac','--release','8','-classpath',os.pathsep.join(str(p) for p in [ANDROID_JAR,*java_jars]),'-d',BUILD/'classes',*sources)
    classes=[p for p in sorted((BUILD/'classes').rglob('*.class')) if '.rsync-tmp' not in p.parts]
    run(JDK/'bin/java','-cp',TOOLS/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',ANDROID_JAR,'--output',BUILD/'dex',*classes,*java_jars)
    unsigned=BUILD/'unsigned.apk'
    shutil.copy2(BUILD/'resources.apk',unsigned)
    with zipfile.ZipFile(unsigned,'a',compression=zipfile.ZIP_DEFLATED) as apk:
        apk.write(BUILD/'dex/classes.dex','classes.dex')
        for lib in sorted(libs.glob('*.so')):
            apk.write(lib,f'lib/arm64-v8a/{lib.name}',compress_type=zipfile.ZIP_STORED)
    aligned=BUILD/'aligned.apk'
    run(TOOLS/'zipalign','-P','16','-f','4',unsigned,aligned)
    if args.unsigned:
        if input_snapshot()!=frozen:raise SystemExit('Build inputs changed while packaging')
        apk=OUT/('FreeCAD-Mobile-Lab-'+RELEASE['version']+'-unsigned-arm64.apk')
        shutil.copy2(aligned,apk)
        run(TOOLS/'zipalign','-c','-P','16','4',apk)
        print(f'Unsigned APK: {apk}')
        return
    if not key.exists():
        run(JDK/'bin/keytool','-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','androiddebugkey','-dname','CN=FreeCAD Mobile Lab Development,O=Independent Prototype,C=TR','-keyalg','RSA','-keysize','2048','-validity','10000')
    if input_snapshot()!=frozen:raise SystemExit('Build inputs changed while packaging')
    suffix='-production' if args.production else '-reproduced' if args.reproduce else ''
    apk=OUT/('FreeCAD-Mobile-Lab-'+RELEASE['version']+suffix+'-arm64.apk')
    run(JDK/'bin/java','-jar',TOOLS/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias',alias,'--ks-pass',storepass,'--key-pass',keypass,'--out',apk,aligned)
    run(JDK/'bin/java','-jar',TOOLS/'lib/apksigner.jar','verify','--verbose',apk)
    run(TOOLS/'zipalign','-c','-P','16','4',apk)
    record=ROOT/'docs'/('apk-inputs'+suffix+'.json');record.write_text(json.dumps({'version_name':RELEASE['version_name'],'apk':apk.name,'sha256':digest(apk),'inputs':frozen,'native_build':'verified 0.9 prebuilts' if args.prebuilt else 'NDK rebuild','signing':'private production key' if args.production else 'retained development certificate','debuggable':debuggable},indent=2)+'\n')
    print(f'APK: {apk} ({apk.stat().st_size/1024/1024:.1f} MiB)')

if __name__ == '__main__':
    main()
