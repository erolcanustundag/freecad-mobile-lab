# FreeCAD Mobile Lab1.6 — full mobile feature release

Android code32, non-debuggable signed ARM64 Android8+ APK with the retained
update certificate. This releases the current mobile feature set; full
FreeCAD/Rhino parity and comprehensive device qualification stay NOT_COMPLETE.

Two four-feature milestones since1.4:
- Native Unicode constraint names, uniqueness/clear and persisted rename.
- Native dimensional expressions with dependency updates, clear and datum guards.
- Read-only solver/constraint/reference inspection.
- Linked original Part extrusion/revolution from constrained closed sketch profiles.
- Native extrusion forward/reverse/symmetric/reversed extent controls.
- Native revolution world axis, angle and symmetry controls.
- Native Part XYZ/yaw/pitch/roll placement.
- Exact native volume/area/unique-edge length/bounds/one-solid centroid inspection.

1.5/code31 is saved as an intermediate signed checkpoint.1.6/code32 combines
both milestones.1785 genuine nativeSketcher/profile/solid checks pass; Part269,
App88 andPython62 regressions and3 resource/9 packaging checks pass.686 reviewed
Turkish/German UI strings, commands/forms and EN/TR/DE guides cover these tools.
Private signing keys are excluded from public source/assets/Actions.

Limits: new profile solid creation requires zeroDOF, one valid closed sketch
wire and one valid resulting solid;2000 result faces,±1Mmm bounds. Expressions
are limited to512 characters and active driving dimensional targets. Inspection
is read-only and capped at2000faces/10000edges. Centroids are geometric, not
density-weighted mass calculations. These are native Part features, not
PartDesign Body/Pad parity. Physical Android1.6 execution is NOT_RUN; earlier
unversioned startup was user-reported. F-Droid remains NOT_SUBMITTED pending
clean native source-build integration. Export important models before changing
installations.
