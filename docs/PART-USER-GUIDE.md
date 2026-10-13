# Original Part document lab — 1.10

The current mobile feature set connects the original FreeCAD1.1.4 Part/Materials modules to the isolated document lab. It is separate from the main mobile CAD recipe workspace. Android execution and broader desktop parity remain pending.

Open Workspace → Document lab, create a document, then open Original Part. Create a native Box, Cylinder, Sphere, Cone or Torus. Set / formula edits their native dimensional properties: choose the object name, property (Length, Width, Height, Radius, Radius1 or Radius2 as applicable), and a value such as 25 mm or 2 cm. Expressions use native document property names. Undo/Redo and explicit transactions use original App semantics. Part booleans choose result name, base object and tool object; the input shapes remain document dependencies.

In the lab command input:

```
NewDoc NativeModel
Add Solid Box
Set Solid.Length 30 mm
Set Solid.Width 10 mm
Set Solid.Height 5 mm
Add Tool Cylinder
Set Tool.Radius 3 mm
Set Tool.Height 10 mm
Cut Result Solid Tool
Preview Result 0.2
Save NativeModel.FCStd
ExportStep Result NativeModel.step
ImportStep Imported NativeModel.step
```

The preview uses genuine Part tessellation and the software viewport. One finger orbits, pinch zooms, two fingers pan. Tolerance must be0.05–2mm. The display is bounded to30,000 triangles and coordinates within±1,000,000mm; increasing tolerance can reduce display detail. This does not alter the saved BRep. Native tessellation may allocate memory before the display limit can be checked; no global Android memory guarantee is claimed. Wires without faces cannot use this triangle preview.

FCStd save/open preserves native whitelisted geometry, properties, expressions, links and supported metadata. Supported geometry types: Part::Feature, Box, Cylinder, Sphere, Cone, Torus, Cut, Fuse, Common, Plane, Extrusion, Revolution, Fillet, Chamfer and Section, plus supported Sketcher::SketchObject profiles. Other types, including PartDesign objects and arbitrary addon proxies, are rejected before restore. The existing QuantityDriver metadata proxy remains the sole supported scripted proxy. FCStd input remains128MiB, expanded ZIP256MiB, Document.xml16MiB and2,000 entries. This is not a general desktop FCStd editor.

Import Part STEP opens the Android file picker and imports up to128MiB into a native Part::Feature. Create a document first. STEP shape transforms are carried by the imported BRep; document history, source labels/assembly tree, colours and materials are not preserved by this shape-only reader. Import is a native transaction with Undo/Redo. The native parser can use memory before a shape is returned; device budgets remain unmeasured.

ExportStep writes the selected original Part object through native Part.export, then opens Android's save picker. Export uses a plain.step/.stp filename. Files do not transfer the whole document/history/materials. The Python console exposes the loaded original Part API; try Api Part.makeBox or Python print(Part.makeBox(20,10,5).Volume). Gui and other workbench APIs remain pending. Macros have the existing tracing budget; native operations can take longer and Recovery/Restart remains available. Save FCStd before restarting.

Turkish: Workspace → Language → Türkçe, or Dil in the main workspace. Native Part menu captions have Turkish and German resources. Canonical object/property/API names and native diagnostics remain unchanged; command numbers use decimal points.

## Sections, wires and measurements


SECTIONS AND EDGE INSPECTION (1.8)
SectionPlane Solid Slice 0 0 5 0 0 1 100 creates a native finite Part plane centred at world XYZ (0,0,5), with normal (0,0,1) and size100mm, and a linked native section. Slice_Plane is the editable helper; PartPlacement changes its world placement. The plane has local UV bounds0..size; its placement offsets those bounds about the requested centre. The source and helper stay as dependencies. Empty/invalid sections and out-of-bounds helper planes roll back together.
WirePreview Slice samples actual world-space native edges for display. Drag to orbit, pinch to zoom, two fingers to pan; Fit resets the view. Edge numbers are current1-based indices. At most128 edges/8192 points; straight edges use2 points, curves65. Tiny/pole edges at or below1e-7mm are skipped for drawing. Sampling changes display detail only; native geometry and STEP exports retain their exact curves. Touch gestures have not been independently tested on Android.
ElementInfo Solid Edge1 reports exact length, bounds, raw curve parameter range and endpoint coordinates. ElementInfo Solid Face1 reports native area/surface type, area centroid and a point/normal evaluated at the middle of the surface parameter range. The area centroid need not lie on the surface; the evaluated point need not lie within every trimmed face. Units are mm/mm²; curve/UV parameters retain native units. Below-tolerance edges report that flag rather than claiming they are topologically degenerate.
FinishSettings Rounded 1,2 2 updates current edge selections and equal radius/distance in mm on a native fillet/chamfer. Native recompute, Undo/Redo and FCStd preserve the edit. Use1–32 unique current1-based edges. This is not a guarantee of stable selections across arbitrary topology changes. Inspect and retry if native geometry fails.

## Native loft/surface features


LOFT, RULED SURFACE, OFFSET AND MIRROR (1.9)
PartLoft Loft ProfileA,ProfileB true false creates a linked native Part loft: result name, comma-separated2–16 unique single-wire profiles, solid flag, ruled flag. Solid lofts need closed profiles; false allows open wire profiles. Profiles remain editable native dependencies. Closed last-to-first loft mode is not exposed. Native failure rolls back. Use bounded supported wire geometry, at most256 edges per profile. This is Part loft modelling, not PartDesign AdditiveLoft.
PartRuled Surface Lower Edge1 Upper Edge1 creates a native ruled surface between two current edges. Selections are1-based native edge names, may belong to the same object if they differ, and must be nonzero. Native source edits recompute the surface; topology changes can invalidate references. General surface blends/continuity controls are not included.
PartOffset Solid Offset 1 creates a linked native solid offset in mm with intersection joins. Negative amounts offset inward; the result must remain one valid closed solid. Set Offset.Value 2 edits the amount. Zero, collapse and invalid geometry roll back. This is an offset of all faces, not a thickness tool with selected removed faces.
PartMirror Solid Mirrored 0 0 0 1 0 0 mirrors about a world plane given by origin XYZ and nonzero normal XYZ. The normal is normalized; source geometry remains linked and editable. Wires and surfaces are supported when the resulting native shape is valid. This is native feature mirroring, distinct from copied sketch geometry.
Undo/Redo, native FCStd and STEP preserve supported outputs; profiles/sources cannot be deleted while their dependants remain. Shapes stay within±1Mmm/2000faces/10000edges. Native algorithms can allocate or take time before result limits are checked; Android memory/lifecycle performance remains unmeasured. ShapeInfo and document reports return null volume for shapes without closed solids: open-face volume integrals are not enclosed volume. Full desktop Part/PartDesign/Rhino parity remains incomplete.

Loft/ruled BSpline inputs are limited to64 poles per selected curve.

## Native fabrication features


SWEEP, THICKNESS, PLANAR OFFSET AND COMPOUND (1.10)
PartSweep Swept Profile Path true false creates a linked native Part sweep: result, profile name(s), whole single-wire path, solid flag, Frenet flag. Use1–8 unique comma-separated single-wire profiles, closed for solids; the path must be a different object. Set up the profile and path in their intended world placements, typically with the profile normal aligned to the initial path tangent. Native geometry failure rolls back; the default transition is Right corner. Source geometry/dimensions remain native dependencies. This is Part sweep modelling, not PartDesign AdditivePipe.
PartThickness Solid Hollow 6 -1 removes current Face6 and creates a1mm inward wall. Use1–16 unique1-based face numbers, retaining at least one face. Signed amounts are mm; negative inward/positive outward follow native offset semantics. Result must be one valid closed solid. Set Hollow.Value -0.2 cm accepts length units; Expression Hollow.Value -Solid.Width / 8 binds a native length expression. Clear with an empty quoted expression before direct editing. Only this native Thickness.Value gains the scoped quantity-property editor. Shape failures, unit mismatch, zero or collapse roll back. Join is Intersection.
PartOffset2D Profile Outline 1 offsets one closed planar wire or one planar face by1mm using intersection joins and no fill. Negative values offset inward. Source/result stay planar and bounded; nonplanar/open wire and collapsed results reject. Set Outline.Value -1 changes the mm amount. Wire-only results use WirePreview; planar faces also support the triangle preview. This is not the full desktop2D offset mode/filled-band tool.
PartCompound Assembly Solid,Hollow combines2–32 unique supported native source shapes with live links. It keeps separate geometry; it does not fuse overlaps or create an Assembly workbench constraint system. ShapeInfo volume is the sum of its closed component solids, so overlapping material is counted separately. Open faces/wires contribute no volume; multiple solids have no single reported centroid. Source edits, Undo/Redo, FCStd and STEP work with native outputs.
Profile/path curves remain limited to256 edges/64 spline poles. All shapes use±1Mmm/2000faces/10000edges budgets. Selections use current native indices; full topology-reference stability remains unfinished. Native computation can allocate/time out before result inspection; Android touch/lifecycle/memory qualification remains NOT_RUN. Save native FCStd before Recovery/Restart.


PartPolygon Hexagon 6 10 creates an XY closed wire with 6 sides and 10 mm circumradius. Set Hexagon.Polygon 8 or Set Hexagon.Circumradius 2 cm; side counts are bounded to 3–128 and side expressions are unsupported. WirePreview displays the wire; native Loft/Sweep can consume it.
PartEllipsoid Oval 3 4 2 uses XYZ semiaxes in mm. Native property names map X=Radius2, Y=Radius3, Z=Radius1. Radius3=0 is the original legacy Y=X fallback. This tool supports full closed ellipsoids only. BRep bounds may be conservative; native volume is a numerical integral with finite error, not an analytic formula.
PartLinkedRefine Solid Clean creates an original linked Part::Refine which recomputes when its source changes; PartRefine remains an independent snapshot.
PartReverse Solid Reversed flips native orientation, including normals; it keeps world position and follows source edits. It does not repair mesh topology or convert open surfaces into solids. ShapeInfo volume is the sum of positive closed-component volumes; oriented_volume_mm3 keeps the signed native integral. Compounds aggregate overlapping components and are not Boolean unions. Open wires/surfaces report no enclosed volume.
New tools are in Original Part in the isolated document lab, with command access, Undo/Redo and FCStd persistence. Android touch execution for this release is not yet automated.
