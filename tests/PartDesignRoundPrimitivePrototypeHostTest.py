# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original cone/sphere feature proof. Mobile exposure is not asserted."""
import math
import tempfile
from pathlib import Path
import FreeCAD as App
import PartDesign
import mobile_part

checks=0
def check(value,message):
    global checks
    assert value,message
    checks+=1

mobile_part.configure();doc=App.newDocument('RoundPrimitiveProof')
body=doc.addObject('PartDesign::Body','Body')
stock=body.newObject('PartDesign::AdditiveBox','Stock')
stock.Length=10;stock.Width=10;stock.Height=10;doc.recompute()
sphere=body.newObject('PartDesign::AdditiveSphere','Dome')
sphere.Radius=2;sphere.Placement.Base=App.Vector(5,5,10);doc.recompute()
cone=body.newObject('PartDesign::AdditiveCone','Cone')
cone.Radius1=1;cone.Radius2=0;cone.Height=3;cone.Placement.Base=App.Vector(2,2,10);doc.recompute()
void=body.newObject('PartDesign::SubtractiveSphere','SphereCut')
void.Radius=1;void.Placement.Base=App.Vector(5,5,5);doc.recompute()
cut=body.newObject('PartDesign::SubtractiveCone','ConeCut')
cut.Radius1=1;cut.Radius2=0;cut.Height=3;cut.Placement.Base=App.Vector(2,2,0);doc.recompute()
for obj,previous,volume in [(sphere,stock,1000+16*math.pi/3),
                            (cone,sphere,1000+19*math.pi/3),
                            (void,cone,1000+5*math.pi),(cut,void,1000+4*math.pi)]:
    check('Invalid' not in obj.State and obj.Shape.isValid(),'Valid native feature')
    check(len(obj.Shape.Solids)==1 and obj.Shape.Solids[0].isClosed(),'Closed original solid')
    check(abs(obj.Shape.Volume-volume)<1e-5,'Analytic spherical/conical union or removal')
    check(obj.BaseFeature==previous,'Original preceding-solid history')
    check(obj.MapMode=='Deactivated' and obj.AttacherType=='Attacher::AttachEngine3D','Original manual primitive mapping')
    if obj.TypeId.endswith('Sphere'):
        check((obj.Angle1.Value,obj.Angle2.Value,obj.Angle3.Value)==(-90,90,360),'Full native sphere defaults')
    else:check(obj.Angle.Value==360,'Full native cone default')
check(body.Tip==cut,'Original solid Tip')
stock.Height=11;doc.recompute()
check(abs(cut.Shape.Volume-(1100-10*math.pi/27))<1e-5,'Native source clips spherical cap and conical tip')
cone.Height=6;doc.recompute()
check(abs(cut.Shape.Volume-(1100+53*math.pi/108))<1e-5,'Native cone height dependency')
doc.UndoMode=1;doc.openTransaction('Dome radius');sphere.Radius=3;doc.recompute();doc.commitTransaction()
check(cut.Shape.isValid() and cut.Shape.Volume>1100+53*math.pi/108,'Native sphere radius increases material')
doc.undo();doc.recompute()
check(abs(cut.Shape.Volume-(1100+53*math.pi/108))<1e-5,'Original native dimension Undo')
body.Placement=App.Placement(App.Vector(1,2,3),App.Rotation(30,20,10));doc.recompute()
check(abs(body.Shape.Volume-(1100+53*math.pi/108))<1e-5,'Body world transform preserves native volume')
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'RoundPrimitiveProof.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));doc.recompute()
    check(doc.Dome.BaseFeature==doc.Stock and doc.Cone.BaseFeature==doc.Dome and doc.SphereCut.BaseFeature==doc.Cone and doc.ConeCut.BaseFeature==doc.SphereCut,'Restored original references')
    check(doc.Body.Tip==doc.ConeCut and abs(doc.ConeCut.Shape.Volume-(1100+53*math.pi/108))<1e-5,'Restored native geometry')
    App.closeDocument(doc.Name)
results=dict(status='HOST_ORIGINAL_ROUND_PRIMITIVE_PROBE_PASS_MOBILE_PENDING',checks=checks,
             types=['PartDesign::AdditiveCone','PartDesign::SubtractiveCone','PartDesign::AdditiveSphere','PartDesign::SubtractiveSphere'],
             geometry='analytic hemisphere/cone and spherical-cap/conical-tip clipping, source dimensions, Undo, Body placement and true FCStd reopen',
             mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
print('PASS original cone/sphere prototype checks:',checks,flush=True)
