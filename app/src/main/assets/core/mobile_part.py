# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded adapter to genuine upstream Part. Never substitutes mobile OCCT recipes."""
import math
import re
import mobile_primitives
from pathlib import Path
try:
    import Part
except ImportError:
    Part = None

TYPES = {"Part::Feature", "Part::Box", "Part::Cylinder", "Part::Sphere", "Part::Cone",
         "Part::Torus", "Part::Cut", "Part::Fuse", "Part::Common", "Part::Extrusion", "Part::Revolution", "Part::Fillet", "Part::Chamfer", "Part::Section", "Part::Plane", "Part::Loft", "Part::RuledSurface", "Part::Offset", "Part::Mirroring", "Part::Sweep", "Part::Thickness", "Part::Offset2D", "Part::Compound", "Part::RegularPolygon", "Part::Ellipsoid", "Part::Refine", "Part::Reverse"}
TYPES.update(mobile_primitives.TYPES)

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
    solids=shape.Solids
    closed=bool(solids) and all(s.isClosed() for s in solids)
    # Volume is a signed orientation integral upstream. A reversed closed solid
    # still occupies the same physical space; compounds aggregate, not union.
    volume=float(sum(abs(s.Volume) for s in solids)) if closed else None
    oriented=float(sum(s.Volume for s in solids)) if closed else None
    return {"null": False, "valid": shape.isValid(), "volume": volume,
            "oriented_volume_mm3": oriented,
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
        if obj.TypeId in mobile_primitives.TYPES:
            mobile_primitives.validate(obj.TypeId,mobile_primitives.parameters(obj))
            info=shape_info(obj)
            if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Primitive geometry must be valid and bounded")
            if obj.TypeId in ("Part::Prism","Part::Wedge"):
                if info["solids"]!=1 or info["volume"] is None or not 1e-9<info["volume"]<1e18:raise ValueError("Prism/wedge must produce one closed solid")
            else:
                if obj.Shape.Faces or len(obj.Shape.Wires)!=1 or len(obj.Shape.Edges)>64:raise ValueError("Helix/spiral must produce one bounded native wire")
                for edge in obj.Shape.Edges:curve_budget(edge)
        if obj.TypeId in ("Part::RegularPolygon","Part::Ellipsoid","Part::Refine","Part::Reverse"):
            if obj.TypeId=="Part::RegularPolygon":
                validate_edit(obj,"Polygon",obj.Polygon)
                validate_edit(obj,"Circumradius",obj.Circumradius.Value)
            elif obj.TypeId=="Part::Ellipsoid":
                for name in ("Radius1","Radius2","Radius3","Angle1","Angle2","Angle3"):
                    validate_edit(obj,name,getattr(obj,name).Value)
            else:
                source=bounded_source(obj.Source)
                if source==obj or source in obj.InListRecursive:raise ValueError("Native feature sources must exist without dependency cycles")
            info=shape_info(obj)
            if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Native primitive/refine/reverse result must be valid and bounded")
            if obj.TypeId=="Part::RegularPolygon" and (obj.Shape.Faces or len(obj.Shape.Wires)!=1 or not obj.Shape.Wires[0].isClosed() or len(obj.Shape.Edges)!=obj.Polygon):raise ValueError("Polygon must produce one closed native wire")
            if obj.TypeId=="Part::Ellipsoid" and (info["solids"]!=1 or info["volume"] is None or not 1e-9<info["volume"]<1e18):raise ValueError("Ellipsoid must produce one bounded closed solid")
        if obj.TypeId in ("Part::Sweep","Part::Thickness","Part::Offset2D","Part::Compound"):
            if obj.TypeId=="Part::Sweep":
                sources=list(obj.Sections)
                if not 1<=len(sources)<=8 or len(set(sources))!=len(sources):raise ValueError("Sweep needs1–8 unique profiles")
                for source in sources:wire_profile(source,bool(obj.Solid))
                link=obj.Spine
                if not isinstance(link,tuple) or len(link)!=2 or link[1]:raise ValueError("Use one whole native wire as sweep path")
                spine=wire_profile(link[0])
                if spine in sources:raise ValueError("Sweep path must differ from its profiles")
                sources.append(spine)
            elif obj.TypeId=="Part::Thickness":
                source,names=obj.Faces
                solid_source(source)
                ids=[]
                for name in names:
                    match=re.fullmatch(r"Face([1-9][0-9]{0,5})",name)
                    if not match:raise ValueError("Use current native FaceN selections")
                    ids.append(int(match.group(1)))
                face_selection(source,ids);sources=[source]
                value=float(obj.Value.Value)
                if not math.isfinite(value) or not 1e-7<abs(value)<=1000000:raise ValueError("Use finite nonzero bounded thickness")
            elif obj.TypeId=="Part::Offset2D":
                sources=[planar_profile(obj.Source)]
                if not math.isfinite(obj.Value) or not 1e-7<abs(obj.Value)<=1000000:raise ValueError("Use finite nonzero bounded planar offset")
                planar_profile(obj)
            else:
                sources=list(obj.Links)
                if not 2<=len(sources)<=32 or len(set(sources))!=len(sources):raise ValueError("Compound needs2–32 unique source shapes")
                for source in sources:bounded_source(source)
            if any(source is None or source==obj or source in obj.InListRecursive for source in sources):raise ValueError("Native feature sources must exist without dependency cycles")
            info=shape_info(obj)
            if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Native sweep/shell/offset/compound result must be valid and bounded")
            if (obj.TypeId=="Part::Thickness" or obj.TypeId=="Part::Sweep" and obj.Solid) and (info["solids"]!=1 or info["volume"] is None or not 1e-9<info["volume"]<1e18):raise ValueError("Native solid feature must produce one bounded closed solid")
            if obj.TypeId=="Part::Thickness" and value<0 and info["volume"]>=abs(source.Shape.Solids[0].Volume)-1e-9:raise ValueError("Inward thickness must remove a cavity; unchanged or collapsed solids are rejected")
        if obj.TypeId in ("Part::Loft","Part::RuledSurface","Part::Offset","Part::Mirroring"):
            if obj.TypeId=="Part::Loft":
                sources=list(obj.Sections)
                if not 2<=len(sources)<=16 or len(set(sources))!=len(sources) or obj.Closed:raise ValueError("Use2–16 unique sections for an open-ended loft")
                for source in sources:wire_profile(source,bool(obj.Solid))
            elif obj.TypeId=="Part::RuledSurface":
                sources=[]
                for link in (obj.Curve1,obj.Curve2):
                    if not isinstance(link,tuple) or len(link)!=2 or len(link[1])!=1:raise ValueError("Ruled surfaces require two single native edge references")
                    edge_source(link[0],link[1][0]);sources.append(link[0])
            else:
                sources=[obj.Source]
                if obj.Source is None:raise ValueError("Native source link must exist")
                if obj.TypeId=="Part::Offset" and (abs(obj.Value)<=1e-7 or abs(obj.Value)>1000000 or not math.isfinite(obj.Value) or len(obj.Source.Shape.Solids)!=1):raise ValueError("Use a finite nonzero offset on one source solid")
                if obj.TypeId=="Part::Mirroring" and (obj.Normal.Length<=1e-7 or any(not math.isfinite(v) or abs(v)>1000000 for v in [*obj.Base,*obj.Normal])):raise ValueError("Use a bounded nonzero mirror plane")
            if any(source is None or source.TypeId not in TYPES|{"Sketcher::SketchObject"} or source==obj or source in obj.InListRecursive for source in sources):raise ValueError("Native feature sources must exist without dependency cycles")
            info=shape_info(obj)
            if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Native surface/solid result must be valid and bounded")
            if (obj.TypeId=="Part::Offset" or obj.TypeId=="Part::Loft" and obj.Solid) and (info["solids"]!=1 or info["volume"] is None or not 1e-9<info["volume"]<1e18):raise ValueError("Native solid feature must create one bounded closed solid")
            if obj.TypeId=="Part::RuledSurface" and not obj.Shape.Faces:raise ValueError("Ruled surface must produce faces")
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
    result.update(type=shape.ShapeType,closed=bool(shape.isClosed()),boundary_edge_length_mm=float(sum(edge.Length for edge in shape.Edges)),units={"bounds":"mm","volume":"mm³","oriented_volume_mm3":"mm³","area":"mm²","boundary_edge_length_mm":"mm"})
    center=shape.Solids[0].CenterOfMass if len(shape.Solids)==1 else None
    result["solid_centroid_mm"]=[center.x,center.y,center.z] if center is not None else None
    if not all(math.isfinite(v) for v in [*([] if result["volume"] is None else [result["volume"],result["oriented_volume_mm3"]]),result["area"],result["boundary_edge_length_mm"],*result["bounds"],*(result["solid_centroid_mm"] or [])]):raise ValueError("Native measurements must be finite")
    return result


def validate_edit(obj,name,value):
    """Precompute guards for the bounded native scalar tools, in mm/degrees."""
    mobile_primitives.validate_edit(obj,name,value)
    if obj.TypeId=="Part::RegularPolygon" and name=="Polygon":
        if type(value) is not int or not 3<=value<=128:raise ValueError("Polygon needs3–128 integer sides")
    elif obj.TypeId=="Part::RegularPolygon" and name=="Circumradius":
        if not math.isfinite(value) or not 1e-7<value<=1000000:raise ValueError("Polygon circumradius must be a positive bounded length")
    elif obj.TypeId=="Part::Ellipsoid":
        if name in ("Radius1","Radius2","Radius3"):
            if not math.isfinite(value) or not (name=="Radius3" and value==0 or 1e-7<value<=1000000):raise ValueError("Ellipsoid radii must be positive bounded lengths; native Radius3=0 uses Radius2")
        elif name in ("Angle1","Angle2","Angle3") and value!={"Angle1":-90,"Angle2":90,"Angle3":360}[name]:raise ValueError("This ellipsoid tool supports full solids only")
    elif obj.TypeId in ("Part::Offset","Part::Offset2D") and name=="Value":
        if not math.isfinite(value) or not 1e-7<abs(value)<=1000000:raise ValueError("Offset needs a finite nonzero bounded amount")


def wire_profile(obj,closed=False):
    if obj is None or obj.TypeId not in TYPES|{"Sketcher::SketchObject"}:raise ValueError("Choose supported native wire geometry")
    info=shape_info(obj);shape=obj.Shape
    if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]) or shape.Faces or len(shape.Wires)!=1 or len(shape.Edges)>256 or closed and not shape.Wires[0].isClosed():raise ValueError("Choose one valid bounded wire; solid lofts require closed profiles")
    for edge in shape.Edges:curve_budget(edge)
    return obj


def edge_source(obj,element):
    if obj is None or obj.TypeId not in TYPES|{"Sketcher::SketchObject"}:raise ValueError("Choose supported native edge geometry")
    info=shape_info(obj);match=re.fullmatch(r"Edge([1-9][0-9]{0,5})",element) if isinstance(element,str) else None
    if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]) or not match or not 1<=int(match.group(1))<=len(obj.Shape.Edges):raise ValueError("Choose a current native EdgeN within the source")
    if obj.Shape.Edges[int(match.group(1))-1].Length<=1e-7:raise ValueError("Choose a nonzero edge for a ruled surface")
    curve_budget(obj.Shape.Edges[int(match.group(1))-1])
    return obj


def curve_budget(edge):
    if edge.Length<=1e-7 or getattr(edge.Curve,"NbPoles",0)>64:raise ValueError("Use nonzero native profile/ruled curves with at most64 spline poles")


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


def bounded_source(obj):
    if obj is None or obj.TypeId not in TYPES|{"Sketcher::SketchObject"}:raise ValueError("Choose supported native geometry")
    info=shape_info(obj)
    if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Source geometry must be valid and bounded")
    return obj


def solid_source(obj):
    bounded_source(obj)
    if len(obj.Shape.Solids)!=1 or not obj.Shape.Solids[0].isClosed():raise ValueError("Choose one closed native solid")
    return obj


def face_selection(obj,ids):
    if not isinstance(ids,list) or not 1<=len(ids)<=16 or len(set(ids))!=len(ids) or any(type(i) is not int or not 1<=i<=len(obj.Shape.Faces) for i in ids) or len(ids)==len(obj.Shape.Faces):raise ValueError("Remove1–16 unique current faces while retaining at least one face")
    return ids


def planar_profile(obj):
    bounded_source(obj);shape=obj.Shape
    if shape.Solids or len(shape.Faces)>1 or len(shape.Wires)!=1 or not shape.Wires[0].isClosed() or len(shape.Edges)>256 or shape.findPlane() is None:raise ValueError("Use one closed planar wire or single planar face within256 edges")
    for edge in shape.Edges:curve_budget(edge)
    return obj
