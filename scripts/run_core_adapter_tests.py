#!/usr/bin/env python3
"""Exercise the same JNI/Python protocol used by Android, on upstream host App."""
import os
from pathlib import Path
import subprocess
import tempfile
import argparse

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--python-tools',action='store_true');p.add_argument('--part',action='store_true');p.add_argument('--part-tests',action='store_true');p.add_argument('--sketch-tests',action='store_true');args=p.parse_args()
if args.part_tests: args.part=True
if args.sketch_tests:args.part=True
test='SketchAdapterHostTest' if args.sketch_tests else 'PartAdapterHostTest' if args.part_tests else 'PythonToolsHostTest' if args.python_tools else 'CoreAdapterHostTest'
BASE=ROOT.parent
env=dict(os.environ)
jdk=Path(env.get('JAVA_HOME',BASE/'toolchains/jdk-system17')).resolve()
python=Path(env.get('CODEX_PRIMARY_RUNTIME_PYTHON','/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3')).resolve().parents[1]
prefix=BASE/'toolchains/freecad-host-prefix/usr/lib/x86_64-linux-gnu'
env['LD_LIBRARY_PATH']=':'.join(str(p) for p in (python/'lib',BASE/('freecad-part-host/lib' if args.part else 'freecad-core-host/lib'),BASE/'toolchains/occt-part-host/lib',BASE/'occt-host/lib',BASE/'freecad-part-host/Mod/Part',BASE/'freecad-part-host/Mod/Material',BASE/'freecad-part-host/Mod/Sketcher',prefix))
classes=ROOT/'core-adapter-test-classes';classes.mkdir(exist_ok=True)
jsonjar=ROOT/'host-test-deps/json.jar'
if args.sketch_tests:
    subprocess.run(['g++','-shared','-fPIC','-I'+str(jdk/'include'),'-I'+str(jdk/'include/linux'),str(ROOT/'tests/SignalProbe.cpp'),'-o',str(classes/'libsignalprobe.so')],check=True,env=env)
subprocess.run([str(jdk/'bin/javac'),'--release','8','-cp',str(jsonjar),'-d',str(classes),
    str(ROOT/'app/src/main/java/org/freecad/mobilelab/CoreNative.java'),
    str(ROOT/'app/src/main/java/org/freecad/mobilelab/CoreCommandLine.java'),
    str(ROOT/'tests'/(test+'.java')),*([str(ROOT/'tests/SignalProbe.java'),str(ROOT/'app/src/main/java/org/freecad/mobilelab/WireFrame.java')] if args.sketch_tests else []),*([str(ROOT/'app/src/main/java/org/freecad/mobilelab'/(name+'.java')) for name in ('PartMesh','MeshFrame','SoftwareRasterizer','RenderSettings','StudioLighting')] if args.part_tests else [])],check=True,env=env)
with tempfile.TemporaryDirectory(prefix='freecad-mobile-core-',dir=ROOT) as temporary:
    home=Path(temporary)
    (home/'lib').mkdir();(home/'lib/python3.12').symlink_to(python/'lib/python3.12',target_is_directory=True)
    (home/'tmp').mkdir()
    subprocess.run([str(jdk/'bin/java'),'-cp',str(classes)+os.pathsep+str(jsonjar),
        'org.freecad.mobilelab.'+test,
        str(ROOT/'core-bridge-host/libfreecad_document_bridge.so'),str(home),
        str(ROOT/'app/src/main/assets/core'),*([str(classes/'libsignalprobe.so')] if args.sketch_tests else [])],check=True,env=env,timeout=90)
