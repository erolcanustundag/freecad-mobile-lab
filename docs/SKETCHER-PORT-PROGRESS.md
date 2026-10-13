# Native Sketcher checkpoint

1.2-rc4 / code27 integrates original FreeCAD1.1.4 Sketcher App and PlaneGCS alongside genuine Part/Materials. BUILD_GUI stays off; the GUI-only SWIG/Pivy check is scoped to GUI builds. Geometry and solver implementations remain upstream.

Four bounded scopes: lines/circles/arcs/ellipses and solver-aware movement/deletion; rational B-splines and construction; native constraints/dimensions/DOF with atomic rollback; supported native FCStd persistence and sampled XY preview. Commands, forms and English/Turkish/German guides are included.

Actual host checks pass:1236 original Sketcher assertions,269 Part regressions,88 document regressions and62 Python-tooling regressions.527 portable locale/command checks,3 resource tests and9 runtime-packaging regressions pass. Tests compare solved dimensions, analytic arc length, rational weights, DOF, conflict rollback, Undo/Redo, Unicode FCStd restore and bounded preview data. See native-sketcher-results.json and real generated Sketch.FCStd/preview.json fixtures.

Testing exposed a process defect: FreeCAD startup replaced the JVM SIGSEGV handler. A host JNI probe checks the actual handler, flags and mask. FREECAD_MOBILE_EMBEDDED now suppresses this desktop registration through an explicit CMake opt-in affecting Application.cpp; default standalone behavior is preserved. The probe passes at initialization and after500 repeated native snapshots under normal JVM execution. This does not establish the cause of earlier phone crashes.

The adapter respects native hidden/read-only flags and protects internal properties. Edits use native transactions/solver calls. Conflicting or redundant constraints roll back. The API browser/console expose original Sketcher. Preview uses sampled local XY curves with pan/pinch/fit; it is not a touch editor or exact vector export.

Bounds:256 entities/constraints per sketch;64 spline poles;degree1–5;8,192 preview points;coordinates within±1,000,000mm. Native parser/solver calls can allocate/block before adapter checks; device memory/runtime is unmeasured. FCStd types remain restricted App/Part/Sketcher and the packaged QuantityDriver proxy. Arbitrary addon/PartDesign/Gui documents are rejected.

The candidate is repackaged after the fault-handler fix; final APK static verification is separate. Physical Android execution, UI layout/gestures, language switching, lifecycle/recovery and file pickers are NOT_RUN for this candidate.

B05/B06/B07 remain PENDING at their full scope. Next are trim/extend/fillet/split, richer sketch editing/diagnostics and PartDesign. Native module availability is a prerequisite, not full workbench parity.

APK packaging stages source assets only; generated Python cache files are excluded and explicitly rejected by verification.1.2-rc2 was never published and is superseded by1.2-rc3.

1.2-rc4 adds four attachment scopes: explicit XY/XZ/YZ/arbitrary placement; native planar FlatFace support/offset/detach; original projected external edges and negative-index constraints; reference-safe FCStd/history/dependency validation. Actual host fixtures check source Height/Length changes, solved endpoints, detach world-placement preservation, native save/reopen, deletion of dependent constraints, 64-edge boundary, rejected cyclic/missing/collapsed references, atomic rollback and unsupported attachment restore. Opening an already-open file now rejects explicitly, preventing the native open API from reusing or closing the prior document during failed restoration.

Only single planar FlatFace support and projected reference edges are exposed. External defining/intersection variants, curved-face attachment, full attachment modes, cross-document references and full topological-edit qualification remain pending. Native topology machinery is retained; numbered input refers to current lists and must be reviewed after major topology changes. The world placement is shown in summaries; sampled preview remains sketch-local XY. External curves are magenta. External references are bounded at64 and preview at8,192 total points.
