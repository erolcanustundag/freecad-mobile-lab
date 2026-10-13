# SPDX-License-Identifier: LGPL-2.1-or-later
"""Host-only original PartDesign prototype; does not claim Android/adapter integration."""
import FreeCAD as A,Part,Sketcher,PartDesign,mobile_part
import json,math
mobile_part.configure();d=A.newDocument("OriginalPartDesignProbe");d.UndoMode=1
b=d.addObject("PartDesign::Body","Body");s=b.newObject("Sketcher::SketchObject","Profile")
p=[A.Vector(0,0,0),A.Vector(10,0,0),A.Vector(10,10,0),A.Vector(0,10,0)]
s.addGeometry([Part.LineSegment(p[i],p[(i+1)%4]) for i in range(4)],False)
for i in range(4):s.addConstraint(Sketcher.Constraint("Block",i))
pad=b.newObject("PartDesign::Pad","Pad");pad.Profile=(s,[]);pad.Length=10;d.recompute()
print("Body",b.TypeId,b.Tip.Name,[o.TypeId for o in b.Group],b.Origin.TypeId)
print("Pad",list(pad.State),pad.Shape.isValid(),pad.Shape.Volume,[(n,pad.getTypeIdOfProperty(n),str(getattr(pad,n))) for n in ["Length","SideType","Type","Profile"]])
assert pad.Shape.isValid() and abs(pad.Shape.Volume-1000)<1e-6
c=b.newObject("Sketcher::SketchObject","CutProfile");c.Placement.Base=A.Vector(0,0,10)
c.addGeometry(Part.Circle(A.Vector(5,5,0),A.Vector(0,0,1),2),False);c.addConstraint(Sketcher.Constraint("Block",0))
pocket=b.newObject("PartDesign::Pocket","Pocket");pocket.Profile=(c,[]);pocket.Length=2;d.recompute()
print("Pocket",list(pocket.State),pocket.Shape.isValid(),pocket.Shape.Volume,b.Tip.Name,pocket.BaseFeature.Name)
assert pocket.Shape.isValid() and abs(pocket.Shape.Volume-(1000-8*math.pi))<1e-5
print("Body properties",[(n,b.getTypeIdOfProperty(n)) for n in ["Tip","BaseFeature","Origin","Group","AllowCompound"]])
print("Origin features",[(o.Name,o.TypeId) for o in b.Origin.OriginFeatures])
d.openTransaction("Pocket depth");pocket.Length=3;d.recompute();d.commitTransaction()
assert abs(pocket.Shape.Volume-(1000-12*math.pi))<1e-5
d.undo();d.recompute();assert abs(pocket.Shape.Volume-(1000-8*math.pi))<1e-5
d.redo();d.recompute();assert abs(pocket.Shape.Volume-(1000-12*math.pi))<1e-5
d.undo();d.recompute()
d.openTransaction("Pad height");pad.Length=12;d.recompute();d.commitTransaction()
assert abs(pad.Shape.Volume-1200)<1e-5 and abs(pocket.Shape.Volume-(1200-8*math.pi))<1e-5
assert b.Tip==pocket and abs(b.Shape.Volume-pocket.Shape.Volume)<1e-5
d.undo();d.recompute();assert abs(pocket.Shape.Volume-(1000-8*math.pi))<1e-5
d.saveAs("/tmp/PartDesignProbe.FCStd");A.closeDocument(d.Name);d=A.openDocument("/tmp/PartDesignProbe.FCStd");d.recompute()
assert d.Body.Tip==d.Pocket and d.Pocket.BaseFeature==d.Pad
assert abs(d.Pocket.Shape.Volume-(1000-8*math.pi))<1e-5
print("PASS: genuine original Body/Pad/Pocket geometry, ownership, dependency, Undo/Redo and FCStd prototype. Android port/adapter NOT_IMPLEMENTED")
