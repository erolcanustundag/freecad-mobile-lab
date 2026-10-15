# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original attachment proof. Does not assert mobile/JNI/device support."""
import math
import tempfile
from pathlib import Path
import FreeCAD as App
import Part
import PartDesign
import Sketcher
import mobile_part

checks = 0
def check(condition, message):
    global checks
    assert condition, message
    checks += 1

mobile_part.configure()
doc = App.newDocument('AttachmentProof')
body = doc.addObject('PartDesign::Body', 'Body')
profile = body.newObject('Sketcher::SketchObject', 'StockProfile')
for p, q in [((0, 0), (10, 0)), ((10, 0), (10, 10)),
             ((10, 10), (0, 10)), ((0, 10), (0, 0))]:
    profile.addGeometry(Part.LineSegment(App.Vector(*p, 0), App.Vector(*q, 0)), False)
stock = body.newObject('PartDesign::Pad', 'Stock')
stock.Profile = (profile, [])
stock.Length = 10
doc.recompute()
top = next(i+1 for i, f in enumerate(stock.Shape.Faces) if f.CenterOfMass.z > 9.99)
plane = body.newObject('PartDesign::Plane', 'Plane')
plane.ResizeMode = 'Manual'; plane.Length = 20; plane.Width = 20
plane.AttachmentSupport = [(stock, ['Face'+str(top)])]
plane.MapMode = 'FlatFace'
axis = body.newObject('PartDesign::Line', 'Axis')
axis.setPropertyStatus('Shape', 'Transient')
axis.ResizeMode = 'Manual'; axis.Length = 20
axis.AttachmentSupport = [(stock, ['Edge1'])]; axis.MapMode = 'Tangent'
point = body.newObject('PartDesign::Point', 'Point')
point.AttachmentSupport = [(stock, ['Vertex1'])]; point.MapMode = 'Vertex'
doc.recompute()
for obj, kind, mode in [(plane, 'Plane', 'FlatFace'), (axis, 'Line', 'Tangent'),
                        (point, 'Point', 'Vertex')]:
    check(obj.TypeId == 'PartDesign::'+kind and obj.MapMode == mode, 'Original class/mode')
    check(obj.AttachmentSupport[0][0] == stock and 'Invalid' not in obj.State, 'Native owned support')
check((point.Shape.Vertexes[0].Point-stock.Shape.Vertexes[0].Point).Length < 1e-8, 'Native point on vertex')
edge = stock.Shape.Edges[0]
check(abs(axis.Placement.Rotation.multVec(App.Vector(0,0,1)).dot(edge.tangentAt(edge.FirstParameter))) > 1-1e-8, 'Native tangent axis')
check(abs(plane.Placement.Base.z-10) < 1e-8, 'Plane on source face')
tool = body.newObject('Sketcher::SketchObject', 'ToolProfile')
tool.AttachmentSupport = [(plane, [''])]; tool.MapMode = 'ObjectXY'
tool.AttachmentOffset = App.Placement(App.Vector(2,3,0), App.Rotation(20,0,0))
tool.addGeometry(Part.Circle(App.Vector(), App.Vector(0,0,1), 1), False)
boss = body.newObject('PartDesign::Pad', 'Boss')
boss.Profile = (tool, []); boss.Length = 4
doc.recompute()
for height in (10, 12, 8):
    stock.Length = height; doc.recompute()
    check(boss.Shape.isValid() and len(boss.Shape.Solids) == 1, 'Native closed single solid')
    check(abs(boss.Shape.Volume-(100*height+4*math.pi)) < 1e-5, 'Analytic material volume')
    check(abs(plane.Placement.Base.z-height) < 1e-8, 'Face dependency follows stock')
    expected = plane.Placement.multiply(tool.AttachmentOffset)
    check((tool.Placement.Base-expected.Base).Length < 1e-8, 'Native offset composition')
    check(tool.Placement.Rotation.isSame(expected.Rotation,1e-8), 'Native offset rotation')
body.Placement = App.Placement(App.Vector(5,6,7), App.Rotation(30,20,10))
doc.recompute()
for obj in (plane, axis, point):
    check((obj.getGlobalPlacement().Base-body.Placement.multVec(obj.Placement.Base)).Length < 1e-8, 'Original Body/world reference frame')
check(body.Tip == boss, 'Construction objects excluded from solid Tip')
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)/'AttachmentProof.FCStd'
    doc.saveAs(str(path)); App.closeDocument(doc.Name)
    doc = App.openDocument(str(path)); doc.recompute()
    for name, mode in [('Plane','FlatFace'),('Axis','Tangent'),('Point','Vertex')]:
        obj = doc.getObject(name)
        check(obj.MapMode == mode and obj.AttachmentSupport[0][0] == doc.Stock, 'Restored native reference')
    check(len(doc.Axis.Shape.Edges) == 1 and not doc.Axis.Shape.Vertexes, 'Restored infinite original axis')
    check(abs(doc.ToolProfile.AttachmentOffset.Base.x-2) < 1e-9, 'Restored native offset')
    check(abs(doc.Boss.Shape.Volume-(800+4*math.pi)) < 1e-5, 'Restored driven solid volume')
    before = doc.Plane.Placement
    doc.Plane.MapMode = 'Deactivated'; doc.Plane.AttachmentSupport = []
    doc.Plane.AttachmentOffset = App.Placement(); doc.Plane.Placement = before
    doc.Stock.Length = 9; doc.recompute()
    check((doc.Plane.Placement.Base-before.Base).Length < 1e-8, 'Detached datum retains native placement')
    App.closeDocument(doc.Name)
results = dict(status='HOST_ORIGINAL_ATTACHMENT_PROBE_PASS_MOBILE_PENDING', checks=checks,
               scopes=['Datum Plane FlatFace on owned planar solid face',
                       'Datum Line Tangent on owned straight solid edge',
                       'Datum Point Vertex on owned solid vertex',
                       'Sketch ObjectXY AttachmentOffset on owned Datum plane/frame'],
               native_fcstd_restore='PASS', mobile_integration='NOT_IMPLEMENTED', android_execution='NOT_RUN')
print('PASS original attachment prototype checks:', checks, flush=True)
