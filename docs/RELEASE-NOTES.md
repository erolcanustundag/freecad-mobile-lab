# FreeCAD Mobile Lab 1.23

Full release of the current mobile feature set, Android code49. Signed ARM64 APK with the compatible update certificate.

Four original PartDesign workflows in the native Document Lab:

- AdditiveBox: linked native box union.
- SubtractiveBox: linked native box cut.
- AdditiveCylinder: linked native cylinder union.
- SubtractiveCylinder: linked native cylinder cut.

BodyAddBox, BodySubBox, BodyAddCylinder and BodySubCylinder accept dimensions and optional X/Y/Z/yaw/pitch/roll. BodyPrimitivePose moves an owned primitive. Set FEATURE.Height 2 cm edits an original quantity; Length/Width/Radius are available where applicable. PartDesign touch forms and EN/TR/DE guides are included. Native BaseFeature links, preceding-solid history and Tip remain editable. Source dimensions and placements update actual downstream geometry. Original Datum references can attach to primitive faces/edges/vertices.

An additive primitive must add material and retain one connected solid. A subtractive primitive needs existing stock, must remove material and must retain one closed solid. Empty, no-op, disconnected, foreign or branched edits roll back. Dimensions and projected world bounds are checked before computation/restoration. Modes, engines, offsets, angles, suppression, tolerance, saved history and placements are guarded. Dedicated tools protect native ownership and placement.

Limits:64primitives per document; sources up to64faces/256edges; world coordinates within1,000,000mm. Cylinders use full360degree geometry with straight default ends. Mapping is original AttachEngine3D/Deactivated with identity offset. Expressions, mapped/partial primitives and other primitive types remain pending.

Validation:278new JNI workflow checks plus6fresh-JVM checks, including64actual connected primitives and limit rollback.19malformedFCStd variants, analytical native volumes, source/unit/pose/world transforms, original references, UndoRedo/atomic rollback, cold restoration and material STEP. Regressions:268attachment+10cold,299Datum+13cold,302Hole,310path,1509PartDesign,2324Sketcher,269Part,88App,62Python,527language/command,3resource and10packaging pass.809reviewed TR/DE entries and localized native guides. APK134ARM64 libraries/extensions and1083Python files pass API26strong-symbol/loader closure,16KiB alignment andv2/v3signature checks. Native library bytes remain unchanged; the four original ARM64 class names are present.

Physical Android1.23 execution is NOT_RUN. Full workbench/Gui/Assembly/FreeCAD/Rhino parity remains NOT_COMPLETE. F-Droid NOT_SUBMITTED. Signing key and private continuation are excluded from public assets. Native cone/sphere prototypes are saved for the next batch and are not mobile features of this release.
