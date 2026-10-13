#!/usr/bin/env python3
"""Build a headless upstream Base/App reference; this does not build an APK."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT.parent/'upstream/FreeCAD-1.1.4')
    p.add_argument('--prefix', type=Path, default=ROOT.parent/'toolchains/freecad-host-prefix/usr')
    p.add_argument('--occt', type=Path, default=ROOT.parent/'occt-host')
    p.add_argument('--build', type=Path, default=ROOT.parent/'freecad-core-host')
    p.add_argument('--python-root', type=Path, default=Path(sys.prefix))
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--configure-only', action='store_true')
    p.add_argument('--part',action='store_true',help='Build original Part/Materials in an isolated reference directory')
    p.add_argument('--sketcher',action='store_true',help='Build original Sketcher/solver; implies --part')
    args = p.parse_args()
    if args.sketcher: args.part=True
    if args.jobs < 1 or args.jobs > 32:
        p.error('--jobs must be 1 to 32')
    source, prefix, occt, build, python = (v.resolve() for v in (args.source,args.prefix,args.occt,args.build,args.python_root))
    if args.sketcher:
        from patch_headless_sketcher import apply
        apply(source)
    python_executable = python/'bin/python3'
    python_version = subprocess.check_output([str(python_executable),'-c','import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],text=True).strip()
    python_library = python/('lib/libpython'+python_version+'.so')
    if not python_library.is_file():
        python_library = python/('lib/libpython'+python_version+'.so.1.0')
    if not python_library.is_file():
        p.error('No matching shared libpython under --python-root')
    if not (source/'src/App/Document.cpp').is_file():
        p.error('Extract the pinned upstream source first; see docs/FREECAD-CORE-PORT.md')
    qt = source/'cMake/FreeCAD_Helpers/SetupQt.cmake'
    text = qt.read_text()
    old = 'set(FREECAD_QT_COMPONENTS Core Concurrent Network Xml)'
    new = ('# Base/App translations are generated in headless builds as well as GUI builds.\n'
           '# Their qt_add_translation calls require LinguistTools in both configurations.\n'
           'set(FREECAD_QT_COMPONENTS Core Concurrent Network Xml LinguistTools)')
    if old in text:
        qt.write_text(text.replace(old,new,1))
    elif new not in text:
        p.error('Unexpected SetupQt.cmake: review the pinned headless translation patch')
    init = (source/'cMake/FreeCAD_Helpers/InitializeFreeCADBuildOptions.cmake').read_text()
    # Freeze the exact module choices; the minimal reference contains no workbench.
    module_options = re.findall(r'option\((BUILD_[A-Z_]+) "Build the FreeCAD', init)
    cmake = ['cmake','-S',str(source),'-B',str(build),'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DCMAKE_POLICY_VERSION_MINIMUM=3.5',
        '-DCMAKE_PREFIX_PATH='+str(prefix)+';'+str(occt),
        '-DFREECAD_QT_VERSION=5','-DBUILD_GUI=OFF','-DBUILD_FEM_VTK=OFF',
        '-DENABLE_DEVELOPER_TESTS=OFF','-DFREECAD_USE_SMESH=OFF','-DBUILD_SMESH=OFF',
        '-DFREECAD_USE_FREETYPE=OFF','-DFREECAD_USE_EXTERNAL_E57FORMAT=ON',
        '-DFREECAD_USE_EXTERNAL_FMT=ON','-DPython3_ROOT_DIR='+str(python),
        '-DPython3_EXECUTABLE='+str(python_executable),
        '-DPython3_LIBRARY='+str(python_library),
        '-DPython3_INCLUDE_DIR='+str(python/('include/python'+python_version)),
        '-DZLIB_LIBRARY_RELEASE='+str(prefix/'lib/x86_64-linux-gnu/libz.so'),
        '-DBoost_NO_BOOST_CMAKE=ON','-DBOOST_ROOT='+str(prefix)]
    cmake += ['-D'+name+'=OFF' for name in sorted(set(module_options))]
    if args.part:
        cmake += ['-DBUILD_PART=ON','-DBUILD_MATERIAL=ON','-DOCCT_CMAKE_FALLBACK=ON','-DOCC_INCLUDE_DIR='+str(occt/'include/opencascade'),'-DOCC_LIBRARY='+str(occt/'lib/libTKernel.so'),'-DOCC_LIBRARY_DIR='+str(occt/'lib')]
    if args.sketcher: cmake += ['-DBUILD_SKETCHER=ON']
    env = dict(os.environ)
    libpath = ':'.join([str(python/'lib'),str(prefix/'lib/x86_64-linux-gnu'),str(occt/'lib')])
    env['LD_LIBRARY_PATH'] = libpath+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env['PATH'] = str(prefix/'lib/qt5/bin')+':'+env['PATH']
    subprocess.run(cmake, check=True, env=env)
    if not args.configure_only:
        subprocess.run(['cmake','--build',str(build),'--target','FreeCADApp','FreeCADBase','FreeCADMainCmd','FreeCADMainPy',*(['Materials','Part'] if args.part else []),*(['Sketcher'] if args.sketcher else []),'--parallel',str(args.jobs)],check=True,env=env)
    print('Host-only core', 'configured' if args.configure_only else 'built', 'at', build)

if __name__ == '__main__':
    main()
