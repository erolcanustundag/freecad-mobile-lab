# Original Sketcher in the native lab

Open Document Lab from recovery, create a document, and select Original Sketcher. Forms and commands call original geometry/solver APIs. Sketch guide is available in English, Turkish and German.

```
NewDoc SketchModel
Sketch Profile
SketchLine Profile 0 0 30 0
Constraint Profile Horizontal 0
Constraint Profile Distance 0 30
Constraint Profile Coincident 0 1 -1 1
SketchPreview Profile
Datum Profile 1 40 mm
Save SketchModel.FCStd
```

This line has zero DOF. Undo/Redo reverses the datum edit. Indices start at0; -1,1 is the origin, and line point1/2 is start/end. Point3 is a circle centre. Deletion can renumber geometry and remove dependent constraints; check the displayed list afterward.

| Tool | Example |
| --- | --- |
| Circle | `SketchCircle Curves 0 0 5` |
| Arc | `SketchArc Curves 20 0 10 0 180` |
| Ellipse | `SketchEllipse Curves 0 30 20 10` |
| Rational B-spline | `SketchSpline Curves 3 0,0;10,20;20,20;30,0 1,2,2,1` |
| Construction | `Construction Curves 3 true` |
| Solver move | `MovePoint Profile 0 2 40 0` |
| Delete | `DeleteGeometry Curves 0` or `DeleteConstraint Profile 1` |
| Units | `Datum Profile 1 4 cm` |

Create Sketch Curves first. Constraints: Horizontal/Vertical (entity), Coincident (entity/point/entity/point), Parallel/Perpendicular/Tangent/Equal (two entities), Distance/Radius/Diameter/Angle (entity/value). Lengths use mm and angles degrees; Datum accepts units. Conflicting/redundant edits roll back.

Preview uses sampled local XY; gold is regular geometry, cyan construction and magenta external edges. Drag/pinch/fit changes the view. Edit via forms/commands; touch constraint editing and spline handles remain pending. Save FCStd and export it through the file picker before closing. See SKETCHER-PORT-PROGRESS.md for bounds, pending features and device evidence.

## Plane and reference workflows

```
NewDoc AttachmentModel
Add Solid Box
Sketch Attached
SketchLine Attached 0 0 10 0
SketchAttach Attached Solid Face6
SketchOffset Attached 0 0 2 0 0 0
External Attached Solid Edge9
Constraint Attached Coincident 0 1 -3 1
Constraint Attached Coincident 0 2 -3 2
Set Solid.Length 25 mm
Set Solid.Height 20 mm
SketchPreview Attached
Save AttachmentModel.FCStd
```

The line follows the projected edge length; the sketch stays2mm above the top face. The first external solver index is-3, then-4, etc. `DeleteExternal Attached 0` uses reference index0 and removes dependent constraints; Undo restores both. `SketchDetach Attached` retains current world placement; Undo restores support. Detach and remove external references before deleting the source. Duplicate/missing/cyclic/collapsed references and invalid recomputes roll back. FCStd preserves native support/external links.

For a free sketch, `SketchPlane Attached XZ 0 0 10` selects XY/XZ/YZ and an XYZ origin in mm; `SketchPlacement Attached 0 0 10 0 0 0` uses XYZ then yaw/pitch/roll degrees. Placement changes require detachment. `SketchOffset` uses the same six values in the attached local coordinates. Preview remains local XY even on rotated or attached sketches. Up to64 projected edges are exposed. Only single planar FlatFace attachment is supported; full attachment modes, intersection/defining external variants and cross-document references remain pending. Inspect face/edge references after major topology changes.

## Native editing tools


NATIVE TRIM / EXTEND / FILLET / SPLIT
SketchTrim Cut 0 10 0 removes the picked span between intersections. With no intersections, original trim can remove the entire entity. Picks use sketch-local XY and must lie on the current curve.
SketchExtend Line 0 5 2 extends endpoint2 by5mm; -2 shortens by2mm. Endpoints are1/2. This tool exposes line segments only. Driving dimensions remain authoritative; the solver may preserve their original length.
For lines (0,0)-(20,0) and (20,0)-(20,20): SketchFillet Corner 0 1 18 0 20 2 2 creates a2mm tangent arc and trims both lines. Only a common-endpoint pair of lines is exposed; picks must be on them and radius smaller than both lengths.
SketchSplit Line 0 7 0 splits at a point on the curve, preserving native constraint updates. Geometry/constraint indices can change: inspect the resulting list. Undo/Redo and FCStd preserve native results. Errors roll back. Broader curved-corner fillets, extension variants and touch editing remain pending.

## Patterns and dimension modes


MIRROR, ARRAYS, SYMMETRY AND REFERENCE DIMENSIONS
SketchMirror Profile 0,1 Y mirrors selected internal geometry across Y; X chooses X, or enter a current line index. Construction flags and eligible internal constraints are copied. This creates mirrored copies, not an automatic live mirror relation. Use Symmetric constraints for live point relations.
SketchArray Rings 0 3 2 10 0 1 false creates3 columns and2 rows: columns follow (10,0), rows follow the clockwise perpendicular (0,-10). The scale1 multiplies the row pitch. true adds native construction spacing lines and constraints; inspect their indices before changing a Datum. Spacing controls positions, not automatic shared radii or a persistent array feature tree.
Constraint Profile Symmetric 0 1 1 1 -2 links two points about the Y axis. Use5 arguments (two geometry/point pairs and an axis) or6 (three point pairs, the last being the centre). X/Y axes are -1/-2; origin is -1,1.
Driving Profile 1 false makes a dimensional constraint a reference measurement; its value follows solved geometry. Driving Profile 1 true restores a driving dimension. Reference datums cannot be edited directly. The report shows driving flags and raw units (mm or radians).
Select1–32 unique internal indices, up to64 array cells, within256 entities/constraints and±1Mmm. Budget checks include spacing helpers and conservative constraint reserves. Copy tools accept current line/circle/arc/ellipse/64-pole spline entities. New commands use sketch-local XY. Undo/Redo, atomic errors and FCStd preserve native results.

## Native constraint tools in1.4

PointOnObject binds a current point to another curve, axis or external projected edge. DistanceX/Y accepts signed line displacement, point-to-origin or two-point forms. Block fixes supported internal geometry; duplicate fixes are rejected. Active toggles a constraint without deleting it and its flag is distinct from driving/reference. Native solver errors roll back. See the three bundled native-sketcher guides for exact command forms, singular orientation limits and inactive dimension behavior.1613 genuine host checks and the ConstraintTools.FCStd fixture cover persistence/history; Android execution remains NOT_RUN.

## Native sections and inspection


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
