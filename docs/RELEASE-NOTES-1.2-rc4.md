# FreeCAD Mobile Lab1.2-rc4 — sketch attachments and references

Signed ARM64 Android8+ engineering candidate, code27. Latest full release remains1.1. Full FreeCAD/Rhino parity and device qualification are NOT_COMPLETE.

Four new bounded native Document Lab scopes:
- Explicit XY/XZ/YZ sketch planes and arbitrary world placement.
- Planar FlatFace support, local attachment offsets and detach preserving world placement.
- Original projected external edges, negative-index solver constraints and distinct preview styling.
- Native reference/dependency persistence, Undo/Redo and atomic validation. Source dimensional edits update attached sketches and constrained geometry. Invalid/cyclic/duplicate/collapsed references roll back; referenced sources require detachment/reference removal before deletion. Failed unsupported FCStd restoration retains the previous document. Already-open files are rejected explicitly.

Includes previous original Part/Materials/Sketcher scopes: primitives/booleans/STEP, rational curves/construction,11 native constraint kinds, units/DOF and FCStd/preview. English/Turkish/German forms and guides cover new tools;665 reviewed TR/DE UI entries each. Advanced diagnostics retain English fallback.

Validation:1236 genuine native Sketcher JNI checks including analytic geometry, reference updates, save/reopen, history, rollback and the64-reference boundary;269 Part,88 App and62 Python regressions;527 locale checks;3 resource and9 packaging tests. Retained VM fault-handler integration and cache-free packaging remain verified. Signing/static16KiB/API26 checks are recorded separately in release gates.

Bounds:256 sketch entities/constraints;64 external edges;64 spline poles;8,192 preview points;±1,000,000mm. Single planar FlatFace/projected edges only. Other attachment modes, defining/intersection external geometry, cross-document references, trim/extend/fillet/split, touch constraint editing, PartDesign and remaining workbenches are pending. Preview is sampled local XY. Full topology-edit qualification and Android memory budgets are pending.

Android execution is NOT_RUN for this candidate. Physical launch, gestures, language, lifecycle/recovery and file-picker tests remain required. Candidate is debuggable, signed with the retained development identity for compatible updates. Keys are excluded from public assets/Git/Actions. Save/export projects before uninstalling or downgrading. Four public assets: signed APK, matching runtime, application source and frozen corresponding upstream sources.
