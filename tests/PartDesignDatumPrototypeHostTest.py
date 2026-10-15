# SPDX-License-Identifier: LGPL-2.1-or-later
"""Native construction/attachment proof, deliberately outside the mobile whitelist."""
import FreeCAD as App,Part,Sketcher,PartDesign,mobile_part,math,tempfile
from pathlib import Path
mobile_part.configure();doc=App.newDocument('DatumProof');body=doc.addObject('PartDesign::Body','Body')
items={name:body.newObject('PartDesign::'+name,name) for name in ('Plane','Line','Point','CoordinateSystem')}
plane=items['Plane'];plane.Placement.Base=App.Vector(1,2,3)
line=items['Line'];line.Placement=App.Placement(App.Vector(2,3,4),App.Rotation(App.Vector(0,1,0),90))
point=items['Point'];point.Placement.Base=App.Vector(3,4,5)
system=items['CoordinateSystem'];system.Placement.Base=App.Vector(4,5,6)
sketch=body.newObject('Sketcher::SketchObject','Profile');sketch.AttachmentSupport=[(plane,[''])];sketch.MapMode='ObjectXY'
sketch.addGeometry(Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),1),False)
pad=body.newObject('PartDesign::Pad','Pad');pad.Profile=(sketch,[]);pad.Length=5
other=body.newObject('Sketcher::SketchObject','SystemProfile');other.AttachmentSupport=[(system,[''])];other.MapMode='ObjectXY';other.addGeometry(Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),1),False)
doc.recompute()
assert body.Tip==pad and pad.Shape.isValid() and abs(pad.Shape.Volume-5*math.pi)<1e-6
assert (sketch.Placement.Base-plane.Placement.Base).Length<1e-9 and (other.Placement.Base-system.Placement.Base).Length<1e-9
assert (point.Shape.Vertexes[0].Point-point.Placement.Base).Length<1e-9
direction=line.Placement.Rotation.multVec(App.Vector(0,0,1));assert abs(line.Shape.Edges[0].Curve.Direction.dot(direction))>1-1e-9
assert len(plane.Shape.Faces)==1 and len(plane.Shape.Edges)==0 and len(line.Shape.Edges[0].Vertexes)==0
plane.Placement=App.Placement(App.Vector(5,6,7),App.Rotation(App.Vector(0,1,0),30));doc.recompute()
expected=plane.Placement.multVec(App.Vector(0,0,2.5));assert (pad.Shape.CenterOfMass-expected).Length<1e-6
assert abs(pad.Shape.Volume-5*math.pi)<1e-6
type_ids=[o.TypeId for o in items.values()];pad_volume=pad.Shape.Volume
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'DatumProof.FCStd';doc.saveAs(str(path));App.closeDocument(doc.Name)
    copy=App.openDocument(str(path));copy.recompute()
    assert copy.Profile.AttachmentSupport[0][0]==copy.Plane and copy.Profile.MapMode=='ObjectXY'
    assert copy.SystemProfile.AttachmentSupport[0][0]==copy.CoordinateSystem
    assert (copy.Pad.Shape.CenterOfMass-expected).Length<1e-6
    App.closeDocument(copy.Name)
results=dict(status='HOST_NATIVE_CONSTRUCTION_ATTACHMENT_PROBE_PASS_MOBILE_PENDING',types=type_ids,attachment='original ObjectXY on owned Plane and CoordinateSystem',pad_volume_mm3=pad_volume,expected_pad_volume_mm3=5*math.pi,source_translation_rotation='PASS',native_fcstd_restore='PASS',plane_and_axis='unbounded analytical geometry; construction-specific preview/validation required',mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
print('PASS original Datum types/analytic geometry/ObjectXY/linked Pad/source movement/native FCStd',flush=True)
