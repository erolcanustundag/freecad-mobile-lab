# SPDX-License-Identifier: LGPL-2.1-or-later
"""Verify the experimental ARM64 module against actual packaged/API26 exports."""
from pathlib import Path
import sys,subprocess,re,json,hashlib
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(ROOT/'scripts'))
from verify_core_apk import symbols,READELF,SYSTEM,NDK
module=BASE/'mobile-mass-android/_mobile_gprops.so';header=subprocess.check_output([str(READELF),'-h',str(module)],text=True);segments=subprocess.check_output([str(READELF),'-lW',str(module)],text=True);dynamic=subprocess.check_output([str(READELF),'-d',str(module)],text=True)
assert 'AArch64' in header
alignment=min(int(l.split()[-1],16) for l in segments.splitlines() if l.strip().startswith('LOAD '));assert alignment>=16384
provided={p.name:p for p in (ROOT/'app/src/main/jniLibs/arm64-v8a').glob('*.so')};needed=re.findall(r'\(NEEDED\).*?\[(.*?)\]',dynamic);assert not set(needed)-set(provided)-SYSTEM
exports,required=symbols(module);assert 'PyInit__mobile_gprops' in exports
available=set()
for p in provided.values():available.update(symbols(p)[0])
for name in SYSTEM:available.update(symbols(NDK/'sysroot/usr/lib/aarch64-linux-android/26'/name)[0])
assert not required-available,sorted(required-available)
result=dict(status='EXPERIMENTAL_ARM64_STATIC_PASS_MOBILE_NOT_PACKAGED',architecture='AArch64',minimum_alignment=alignment,python_entrypoint='PyInit__mobile_gprops',native_loader_closure=True,strong_symbol_api26_closure=True,needed=needed,size_bytes=module.stat().st_size,sha256=hashlib.sha256(module.read_bytes()).hexdigest(),source_sha256=hashlib.sha256((ROOT/'tests/MobileMassPrototype.cpp').read_bytes()).hexdigest(),android_execution='NOT_RUN',app_integration='NOT_IMPLEMENTED')
(ROOT/'docs/native-mass-adapter-prototype-static-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
