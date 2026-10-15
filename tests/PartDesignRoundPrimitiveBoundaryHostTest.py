# SPDX-License-Identifier: LGPL-2.1-or-later
"""Native cone/sphere boundary evidence for the next mobile qualification."""
import math
import tempfile
from pathlib import Path
import FreeCAD as App
import PartDesign
import mobile_part

checks=0
observed={}
def check(value,message):
    global checks
    assert value,message
    checks+=1
def start(name):
    doc=App.newDocument(name);body=doc.addObject('PartDesign::Body','Body');body.AllowCompound=False
    return doc,body

mobile_part.configure()
for name,r1,r2,expected in [('ApexCone',0,2,4*math.pi),('EqualRadiiCone',1,1,3*math.pi)]:
    doc,body=start(name);obj=body.newObject('PartDesign::AdditiveCone','Cone')
    obj.Radius1=r1;obj.Radius2=r2;obj.Height=3;doc.recompute()
    check(obj.TypeId=='PartDesign::AdditiveCone','Original cone type retained')
    check(obj.Shape.isValid() and len(obj.Shape.Solids)==1 and obj.Shape.Solids[0].isClosed(),'Valid original cone/cylinder-equivalent solid')
    check(abs(obj.Shape.Volume-expected)<1e-7,'Native analytic apex/equal-radii cone volume')
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/(name+'.FCStd');doc.saveAs(str(path));App.closeDocument(doc.Name)
        doc=App.openDocument(str(path));doc.recompute()
        check(doc.Cone.Radius1.Value==r1 and doc.Cone.Radius2.Value==r2,'Restored original radius fields')
        check(abs(doc.Cone.Shape.Volume-expected)<1e-7,'Native apex/equal-radii restoration')
    App.closeDocument(doc.Name)
for kind in ('Cone','Sphere'):
    doc,body=start('PointContact'+kind)
    stock=body.newObject('PartDesign::AdditiveBox','Stock');stock.Length=10;stock.Width=10;stock.Height=5;doc.recompute()
    obj=body.newObject('PartDesign::Additive'+kind,'Touch')
    if kind=='Cone':obj.Radius1=0;obj.Radius2=2;obj.Height=3;obj.Placement.Base=App.Vector(5,5,5)
    else:obj.Radius=2;obj.Placement.Base=App.Vector(5,5,7)
    doc.recompute()
    check(body.AllowCompound is False,'Mobile single-solid Body policy')
    check(obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1 or 'Invalid' in obj.State or abs(obj.Shape.Volume)-abs(stock.Shape.Volume)<=1e-7,'Point-only contact cannot pass positive connected-solid validation')
    observed['point_contact_'+kind]=dict(state=list(obj.State),solids=len(obj.Shape.Solids) if not obj.Shape.isNull() else 0,material_delta_mm3=None if obj.Shape.isNull() else obj.Shape.Volume-stock.Shape.Volume)
    App.closeDocument(doc.Name)
for kind in ('Cone','Sphere'):
    doc,body=start('Zero'+kind);obj=body.newObject('PartDesign::Additive'+kind,'Zero')
    if kind=='Cone':obj.Radius1=0;obj.Radius2=0;obj.Height=3
    else:obj.Radius=0
    doc.recompute()
    check(obj.Shape.isNull() or not obj.Shape.isValid() or abs(obj.Shape.Volume)<=1e-7,'Zero-radius native output cannot satisfy positive valid material policy')
    observed['zero_'+kind]=dict(state=list(obj.State),valid=False if obj.Shape.isNull() else obj.Shape.isValid(),volume_mm3=None if obj.Shape.isNull() else obj.Shape.Volume)
    App.closeDocument(doc.Name)
results=dict(status='HOST_ORIGINAL_BOUNDARY_PROBE_PASS_MOBILE_PENDING',checks=checks,observed=observed,
             qualified=['zero base radius cone as a valid first native solid','equal cone radii retain the original cone class with native cylinder-equivalent geometry','true native FCStd reopening'],
             required_mobile_guards=['nonnegative cone radii with at least one positive radius; equal radii are supported by the native kernel','positive sphere radius before computation','one valid closed solid, positive material delta and explicit geometry validation; object state alone is insufficient'],
             mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
print('PASS original cone/sphere boundary checks:',checks,flush=True)
