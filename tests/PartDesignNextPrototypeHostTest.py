# SPDX-License-Identifier: LGPL-2.1-or-later
"""Host-only next PartDesign API proof; mobile integration remains pending."""
import FreeCAD as A,Part,Sketcher,PartDesign,mobile_part,json,math
# Host reference only: original module prerequisites must be restored.
mobile_part.configure()
def sketch(b,name,kind='rectangle',z=0,r=1):
 s=b.newObject('Sketcher::SketchObject',name);s.Placement.Base=A.Vector(0,0,z)
 if kind=='rectangle':
  p=[A.Vector(10,0,0),A.Vector(12,0,0),A.Vector(12,5,0),A.Vector(10,5,0)]
  s.addGeometry([Part.LineSegment(p[i],p[(i+1)%4]) for i in range(4)],False)
 else:s.addGeometry(Part.Circle(A.Vector(11,2,0) if kind=='groove' else A.Vector(),A.Vector(0,0,1),r),False)
 return s
d=A.newDocument('NextPartDesignProof');b=d.addObject('PartDesign::Body','RotationalBody');b.AllowCompound=False;s=sketch(b,'Profile')
f=b.newObject('PartDesign::Revolution','Revolution');f.Profile=(s,[]);f.ReferenceAxis=(s,['V_Axis']);f.Angle=360;d.recompute()
print('REVPROPS',[(n,f.getTypeIdOfProperty(n),str(getattr(f,n))) for n in ['Angle','Angle2','Type','Midplane','Reversed','ReferenceAxis']],flush=True);print('REVOLUTION',list(f.State),f.Type,f.Shape.Volume,f.Shape.isValid(),flush=True);assert abs(f.Shape.Volume-220*math.pi)<1e-5
c=sketch(b,'Cut','groove',r=.3);g=b.newObject('PartDesign::Groove','Groove');g.Profile=(c,[]);g.ReferenceAxis=(c,['V_Axis']);g.Angle=360;d.recompute()
print('GROOVE',list(g.State),g.Type,g.Shape.Volume,g.Shape.isValid(),flush=True);assert abs(g.Shape.Volume-(220*math.pi-2*math.pi**2*11*.09))<1e-5
b=d.addObject('PartDesign::Body','LoftBody');b.AllowCompound=False;s=sketch(b,'Lower','circle',0,2);t=sketch(b,'Upper','circle',5,1);f=b.newObject('PartDesign::AdditiveLoft','AdditiveLoft');f.Profile=(s,[]);f.Sections=[(t,[''])];f.Ruled=True;d.recompute()
print('LOFTSTATUS',list(f.State),f.getStatusString(),str(f.Sections),f.Shape.isNull(),flush=True);print('ADDLOFT',f.Shape.Volume,f.Shape.isValid(),flush=True);assert abs(f.Shape.Volume-35*math.pi/3)<1e-5
s=sketch(b,'BoreLower','circle',0,.4);t=sketch(b,'BoreUpper','circle',5,.2);g=b.newObject('PartDesign::SubtractiveLoft','SubtractiveLoft');g.Profile=(s,[]);g.Sections=[(t,[''])];g.Ruled=True;d.recompute()
print('SUBLOFT',list(g.State),str(g.Sections),g.Shape.Volume,g.Shape.isValid(),flush=True);assert abs(g.Shape.Volume-(35*math.pi/3-1.4*math.pi/3))<1e-5
print('PASS original Revolution/Groove/AdditiveLoft/SubtractiveLoft API/analytic host proof. Mobile controls/Android workflows NOT_IMPLEMENTED.',flush=True)
