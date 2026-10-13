# FreeCAD Mobile Lab1.7 — full mobile feature release

Android code33, non-debuggable signed ARM64 Android8+ APK with the retained
update certificate. This releases the current mobile feature set; full
FreeCAD/Rhino parity and comprehensive device qualification stay NOT_COMPLETE.

Three four-feature milestones since1.4:
- Native Unicode constraint names, uniqueness/clear and persisted rename.
- Native dimensional expressions with dependency updates, clear and datum guards.
- Read-only solver/constraint/reference inspection.
- Linked original Part extrusion/revolution from constrained closed sketch profiles.
- Native extrusion forward/reverse/symmetric/reversed extent controls.
- Native revolution world axis, angle and symmetry controls.
- Native Part XYZ/yaw/pitch/roll placement.
- Exact native volume/area/unique-edge length/bounds/one-solid centroid inspection.
- Linked native edge fillet and equal-distance chamfer.
- Labelled native refinement snapshots.
- Linked native shape intersection sections.
- Fixed one-solid Compound centroid inspection.

1.5/code31 and1.6/code32 are saved intermediate signed checkpoints.1.7/code33
combines all three milestones.1839 genuine nativeSketcher/profile/solid/finishing checks pass; Part269,
App88 andPython62 regressions and3 resource/9 packaging checks pass.690 reviewed
Turkish/German UI strings, commands/forms and EN/TR/DE guides cover these tools.
Private signing keys are excluded from public source/assets/Actions.

Limits: new profile solid creation requires zeroDOF, one valid closed sketch
wire and one valid resulting solid;2000 result faces,±1Mmm bounds. Expressions
are limited to512 characters and active driving dimensional targets. Inspection
is read-only and capped at2000faces/10000edges. Centroids are geometric, not
density-weighted mass calculations. These are native Part features, not
PartDesign Body/Pad parity. Physical Android1.7 execution is NOT_RUN; earlier
unversioned startup was user-reported. F-Droid remains NOT_SUBMITTED pending
clean native source-build integration. Export important models before changing
installations.

Finishing uses1–32 unique current edge numbers starting at1. Source changes
recompute fillet/chamfer/section results; topology changes can invalidate edge
selection. Refinement is a snapshot and does not update with its source. Wire
sections support inspection and STEP export; face/solid triangle preview does
not display wires. Empty/invalid/budget-exceeding operations roll back.
