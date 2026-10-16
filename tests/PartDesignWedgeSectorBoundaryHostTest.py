# SPDX-License-Identifier: LGPL-2.1-or-later
"""Signed/slanted wedge and native angular boundary evidence before exposure."""
import FreeCAD as App
import PartDesign,mobile_part,math,json,tempfile
from pathlib import Path
mobile_part.configure();checks=0

def check(v,msg):
 global checks
 assert v,msg
 checks+=1
# Offset end rectangles may extend beyond the first rectangle; native wedge
# integration depends on rectangle dimensions, not their lateral translations.
d=App.newDocument('WedgeBoundary');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveWedge','Wedge')
for p,v in dict(Xmin=-2,Xmax=2,Ymin=-1,Ymax=2,Zmin=-1,Zmax=1,X2min=3,X2max=5,Z2min=2,Z2max=3).items():setattr(o,p,v)
d.recompute();check(o.Shape.isValid() and len(o.Shape.Solids)==1,'Signed slanted endpoint rectangles valid');check(abs(o.Shape.Volume-14)<1e-6,'Exact native slanted wedge volume')
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'SlantedWedge.FCStd';d.saveAs(str(p));App.closeDocument(d.Name);d=App.openDocument(str(p));d.recompute();check(abs(d.Wedge.Shape.Volume-14)<1e-6 and d.Wedge.Xmin.Value==-2,'True signed wedge restoration')
App.closeDocument(d.Name)
for angle in [1,90,180,359,360]:
 d=App.newDocument('ConeSectorBoundary');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveCone','Cone');o.Radius1=2;o.Radius2=0;o.Height=3;o.Angle=angle;d.recompute();check(o.Shape.isValid() and len(o.Shape.Solids)==1,'Valid angular cone');check(abs(o.Shape.Volume-4*math.pi*angle/360)<1e-6,'Exact cone sector volume');App.closeDocument(d.Name)
for lo,hi,angle in [(-90,90,360),(-90,0,180),(0,30,180),(-30,30,90),(10,20,1)]:
 d=App.newDocument('SphereSegmentBoundary');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveSphere','Sphere');o.Radius=2;o.Angle1=lo;o.Angle2=hi;o.Angle3=angle;d.recompute();z1=2*math.sin(math.radians(lo));z2=2*math.sin(math.radians(hi));volume=math.pi*(4*(z2-z1)-(z2**3-z1**3)/3)*angle/360
 check(o.Shape.isValid() and len(o.Shape.Solids)==1,'Valid latitude/azimuth segment');check(abs(o.Shape.Volume-volume)<1e-6,'Exact spherical segment volume');App.closeDocument(d.Name)
r=dict(status='HOST_ORIGINAL_WEDGE_SECTOR_BOUNDARY_PASS_MOBILE_PENDING',checks=checks,mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN',qualified='positive rectangular ends including signed/slanted coordinates; full and bounded cone/sphere angles',pending='degenerate wedge endpoint rectangles; tiny-angle/material policy and mobile pre-compute guards')
Path('docs/native-partdesign-wedge-sector-boundary-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
