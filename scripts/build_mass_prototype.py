from pathlib import Path
import subprocess,os,hashlib,json
r=Path(__file__).resolve().parents[1];b=r.parent;source=r/'tests/MobileMassPrototype.cpp';names=['TKTopAlgo','TKBRep','TKGeomAlgo','TKGeomBase','TKG3d','TKG2d','TKMath','TKernel'];records={}
for platform in ['host','android']:
 out=b/('mobile-mass-'+platform);out.mkdir(exist_ok=True);library=out/'_mobile_gprops.so'
 if platform=='host':
  py=Path(os.environ['CODEX_PRIMARY_RUNTIME_PYTHON']).parent.parent;occt=b/'occt-host';command=['g++','-I'+str(py/'include/python3.12'),'-I'+str(occt/'include/opencascade'),'-L'+str(occt/'lib'),'-Wl,-rpath-link,'+str(occt/'lib')]
 else:
  ndk=b/'toolchains/android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64';py=b/'upstream/cpython-3.13.16/cross-build/aarch64-linux-android/prefix';libs=r/'app/src/main/jniLibs/arm64-v8a';occt=r/'vendor/occt/arm64-v8a';command=[str(ndk/'bin/aarch64-linux-android26-clang++'),'-I'+str(py/'include/python3.13'),'-I'+str(occt/'include/opencascade'),'-L'+str(libs),'-Wl,-rpath-link,'+str(libs),'-lpython3.13','-Wl,-z,max-page-size=16384','-nostdlib++','-lc++_shared']
 command+=['-std=c++17','-O2','-shared','-fPIC','-fvisibility=hidden',str(source),*['-l'+n for n in names],'-o',str(library)]
 subprocess.run(command,check=True);records[platform]=dict(path=str(library),size_bytes=library.stat().st_size,sha256=hashlib.sha256(library.read_bytes()).hexdigest())
print(json.dumps(records,indent=2));(b/'mass-prototype-build.json').write_text(json.dumps(records,indent=2)+'\n')
