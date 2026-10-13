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

Preview uses sampled local XY; gold is regular geometry, cyan construction. Drag/pinch/fit changes the view. Edit via forms/commands; touch constraint editing and spline handles remain pending. Save FCStd and export it through the file picker before closing. See SKETCHER-PORT-PROGRESS.md for bounds, pending features and device evidence.
