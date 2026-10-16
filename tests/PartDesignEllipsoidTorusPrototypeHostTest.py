# SPDX-License-Identifier: LGPL-2.1-or-later
"""Prove original ellipsoid/torus APIs and geometry before mobile integration."""
import math,tempfile,json
from pathlib import Path
import FreeCAD as App
import PartDesign,mobile_part
mobile_part.configure();checks=0
def check(v,why):
 global checks
 assert v,why
 checks+=1

def valid(o,v):
 check(o.Shape.isValid() and len(o.Shape.Solids)==1 and o.Shape.Solids[0].isClosed(),'Original closed solid')
 check(abs(o.Shape.Volume-v)<1e-5,'Analytic native material volume: '+str(o.Shape.Volume)+' / '+str(v))
d=App.newDocument('EllipsoidTorusProof');b=d.addObject('PartDesign::Body','Body');b.AllowCompound=False
s=b.newObject('PartDesign::AdditiveBox','Stock');s.Length=30;s.Width=30;s.Height=10;d.recompute()
e=b.newObject('PartDesign::AdditiveEllipsoid','Dome');e.Radius1=2;e.Radius2=1;e.Radius3=1;e.Placement.Base=App.Vector(5,5,10);d.recompute();valid(e,9000+4*math.pi/3)
t=b.newObject('PartDesign::AdditiveTorus','Ring');t.Radius1=2;t.Radius2=.5;t.Placement.Base=App.Vector(20,20,10);d.recompute();valid(t,9000+4*math.pi/3+.5*math.pi**2)
c=b.newObject('PartDesign::SubtractiveEllipsoid','Void');c.Radius1=1;c.Radius2=.5;c.Radius3=.5;c.Placement.Base=App.Vector(5,5,5);d.recompute();valid(c,9000+math.pi+.5*math.pi**2)
r=b.newObject('PartDesign::SubtractiveTorus','Channel');r.Radius1=2;r.Radius2=.25;r.Placement.Base=App.Vector(20,20,5);d.recompute();v=9000+math.pi+.25*math.pi**2;valid(r,v)
for o,prev in [(e,s),(t,e),(c,t),(r,c)]:
 check(o.BaseFeature==prev,'Original preceding BaseFeature')
 check(o.MapMode=='Deactivated' and o.AttacherType=='Attacher::AttachEngine3D','Native mapping')
 check((o.Angle1.Value,o.Angle2.Value,o.Angle3.Value)==((-180,180,360) if o.TypeId.endswith('Torus') else (-90,90,360)),'Native full angular defaults')
check(b.Tip==r,'Native Tip')
d.UndoMode=1;d.openTransaction('Ring radius');t.Radius1=3;d.recompute();d.commitTransaction();valid(r,9000+math.pi+.5*math.pi**2);d.undo();d.recompute();valid(r,v)
e.Radius3=2;d.recompute();valid(r,9000+7*math.pi/3+.25*math.pi**2)
s.Length=31;d.recompute();valid(r,9300+7*math.pi/3+.25*math.pi**2)
b.Placement=App.Placement(App.Vector(1,2,3),App.Rotation(30,20,10));d.recompute();valid(b,9300+7*math.pi/3+.25*math.pi**2)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'OriginalEllipsoidTorus.FCStd';d.saveAs(str(p));App.closeDocument(d.Name);d=App.openDocument(str(p));d.recompute();valid(d.Body,9300+7*math.pi/3+.25*math.pi**2)
 check(d.Channel.BaseFeature==d.Void and d.Void.BaseFeature==d.Ring and d.Ring.BaseFeature==d.Dome and d.Dome.BaseFeature==d.Stock,'True native restoration')
 check(d.Dome.TypeId=='PartDesign::AdditiveEllipsoid' and d.Channel.TypeId=='PartDesign::SubtractiveTorus','Original classes retained');App.closeDocument(d.Name)
result=dict(status='HOST_ORIGINAL_ELLIPSOID_TORUS_PROBE_PASS_MOBILE_PENDING',checks=checks,types=['PartDesign::'+x for x in ['AdditiveEllipsoid','SubtractiveEllipsoid','AdditiveTorus','SubtractiveTorus']],mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
print(json.dumps(result,indent=2));Path('docs/native-partdesign-ellipsoid-torus-prototype-results.json').write_text(json.dumps(result,indent=2)+'\n')
