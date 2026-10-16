#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Prepare verified public release transports locally; no network or ref mutation."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def prepare(source_commit,output):
    if not re.fullmatch('[0-9a-f]{40}',source_commit):raise ValueError('Use the exact sealed source commit')
    release=json.loads((ROOT/'release.json').read_text());version=release['version'];lock=json.loads((ROOT/'docs/RELEASE-ASSETS.json').read_text())
    if lock['version']!=version or lock['prerelease'] or len(lock['assets'])!=4:raise ValueError('Expected four matching full-release assets')
    sealed=json.loads((ROOT/'docs/apk-inputs.json').read_text())
    for name,expected in sealed['inputs'].items():
        if digest(ROOT/name)!=expected:raise ValueError('Sealed application input drift: '+name)
    output.mkdir(parents=True,exist_ok=True);parts=output/'parts';parts.mkdir(exist_ok=True)
    old=json.loads((ROOT/'docs/GITHUB-PUBLICATION.json').read_text());assets=[];blobs={}
    for index,item in enumerate(lock['assets']):
        path=ROOT/'dist/public-release'/item['name']
        if path.stat().st_size!=item['size_bytes'] or digest(path)!=item['sha256']:raise ValueError('Public asset bytes differ: '+item['name'])
        asset={key:item[key] for key in ('name','size_bytes','sha256')}
        if item['kind']=='corresponding-source':
            previous=next(a for a in old['assets'] if a['name'].endswith('-corresponding-sources.zip'))
            if previous['digest']!='sha256:'+item['sha256'] or previous['size']!=item['size_bytes']:raise ValueError('Frozen source reuse differs')
            asset['reuse_url']=previous['browser_download_url']
        else:
            packed=path
            if item['kind']=='apk':
                packed=output/'apk-transport.zip'
                info=zipfile.ZipInfo(path.name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                with zipfile.ZipFile(packed,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:z.writestr(info,path.read_bytes())
                asset['apk_zip']=True
            names=[]
            with packed.open('rb') as stream:
                part=0
                while data:=stream.read(1024*1024):
                    name=f'parts/{index:02d}-{part:03d}.bin';(output/name).write_bytes(data);names.append(name)
                    blobs[name]=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();part+=1
            asset.update(parts=names,transport_size=packed.stat().st_size,transport_sha256=digest(packed))
        assets.append(asset)
    if len(blobs)>200:raise ValueError('Transport exceeds the validated publisher budget')
    plan=dict(repo='erolcanustundag/freecad-mobile-lab',tag='v'+version,branch='release-upload-'+version.replace('.','-'),source_commit=source_commit,body=(ROOT/'docs/RELEASE-NOTES.md').read_text(),assets=assets,part_blobs=blobs)
    (output/'manifest.json').write_text(json.dumps(plan,indent=2)+'\n')
    publisher=(ROOT/'scripts/release_publisher.py').read_text();match=re.search(r"plan\['tag'\]=='v([0-9.]+)'",publisher)
    if not match:raise ValueError('Cannot identify publisher version assertions')
    old_version=match[1]
    (output/'publish.py').write_text(publisher.replace('release-upload-'+old_version.replace('.','-'),plan['branch']).replace(old_version,version))
    template=(ROOT/'docs/ci/publish-full-release.template.yml').read_text()
    (output/'workflow.yml').write_text(template.replace('release-upload-'+old_version.replace('.','-'),plan['branch']).replace(old_version,version))
    print(json.dumps(dict(version=version,source_commit=source_commit,parts=len(blobs),assets=len(assets),output=str(output))))
    return plan
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-commit',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args();prepare(a.source_commit,a.output.resolve())
