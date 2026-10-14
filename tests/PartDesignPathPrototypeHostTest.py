# SPDX-License-Identifier: LGPL-2.1-or-later
"""Host-only original Pipe/Helix prototype; mobile integration remains pending."""
import FreeCAD as A,Part,Sketcher,PartDesign,mobile_part,math,json
mobile_part.configure();d=A.newDocument("Extents")
def profile(b,name,z=0,circle=False):
 s=b.newObject("Sketcher::SketchObject",name);s.Placement.Base=A.Vector(0,0,z)
 if circle:s.addGeometry(Part.Circle(A.Vector(5,5,0),A.Vector(0,0,1),1),False)
 else:
  p=[A.Vector(0,0,0),A.Vector(10,0,0),A.Vector(10,10,0),A.Vector(0,10,0)]
  s.addGeometry([Part.LineSegment(p[i],p[(i+1)%4]) for i in range(4)],False)
 return s
def fresh(name):
 b=d.addObject("PartDesign::Body",name);b.AllowCompound=False;return b
def feature(b,s,name,kind,mode="Length",side="One side",reversed=False,face=None):
 f=b.newObject("PartDesign::"+kind,name);f.Profile=(s,[]);f.Type=mode;f.SideType=side;f.Reversed=reversed;f.Length=10
 if face:f.UpToFace=face
 d.recompute();return f
def info(f):
 sh=f.Shape;return dict(type=f.TypeId,mode=f.Type,side=f.SideType,reversed=f.Reversed,status=f.getStatusString(),volume=sh.Volume,bounds=[sh.BoundBox.ZMin,sh.BoundBox.ZMax],valid=sh.isValid(),properties={p:repr(getattr(f,p)) for p in ["Type2","Length2","TaperAngle","Offset","AlongSketchNormal","UseCustomVector","Midplane","UpToFace","UpToFace2","ReferenceAxis"]})
results={}
def pipe(label,kind,stock=False):
 b=fresh(label)
 if stock:
  s=profile(b,label+"Base");base=feature(b,s,label+"Pad","Pad")
 s=b.newObject("Sketcher::SketchObject",label+"Section");s.addGeometry(Part.Circle(A.Vector(5,5,0) if stock else A.Vector(0,0,0),A.Vector(0,0,1),1),False)
 path=b.newObject("Sketcher::SketchObject",label+"Path");path.Placement=A.Placement(A.Vector(5,5,0) if stock else A.Vector(0,0,0),A.Rotation(A.Vector(1,0,0),90));path.addGeometry(Part.LineSegment(A.Vector(0,0,0),A.Vector(0,10,0)),False)
 f=b.newObject("PartDesign::"+kind,label+"Feature");f.Profile=(s,[]);f.Spine=(path,["Edge1"]);f.Mode="Standard";f.Transition="Transformed";f.Transformation="Constant";d.recompute()
 print(label,f.TypeId,f.getStatusString(),f.Shape.Volume,f.PropertiesList,flush=True)
 assert f.Shape.isValid() and len(f.Shape.Solids)==1
 expected=1000-10*math.pi if stock else 10*math.pi;assert abs(f.Shape.Volume-expected)<1e-5
 results[label]=dict(type=f.TypeId,volume_mm3=f.Shape.Volume,expected_volume_mm3=expected,mode=f.Mode,transition=f.Transition,transformation=f.Transformation,spine_subs=list(f.Spine[1]))
pipe("AddPipe","AdditivePipe");pipe("CutPipe","SubtractivePipe",True)
# Axis from the original Body, profile plane XZ and radial placement.
for label,kind in [("AddHelix","AdditiveHelix"),("CutHelix","SubtractiveHelix")]:
 b=fresh(label)
 if kind=="SubtractiveHelix":
  base=b.newObject("Sketcher::SketchObject",label+"Base");base.addGeometry(Part.Circle(A.Vector(0,0,0),A.Vector(0,0,1),6),False);pad=feature(b,base,label+"Pad","Pad")
 s=b.newObject("Sketcher::SketchObject",label+"Section");s.Placement=A.Placement(A.Vector(0,0,0),A.Rotation(A.Vector(1,0,0),90));s.addGeometry(Part.Circle(A.Vector(5,0,0),A.Vector(0,0,1),0.5),False)
 if kind=="SubtractiveHelix":s.Placement.Base=A.Vector(0,0,2)
 f=b.newObject("PartDesign::"+kind,label+"Feature");f.Profile=(s,[]);axis=next(o for o in b.Origin.OriginFeatures if o.Role=="Z_Axis");f.ReferenceAxis=(axis,[""]);f.Mode="pitch-height-angle";f.Pitch=3;f.Height=6;f.Angle=0;f.HasBeenEdited=True;d.recompute()
 print(label,f.TypeId,f.getStatusString(),f.Shape.Volume if not f.Shape.isNull() else None,{n:repr(getattr(f,n)) for n in ['Mode','Pitch','Height','Turns','ReferenceAxis','Axis','Base']},flush=True)
 assert f.Shape.isValid() and len(f.Shape.Solids)==1
 expected=5*math.pi*math.pi if kind=="AdditiveHelix" else 360*math.pi-5*math.pi*math.pi
 assert abs(f.Shape.Volume-expected)<1e-3
 results[label]=dict(type=f.TypeId,volume_mm3=f.Shape.Volume,ideal_axis_meridian_volume_mm3=expected,native_integration_tolerance_mm3=1e-3,pitch_mm=f.Pitch.Value,height_mm=f.Height.Value,turns=f.Turns,mode=f.Mode,axis_role=f.ReferenceAxis[0].Role)
results.update(status="HOST_NATIVE_API_PROBE_PASS_MOBILE_PENDING",mobile_integration="NOT_IMPLEMENTED",android_execution="NOT_RUN",freecad="1.1.4")
print("PASS original Pipe/Helix native class/property/geometry prototype",flush=True)
