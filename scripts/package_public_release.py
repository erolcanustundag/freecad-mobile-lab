#!/usr/bin/env python3
"""Package a candidate's public assets without keys, private notes or build trees.

The application ZIP and corresponding-source ZIP are separate: the former
contains repository sources; the latter supplies the frozen upstream archives
and OCCT tree. Native binaries are an independently pinned release asset.
"""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent

def digest(path):
    with path.open('rb') as src:
        value = hashlib.file_digest(src, 'sha256').hexdigest()
    return value

def write_zip(path, entries):
    temporary = path.with_suffix('.tmp.zip')
    checksums = {}
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for source, name, stored in entries:
                if name in checksums or Path(name).is_absolute() or '..' in Path(name).parts:
                    raise ValueError('Invalid or duplicate archive path: '+name)
                checksums[name] = digest(source)
                archive.write(source, name, compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('Archive CRC failure')
            for source, name, _ in entries:
                if digest(source) != checksums[name] or hashlib.sha256(archive.read(name)).hexdigest() != checksums[name]:
                    raise ValueError('Source changed while packaging: '+name)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    print('Verified', path.name, len(entries), 'files,', path.stat().st_size, 'bytes', flush=True)
    return checksums

def package_repository(out, version, published_apk, runtime_path, upstream):
    if not (ROOT/'.git').is_dir():
        subprocess.run(['git','init','-b','main'], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    names = subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'], cwd=ROOT).decode().split('\0')
    # Header dependencies are omitted from Git but included in the full source
    # asset used by bootstrap_vendor_sources.py.
    names += [str(p.relative_to(ROOT)) for dependency in ('boost','eigen')
              for p in (ROOT/'vendor'/dependency).rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and '.rsync-tmp' not in p.parts]
    files = []
    for name in sorted(set(names)-{''}):
        source = ROOT/name
        if not source.is_file():
            continue
        if source.suffix in ('.keystore','.jks','.pem','.key') or name in ('docs/CONTINUE.md','docs/RELEASE-PREPARATION-PRIVATE.json'):
            raise ValueError('Private path in source selection: '+name)
        if source.stat().st_size > 95*1024*1024:
            raise ValueError('Source path exceeds GitHub file limit: '+name)
        files.append((source, 'FreeCADMobileLab/native-cad/'+name, False))
    public_source = out/f'FreeCAD-Mobile-Lab-{version}-public-source.zip'
    write_zip(public_source, files)
    sums = '\n'.join(digest(path)+'  '+path.name for path in [published_apk, runtime_path, upstream, public_source])+'\n'
    (out/'SHA256SUMS').write_text(sums)
    manifest=json.loads((ROOT/'docs/RELEASE-ASSETS.json').read_text())
    manifest['assets']=[item for item in manifest['assets'] if item['kind']!='application-source']
    manifest['assets'].append(dict(name=public_source.name,kind='application-source',size_bytes=public_source.stat().st_size,sha256=digest(public_source)))
    # Write this after sealing the source ZIP to avoid a self-referential hash.
    (ROOT/'docs/RELEASE-ASSETS.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Public source excludes keys/private continuation. Publication remains PENDING.', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-only', action='store_true', help='Refresh repository sources after verifying the existing locked release assets')
    args = parser.parse_args()
    release = json.loads((ROOT/'release.json').read_text())
    version = release['version']
    inputs = json.loads((ROOT/'docs/apk-inputs.json').read_text())
    apk = ROOT/'dist'/inputs['apk']
    if digest(apk) != inputs['sha256']:
        raise ValueError('APK differs from recorded build')
    for name, checksum in inputs['inputs'].items():
        if digest(ROOT/name) != checksum:
            raise ValueError('Sealed input differs: '+name)
    subprocess.run(['python3', str(ROOT/'scripts/check_core_runtime_inputs.py')], check=True)
    out = ROOT/'dist/public-release';out.mkdir(parents=True, exist_ok=True)
    # A hard link is safe here: packaging does not mutate the sealed APK.
    published_apk = out/apk.name
    if published_apk.exists():
        if digest(published_apk) != digest(apk):
            raise ValueError('Existing public APK differs')
    else:
        published_apk.hardlink_to(apk)
    if args.source_only:
        manifest = json.loads((ROOT/'docs/RELEASE-ASSETS.json').read_text())
        if manifest['version'] != version:
            raise ValueError('Release lock version differs')
        for item in manifest['assets']:
            path = out/item['name']
            if path.stat().st_size != item['size_bytes'] or digest(path) != item['sha256']:
                raise ValueError('Existing release asset differs: '+item['name'])
        runtime_path = out/next(x['name'] for x in manifest['assets'] if x['kind']=='native-runtime')
        upstream = out/next(x['name'] for x in manifest['assets'] if x['kind']=='corresponding-source')
        manifest['assets']=[item for item in manifest['assets'] if item['kind']!='application-source']
        (ROOT/'docs/RELEASE-ASSETS.json').write_text(json.dumps(manifest,indent=2)+'\n')
        package_repository(out, version, published_apk, runtime_path, upstream)
        return
    runtime = sorted((ROOT/'app/src/main/jniLibs/arm64-v8a').glob('*.so'))
    runtime += [ROOT/'app/libs/Qt6Android.jar', ROOT/'app/src/main/assets/core/python-home.zip']
    runtime_path = out/f'FreeCAD-Mobile-Lab-{version}-native-runtime.zip'
    runtime_hashes = write_zip(runtime_path, [(p, str(p.relative_to(ROOT)), False) for p in runtime])
    assets = [dict(name=published_apk.name, kind='apk', size_bytes=published_apk.stat().st_size, sha256=digest(published_apk)),
              dict(name=runtime_path.name, kind='native-runtime', size_bytes=runtime_path.stat().st_size, sha256=digest(runtime_path),
                   files=[dict(path=str(p.relative_to(ROOT)), size_bytes=p.stat().st_size, sha256=runtime_hashes[str(p.relative_to(ROOT))]) for p in runtime])]
    toolchains = json.loads((ROOT/'docs/FREECAD-ANDROID-TOOLCHAINS.json').read_text())
    specs = [(toolchains[k], name) for k, name in (
        ('freecad_source','FreeCAD-1.1.4.tar.gz'), ('cpython_source','cpython-v3.13.16.tar.gz'),
        ('qtbase_source','qtbase-everywhere-src-6.8.3.tar.xz'), ('boost','boost_1_87_0.tar.bz2'),
        ('icu','icu4c-74_2-src.tgz'), ('xerces','xerces-c-3.2.5.tar.gz'))]
    specs += [(item, item['archive']) for item in toolchains['cmake_dependencies']]
    entries = []
    for item, name in specs:
        source = BASE/'toolchains'/name
        algorithm = 'sha256' if 'sha256' in item else 'sha512'
        if hashlib.new(algorithm, source.read_bytes()).hexdigest() != item[algorithm]:
            raise ValueError('Upstream archive checksum differs: '+name)
        entries.append((source, 'FreeCADMobileLab/toolchains/'+name, True))
    dependencies = json.loads((ROOT/'docs/PYTHON-DEPENDENCY-SOURCES.json').read_text())['dependencies']
    for item in dependencies:
        for prefix in ('','recipe_'):
            name = item[prefix+'archive'];source = BASE/'toolchains/python-dependency-sources'/name
            if digest(source) != item[prefix+'sha256']:
                raise ValueError('Python dependency source differs: '+name)
            entries.append((source, 'FreeCADMobileLab/toolchains/python-dependency-sources/'+name, True))
    occt = BASE/'occt-source'
    sources = [p for part in ('src','adm') for p in (occt/part).rglob('*') if p.is_file()]
    sources += [p for p in occt.iterdir() if p.is_file()]
    if not sources:
        raise ValueError('OCCT corresponding source is missing')
    entries += [(p, 'FreeCADMobileLab/occt-source/'+str(p.relative_to(occt)), False) for p in sorted(set(sources))]
    upstream = out/f'FreeCAD-Mobile-Lab-{version}-corresponding-sources.zip'
    write_zip(upstream, entries)
    assets.append(dict(name=upstream.name, kind='corresponding-source', size_bytes=upstream.stat().st_size, sha256=digest(upstream)))
    manifest = dict(version=version, tag='v'+version, title='FreeCAD Mobile Lab '+version+' · experimental Android candidate',
                    milestone_gate='NOT_COMPLETE', android_runtime='NOT_RUN', publication='PENDING', assets=assets)
    (ROOT/'docs/RELEASE-ASSETS.json').write_text(json.dumps(manifest, indent=2)+'\n')
    package_repository(out, version, published_apk, runtime_path, upstream)

if __name__ == '__main__':
    main()
