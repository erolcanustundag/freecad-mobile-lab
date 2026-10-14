# SPDX-License-Identifier: LGPL-2.1-or-later
"""Host-only original PartDesign patterns; mobile integration remains pending."""
import FreeCAD as A,Part,Sketcher,PartDesign,mobile_part,math
mobile_part.configure();d=A.newDocument('PatternProbe')
def stock(name):
 b=d.addObject('PartDesign::Body',name);b.AllowCompound=False;s=b.newObject('Sketcher::SketchObject',name+'Profile')
 p=[A.Vector(0,0,0),A.Vector(10,0,0),A.Vector(10,10,0),A.Vector(0,10,0)]
 s.addGeometry([Part.LineSegment(p[i],p[(i+1)%4]) for i in range(4)],False)
 f=b.newObject('PartDesign::Pad',name+'Pad');f.Profile=(s,[]);f.Length=10;d.recompute();return b,s,f
def frame(b,role):return next(o for o in b.Origin.OriginFeatures if o.Role==role)
def info(f):return dict(type=f.TypeId,state=list(f.State),status=f.getStatusString(),volume=f.Shape.Volume if not f.Shape.isNull() else None,solids=len(f.Shape.Solids) if not f.Shape.isNull() else None)
b,s,p=stock('MirrorBody');f=b.newObject('PartDesign::Mirrored','Mirrored');f.Originals=[p];f.MirrorPlane=(frame(b,'XZ_Plane'),['']);d.recompute();print('MIRROR',info(f),flush=True);assert abs(f.Shape.Volume-2000)<1e-5
b,s,p=stock('LinearBody');f=b.newObject('PartDesign::LinearPattern','Linear');f.Originals=[p];f.Direction=(s,['H_Axis']);f.Mode='Extent';f.Length=8;f.Occurrences=2;d.recompute();print('LINEAR',info(f),flush=True);assert abs(f.Shape.Volume-1800)<1e-5
b,s,p=stock('PolarBody');f=b.newObject('PartDesign::PolarPattern','Polar');f.Originals=[p];f.Axis=(frame(b,'Z_Axis'),['']);f.Mode='Extent';f.Angle=360;f.Occurrences=4;d.recompute();print('POLAR',info(f),flush=True);assert abs(f.Shape.Volume-4000)<1e-5
b,s,p=stock('ScaleBody');f=b.newObject('PartDesign::Scaled','Scaled');f.Originals=[p];f.Factor=2;f.Occurrences=2;d.recompute();print('SCALED',info(f),flush=True);assert abs(f.Shape.Volume-8000)<1e-5
print('PASS original native pattern geometry proof; bounded mobile workflows NOT_IMPLEMENTED.',flush=True)
