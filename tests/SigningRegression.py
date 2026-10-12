#!/usr/bin/env python3
"""Exercise signing guards and the production path with a disposable QA identity.
The QA certificate is not a public release identity; key/password never enter the source bundle.
"""
import hashlib,json,os,secrets,shutil,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JDK=Path(os.environ['JAVA_HOME']);SDK=Path(os.environ.get('ANDROID_SDK_ROOT',ROOT.parent/'toolchains/android-sdk'));builder=ROOT/'scripts/build_apk.py'
checks=0
env=os.environ.copy()
for name in ('CAD_SIGNING_KEYSTORE','CAD_SIGNING_ALIAS','CAD_STORE_PASSWORD','CAD_KEY_PASSWORD'):env.pop(name,None)
def reject(e,message):
    global checks
    result=subprocess.run(['python3',str(builder),'--production','--prebuilt'],env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if result.returncode==0 or message not in result.stdout:raise AssertionError('Signing guard failed: '+message)
    checks+=1
reject(env,'Production signing requires')
with tempfile.TemporaryDirectory(prefix='signing-qa-',dir=ROOT.parent) as directory:
    folder=Path(directory);public=ROOT/'apk-build/development.keystore';copied=folder/'copied.keystore';shutil.copy2(public,copied)
    qaenv={**env,'CAD_SIGNING_KEYSTORE':str(copied),'CAD_SIGNING_ALIAS':'androiddebugkey','CAD_STORE_PASSWORD':'android','CAD_KEY_PASSWORD':'android'}
    reject(qaenv,'Use a private signing key')
    repacked=folder/'repacked.keystore'
    subprocess.run([str(JDK/'bin/keytool'),'-importkeystore','-srckeystore',str(public),'-srcstorepass','android','-srcalias','androiddebugkey','-destkeystore',str(repacked),'-deststorepass','android','-destkeypass','android','-destalias','renamed','-noprompt'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    qaenv.update(CAD_SIGNING_KEYSTORE=str(repacked),CAD_SIGNING_ALIAS='renamed');reject(qaenv,'public development certificate cannot')
    private=folder/'disposable.keystore';password=secrets.token_urlsafe(24);qaenv.update(CAD_SIGNING_KEYSTORE=str(private),CAD_SIGNING_ALIAS='qa',CAD_STORE_PASSWORD=password,CAD_KEY_PASSWORD=password)
    subprocess.run([str(JDK/'bin/keytool'),'-genkeypair','-keystore',str(private),'-storepass:env','CAD_STORE_PASSWORD','-keypass:env','CAD_KEY_PASSWORD','-alias','qa','-dname','CN=Disposable Signing QA','-keyalg','RSA','-keysize','2048','-validity','30'],check=True,env=qaenv,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    subprocess.run(['python3',str(builder),'--production','--prebuilt'],env=qaenv,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    release=json.loads((ROOT/'release.json').read_text());apk=ROOT/'dist'/('FreeCAD-Mobile-Lab-'+release['version']+'-production-arm64.apk');record=ROOT/'docs/apk-inputs-production.json'
    try:
        cert=subprocess.check_output([str(JDK/'bin/keytool'),'-exportcert','-keystore',str(private),'-storepass:env','CAD_STORE_PASSWORD','-alias','qa'],env=qaenv,stderr=subprocess.DEVNULL)
        result=subprocess.check_output([str(JDK/'bin/java'),'-jar',str(SDK/'build-tools/35.0.0/lib/apksigner.jar'),'verify','--verbose','--print-certs',str(apk)],text=True)
        assert hashlib.sha256(cert).hexdigest() in result and 'Verified using v3 scheme (APK Signature Scheme v3): true' in result;checks+=1
        tree=subprocess.check_output([str(SDK/'build-tools/35.0.0/aapt2'),'dump','xmltree',str(apk),'--file','AndroidManifest.xml'],text=True)
        assert 'debuggable' not in tree;checks+=1
        with zipfile.ZipFile(apk) as z:
            assert z.testzip() is None and len([n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')])==31;checks+=1
    finally:
        apk.unlink(missing_ok=True);apk.with_suffix(apk.suffix+'.idsig').unlink(missing_ok=True);record.unlink(missing_ok=True)
print('PASS:',checks,'signing assertions: missing/copied/repacked-development rejection, disposable private signing certificate, non-debuggable production manifest, 31 native libraries')
print('The disposable QA key and APK were deleted; real production identity and Android update migration remain pending.')
