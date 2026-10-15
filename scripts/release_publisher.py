# SPDX-License-Identifier: LGPL-2.1-or-later
# Version-stamped validated GitHub Actions publisher; see docs/RELEASING.md.
import os,json,pathlib,hashlib,urllib.request,urllib.error,urllib.parse,zipfile
ROOT=pathlib.Path('.release-transport');plan=json.loads((ROOT/'manifest.json').read_text())
REPO='erolcanustundag/freecad-mobile-lab';API='https://api.github.com/repos/'+REPO
assert plan['repo']==REPO and plan['tag']=='v1.23' and plan['branch']=='release-upload-1-23'
assert os.environ['GITHUB_REPOSITORY']==REPO and os.environ['GITHUB_REF']=='refs/heads/'+plan['branch']
TOKEN=os.environ['GITHUB_TOKEN'];headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','User-Agent':'freecad-mobile-release','X-GitHub-Api-Version':'2022-11-28'}
def api(path,method='GET',data=None,raw=False):
    url=path if path.startswith('https://') else API+'/'+path
    h=dict(headers)
    if raw:h['Content-Type']='application/octet-stream'
    elif data is not None:h['Content-Type']='application/json';data=json.dumps(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url,data=data,method=method,headers=h),timeout=300) as r:
        body=r.read();return json.loads(body) if body else None
# Keep binary chunks out of the publication branch. Read only the exact
# public Git blobs already uploaded and cryptographically verified by the builder.
import base64,re
from concurrent.futures import ThreadPoolExecutor
part_names={n for a in plan['assets'] for n in a.get('parts',[])}
assert set(plan['part_blobs'])==part_names and len(part_names)<=200
def fetch_part(name):
    assert re.fullmatch(r'parts/[0-9]{2}-[0-9]{3}\.bin',name)
    expected=plan['part_blobs'][name]
    result=api('git/blobs/'+expected)
    assert result['sha']==expected and result['encoding']=='base64'
    data=base64.b64decode(result['content'].replace('\n',''),validate=True)
    assert len(data)==result['size'] and len(data)<=1024*1024
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==expected
    dest=ROOT/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(fetch_part,sorted(part_names)))

def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
out=pathlib.Path('release-assets');out.mkdir(exist_ok=True)
for a in plan['assets']:
    p=out/a['name']
    if a.get('reuse_url'):
        urllib.request.urlretrieve(a['reuse_url'],p)
    else:
        packed=out/(a['name']+'.transport')
        with packed.open('wb') as f:
            for n in a['parts']:f.write((ROOT/n).read_bytes())
        assert packed.stat().st_size==a['transport_size'] and sha(packed)==a['transport_sha256']
        if a.get('apk_zip'):
            with zipfile.ZipFile(packed) as z:
                assert z.namelist()==[a['name']] and z.testzip() is None
                p.write_bytes(z.read(a['name']))
        else:packed.replace(p)
    assert p.stat().st_size==a['size_bytes'] and sha(p)==a['sha256'],a['name']
    with zipfile.ZipFile(p) as z:assert z.testzip() is None
names={a['name'] for a in plan['assets']};assert len(names)==4
releases=api('releases?per_page=100');existing=[r for r in releases if r['tag_name']==plan['tag']];assert len(existing)<=1
if existing:release=api('releases/'+str(existing[0]['id']))
else:
    release=api('releases','POST',{'tag_name':plan['tag'],'target_commitish':plan['source_commit'],'name':'FreeCAD Mobile Lab 1.23 · native Android CAD','body':plan['body'],'draft':True,'prerelease':False})
rid=release['id']
assert release['target_commitish']==plan['source_commit']
try:
    tag=api('git/ref/tags/'+plan['tag'])
    assert tag['object']['type']=='commit' and tag['object']['sha']==plan['source_commit']
except urllib.error.HTTPError as e:
    # A fresh draft does not materialize its tag until publication.
    if e.code!=404 or not release['draft']:raise
for a in plan['assets']:
    found=[x for x in api('releases/'+str(rid)+'/assets?per_page=100') if x['name']==a['name']]
    if found:
        assert len(found)==1
        x=found[0]
        if x['size']==a['size_bytes'] and x.get('digest')=='sha256:'+a['sha256']:continue
        assert release['draft'],'Never change published nonmatching assets'
        api('releases/assets/'+str(x['id']),'DELETE')
    p=out/a['name'];url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(a['name'])
    result=api(url,'POST',p.read_bytes(),raw=True)
    assert result['size']==a['size_bytes'] and result.get('digest')=='sha256:'+a['sha256']
assets=api('releases/'+str(rid)+'/assets?per_page=100');assert {a['name'] for a in assets}==names
for a in plan['assets']:
    x=next(x for x in assets if x['name']==a['name']);assert x['size']==a['size_bytes'] and x.get('digest')=='sha256:'+a['sha256']
api('releases/'+str(rid),'PATCH',{'draft':False,'prerelease':False,'make_latest':'true'})
tag=api('git/ref/tags/'+plan['tag']);assert tag['object']['type']=='commit' and tag['object']['sha']==plan['source_commit']
release=api('releases/'+str(rid));assert not release['draft'] and not release['prerelease'] and api('releases/latest')['id']==rid
print(json.dumps({'release_id':rid,'url':release['html_url'],'source_commit':plan['source_commit'],'assets':[{k:x[k] for k in ('id','name','size','digest')} for x in assets]}),flush=True)
ref=api('git/ref/heads/'+plan['branch']);assert ref['object']['sha']==os.environ['GITHUB_SHA']
api('git/refs/heads/'+plan['branch'],'DELETE')
print('Owned temporary transport branch removed; main untouched.',flush=True)
