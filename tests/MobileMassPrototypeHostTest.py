# SPDX-License-Identifier: LGPL-2.1-or-later
"""Exercise the experimental CPython/OCCT bridge; not a mobile capability."""
import sys,math,tempfile,json
from pathlib import Path
import FreeCAD as App
import Part,mobile_part
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'mobile-mass-host'));import _mobile_gprops as mass
mobile_part.configure();checks=0

def check(v,msg):
 global checks
 assert v,msg
 checks+=1

def data(shape):
 text=shape.exportBrepToString()
 return text.encode('utf-8') if isinstance(text,str) else text

def reject(callback):
 try:callback()
 except (ValueError,RuntimeError,TypeError):check(True,'Rejected unsupported request');return
 raise AssertionError('Expected rejection')

box=Part.makeBox(2,3,4);r=mass.measure(data(box));check(abs(r['volume']-24)<1e-8,'Analytic box volume');check(all(abs(a-b)<1e-8 for a,b in zip(r['centroid'],[1,1.5,2])),'Analytic centroid');check(r['faces']==6 and r['edges']==12,'Unique topology counts')
pose=App.Placement(App.Vector(10,-20,30),App.Rotation(30,20,10));box.Placement=pose;r=mass.measure(data(box));point=pose.multVec(App.Vector(1,1.5,2));check(all(abs(a-b)<1e-7 for a,b in zip(r['centroid'],point)),'World pose centroid');check(abs(r['volume']-24)<1e-8,'Rigid transform volume')
box.reverse();r=mass.measure(data(box));check(abs(r['volume']-24)<1e-8 and r['signed_volume']<0,'Orientation sign separate from material volume')
for eps in [0,1e-11,.001,float('nan'),float('inf')]:reject(lambda:mass.measure(data(box),eps))
reject(lambda:mass.measure(b''));reject(lambda:mass.measure(b'not a BRep'));reject(lambda:mass.measure(b'x'*(4*1024*1024+1)));reject(lambda:mass.measure('not bytes'));reject(lambda:mass.measure(data(Part.makePlane(2,2))))
far=Part.makeBox(1,1,1,App.Vector(1000001,0,0));reject(lambda:mass.measure(data(far)))
for sides in [62,63]:
 points=[App.Vector(math.cos(2*math.pi*i/sides),math.sin(2*math.pi*i/sides),0) for i in range(sides)];points.append(points[0]);prism=Part.Face(Part.makePolygon(points)).extrude(App.Vector(0,0,1))
 if sides==63:reject(lambda:mass.measure(data(prism)))
 else:
  r=mass.measure(data(prism));check(r['faces']==64 and abs(r['volume']-sides/2*math.sin(2*math.pi/sides))<1e-8,'Real64face boundary')
import PartDesign
d=App.newDocument('MassPrototype');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveEllipsoid','Ellipsoid');o.Radius1=2;o.Radius2=1;o.Radius3=1;d.recompute();r=mass.measure(data(o.Shape),1e-10);ideal=8*math.pi/3;coarse=o.Shape.Volume
check(abs(r['volume']-ideal)*1000<abs(coarse-ideal),'Adaptive native ellipsoid improvement');check(r['estimated_relative_integration_error']<=1e-10,'Requested integration estimate');observed=dict(r,analytic_volume=ideal,default_native_volume=coarse,ideal_volume_discrepancy=abs(r['volume']-ideal))
with tempfile.TemporaryDirectory() as td:
 path=Path(td)/'MassPrototype.FCStd';d.saveAs(str(path));App.closeDocument(d.Name);d=App.openDocument(str(path));d.recompute();restored=mass.measure(data(d.Ellipsoid.Shape),1e-10);check(abs(restored['volume']-r['volume'])<1e-10,'Native FCStd/BRep roundtrip');App.closeDocument(d.Name)
result=dict(status='HOST_NATIVE_MASS_PROTOTYPE_PASS_MOBILE_NOT_IMPLEMENTED',checks=checks,ellipsoid_observation=observed,android_execution='NOT_RUN',mobile_integration='NOT_IMPLEMENTED',limits=dict(brep_bytes=4*1024*1024,faces=64,edges=256,world_coordinate_mm=1000000,relative_tolerance=[1e-10,1e-4]),pending=['production integration and consistent material validation','Android execution and malformed/geometry/performance qualification','ellipsoid factories/angles and JNI/cold/UI qualification'])
(ROOT/'docs/native-mass-adapter-prototype-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
