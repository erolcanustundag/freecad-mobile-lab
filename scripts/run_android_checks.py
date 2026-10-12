#!/usr/bin/env python3
"""Run the separately packaged smoke instrumentation on a connected ARM64 phone.
Export user projects first: the test starts empty and forces a CAD-process crash.
"""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--serial');a=p.parse_args()
report={'android_runtime':'NOT_RUN','reason':'','stable_1_0':'NOT_COMPLETE'}
def save():
    (ROOT/'docs/device-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
adb=shutil.which('adb')
if not adb:
    report['reason']='No Android debug bridge is available; no connected Android test executed';save();sys.exit(2)
base=[adb]+(['-s',a.serial] if a.serial else [])
def run(*args,timeout=180):return subprocess.check_output(base+list(args),text=True,stderr=subprocess.STDOUT,timeout=timeout)
try:
    state=run('get-state',timeout=15).strip()
    if state!='device':raise RuntimeError('Selected device is unavailable or unauthorized')
    abi=run('shell','getprop','ro.product.cpu.abilist').strip()
    if 'arm64-v8a' not in abi:raise RuntimeError('ARM64 device required for delivered APK')
    release=json.loads((ROOT/'release.json').read_text())
    apk=ROOT/'dist'/('FreeCAD-Mobile-Lab-'+release['version']+'-arm64.apk')
    smoke=ROOT.parent/'android-qa/smoke/startup-smoke.apk'
    run('install','-r',str(apk));run('install','-r',str(smoke))
    result=run('shell','am','instrument','-w','org.freecad.mobilelab.test/org.freecad.mobilelab.test.StartupSmokeInstrumentation',timeout=600)
    (ROOT/'docs/device-smoke.txt').write_text(result)
    if 'INSTRUMENTATION_CODE: -1' not in result or 'FAIL:' in result:raise RuntimeError('Instrumentation did not report successful completion')
    report.update(android_runtime='SMOKE_PASS_ONLY',reason='JNI, recovery, software Box, commands, guide and forced-crash recovery passed; full device matrix remains pending',abi=abi)
except Exception as e:report['reason']=str(e)
save()
sys.exit(0 if report['android_runtime']=='SMOKE_PASS_ONLY' else 2)
