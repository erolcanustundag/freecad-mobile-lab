#!/usr/bin/env python3
"""Extract official pinned Qt host tools and Android libraries for core builds.

Requires py7zr. Host binaries stay separate from Android APK inputs.
"""
from pathlib import Path
import argparse
import concurrent.futures
import hashlib
import json
import urllib.request
import py7zr

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache', type=Path, default=ROOT.parent/'toolchains/qt-archives')
    p.add_argument('--output', type=Path, default=ROOT.parent/'toolchains/qt')
    args = p.parse_args()
    manifest_path = ROOT/'docs/FREECAD-ANDROID-TOOLCHAINS.json'
    manifest = json.loads(manifest_path.read_text())
    args.cache.mkdir(parents=True,exist_ok=True)
    args.output.mkdir(parents=True,exist_ok=True)
    def fetch(entry):
        path = args.cache/(entry['platform']+'-'+entry['name'])
        def valid(file):
            return file.is_file() and hashlib.sha1(file.read_bytes()).hexdigest()==entry['sha1']
        if not valid(path):
            temp = path.with_suffix('.partial')
            try:
                with urllib.request.urlopen(entry['url'],timeout=60) as response,temp.open('wb') as stream:
                    while data:=response.read(1024*1024):
                        stream.write(data)
                        if stream.tell()>256*1024*1024:
                            raise ValueError('Qt archive exceeds 256 MiB')
                if not valid(temp):
                    raise ValueError('Qt archive checksum mismatch: '+entry['name'])
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
        return entry,path
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        fetched=list(pool.map(fetch,manifest['qt_6_8_3']))
    for entry,path in fetched:
        destination=args.output/entry['platform']
        if entry['name'].startswith('icu-'):
            destination=destination/'lib'
        destination.mkdir(parents=True,exist_ok=True)
        with py7zr.SevenZipFile(path,'r') as archive:
            for name in archive.getnames():
                if Path(name).is_absolute() or '..' in Path(name).parts:
                    raise ValueError('Invalid Qt archive path')
            archive.extractall(destination)
        entry.update(status='HASH_VERIFIED_EXTRACTED',size=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        print('Extracted',entry['platform'],entry['name'],flush=True)
    # Some Qt IFW tool archives omit executable permission bits. Restore them
    # only for trusted host ELF binaries and scripts, never Android binaries.
    for directory in ('bin','libexec'):
        for file in (args.output/'linux-x86_64'/directory).glob('*'):
            if file.is_file() and not file.is_symlink():
                with file.open('rb') as stream:magic=stream.read(4)
                if magic==b'\x7fELF' or magic.startswith(b'#!'):
                    file.chmod(file.stat().st_mode|0o111)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Qt dependencies at',args.output)

if __name__=='__main__':
    main()
