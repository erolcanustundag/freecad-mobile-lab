# SPDX-License-Identifier: LGPL-2.1-or-later
"""Host-only original PartDesign dress-up API probe; no Android/app integration claim."""
import FreeCAD as A,Part,Sketcher,PartDesign,mobile_part,math
mobile_part.configure();d=A.newDocument('OriginalDressupProbe');d.UndoMode=1

def body(name):
 box=d.addObject('Part::Box',name+'Source');d.recompute();b=d.addObject('PartDesign::Body',name);b.AllowCompound=False;b.BaseFeature=box;d.recompute();return b

def status(f):
 return dict(type=f.TypeId,state=list(f.State),status=f.getStatusString(),volume=f.Shape.Volume if not f.Shape.isNull() else None,valid=not f.Shape.isNull() and f.Shape.isValid())
b=body('FilletBody');source=b.Tip;f=b.newObject('PartDesign::Fillet','Fillet');f.Base=(source,['Edge1']);f.Radius=1;d.recompute();print('FILLET',status(f),flush=True);assert abs(f.Shape.Volume-(1000-10*(1-math.pi/4)))<1e-5
b=body('ChamferBody');source=b.Tip;f=b.newObject('PartDesign::Chamfer','Chamfer');f.Base=(source,['Edge1']);f.ChamferType='Equal distance';f.Size=1;d.recompute();print('CHAMFER',status(f),flush=True);assert abs(f.Shape.Volume-995)<1e-5
b=body('ThicknessBody');source=b.Tip;f=b.newObject('PartDesign::Thickness','Thickness');f.Base=(source,['Face6']);f.Value=1;f.Reversed=True;d.recompute();print('THICKNESS',status(f),flush=True);assert abs(f.Shape.Volume-424)<1e-5
b=body('DraftBody');source=b.Tip;f=b.newObject('PartDesign::Draft','Draft');f.Base=(source,['Face1']);f.NeutralPlane=(source,['Face5']);f.PullDirection=(b.Origin.OriginFeatures[2],['']);f.Angle=5;d.recompute();print('DRAFT',status(f),flush=True);assert not f.Shape.isNull() and f.Shape.isValid() and abs(f.Shape.Volume-(1000-500*math.tan(math.radians(5))))<1e-5
print('PASS original host Fillet/Chamfer/Thickness/Draft API proof. Android adapter/controls NOT_IMPLEMENTED.',flush=True)
