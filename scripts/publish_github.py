#!/usr/bin/env python3
"""Publish a reviewed source repository and prerelease assets using authenticated gh.

No credentials are accepted as arguments or written to files. This does not
pretend that local packaging completed Android/device or desktop-parity gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',help='OWNER/freecad-mobile-lab; defaults to the authenticated user')
p.add_argument('--assets',required=True,type=Path)
p.add_argument('--publish',action='store_true',help='Perform the explicitly authorized public upload')
args=p.parse_args()
manifest=json.loads((ROOT/'docs/RELEASE-ASSETS.json').read_text())
assets=[]
for item in manifest['assets']:
    path=args.assets/item['name']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Release asset missing or changed: '+item['name'])
    assets.append(path.resolve())
if not args.publish:
    print('Ready:',manifest['tag'],'public source repository, experimental prerelease,',len(assets),'verified assets')
    raise SystemExit(0)
if not shutil.which('gh'):raise SystemExit('Authenticated GitHub CLI is required')
subprocess.run(['gh','auth','status'],check=True)
user=json.loads(subprocess.check_output(['gh','api','user'],text=True))
repo=args.repo or user['login']+'/freecad-mobile-lab'
if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repo):raise SystemExit('Invalid repository name')
if not (ROOT/'.git').is_dir():
    subprocess.run(['git','init','-b','main'],cwd=ROOT,check=True)
has_head=subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=ROOT,capture_output=True).returncode==0
if not has_head:
    subprocess.run(['git','config','user.name',user.get('name') or user['login']],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email',str(user['id'])+'+'+user['login']+'@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','add','.'],cwd=ROOT,check=True)
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    if any(n.endswith(('.keystore','.jks','.pem','.key')) or n=='docs/CONTINUE.md' for n in tracked if n):raise SystemExit('Private file in the staged repository')
    subprocess.run(['git','commit','-m','Prepare experimental FreeCAD Mobile Lab Android prerelease'],cwd=ROOT,check=True)
elif subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip():
    raise SystemExit('Working tree has uncommitted changes; review and commit before publishing')
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
if any(n.endswith(('.keystore','.jks','.pem','.key')) or n=='docs/CONTINUE.md' for n in tracked if n):raise SystemExit('Private file in the source repository')
# Refuse to merge into an existing repository without a separately reviewed plan.
existing=subprocess.run(['gh','repo','view',repo],capture_output=True)
if existing.returncode==0:raise SystemExit('Repository already exists; inspect it before choosing an update path')
subprocess.run(['gh','repo','create',repo,'--public','--description','Independent experimental native CAD for Android; incomplete FreeCAD desktop parity','--source',str(ROOT),'--remote','origin','--push'],cwd=ROOT,check=True)
subprocess.run(['gh','release','create',manifest['tag'],'--repo',repo,'--target','main','--prerelease','--title',manifest['title'],'--notes-file',str(ROOT/'docs/RELEASE-NOTES.md'),*[str(path) for path in assets]],check=True)
release=json.loads(subprocess.check_output(['gh','api','repos/'+repo+'/releases/tags/'+manifest['tag']],text=True))
if not release['prerelease'] or {a['name'] for a in release['assets']}!={a['name'] for a in manifest['assets']}:raise SystemExit('Remote release verification failed')
remote={a['name']:a for a in release['assets']}
for item in manifest['assets']:
    asset=remote[item['name']]
    if asset['size']!=item['size_bytes'] or asset.get('digest')!='sha256:'+item['sha256']:raise SystemExit('Remote asset size/digest differs: '+item['name'])
print('Published:',release['html_url'])
