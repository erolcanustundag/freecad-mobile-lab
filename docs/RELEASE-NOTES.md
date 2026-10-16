# FreeCAD Mobile Lab 1.24

Full release of the current mobile feature set, Android code50. Signed ARM64 APK retains the compatible update certificate.

Four original PartDesign Body workflows:

- AdditiveCone and SubtractiveCone: native linked conical unions/cuts, including zero-radius apices and equal-radius cones.
- AdditiveSphere and SubtractiveSphere: native linked full-sphere unions/cuts.

Use `BodyAddCone` / `BodySubCone BODY NAME R1 R2 HEIGHT` and `BodyAddSphere` / `BodySubSphere BODY NAME RADIUS`, optionally followed by `X Y Z YAW PITCH ROLL`. Touch forms and native guides support English, Turkish and German; 815 reviewed Turkish/German UI entries. `Set` accepts length units; `BodyPrimitivePose` edits the original feature placement.

227 actual JNI checks plus6 fresh-JVM checks qualify analytic geometry, clipped source updates, dimensions/units, original history, Undo/Redo, atomic rollback,23 malformed FCStd cases, native reopening and STEP. Shared primitive budgets include64 actual connected native features and rejection of further cone/sphere operations. All existing native regressions pass:280primitive/268attachment/299Datum/302Hole/310path/1509PartDesign/2324Sketcher/269Part/88App/62Python, plus527locale/3resource/10packaging checks.

Full angular defaults/manual mapping, source64faces/256edges,64primitives and1,000,000mm world limits remain enforced. Additions must add connected material; cuts must remove material and retain one closed solid. Invalid requests roll back.

APK static verification:134 ARM64 libraries/extensions,1083 Python assets, API26 native dependency/strong-symbol closure,16KiB alignment and compatible v2/v3 signatures. Physical Android1.24 execution is NOT_RUN. Full desktop FreeCAD/Rhino/Gui/Assembly parity is NOT COMPLETE; F-Droid submission remains pending. Original torus/prism host prototypes are saved for the next batch; they are not mobile features in1.24.
