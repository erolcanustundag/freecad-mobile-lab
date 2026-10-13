# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded edits to original FreeCAD Sketcher; geometry/solve stay upstream."""
import math
import FreeCAD as App
import mobile_part
try:
    import Sketcher
except ImportError:
    Sketcher = None

MAX_GEOMETRY = 256
MAX_CONSTRAINTS = 256
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
    if operation=="sketch_geometry":
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
            args=[index(args[0],obj.GeometryCount,True),args[1],index(args[2],obj.GeometryCount,True),args[3]]
            if any(type(p) is not int or p not in (1,2,3) for p in (args[1],args[3])):
                raise ValueError("Endpoint positions must be 1, 2 or 3")
        elif kind in ("Distance","Radius","Diameter","Angle"):
            value=number(args[1],36000 if kind=="Angle" else 1000000)
            if kind!="Angle" and value<=1e-7:raise ValueError("Constraint length must be positive")
            args=[index(args[0],obj.GeometryCount),math.radians(value) if kind=="Angle" else value]
        else:
            args=[index(i,obj.GeometryCount,True) for i in args]
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
    solve(obj)

def summary(obj):
    if obj.TypeId!="Sketcher::SketchObject":return None
    require(obj)
    return {"geometry_count":obj.GeometryCount,"constraint_count":obj.ConstraintCount,
            "dof":obj.DoF,"conflicts":list(obj.ConflictingConstraints),
            "redundant":list(obj.RedundantConstraints),
            "geometry":[{"index":i,"type":g.TypeId,"construction":obj.getConstruction(i)} for i,g in enumerate(obj.Geometry)],
            "constraints":[{"index":i,"type":c.Type,"value":float(c.Value)} for i,c in enumerate(obj.Constraints)]}

def preview(obj):
    require(obj)
    curves=[];count=0
    for i,g in enumerate(obj.Geometry):
        shape=g.toShape()
        # Fixed sample count bounds allocation even for an enormous spline.
        points=shape.discretize(Number=2 if g.TypeId=="Part::GeomLineSegment" else 65)
        count+=len(points)
        if count>8192:raise ValueError("Sketch preview exceeds 8,192 points")
        curves.append({"index":i,"construction":obj.getConstruction(i),
                       "points":[[number(p.x),number(p.y)] for p in points]})
    return {"object":obj.Name,"dof":obj.DoF,"curves":curves,"coordinates":"sketch-local XY mm"}
