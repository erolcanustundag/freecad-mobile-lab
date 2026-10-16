# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original torus/prism classes, analytic material and history proof."""
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
d=App.newDocument('TorusPrismProof');b=d.addObject('PartDesign::Body','Body');b.AllowCompound=False
s=b.newObject('PartDesign::AdditiveBox','Stock');s.Length=30;s.Width=30;s.Height=10;d.recompute()
p=b.newObject('PartDesign::AdditivePrism','Boss');p.Polygon=6;p.Circumradius=2;p.Height=3;p.Placement.Base=App.Vector(5,5,10);d.recompute();valid(p,9000+18*math.sqrt(3))
t=b.newObject('PartDesign::AdditiveTorus','Ring');t.Radius1=2;t.Radius2=.5;t.Placement.Base=App.Vector(20,20,10);d.recompute();valid(t,9000+18*math.sqrt(3)+.5*math.pi**2)
c=b.newObject('PartDesign::SubtractivePrism','Notch');c.Polygon=4;c.Circumradius=1;c.Height=2;c.Placement.Base=App.Vector(5,5,0);d.recompute();valid(c,8996+18*math.sqrt(3)+.5*math.pi**2)
r=b.newObject('PartDesign::SubtractiveTorus','Channel');r.Radius1=2;r.Radius2=.25;r.Placement.Base=App.Vector(20,20,5);d.recompute();v=8996+18*math.sqrt(3)+.25*math.pi**2;valid(r,v)
for o,prev in [(p,s),(t,p),(c,t),(r,c)]:
 check(o.BaseFeature==prev,'Original preceding BaseFeature')
 check(o.MapMode=='Deactivated' and o.AttacherType=='Attacher::AttachEngine3D','Native mapping')
 check((o.Angle1.Value,o.Angle2.Value,o.Angle3.Value)==(-180,180,360) if o.TypeId.endswith('Torus') else (o.FirstAngle.Value,o.SecondAngle.Value)==(0,0),'Native angular defaults')
check(b.Tip==r,'Native Tip')
d.UndoMode=1;d.openTransaction('Ring radius');t.Radius1=3;d.recompute();d.commitTransaction();valid(r,8996+18*math.sqrt(3)+.5*math.pi**2);d.undo();d.recompute();valid(r,v)
p.Polygon=4;d.recompute();valid(r,9020+.25*math.pi**2)
s.Length=31;d.recompute();valid(r,9320+.25*math.pi**2)
b.Placement=App.Placement(App.Vector(1,2,3),App.Rotation(30,20,10));d.recompute();valid(b,9320+.25*math.pi**2)
with tempfile.TemporaryDirectory() as td:
 path=Path(td)/'OriginalTorusPrism.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));d.recompute();valid(d.Body,9320+.25*math.pi**2)
 check(d.Channel.BaseFeature==d.Notch and d.Notch.BaseFeature==d.Ring and d.Ring.BaseFeature==d.Boss and d.Boss.BaseFeature==d.Stock,'True native restoration')
 check(d.Boss.TypeId=='PartDesign::AdditivePrism' and d.Channel.TypeId=='PartDesign::SubtractiveTorus','Original classes retained');App.closeDocument(d.Name)
result=dict(status='HOST_ORIGINAL_TORUS_PRISM_PROBE_PASS_MOBILE_PENDING',checks=checks,types=['PartDesign::'+x for x in ['AdditivePrism','SubtractivePrism','AdditiveTorus','SubtractiveTorus']],mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
print(json.dumps(result,indent=2));Path('docs/native-partdesign-torus-prism-prototype-results.json').write_text(json.dumps(result,indent=2)+'\n')
