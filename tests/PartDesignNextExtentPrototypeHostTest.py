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
for label,mode in [("PadFace","UpToFace"),("PadLast","UpToLast")]:
 b=fresh(label);base=profile(b,label+"Base");p=feature(b,base,label+"Pad","Pad");s=b.newObject("Sketcher::SketchObject",label+"Profile");s.addGeometry(Part.Circle(A.Vector(10,5,0),A.Vector(0,0,1),1),False)
 top=next(i+1 for i,f in enumerate(p.Shape.Faces) if abs(f.CenterOfMass.z-10)<1e-6 and abs(f.normalAt(0,0).z)>0.99)
 f=feature(b,s,label+"Feature","Pad",mode,face=(p,["Face"+str(top)]) if mode=="UpToFace" else None);v=info(f);print(label,v,flush=True);assert f.Shape.isValid() and len(f.Shape.Solids)==1;assert abs(f.Shape.Volume-(1000+5*math.pi))<1e-5;results[label]=v
b=fresh("PocketFirst");base=profile(b,"PocketFirstBase");p=feature(b,base,"PocketFirstPad","Pad");s=profile(b,"PocketFirstProfile",8,True);f=feature(b,s,"PocketFirstFeature","Pocket","UpToFirst");v=info(f);print("PocketFirst",v,flush=True);assert abs(f.Shape.Volume-(1000-8*math.pi))<1e-5;results["PocketFirst"]=v
b=fresh("TwoSided");s=profile(b,"TwoSidedProfile");f=b.newObject("PartDesign::Pad","TwoSidedPad");f.Profile=(s,[]);f.Type="Length";f.Type2="Length";f.SideType="Two sides";f.Length=4;f.Length2=6;d.recompute();v=info(f);print("TwoSided",v,flush=True);assert f.Shape.isValid() and abs(f.Shape.Volume-1000)<1e-5;assert all(abs(x-y)<1e-6 for x,y in zip(v["bounds"],[-6,4]));results["TwoSided"]=v
results.update(status="HOST_NATIVE_API_PROBE_PASS_MOBILE_PENDING",mobile_integration="NOT_IMPLEMENTED",android_execution="NOT_RUN",freecad="1.1.4")
print("PASS original PadUpToFace/UpToLast/PocketUpToFirst/TwoSides reference geometries",flush=True)
