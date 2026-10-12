#!/usr/bin/env python3
"""Set the version used by SDK packaging, Gradle, diagnostics and verification."""
import argparse,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('version');parser.add_argument('code',type=int)
parser.add_argument('suffix',nargs='?',default='preview')
parser.add_argument('--channel',choices=('candidate','release'),default='candidate')
args=parser.parse_args();version=args.version;code=args.code;suffix=args.suffix
assert re.fullmatch(r'\d+\.\d+(?:\.\d+)?(?:-rc\d+)?',version) and code>5
name=version+'-'+suffix if suffix else version
release={'version':version,'version_name':name,'version_code':code,'channel':args.channel,'status':'engineering checkpoint; Android device gate pending'}
if args.channel=='release':release.update(scope='current mobile feature set',status='initial public mobile feature release; broader device qualification pending')
(root/'release.json').write_text(json.dumps(release,indent=2)+'\n')
(root/'app/src/main/java/org/freecad/mobilelab/ReleaseInfo.java').write_text('package org.freecad.mobilelab;\nfinal class ReleaseInfo { static final String VERSION="'+name+'"; static final int CODE='+str(code)+'; }\n')
p=root/'app/build.gradle';s=p.read_text();s=re.sub(r'versionCode \d+','versionCode '+str(code),s);s=re.sub(r"versionName '[^']+'","versionName '"+name+"'",s);p.write_text(s)
print(name,code)
