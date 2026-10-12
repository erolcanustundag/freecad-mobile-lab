#!/usr/bin/env python3
"""Exercise the same JNI/Python protocol used by Android, on upstream host App."""
import os
from pathlib import Path
import subprocess
import tempfile
import argparse

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--python-tools',action='store_true');args=p.parse_args()
test='PythonToolsHostTest' if args.python_tools else 'CoreAdapterHostTest'
BASE=ROOT.parent
env=dict(os.environ)
jdk=Path(env.get('JAVA_HOME',BASE/'toolchains/jdk-system17')).resolve()
python=Path(env.get('CODEX_PRIMARY_RUNTIME_PYTHON','/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3')).resolve().parents[1]
prefix=BASE/'toolchains/freecad-host-prefix/usr/lib/x86_64-linux-gnu'
env['LD_LIBRARY_PATH']=':'.join(str(p) for p in (python/'lib',BASE/'freecad-core-host/lib',prefix))
classes=ROOT/'core-adapter-test-classes';classes.mkdir(exist_ok=True)
jsonjar=ROOT/'host-test-deps/json.jar'
subprocess.run([str(jdk/'bin/javac'),'--release','8','-cp',str(jsonjar),'-d',str(classes),
    str(ROOT/'app/src/main/java/org/freecad/mobilelab/CoreNative.java'),
    str(ROOT/'app/src/main/java/org/freecad/mobilelab/CoreCommandLine.java'),
    str(ROOT/'tests'/(test+'.java'))],check=True,env=env)
with tempfile.TemporaryDirectory(prefix='freecad-mobile-core-',dir=ROOT) as temporary:
    home=Path(temporary)
    (home/'lib').mkdir();(home/'lib/python3.12').symlink_to(python/'lib/python3.12',target_is_directory=True)
    (home/'tmp').mkdir()
    subprocess.run([str(jdk/'bin/java'),'-cp',str(classes)+os.pathsep+str(jsonjar),
        'org.freecad.mobilelab.'+test,
        str(ROOT/'core-bridge-host/libfreecad_document_bridge.so'),str(home),
        str(ROOT/'app/src/main/assets/core')],check=True,env=env,timeout=90)
