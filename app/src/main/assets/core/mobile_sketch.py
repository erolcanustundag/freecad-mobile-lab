# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded edits to original FreeCAD Sketcher; geometry/solve stay upstream."""
import math
import re
import FreeCAD as App
import mobile_part
try:
    import Sketcher
except ImportError:
    Sketcher = None

MAX_GEOMETRY = 256
MAX_CONSTRAINTS = 256
MAX_EXTERNAL = 64
TYPES = {"Sketcher::SketchObject"}

def available():
    return Sketcher is not None and mobile_part.available()

def require(obj):
    if not available():
        raise ValueError("Original Sketcher is not available in this runtime")
    if obj.TypeId != "Sketcher::SketchObject":
        raise ValueError("Select a native Sketcher sketch")
    if obj.GeometryCount > MAX_GEOMETRY or obj.ConstraintCount > MAX_CONSTRAINTS:
        raise ValueError("Mobile sketch limit is 256 entities and 256 constraints")
    if len(obj.ExternalGeometry)>MAX_EXTERNAL or len(obj.ExternalGeo)>MAX_EXTERNAL+2:
        raise ValueError("Mobile sketch limit is 64 external edges")

def reference(obj, source_name, element, kind):
    source=obj.Document.getObject(source_name) if isinstance(source_name,str) else None
    if source is None or source==obj or source in obj.InListRecursive:
        raise ValueError("Sketch reference is missing, self-referential or cyclic")
    if source.TypeId not in mobile_part.TYPES|TYPES or not hasattr(source,"Shape"):
        raise ValueError("Select a supported native Part or Sketcher reference")
    if not isinstance(element,str) or not re.fullmatch(kind+r"[1-9][0-9]{0,5}",element):
        raise ValueError("Use a current numbered Face or Edge reference")
    shape=source.Shape
    if shape.isNull() or "Invalid" in source.State:
        raise ValueError("Sketch reference has no valid native shape")
    elements=shape.Faces if kind=="Face" else shape.Edges
    n=int(element[len(kind):])-1
    if n>=len(elements):raise ValueError("Referenced face or edge does not exist")
    selected=elements[n]
    if kind=="Face" and selected.Surface.TypeId!="Part::GeomPlane":
        raise ValueError("FlatFace attachment requires a planar face")
    return source

def placement(values):
    if not isinstance(values,list) or len(values)!=6:
        raise ValueError("Use X Y Z in mm and yaw pitch roll in degrees")
    xyz=[number(v) for v in values[:3]]
    angles=[number(v,36000) for v in values[3:]]
    return App.Placement(App.Vector(*xyz),App.Rotation(*angles))

def validate(obj):
    require(obj)
    if obj.MapMode not in ("Deactivated","FlatFace"):
        raise ValueError("This mobile adapter supports free planes and FlatFace attachment")
    if obj.MapMode=="FlatFace":
        links=obj.AttachmentSupport
        if len(links)!=1 or len(links[0][1])!=1:
            raise ValueError("FlatFace requires one current planar face")
        reference(obj,links[0][0].Name,links[0][1][0],"Face")
    for source,elements in obj.ExternalGeometry:
        if source is None or len(elements)!=1:raise ValueError("External edge reference is missing")
        reference(obj,source.Name,elements[0],"Edge")
    if len(obj.ExternalGeo)!=len(obj.ExternalGeometry)+2:
        raise ValueError("External edge projection failed; edit was rolled back")
    if any(g.toShape().ShapeType!="Edge" for g in obj.ExternalGeo[2:]):
        raise ValueError("External edge collapses in this sketch plane; choose another edge or plane")
    for value in (obj.Placement.Base.x,obj.Placement.Base.y,obj.Placement.Base.z):number(value)
    if "Invalid" in obj.State:raise ValueError("Sketch recompute failed; edit was rolled back")

def validate_document(doc):
    for obj in doc.Objects:
        if obj.TypeId in TYPES:validate(obj)

def placement_summary(value):
    return {"xyz_mm":[value.Base.x,value.Base.y,value.Base.z],"quaternion":list(value.Rotation.Q)}

def number(value, limit=1000000):
    if isinstance(value, bool):
        raise ValueError("Use a finite number")
    result=float(value)
    if not math.isfinite(result) or abs(result)>limit:
        raise ValueError("Sketch values must be finite and within ±1,000,000")
    return result

def index(value, count, axes=False):
    if type(value) is not int or not (-2 if axes else 0)<=value<count:
        raise ValueError("Sketch index is outside the current entity list")
    return value

def point(values):
    if not isinstance(values, list) or len(values)!=2:
        raise ValueError("Use an XY coordinate pair in millimetres")
    return App.Vector(number(values[0]), number(values[1]), 0)

def geometry(spec):
    if not isinstance(spec, dict):
        raise ValueError("Use a sketch geometry specification")
    Part=mobile_part.Part
    kind=spec.get("kind")
    if kind=="Line":
        start,end=point(spec["start"]),point(spec["end"])
        if (end-start).Length<1e-7:raise ValueError("Line endpoints must differ")
        return Part.LineSegment(start,end)
    if kind in ("Circle","Arc"):
        center=point(spec["center"]);radius=number(spec["radius"])
        if radius<=1e-7:raise ValueError("Radius must be positive")
        circle=Part.Circle(center,App.Vector(0,0,1),radius)
        if kind=="Circle":return circle
        start,end=number(spec["start_angle"],36000),number(spec["end_angle"],36000)
        if not 1e-7<end-start<360:raise ValueError("Arc sweep must be greater than 0 and less than 360 degrees")
        return Part.ArcOfCircle(circle,math.radians(start),math.radians(end))
    if kind=="Ellipse":
        center=point(spec["center"]);major,minor=number(spec["major"]),number(spec["minor"])
        if not 1e-7<minor<=major:raise ValueError("Ellipse radii must satisfy 0 < minor ≤ major")
        return Part.Ellipse(center,major,minor)
    if kind=="BSpline":
        values=spec["poles"];degree=spec.get("degree",3)
        if not isinstance(values,list) or not 2<=len(values)<=64:raise ValueError("Use 2 to 64 spline poles")
        if type(degree) is not int or not 1<=degree<=min(5,len(values)-1):raise ValueError("Spline degree must be 1 to 5 and less than the pole count")
        poles=[point(p) for p in values]
        weights=spec.get("weights",[1]*len(poles))
        if not isinstance(weights,list) or len(weights)!=len(poles):raise ValueError("Provide one positive weight per pole")
        weights=[number(w) for w in weights]
        if any(w<=1e-7 for w in weights):raise ValueError("Spline weights must be positive")
        intervals=len(poles)-degree
        knots=[i/intervals for i in range(intervals+1)]
        mults=[degree+1]+[1]*(intervals-1)+[degree+1]
        curve=Part.BSplineCurve()
        curve.buildFromPolesMultsKnots(poles,mults,knots,False,degree,weights)
        return curve
    raise ValueError("Supported sketch entities: Line, Circle, Arc, Ellipse, BSpline")

def solve(obj):
    result=obj.solve()
    if result!=0 or obj.ConflictingConstraints or obj.RedundantConstraints:
        raise ValueError("Sketch constraints conflict or are redundant; edit was rolled back")

def edit(obj, request):
    require(obj)
    operation=request["op"]
    if operation=="sketch_plane":
        if obj.MapMode!="Deactivated":raise ValueError("Detach the sketch before changing its free plane")
        rotations={"XY":App.Rotation(),"XZ":App.Rotation(App.Vector(1,0,0),90),
                   "YZ":App.Rotation(App.Vector(0,1,0),90)}
        plane=request.get("plane");origin=request.get("origin")
        if plane not in rotations or not isinstance(origin,list) or len(origin)!=3:
            raise ValueError("Use XY, XZ or YZ and an XYZ origin in millimetres")
        obj.Placement=App.Placement(App.Vector(*[number(v) for v in origin]),rotations[plane])
    elif operation=="sketch_placement":
        if obj.MapMode!="Deactivated":raise ValueError("Detach the sketch before changing its free plane")
        obj.Placement=placement(request["values"])
    elif operation=="sketch_attach":
        source=reference(obj,request.get("source"),request.get("element"),"Face")
        obj.AttachmentSupport=[(source,[request["element"]])]
        obj.AttachmentOffset=App.Placement()
        obj.MapMode="FlatFace"
    elif operation=="sketch_offset":
        if obj.MapMode!="FlatFace":raise ValueError("Attach the sketch before setting an attachment offset")
        obj.AttachmentOffset=placement(request["values"])
    elif operation=="sketch_detach":
        world=obj.Placement
        obj.MapMode="Deactivated";obj.AttachmentSupport=[];obj.AttachmentOffset=App.Placement()
        obj.Placement=world
    elif operation=="sketch_external":
        if len(obj.ExternalGeometry)>=MAX_EXTERNAL:raise ValueError("Sketch supports at most 64 external edges")
        source=reference(obj,request.get("source"),request.get("element"),"Edge")
        if any(link==source and request["element"] in names for link,names in obj.ExternalGeometry):
            raise ValueError("This external edge is already referenced")
        obj.addExternal(source.Name,request["element"],False,False)
    elif operation=="sketch_delete_external":
        obj.delExternal(index(request["index"],len(obj.ExternalGeometry)))
    elif operation in ("sketch_trim","sketch_split"):
        entity=index(request["index"],obj.GeometryCount)
        pick=point(request["point"])
        shape=obj.Geometry[entity].toShape()
        if shape.distToShape(mobile_part.Part.Vertex(pick))[0]>1e-6:
            raise ValueError("Pick a point on the current sketch curve")
        getattr(obj,"trim" if operation=="sketch_trim" else "split")(entity,pick)
    elif operation=="sketch_extend":
        entity=index(request["index"],obj.GeometryCount);position=request["position"]
        if type(position) is not int or position not in (1,2):
            raise ValueError("Line endpoint must be 1 or 2")
        curve=obj.Geometry[entity];amount=number(request["amount"])
        if curve.TypeId!="Part::GeomLineSegment":
            raise ValueError("This extend tool supports native line segments")
        if abs(amount)<1e-7 or curve.length()+amount<=1e-7:
            raise ValueError("Extension must preserve a positive line length")
        obj.extend(entity,amount,position)
    elif operation=="sketch_fillet":
        first=index(request["first"],obj.GeometryCount);second=index(request["second"],obj.GeometryCount)
        if first==second:raise ValueError("Choose two different lines")
        a,b=obj.Geometry[first],obj.Geometry[second];radius=number(request["radius"])
        if a.TypeId!="Part::GeomLineSegment" or b.TypeId!="Part::GeomLineSegment":
            raise ValueError("This fillet tool supports two native line segments")
        if not 1e-7<radius<min(a.length(),b.length()):
            raise ValueError("Fillet radius must be positive and smaller than both lines")
        if min((u-v).Length for u in (a.StartPoint,a.EndPoint) for v in (b.StartPoint,b.EndPoint))>1e-7:
            raise ValueError("Choose lines meeting at a common endpoint")
        picks=[point(request["first_point"]),point(request["second_point"])]
        for curve,pick in zip((a,b),picks):
            if curve.toShape().distToShape(mobile_part.Part.Vertex(pick))[0]>1e-6:
                raise ValueError("Pick points on both current lines")
        obj.fillet(first,second,picks[0],picks[1],radius,True,False,False)
    elif operation=="sketch_geometry":
        if obj.GeometryCount>=MAX_GEOMETRY:raise ValueError("Sketch supports at most 256 entities")
        construction=request.get("construction",False)
        if type(construction) is not bool:raise ValueError("Construction must be true or false")
        obj.addGeometry(geometry(request["geometry"]),construction)
    elif operation=="sketch_delete_geometry":
        obj.delGeometry(index(request["index"],obj.GeometryCount))
    elif operation=="sketch_construction":
        value=request["value"]
        if type(value) is not bool:raise ValueError("Construction must be true or false")
        obj.setConstruction(index(request["index"],obj.GeometryCount),value)
    elif operation=="sketch_move":
        entity=index(request["index"],obj.GeometryCount);position=request["position"]
        if type(position) is not int or position not in (1,2,3):raise ValueError("Point position must be 1, 2 or 3")
        obj.moveGeometry(entity,position,point(request["point"]),False)
    elif operation=="sketch_constraint":
        if obj.ConstraintCount>=MAX_CONSTRAINTS:raise ValueError("Sketch supports at most 256 constraints")
        kind=request["kind"];args=request.get("args")
        signatures={"Horizontal":1,"Vertical":1,"Coincident":4,"Parallel":2,
                    "Perpendicular":2,"Tangent":2,"Equal":2,"Distance":2,
                    "Radius":2,"Diameter":2,"Angle":2}
        if kind not in signatures or not isinstance(args,list) or len(args)!=signatures[kind]:
            raise ValueError("Unsupported constraint or argument count")
        if kind=="Coincident":
            args=[constraint_index(obj,args[0]),args[1],constraint_index(obj,args[2]),args[3]]
            if any(type(p) is not int or p not in (1,2,3) for p in (args[1],args[3])):
                raise ValueError("Endpoint positions must be 1, 2 or 3")
        elif kind in ("Distance","Radius","Diameter","Angle"):
            value=number(args[1],36000 if kind=="Angle" else 1000000)
            if kind!="Angle" and value<=1e-7:raise ValueError("Constraint length must be positive")
            args=[index(args[0],obj.GeometryCount),math.radians(value) if kind=="Angle" else value]
        else:
            args=[constraint_index(obj,i) for i in args]
        obj.addConstraint(Sketcher.Constraint(kind,*args))
    elif operation=="sketch_delete_constraint":
        obj.delConstraint(index(request["index"],obj.ConstraintCount))
    elif operation=="sketch_datum":
        constraint=index(request["index"],obj.ConstraintCount)
        value=request["value"]
        if not isinstance(value,str) or len(value)>128:raise ValueError("Use a dimension such as 30 mm or 45 deg")
        quantity=App.Units.Quantity(value)
        number(quantity.Value)
        obj.setDatum(constraint,quantity)
    else:
        raise ValueError("Unknown sketch edit")
    obj.Document.recompute()
    validate(obj)
    solve(obj)

def constraint_index(obj, value):
    if type(value) is not int or not -len(obj.ExternalGeo)<=value<obj.GeometryCount:
        raise ValueError("Sketch constraint index is outside the current internal/external geometry")
    return value

def summary(obj):
    if obj.TypeId!="Sketcher::SketchObject":return None
    require(obj)
    return {"geometry_count":obj.GeometryCount,"constraint_count":obj.ConstraintCount,
            "dof":obj.DoF,"conflicts":list(obj.ConflictingConstraints),
            "redundant":list(obj.RedundantConstraints),
            "placement":placement_summary(obj.Placement),"map_mode":str(obj.MapMode),
            "attachment_offset":placement_summary(obj.AttachmentOffset),
            "support":[{"object":link.Name,"elements":list(names)} for link,names in obj.AttachmentSupport],
            "external":[{"reference_index":i,"geometry_index":-3-i,"object":link.Name,"elements":list(names)} for i,(link,names) in enumerate(obj.ExternalGeometry)],
            "geometry":[{"index":i,"type":g.TypeId,"construction":obj.getConstruction(i)} for i,g in enumerate(obj.Geometry)],
            "constraints":[{"index":i,"type":c.Type,"value":float(c.Value)} for i,c in enumerate(obj.Constraints)]}

def preview(obj):
    require(obj)
    curves=[];count=0
    geometries=[(i,g,obj.getConstruction(i),False) for i,g in enumerate(obj.Geometry)]
    geometries += [(-i-1,g,True,True) for i,g in enumerate(obj.ExternalGeo) if i>=2]
    for i,g,construction,external in geometries:
        shape=g.toShape()
        # Fixed sample count bounds allocation even for an enormous spline.
        points=shape.discretize(Number=2 if g.TypeId=="Part::GeomLineSegment" else 65)
        count+=len(points)
        if count>8192:raise ValueError("Sketch preview exceeds 8,192 points")
        curves.append({"index":i,"construction":construction,"external":external,
                       "points":[[number(p.x),number(p.y)] for p in points]})
    return {"object":obj.Name,"dof":obj.DoF,"curves":curves,"coordinates":"sketch-local XY mm",
            "placement":placement_summary(obj.Placement),"map_mode":str(obj.MapMode)}
