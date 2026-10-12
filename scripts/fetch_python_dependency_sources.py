#!/usr/bin/env python3
"""Fetch frozen CPython dependency sources and their Android build recipes."""
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest = json.loads((ROOT/'docs/PYTHON-DEPENDENCY-SOURCES.json').read_text())
    cache = ROOT.parent/'toolchains/python-dependency-sources'
    cache.mkdir(parents=True, exist_ok=True)
    for item in manifest['dependencies']:
        for prefix in ('', 'recipe_'):
            name = item[prefix+'archive']
            if Path(name).name != name:
                raise ValueError('Invalid archive name')
            destination = cache/name
            checksum = item[prefix+'sha256']
            def valid(path):
                return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == checksum
            if not valid(destination):
                temp = destination.with_suffix('.partial')
                try:
                    with urllib.request.urlopen(item[prefix+'url'], timeout=60) as src, temp.open('wb') as out:
                        while data := src.read(1024*1024):
                            out.write(data)
                            if out.tell() > 128*1024*1024:
                                raise ValueError('Oversized dependency archive')
                    if not valid(temp):
                        raise ValueError('Dependency archive checksum mismatch: '+name)
                    temp.replace(destination)
                finally:
                    temp.unlink(missing_ok=True)
            with tarfile.open(destination) as archive:
                archive.extractall(ROOT.parent/'upstream/python-dependencies', filter='data')
            print('Verified and extracted', name)

if __name__ == '__main__':
    main()
