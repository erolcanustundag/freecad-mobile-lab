# SPDX-License-Identifier: LGPL-2.1-or-later
"""Parameter bounds before upstream primitive setters trigger recomputation."""
import math

TYPES={"Part::Prism","Part::Wedge","Part::Helix","Part::Spiral"}
FIELDS={"Part::Prism":("Polygon","Circumradius","Height"),
        "Part::Wedge":("Xmin","Ymin","Zmin","X2min","Z2min","Xmax","Ymax","Zmax","X2max","Z2max"),
        "Part::Helix":("Pitch","Height","Radius","Angle","SegmentLength"),
        "Part::Spiral":("Radius","Growth","Rotations","SegmentLength")}

def parameters(obj):
    return {n:(getattr(obj,n).Value if hasattr(getattr(obj,n),"Value") else getattr(obj,n)) for n in FIELDS[obj.TypeId]}

def validate(kind,p):
    if any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1000000 for v in p.values()):raise ValueError("Primitive parameters must be finite and bounded")
    if kind=="Part::Prism":
        if type(p["Polygon"]) is not int or not 3<=p["Polygon"]<=128 or min(p["Circumradius"],p["Height"])<=1e-7:raise ValueError("Prism needs3–128 sides and positive radius/height")
    elif kind=="Part::Wedge":
        if min(p["Xmax"]-p["Xmin"],p["Ymax"]-p["Ymin"],p["Zmax"]-p["Zmin"])<=1e-7 or p["X2max"]<p["X2min"] or p["Z2max"]<p["Z2min"]:raise ValueError("Wedge needs positive base XYZ spans and nonnegative top X/Z spans")
    elif kind=="Part::Helix":
        if min(p["Pitch"],p["Height"],p["Radius"])<=1e-7 or not 1e-7<p["Height"]/p["Pitch"]<=16 or p["Angle"]!=0 or p["SegmentLength"] not in (0,1) or p["SegmentLength"]==0 and p["Height"]/p["Pitch"]>2:raise ValueError("Use a cylindrical helix up to16 turns, one-turn segments; legacy unsplit helices up to2 turns")
    else:
        if p["Radius"]<=1e-7 or p["Growth"]<0 or not 1e-7<p["Rotations"]<=16 or p["Radius"]+p["Growth"]*p["Rotations"]>1000000 or p["SegmentLength"]!=1:raise ValueError("Use positive spiral radius/turns, nonnegative growth, up to16 turns and bounded outer radius with one-turn segments")

def validate_edit(obj,name,value):
    if obj.TypeId not in TYPES or name not in FIELDS[obj.TypeId]:return
    p=parameters(obj);p[name]=value;validate(obj.TypeId,p)

def helix_settings(obj,pitch,height,radius,left):
    validate("Part::Helix",dict(Pitch=pitch,Height=height,Radius=radius,Angle=0,SegmentLength=1))
    if type(left) is not bool:raise ValueError("Helix handedness needs a boolean")
    # onChanged executes immediately: avoid huge intermediate Height/Pitch.
    obj.Height=min(obj.Pitch.Value,pitch,height)
    obj.SegmentLength=1;obj.Angle=0;obj.Pitch=pitch;obj.Height=height;obj.Radius=radius
    obj.LocalCoord="Left-handed" if left else "Right-handed";obj.Style="New style"

def spiral_settings(obj,radius,growth,turns):
    validate("Part::Spiral",dict(Radius=radius,Growth=growth,Rotations=turns,SegmentLength=1))
    obj.Growth=0;obj.SegmentLength=1;obj.Radius=radius;obj.Rotations=turns;obj.Growth=growth
