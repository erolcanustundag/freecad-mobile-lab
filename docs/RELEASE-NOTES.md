# FreeCAD Mobile Lab 1.4 — full mobile feature release

Full/latest GitHub release, Android code30, signed ARM64 Android8+ APK,
non-debuggable and compatible with the retained update certificate. Releases
current mobile features; full FreeCAD/Rhino parity and broader device
qualification remain NOT_COMPLETE.

Four new native Sketcher scopes in Document Lab:
- Point-on-object constraints for current points and other curves, axes or projected external edges.
- Signed horizontal/vertical dimensions: line displacement, point-to-origin and point-pair forms; unit-aware datum edits and reference measurements.
- Block constraints fixing supported internal geometry, including rational B-splines; duplicate Block requests rejected explicitly.
- Active/inactive constraint controls, independently visible from driving/reference mode; activation conflicts roll back without changing history.

Forms, command input and localized EN/TR/DE guides cover all four tools.
677 reviewed Turkish/German UI strings each. Technical diagnostics retain
English fallback. F-Droid descriptions and unsigned packaging preparation are
retained; official F-Droid submission and clean native build integration remain pending.

1613 genuine native Sketcher JNI checks pass, including analytic point/curve
relationships, signed coordinates, inactive datums, reference updates, Block
DOF, activation errors, atomic rollback, Undo/Redo and FCStd restoration.
Part269/App88/Python62 regressions, locale527, resource3 and packaging9 checks
also pass. Signing, native dependency/API26 closure and16KiB alignment are
verified before publication. Physical Android1.4 execution is NOT_RUN.

Limits remain256 sketch entities/constraints,64 external edges/64 spline
poles,8192 preview points and±1Mmm values. Point-on-object uses native curve
semantics, not clamped segment parameters. Block reactivation fixes current
geometry, not an earlier stored pose. Native solver singularities can reject
large orientation changes from an exactly perpendicular line; disable conflicting
conditions and move an endpoint slightly before retrying. Inactive dimension
datums are applied only on successful activation. Touch editing and full
workbench semantics remain pending. Save/export important models before
changing installations. Private signing keys are excluded from public assets.
