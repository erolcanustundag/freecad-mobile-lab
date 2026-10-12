#!/usr/bin/env python3
"""Check publicly documented version, roadmap and release boundaries."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/'release.json').read_text())
readme=(ROOT/'README.md').read_text()
if release['version'] not in readme:raise ValueError('README version differs from release.json')
if 'experimental' not in readme.lower() or 'NOT COMPLETE' not in readme:raise ValueError('Missing honest prerelease status')
ledger=json.loads((ROOT/'docs/FREECAD-PARITY-BATCHES.json').read_text())
if ledger['stable_1_0']!='NOT_COMPLETE':raise ValueError('Stable 1.0 gate has not been verified')
if any('PENDING' not in f['status'] for b in ledger['batches'][4:] for f in b['features']):raise ValueError('Unverified workbench scope was marked complete')
print('PASS: public version and unfinished parity/release gates agree')
