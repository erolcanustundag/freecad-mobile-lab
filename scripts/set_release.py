#!/usr/bin/env python3
"""Set the version used by SDK packaging, Gradle, diagnostics and verification."""
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
version=sys.argv[1];code=int(sys.argv[2]);suffix=sys.argv[3] if len(sys.argv)>3 else 'preview'
assert re.fullmatch(r'\d+\.\d+(?:\.\d+)?(?:-rc\d+)?',version) and code>5
name=version+'-'+suffix if suffix else version
(root/'release.json').write_text(json.dumps({'version':version,'version_name':name,'version_code':code,'status':'engineering checkpoint; Android device gate pending'},indent=2)+'\n')
(root/'app/src/main/java/org/freecad/mobilelab/ReleaseInfo.java').write_text('package org.freecad.mobilelab;\nfinal class ReleaseInfo { static final String VERSION="'+name+'"; static final int CODE='+str(code)+'; }\n')
p=root/'app/build.gradle';s=p.read_text();s=re.sub(r'versionCode \d+','versionCode '+str(code),s);s=re.sub(r"versionName '[^']+'","versionName '"+name+"'",s);p.write_text(s)
print(name,code)
