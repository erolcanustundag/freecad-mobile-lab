#!/usr/bin/env python3
"""Materialise pinned Ubuntu host-only dependencies without changing the OS.

These amd64 development packages are reference-build inputs, never APK inputs.
The manifest pins snapshot URLs and their repository SHA512 digests.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT.parent/'toolchains/freecad-host-debs')
    parser.add_argument('--prefix', type=Path, default=ROOT.parent/'toolchains/freecad-host-prefix')
    args = parser.parse_args()
    if os.uname().machine != 'x86_64':
        parser.error('This pinned reference prefix is Linux x86_64 only')
    manifest = json.loads((ROOT/'docs/FREECAD-HOST-DEPENDENCIES.json').read_text())
    args.cache.mkdir(parents=True, exist_ok=True)
    args.prefix.mkdir(parents=True, exist_ok=True)

    def valid(path, entry):
        return path.is_file() and path.stat().st_size == entry['size'] and hashlib.sha512(path.read_bytes()).hexdigest() == entry['sha512']

    def fetch(entry):
        path = args.cache/entry['filename']
        if not valid(path, entry):
            temp = path.with_suffix('.partial')
            try:
                with urllib.request.urlopen(entry['url'], timeout=60) as response, temp.open('wb') as output:
                    while True:
                        data = response.read(1024*1024)
                        if not data:
                            break
                        output.write(data)
                        if output.tell() > entry['size']:
                            raise ValueError('Package exceeds pinned size: '+entry['filename'])
                if not valid(temp, entry):
                    raise ValueError('Package checksum mismatch: '+entry['filename'])
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
        return path

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(fetch, manifest['packages']))
    # Extraction is sequential; packages can share paths.
    for path in paths:
        subprocess.run(['dpkg-deb', '-x', str(path), str(args.prefix)], check=True)
    # qt5-qmake-bin contains the binary; qt5-qmake supplies this architecture
    # symlink. Reproduce that link in the isolated prefix without OS installation.
    qmake = args.prefix/'usr/lib/x86_64-linux-gnu/qt5/bin/qmake'
    if not qmake.exists():
        qmake.symlink_to('../../../qt5/bin/qmake')
    print('Verified and extracted', len(paths), 'host-only packages into', args.prefix)

if __name__ == '__main__':
    main()
