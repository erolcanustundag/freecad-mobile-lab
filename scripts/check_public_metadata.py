#!/usr/bin/env python3
"""Check publicly documented version, roadmap and release boundaries."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/'release.json').read_text())
readme=(ROOT/'README.md').read_text()
if release['version'] not in readme:raise ValueError('README version differs from release.json')
if 'NOT COMPLETE' not in readme:raise ValueError('Missing unfinished desktop-parity status')
ledger=json.loads((ROOT/'docs/FREECAD-PARITY-BATCHES.json').read_text())
if ledger['stable_1_0']!='NOT_COMPLETE':raise ValueError('The original full-parity milestone has not been verified')
if any('PENDING' not in f['status'] for b in ledger['batches'][4:] for f in b['features']):raise ValueError('Unverified workbench scope was marked complete')
if release.get('channel')=='release':
    if release.get('scope')!='current mobile feature set':raise ValueError('Public release must declare its bounded scope')
    if 'USER_REPORTED_STARTUP'!=json.loads((ROOT/'docs/device-results.json').read_text())['android_runtime']:raise ValueError('Phone evidence scope differs')
    if 'broader device qualification pending' not in release['status']:raise ValueError('Unverified device coverage must remain explicit')
    if 'current mobile feature set' not in readme:raise ValueError('README must distinguish the product release from desktop parity')
print('PASS: release scope, phone evidence and unfinished desktop parity agree')
