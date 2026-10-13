#!/usr/bin/env python3
"""Keep the host VM's fault handler when FreeCAD runs as an embedded library.

This only changes Application.cpp with an explicit CMake opt-in. Standalone
desktop builds retain their original handler. Geometry and solver are unchanged.
"""
from pathlib import Path
def apply(source):
    source=Path(source)
    path=source/'src/App/Application.cpp';text=path.read_text()
    old='#elif defined(FC_OS_LINUX)\n        std::signal(SIGSEGV,segmentation_fault_handler);'
    new='#elif defined(FC_OS_LINUX) && !defined(FREECAD_MOBILE_EMBEDDED)\n        std::signal(SIGSEGV,segmentation_fault_handler);'
    if old in text:path.write_text(text.replace(old,new,1))
    elif new not in text:raise ValueError('Unexpected upstream Linux signal registration')
    path=source/'src/App/CMakeLists.txt';text=path.read_text()
    marker='add_library(FreeCADApp SHARED)'
    new=marker+'\n\n# Embedded VMs own their process signal handlers.\nif(FREECAD_MOBILE_EMBEDDED)\n    set_source_files_properties(Application.cpp PROPERTIES COMPILE_DEFINITIONS FREECAD_MOBILE_EMBEDDED=1)\nendif()'
    if new not in text:
        if marker not in text:raise ValueError('Unexpected upstream App target')
        path.write_text(text.replace(marker,new,1))
