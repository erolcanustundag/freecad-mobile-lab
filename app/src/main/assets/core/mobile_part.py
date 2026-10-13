# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded adapter to genuine upstream Part. Never substitutes mobile OCCT recipes."""
import math
from pathlib import Path
try:
    import Part
except ImportError:
    Part = None

TYPES = {"Part::Feature", "Part::Box", "Part::Cylinder", "Part::Sphere", "Part::Cone",
         "Part::Torus", "Part::Cut", "Part::Fuse", "Part::Common", "Part::Extrusion", "Part::Revolution", "Part::Fillet", "Part::Chamfer", "Part::Section", "Part::Plane"}

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


def profile(source, require_constrained=False):
    if source is None or source.TypeId!="Sketcher::SketchObject":raise ValueError("Choose a native sketch profile")
    if require_constrained and source.DoF!=0:raise ValueError("Fully constrain the sketch before creating a solid")
    shape=source.Shape
    if shape.isNull() or len(shape.Wires)!=1 or not shape.Wires[0].isClosed() or not shape.isValid():
        raise ValueError("This profile tool requires one valid closed sketch wire")
    if len(shape.Edges)>256:raise ValueError("Profile exceeds256 edges")
    return source

def validate_document(doc):
    for obj in doc.Objects:
        if obj.TypeId=="Part::Plane":
            info=shape_info(obj)
            if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Native helper plane must be valid within±1,000,000mm")
        if obj.TypeId in ("Part::Fillet","Part::Chamfer","Part::Section"):
            if obj.TypeId=="Part::Section":sources=[obj.Base,obj.Tool]
            else:sources=[obj.Base]
            if any(source is None or source.TypeId not in TYPES|{"Sketcher::SketchObject"} or source==obj or source in obj.InListRecursive for source in sources):raise ValueError("Native operation sources must exist without dependency cycles")
            info=shape_info(obj)
            if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Native finishing result must be valid and bounded")
            if obj.TypeId!="Part::Section" and info["solids"]!=1:raise ValueError("Edge finishing requires one resulting solid")
        if obj.TypeId not in ("Part::Extrusion","Part::Revolution"):continue
        profile(obj.Base if obj.TypeId=="Part::Extrusion" else obj.Source)
        shape=obj.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or len(shape.Faces)>2000 or not 1e-9<shape.Volume<1e18:
            raise ValueError("Profile operation must create one valid bounded solid")
        box=shape.BoundBox
        if any(not math.isfinite(v) or abs(v)>1000000 for v in (box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax)):
            raise ValueError("Profile solid bounds must stay within±1,000,000mm")


def shape_info(obj):
    require()
    if not hasattr(obj,"Shape") or obj.Shape.isNull():raise ValueError("Choose nonempty native Part geometry")
    shape=obj.Shape
    if len(shape.Faces)>2000 or len(shape.Edges)>10000:raise ValueError("Shape inspection limit is2000 faces/10000 edges")
    result=summary(obj)
    result.update(type=shape.ShapeType,closed=bool(shape.isClosed()),boundary_edge_length_mm=float(sum(edge.Length for edge in shape.Edges)),units={"bounds":"mm","volume":"mm³","area":"mm²","boundary_edge_length_mm":"mm"})
    center=shape.Solids[0].CenterOfMass if len(shape.Solids)==1 else None
    result["solid_centroid_mm"]=[center.x,center.y,center.z] if center is not None else None
    if not all(math.isfinite(v) for v in [result["volume"],result["area"],result["boundary_edge_length_mm"],*result["bounds"],*(result["solid_centroid_mm"] or [])]):raise ValueError("Native measurements must be finite")
    return result


def wire_preview(obj):
    shape_info(obj)
    edges=obj.Shape.Edges
    if len(edges)>128:raise ValueError("Wire preview is limited to128 edges")
    curves=[];total=0
    for i,edge in enumerate(edges):
        if edge.Length<=1e-7:continue
        count=2 if edge.Curve.TypeId=="Part::GeomLine" else 65
        if total+count>8192:raise ValueError("Wire preview exceeds8192 points")
        points=[[float(v) for v in point] for point in edge.discretize(Number=count)]
        if any(not math.isfinite(v) or abs(v)>1000000 for point in points for v in point):raise ValueError("Wire preview must stay within±1,000,000mm")
        total+=len(points);curves.append({"index":i+1,"points":points})
    if not total:raise ValueError("Choose geometry with drawable native edges")
    return {"object":obj.Name,"curves":curves,"point_count":total}


def element_info(obj,kind,index):
    shape_info(obj)
    if kind not in ("edge","face") or type(index) is not int:raise ValueError("Use a current EdgeN or FaceN")
    elements=obj.Shape.Edges if kind=="edge" else obj.Shape.Faces
    if not 1<=index<=len(elements):raise ValueError("Native element number is outside the current shape")
    part=elements[index-1];box=part.BoundBox
    result={"object":obj.Name,"element":kind.title()+str(index),"bounds_mm":[box.XMin,box.YMin,box.ZMin,box.XMax,box.YMax,box.ZMax]}
    if kind=="edge":
        if part.Length<=1e-7:
            point=list(part.Vertexes[0].Point) if part.Vertexes else None
            result.update(below_preview_tolerance=True,curve_type=None,length_mm=float(part.Length),parameter_range=None,start_mm=point,end_mm=point)
        else:
            result.update(below_preview_tolerance=False,curve_type=part.Curve.TypeId,length_mm=float(part.Length),parameter_range=[part.FirstParameter,part.LastParameter],start_mm=list(part.valueAt(part.FirstParameter)),end_mm=list(part.valueAt(part.LastParameter)))
    else:
        u0,u1,v0,v1=part.ParameterRange;u=(u0+u1)/2;v=(v0+v1)/2
        result.update(surface_type=part.Surface.TypeId,area_mm2=float(part.Area),area_centroid_mm=list(part.CenterOfMass),sample_point_mm=list(part.valueAt(u,v)),normal_at_sample=list(part.normalAt(u,v)),uv_sample=[u,v])
    return result
