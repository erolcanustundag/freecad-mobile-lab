# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original additive/subtractive box/cylinder proof; mobile exposure pending."""
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

mobile_part.configure()
doc=App.newDocument('PrimitiveProof')
body=doc.addObject('PartDesign::Body','Body')
box=body.newObject('PartDesign::AdditiveBox','Box')
box.Length=10;box.Width=10;box.Height=10
doc.recompute()
cylinder=body.newObject('PartDesign::AdditiveCylinder','Boss')
cylinder.Radius=2;cylinder.Height=4;cylinder.Angle=360
cylinder.Placement.Base=App.Vector(5,5,10)
doc.recompute()
cutbox=body.newObject('PartDesign::SubtractiveBox','Notch')
cutbox.Length=2;cutbox.Width=2;cutbox.Height=5
cutbox.Placement.Base=App.Vector(1,1,0)
doc.recompute()
cutcyl=body.newObject('PartDesign::SubtractiveCylinder','Bore')
cutcyl.Radius=1;cutcyl.Height=6;cutcyl.Angle=360
cutcyl.Placement.Base=App.Vector(5,5,0)
doc.recompute()
for obj,source,volume in [(box,None,1000),(cylinder,box,1000+16*math.pi),
                           (cutbox,cylinder,980+16*math.pi),(cutcyl,cutbox,980+10*math.pi)]:
    check('Invalid' not in obj.State and obj.Shape.isValid(),'Valid original primitive result')
    check(len(obj.Shape.Solids)==1 and obj.Shape.Solids[0].isClosed(),'Closed original solid')
    check(abs(obj.Shape.Volume-volume)<1e-5,'Analytic union/removal volume')
    check(obj.BaseFeature==source,'Original history dependency')
    check(obj.MapMode=='Deactivated' and not obj.AttachmentSupport,'Manual original feature placement')
    check(obj.AttacherType=='Attacher::AttachEngine3D','Original primitive attachment engine')
check(body.Tip==cutcyl,'Original last solid Tip')
box.Height=12;doc.recompute()
check(abs(cutcyl.Shape.Volume-(1180+2*math.pi))<1e-5,'Native source resize changes dependent overlap')
cylinder.Height=6;doc.recompute()
check(abs(cutcyl.Shape.Volume-(1180+10*math.pi))<1e-5,'Native primitive dimension edits')
doc.UndoMode=1;doc.openTransaction('Primitive radius');cutcyl.Radius=1.5;doc.recompute();doc.commitTransaction()
check(abs(cutcyl.Shape.Volume-(1180+16*math.pi-13.5*math.pi))<1e-5,'Native bore radius changes removal')
doc.undo();doc.recompute();check(abs(cutcyl.Shape.Volume-(1180+10*math.pi))<1e-5,'Native primitive Undo')
body.Placement=App.Placement(App.Vector(1,2,3),App.Rotation(30,20,10));doc.recompute()
check(abs(body.Shape.Volume-(1180+10*math.pi))<1e-5,'Native Body/world transform')
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'PrimitiveProof.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
    doc=App.openDocument(str(path));doc.recompute()
    check(doc.Boss.BaseFeature==doc.Box and doc.Notch.BaseFeature==doc.Boss and doc.Bore.BaseFeature==doc.Notch,'Restored original history links')
    check(doc.Body.Tip==doc.Bore and abs(doc.Bore.Shape.Volume-(1180+10*math.pi))<1e-5,'Restored original solid')
    check((doc.Body.Placement.Base-App.Vector(1,2,3)).Length<1e-8,'Restored native Body placement')
    App.closeDocument(doc.Name)
results=dict(status='HOST_ORIGINAL_PRIMITIVE_PROBE_PASS_MOBILE_PENDING',checks=checks,
             types=['PartDesign::AdditiveBox','PartDesign::SubtractiveBox','PartDesign::AdditiveCylinder','PartDesign::SubtractiveCylinder'],
             geometry='analytic native unions/removal, source overlap, dimensions, Undo, Body placement and true FCStd reopen',
             mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
print('PASS original primitive prototype checks:',checks,flush=True)
