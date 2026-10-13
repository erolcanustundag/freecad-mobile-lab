# FreeCAD Mobile Lab1.3 — full mobile feature release

Full/latest GitHub release, Android code29, signed ARM64 Android8+ APK, non-debuggable and compatible with the retained update certificate. Releases the current mobile feature set; full FreeCAD/Rhino parity and broader device qualification remain NOT_COMPLETE.

Four new original Sketcher scopes in Document Lab:
- Native mirrored copies across X/Y or a current line, preserving construction flags and eligible constraints.
- Rectangular arrays, optional native spacing construction geometry/constraints, editable spacing dimensions.
- Axis or point-centred symmetry constraints with solver-aware point movement.
- Driving/reference dimension controls, measured-value updates, visible mode/unit reporting and guarded datum edits.

EN/TR/DE forms, command input and localized guides cover these tools.673 reviewed Turkish/German strings each; technical diagnostics retain English fallback.

1438 genuine native Sketcher JNI checks pass, including analytic coordinates/weights, grid spacing updates, native symmetry/DOF, reference measurement updates, errors/budget boundaries, multi-edit rollback, Undo/Redo and FCStd restoration. Part269/App88/Python62 regressions and portable locale/resources/packaging checks are recorded separately. APK signing, native133-library/extension closure and16KiB/API26 checks precede publication.

Limits:256 sketch entities/constraints,64 external edges/64 spline poles,8192 preview points,±1Mmm; pattern selection1–32 internal entities and up to64 array cells. Conservative budgets reserve native helpers/constraints. Mirror creates copies; live point relations require Symmetric constraints. Array spacing is constrained only when requested; it does not create a persistent array feature tree or automatically share radii. Copies support the exposed bounded line/circle/arc/ellipse/spline types. Broader native pattern/constraint options, touch editing, PartDesign and full workbench parity remain pending.

The user previously reported startup working, without a version/device log. Android execution/gestures/lifecycle/SAF/language/memory qualification for1.3 remains NOT_RUN. Save/export models before uninstalling/downgrading. Signing keys are excluded from public Git, assets and Actions.
