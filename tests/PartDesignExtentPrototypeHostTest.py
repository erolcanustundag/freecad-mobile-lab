# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original 1.1.4 extent property and analytic geometry reference proof."""
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
for label,side,rev,expected in [("ReversePad","One side",True,[-10,0]),("SymmetricPad","Symmetric",False,[-5,5])]:
 b=fresh(label);s=profile(b,label+"Profile");p=feature(b,s,label+"Feature","Pad",side=side,reversed=rev);v=info(p);print(label,v,flush=True);assert abs(p.Shape.Volume-1000)<1e-5;assert all(abs(x-y)<1e-6 for x,y in zip(v["bounds"],expected));results[label]=v
for label,z,mode,side,rev,depth in [("ReversePocket",0,"Length","One side",True,10),("SymmetricPocket",5,"Length","Symmetric",False,10),("ThroughPocket",10,"ThroughAll","One side",False,10),("FacePocket",8,"UpToFace","One side",False,8)]:
 b=fresh(label);s=profile(b,label+"Base");p=feature(b,s,label+"Pad","Pad");hole=profile(b,label+"Profile",z,True);face=None
 if mode=="UpToFace":
  i=next(i+1 for i,f in enumerate(p.Shape.Faces) if abs(f.CenterOfMass.z)<1e-6 and abs(f.normalAt(0,0).z)>0.99);face=(p,["Face"+str(i)])
 f=feature(b,hole,label+"Feature","Pocket",mode,side,rev,face);v=info(f);print(label,v,flush=True);assert f.Shape.isValid() and len(f.Shape.Solids)==1;assert abs(f.Shape.Volume-(1000-math.pi*depth))<1e-5;results[label]=v
results["status"]="PASS";results["android_execution"]="NOT_RUN";
print("PASS native reversed/symmetric/ThroughAll/UpToFace analytic geometries",flush=True)
