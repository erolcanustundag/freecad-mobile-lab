# SPDX-License-Identifier: LGPL-2.1-or-later
"""Native torus/prism boundaries; mobile policy must reject invalid requests."""
import FreeCAD as App
import PartDesign,mobile_part,math,json,tempfile
from pathlib import Path
mobile_part.configure();checks=0

def check(v,msg):
 global checks
 assert v,msg
 checks+=1
for polygon in (3,4,32):
 d=App.newDocument('PrismBoundary');b=d.addObject('PartDesign::Body','Body');b.AllowCompound=False;o=b.newObject('PartDesign::AdditivePrism','Prism');o.Polygon=polygon;o.Circumradius=2;o.Height=3;d.recompute()
 check(o.Shape.isValid() and len(o.Shape.Solids)==1,'Original prism closed solid')
 check(abs(o.Shape.Volume-polygon/2*4*math.sin(2*math.pi/polygon)*3)<1e-5,'Analytic polygon prism')
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'Boundary.FCStd';d.saveAs(str(p));App.closeDocument(d.Name);d=App.openDocument(str(p));d.recompute();check(d.Prism.Polygon==polygon and d.Prism.Shape.isValid(),'True boundary restore')
 App.closeDocument(d.Name)
# Horn/spindle and zero torus parameters are never assumed safe from State alone.
observed=[]
for major,minor in [(2,.5),(1,1),(.5,1),(2,0),(0,1)]:
 d=App.newDocument('TorusBoundary');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveTorus','Torus');o.Radius1=major;o.Radius2=minor;d.recompute()
 valid=not o.Shape.isNull() and o.Shape.isValid();observed.append(dict(major=major,minor=minor,state=list(o.State),valid=valid,volume=o.Shape.Volume if valid else None))
 if major>minor>0:check(valid and abs(o.Shape.Volume-2*math.pi**2*major*minor**2)<1e-5,'Analytic ring torus')
 App.closeDocument(d.Name)
r=dict(status='HOST_ORIGINAL_TORUS_PRISM_BOUNDARY_PASS_MOBILE_PENDING',checks=checks,observations=observed,mobile_policy='integer Polygon3..32; positive Circumradius/Height; ring torus Radius1>Radius2>0, full native defaults; reject horn/spindle/zero',mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN')
Path('docs/native-partdesign-torus-prism-boundary-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
