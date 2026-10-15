# FreeCAD Mobile Lab 1.22

Full release of the current mobile feature set, Android code48. The signed ARM64 APK retains the compatible update certificate.

Four original native attachment workflows:

- Datum Plane: FlatFace on one planar face of an owned Body solid.
- Datum Axis: Tangent along one straight edge of an owned Body solid.
- Datum Point: Vertex on one vertex of an owned Body solid.
- Sketch ObjectXY: native translation/rotation AttachmentOffset on an owned Datum plane or coordinate system.

DatumAttach BODY DATUM SOLID ELEMENT preserves original support references and follows source dimensions. DatumDetach BODY DATUM retains the current pose; detach before using DatumPose. SketchOffset composes the original source frame and offset before dependent checks. Pad, Hole, Pipe and Helix are exercised with native offsets. Touch forms, Rhino-style command input and EN/TR/DE native guides are included. DatumInfo reports the native support; DatumPreview shows finite construction guides.

Guards cover supported engines/modes, current element kind/number, source geometry, same-Body ownership, dependency cycles, finite offsets, direct-placement protection and safe removal. Saved references/counts/modes/offsets and dependency cycles are checked before native restoration. Sources are limited to64faces/256edges/512vertices; curved or multiple supports and mapped coordinate systems remain pending. Datum roots retain identity offsets; ObjectXY sketches accept finite normalized offsets within the1,000,000mm geometry budget. External geometry and expressions in those sketches remain pending.

Validation:268new JNI workflow checks and10fresh-JVM checks;299Datum+13cold-JVM,302Hole,310path,1509PartDesign,2324Sketcher,269Part,88App,62Python,527language/command,3resource and10packaging regressions pass. Coverage includes native analytic solids, source edits, Body/world transforms, offset composition and dependent preflight, UndoRedo/atomic rollback,19malformedFCStd variants, native close/reopen, cold restoration and material STEP.804reviewed TR/DE entries. APK134ARM64 libraries/extensions and1082Python files pass API26strong-symbol/loader closure,16KiB alignment andv2/v3signature checks. Native library bytes remain unchanged.

Release manifests now distinguish this version's untested Android execution from the earlier unversioned user startup report. Physical Android1.22 execution is NOT_RUN. Full workbench/Gui/Assembly/FreeCAD/Rhino parity remains NOT_COMPLETE. F-Droid NOT_SUBMITTED. Signing key and private continuation are excluded from public assets.
