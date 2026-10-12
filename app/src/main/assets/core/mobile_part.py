# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded adapter to genuine upstream Part. Never substitutes mobile OCCT recipes."""
import math
from pathlib import Path
try:
    import Part
except ImportError:
    Part = None

TYPES = {"Part::Feature", "Part::Box", "Part::Cylinder", "Part::Sphere", "Part::Cone",
         "Part::Torus", "Part::Cut", "Part::Fuse", "Part::Common"}

def available():
    return Part is not None

def require():
    if Part is None:
        raise ValueError("Original Part module is not available in this runtime")

def configure():
    if not available():
        return
    import FreeCAD as App
    resources=Path(__file__).resolve().parent/'resources/Mod/Material/Resources'
    if not (resources/'Materials/Standard/Default.FCMat').is_file() or not (resources/'Models').is_dir():
        raise ValueError("Bundled native material resources are missing")
    # Use upstream's documented module-library preferences. Its compiled desktop
    # resource path cannot point at a versioned private Android asset tree.
    preferences=App.ParamGet("User parameter:BaseApp/Preferences/Mod/Material/Resources")
    preferences.SetBool("UseBuiltInMaterials",False)
    preferences.SetBool("UseMaterialsFromWorkbenches",True)
    library=App.ParamGet("User parameter:BaseApp/Preferences/Mod/Material/Resources/Modules/MobileBundled")
    library.SetString("ModuleDir",str(resources/'Materials'))
    library.SetString("ModuleModelDir",str(resources/'Models'))
    library.SetBool("ModuleReadOnly",True)

def summary(obj):
    if not hasattr(obj, "Shape"):
        return None
    shape = obj.Shape
    if shape.isNull():
        return {"null": True, "valid": False}
    box = shape.BoundBox
    return {"null": False, "valid": shape.isValid(), "volume": float(shape.Volume),
            "area": float(shape.Area), "edges": len(shape.Edges), "faces": len(shape.Faces),
            "solids": len(shape.Solids), "bounds": [box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax]}

def mesh(obj, tolerance=0.2, maximum=30000):
    require()
    if not math.isfinite(tolerance) or not 0.05 <= tolerance <= 2:
        raise ValueError("Preview tolerance must be 0.05 to 2 mm")
    if not hasattr(obj, "Shape") or obj.Shape.isNull():
        raise ValueError("Select an object with nonempty Part geometry")
    points, triangles = obj.Shape.tessellate(tolerance)
    if not triangles:
        raise ValueError("Part preview requires faces or solids, not wire-only geometry")
    if len(triangles) > maximum:
        raise ValueError("Part preview exceeds 30,000 triangles; increase tolerance")
    vertices=[]
    for tri in triangles:
        for index in tri:
            p=points[index]
            values=[float(p.x),float(p.y),float(p.z)]
            if not all(math.isfinite(x) for x in values):
                raise ValueError("Part preview contains nonfinite coordinates")
            vertices.extend(values)
    return vertices

def export_step(obj, root, name):
    require()
    if not isinstance(name,str) or not 1 <= len(name) <= 160 or '\x00' in name or '/' in name or '\\' in name or not name.lower().endswith(('.step','.stp')):
        raise ValueError("Use a plain STEP filename")
    destination=(Path(root)/name).resolve()
    if destination.parent != Path(root).resolve():
        raise ValueError("STEP must stay in the document directory")
    if not hasattr(obj,"Shape") or obj.Shape.isNull() or not obj.Shape.isValid():
        raise ValueError("Export requires valid Part geometry")
    Part.export([obj],str(destination))
    return name

def read_step(root, name):
    require()
    if not isinstance(name,str) or not 1 <= len(name) <= 160 or '\x00' in name or '/' in name or '\\' in name or not name.lower().endswith(('.step','.stp')):
        raise ValueError("Use a plain STEP filename")
    source=(Path(root)/name).resolve()
    if source.parent != Path(root).resolve():
        raise ValueError("STEP must stay in the document directory")
    if source.stat().st_size > 128*1024*1024:
        raise ValueError("STEP input exceeds 128 MiB")
    shape=Part.read(str(source))
    if shape.isNull() or not shape.isValid():
        raise ValueError("STEP import did not produce valid Part geometry")
    return shape
