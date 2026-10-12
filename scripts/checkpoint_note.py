#!/usr/bin/env python3
import json,hashlib,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];r=json.loads((root/'release.json').read_text());version=r['version'];apk=root/'dist'/('FreeCAD-Mobile-Lab-'+version+'-arm64.apk')
inputs=json.loads((root/'docs/apk-inputs.json').read_text())
assert inputs['sha256']==hashlib.sha256(apk.read_bytes()).hexdigest()
for name,value in inputs['inputs'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==value,('Input drift',name)
notes=sys.argv[1] if len(sys.argv)>1 else ''
record={**r,'apk':apk.name,'size_bytes':apk.stat().st_size,'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'engineering_changes':notes,'android_runtime':'physical startup/lifecycle/SAF workflows pending','signing':'retained public development identity','milestone_gate':'not complete until roadmap device/workflow criteria pass'}
p=root/'docs/CHECKPOINTS.json';all_records=json.loads(p.read_text()) if p.exists() else [];all_records=[x for x in all_records if x['version']!=version];all_records.append(record);p.write_text(json.dumps(all_records,indent=2)+'\n')
(root/'docs/checkpoint-record.json').write_text(json.dumps(record,indent=2)+'\n')
continuation='''# Continuous app development\n\nGoal: continue autonomously toward the roadmap 1.0 milestone; save a signed APK per engineering checkpoint. Do not ask routine implementation questions. The Rhino-style command input is required.\n\n'''
continuation+='Current: '+r['version_name']+' / code '+str(r['version_code'])+'.\n\n'
for x in all_records:continuation+='- '+x['version_name']+': '+x['engineering_changes']+'\n'
continuation+='''\nEngineering checkpoints are previews. The phone instant-crash root cause is unverified. Physical Android launch, lifecycle, picker and device matrix checks remain release gates. Never infer a stable 1.0 from APK filenames or host tests.\n\nRead docs/ROADMAP.md, docs/CHECKPOINTS.json and per-version test logs. Finish remaining roadmap tasks rather than treating selected tools as full Rhino parity. Baseline includes 25,694 host assertions plus large STL checks and 459 freeform assertions.\n\nBuild with scripts/set_release.py VERSION CODE [SUFFIX], scripts/build_apk.py and scripts/verify_apk.py. Native ARM build: sketcher-build; host: host-build with ../occt-host. JDK17, SDK35 and NDK27c live under ../toolchains when restored. Host JSON JAR: host-test-deps/json.jar.\n\nBuild and verify each APK, package matching sources using scripts/package_source.py, save the APK separately, and replace the existing source bundle. Save this continuation file with it. Retained development signing allows prototype upgrades; private production signing/migration remains a separate 1.0 gate. Refresh saved artifact identities and versions before replacement in a new turn.\n'''
(root/'docs/CONTINUE.md').write_text(continuation)
print(version,record['sha256'])
