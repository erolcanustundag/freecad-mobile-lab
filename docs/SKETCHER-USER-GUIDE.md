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
