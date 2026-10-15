# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original native Hole mode probes; not a mobile capability declaration."""
import FreeCAD as App,Part,Sketcher,PartDesign,mobile_part,math
mobile_part.configure()
doc=App.newDocument('HolePrototypes');results={}
for name,extent,cut in [('Blind','Dimension','None'),('Through','ThroughAll','None'),('Counterbore','Dimension','Counterbore'),('Countersink','Dimension','Countersink')]:
    b=doc.addObject('PartDesign::Body',name+'Body');b.AllowCompound=False
    base=b.newObject('Sketcher::SketchObject',name+'Base')
    points=[App.Vector(0,0,0),App.Vector(10,0,0),App.Vector(10,10,0),App.Vector(0,10,0)]
    base.addGeometry([Part.LineSegment(points[i],points[(i+1)%4]) for i in range(4)],False)
    pad=b.newObject('PartDesign::Pad',name+'Pad');pad.Profile=(base,[]);pad.Length=10
    profile=b.newObject('Sketcher::SketchObject',name+'Profile');profile.addGeometry(Part.Circle(App.Vector(5,5,0),App.Vector(0,0,1),1),False);profile.Placement.Base=App.Vector(0,0,10)
    doc.recompute()
    hole=b.newObject('PartDesign::Hole',name+'Hole');hole.Profile=(profile,[])
    hole.Threaded=False;hole.ThreadType='None';hole.ModelThread=False;hole.DrillPoint='Flat'
    hole.DepthType=extent;hole.Diameter=2;hole.Depth=4;hole.HoleCutType=cut
    if cut!='None':hole.HoleCutCustomValues=True;hole.HoleCutDiameter=4;hole.HoleCutDepth=1;hole.HoleCutCountersinkAngle=90
    doc.recompute()
    removed={'Blind':4*math.pi,'Through':10*math.pi,'Counterbore':7*math.pi,'Countersink':16*math.pi/3}[name]
    expected=1000-removed;shape=hole.Shape
    assert shape.isValid() and len(shape.Solids)==1 and abs(shape.Volume-expected)<1e-5,(name,hole.getStatusString(),shape.Volume,expected)
    assert hole.BaseFeature==pad and hole.Profile[0]==profile and b.Tip==hole
    results[name]=dict(type=hole.TypeId,volume_mm3=shape.Volume,expected_mm3=expected,depth_type=hole.DepthType,cut=hole.HoleCutType,drill=hole.DrillPoint)
    print(name,'PASS',shape.Volume,flush=True)
results.update(status='HOST_NATIVE_PROTOTYPE_PASS_MOBILE_PENDING',mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN',freecad='1.1.4')
