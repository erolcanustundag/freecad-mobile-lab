# SPDX-License-Identifier: LGPL-2.1-or-later
"""Record native ellipsoid integration accuracy; no mobile qualification claim."""
import FreeCAD as App
import PartDesign,mobile_part,math,json,tempfile
from pathlib import Path
mobile_part.configure();d=App.newDocument('EllipsoidMeasurement');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveEllipsoid','Ellipsoid');o.Radius1=2;o.Radius2=1;o.Radius3=1;d.recompute()
assert o.Shape.isValid() and len(o.Shape.Solids)==1
v=8*math.pi/3;measured=o.Shape.Volume
report=dict(status='NATIVE_ELLIPSOID_MEASUREMENT_INVESTIGATION_REQUIRED',native_type=o.TypeId,analytic_volume=v,native_volume=measured,absolute_error=abs(v-measured),relative_error=abs(v-measured)/v,surface_type=type(o.Shape.Faces[0].Surface).__name__,mobile_integration='NOT_IMPLEMENTED',qualification='NOT_QUALIFIED',note='Native BSpline-surface volume integration differs from analytic ellipsoid volume; investigate accurate integration and bounding before exposure.')
Path('docs/native-ellipsoid-measurement-probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));App.closeDocument(d.Name)
