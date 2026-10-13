#!/usr/bin/env python3
"""Scope the upstream GUI-only SWIG/Pivy check to actual GUI builds.

Sketcher App and PlaneGCS use FreeCAD-generated Python bindings, not SWIG.
The original GUI remains disabled; no solver/geometry code is replaced.
"""
from pathlib import Path
def apply(source):
    path=Path(source)/'cMake/FreeCAD_Helpers/SetupSwig.cmake'
    old='if(BUILD_SKETCHER)'
    new='if(BUILD_SKETCHER AND BUILD_GUI)'
    text=path.read_text()
    if old in text:path.write_text(text.replace(old,new,1))
    elif new not in text:raise ValueError('Unexpected upstream Sketcher SWIG check')
