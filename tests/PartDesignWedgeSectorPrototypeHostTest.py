# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original wedge and round-sector proof; mobile integration is not asserted."""
import math,tempfile,json
from pathlib import Path
import FreeCAD as App
import PartDesign,mobile_part
mobile_part.configure();checks=0

def check(v,msg):
 global checks
 assert v,msg
 checks+=1

def valid(o,volume):
 check(o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.Solids[0].isClosed(),'Closed original solid')
 check(abs(o.Shape.Volume-volume)<1e-5,'Analytic wedge/sector material')

def wedge(body,kind,name,x,y,z,x2,pose):
 o=body.newObject('PartDesign::'+kind,name)
 for field,value in dict(Xmin=0,Xmax=x,Ymin=0,Ymax=y,Zmin=0,Zmax=z,X2min=0,X2max=x2,Z2min=0,Z2max=z).items():setattr(o,field,value)
 o.Placement.Base=App.Vector(*pose);return o

d=App.newDocument('WedgeSectorProof');b=d.addObject('PartDesign::Body','Body');b.AllowCompound=False
s=b.newObject('PartDesign::AdditiveBox','Stock');s.Length=30;s.Width=30;s.Height=10;d.recompute()
w=wedge(b,'AdditiveWedge','Wedge',4,3,2,2,(5,5,10));d.recompute();valid(w,9018)
c=wedge(b,'SubtractiveWedge','WedgeCut',2,3,2,1,(5,5,0));d.recompute();valid(c,9009)
k=b.newObject('PartDesign::AdditiveCone','ConeSector');k.Radius1=1;k.Radius2=0;k.Height=3;k.Angle=180;k.Placement.Base=App.Vector(20,20,10);d.recompute();valid(k,9009+.5*math.pi)
q=b.newObject('PartDesign::AdditiveSphere','SphereSector');q.Radius=1;q.Angle1=0;q.Angle2=90;q.Angle3=180;q.Placement.Base=App.Vector(10,20,10);d.recompute();valid(q,9009+5*math.pi/6)
for o,previous in [(w,s),(c,w),(k,c),(q,k)]:
 check(o.BaseFeature==previous,'Original preceding BaseFeature')
 check(o.MapMode=='Deactivated','Native manual mapping')
check(b.Tip==q,'Native Tip')
d.UndoMode=1;d.openTransaction('Cone sector');k.Angle=90;d.recompute();d.commitTransaction();valid(q,9009+7*math.pi/12);d.undo();d.recompute();valid(q,9009+5*math.pi/6)
q.Angle2=30;d.recompute();valid(q,9009+35*math.pi/48)
w.Xmax=6;d.recompute();valid(q,9015+35*math.pi/48)
b.Placement=App.Placement(App.Vector(1,2,3),App.Rotation(30,20,10));d.recompute();valid(b,9015+35*math.pi/48)
with tempfile.TemporaryDirectory() as td:
 path=Path(td)/'WedgeSector.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));d.recompute();valid(d.Body,9015+35*math.pi/48)
 check(d.WedgeCut.BaseFeature==d.Wedge and d.ConeSector.BaseFeature==d.WedgeCut and d.SphereSector.BaseFeature==d.ConeSector,'True restored references')
 check(d.ConeSector.Angle.Value==180 and d.SphereSector.Angle2.Value==30,'Native angles restored');App.closeDocument(d.Name)
r=dict(status='HOST_ORIGINAL_WEDGE_SECTOR_PROBE_PASS_MOBILE_PENDING',checks=checks,scopes=['PartDesign::AdditiveWedge','PartDesign::SubtractiveWedge','original Cone angular sector','original Sphere latitude/azimuth segment'],mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
Path('docs/native-partdesign-wedge-sector-prototype-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
