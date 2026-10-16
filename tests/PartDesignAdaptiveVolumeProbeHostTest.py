# SPDX-License-Identifier: LGPL-2.1-or-later
"""Compare original/adaptive OCCT integration. No mobile qualification claim."""
import FreeCAD as App
import PartDesign,mobile_part,subprocess,json,math,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
mobile_part.configure();checks=0

def check(v,msg):
 global checks
 assert v,msg
 checks+=1
with tempfile.TemporaryDirectory(prefix='adaptive-volume-',dir=BASE) as td:
 tool=Path(td)/'volume-probe';occt=BASE/'occt-host'
 subprocess.run(['g++','-std=c++17','-O2','-I'+str(occt/'include/opencascade'),str(ROOT/'tests/NativeAdaptiveVolumeProbe.cpp'),'-L'+str(occt/'lib'),'-Wl,-rpath-link,'+str(occt/'lib'),*['-l'+s for s in ['TKTopAlgo','TKBRep','TKGeomAlgo','TKGeomBase','TKG3d','TKG2d','TKMath','TKernel']],'-o',str(tool)],check=True)
 d=App.newDocument('AdaptiveMass');b=d.addObject('PartDesign::Body','Body');o=b.newObject('PartDesign::AdditiveEllipsoid','Ellipsoid');o.Radius1=2;o.Radius2=1;o.Radius3=1;d.recompute();check(o.Shape.isValid() and len(o.Shape.Solids)==1,'Original ellipsoid')
 path=Path(td)/'Ellipsoid.brep';o.Shape.exportBrep(str(path));r=json.loads(subprocess.check_output([str(tool),str(path)],text=True));r['analytic_volume']=8*math.pi/3;r['native_python_volume']=o.Shape.Volume;r['absolute_adaptive_error']=abs(r['adaptive_volume']-r['analytic_volume']);r['absolute_default_error']=abs(r['default_volume']-r['analytic_volume']);r['maximum_shape_tolerance_mm']=o.Shape.getTolerance(1)
 check(abs(r['default_volume']-o.Shape.Volume)<1e-10,'Original Python getter uses the nonadaptive OCCT overload')
 check(r['absolute_adaptive_error']*1000<r['absolute_default_error'],'Adaptive integration improves the measured analytic error by at least1000x')
 check(r['estimated_relative_error']<1e-10,'Reported adaptive integration error estimate')
 check(r['absolute_adaptive_error']>1e-8,'Retain the unresolved ideal-geometry discrepancy explicitly')
 fcstd=Path(td)/'AdaptiveMass.FCStd';d.saveAs(str(fcstd));App.closeDocument(d.Name);d=App.openDocument(str(fcstd));d.recompute();d.Ellipsoid.Shape.exportBrep(str(path));again=json.loads(subprocess.check_output([str(tool),str(path)],text=True));check(abs(again['adaptive_volume']-r['adaptive_volume'])<1e-10,'Native restore preserves the measured BRep');App.closeDocument(d.Name)
 result=dict(status='HOST_ADAPTIVE_VOLUME_RESEARCH_PASS_MOBILE_PENDING',checks=checks,observation=r,original_getter='TopoShapePyImp.cpp getVolume calls default BRepGProp::VolumeProperties',research='Adaptive OCCT integration improves the observed mass error. The remaining1.29e-7mm3 ideal-geometry discrepancy is recorded, not hidden or qualified as exact.',mobile_integration='NOT_IMPLEMENTED',android_execution='NOT_RUN',pending=['bounded Android native adapter and matching source/runtime checkpoints','integration error versus geometry tolerance and performance qualification','original additive/subtractive ellipsoid workflow qualification'])
 (ROOT/'docs/native-adaptive-volume-research-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
