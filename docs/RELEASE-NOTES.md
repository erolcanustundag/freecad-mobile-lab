# FreeCAD Mobile Lab 1.21

Full release of the current mobile feature set, Android code47. Signed ARM64 APK retains the compatible update certificate.

Four original non-solid PartDesign construction workflows:

- Owned Datum planes with manual display sizing.
- Owned Datum axes with manual display length.
- Owned Datum points.
- Owned coordinate systems.

Native ObjectXY/AttachmentSupport on a whole owned plane or frame drives a sketch and its original Pad, Hole, Pipe or Helix. DatumPose changes the native reference; dependent geometry follows. SketchDetach retains the current placement while removing its support. Used references cannot be removed. Solid history and Tip remain separate from construction objects; construction-only Bodies can move without inventing solid measurements.

BodyPlane, BodyAxis, BodyPoint, BodyFrame, DatumPose, BodySketchDatum, DatumInfo, DatumPreview and RemoveDatum commands and touch forms are included with EN/TR/DE guides. Finite world-space guides and native frame inspection replace generic tessellation for mathematically unbounded references. Plane/axis display dimensions are viewport sizes, not material boundaries. Construction references and linked instances have no material mesh, solid measurements or STEP export; export a driven solid.

Fixed infinite-axis FCStd cache loss by marking the derived Shape transient. The original native constructor recreates the actual analytic line; placement/direction persist. A fresh JVM/interpreter verifies this independently of the saving process. Saved modes, whole owned support links, placement/quaternion, sizing and sketch geometry/constraint/reference counts are checked before native restoration.

Validation:299Datum JNI workflow checks plus13cold-JVM checks,302Hole,310path and1509existing PartDesign checks.2324Sketcher,269Part,88App,62Python,527language/command,3resource and10packaging regressions. Includes source/rotation/Body placement and dimensions, closed-solid volumes, original references, detach/UndoRedo, atomic rollback,18malformedFCStd variants, validFCStd and materialSTEP.800reviewed TR/DE entries/four guide types. APK134ARM64 libraries/extensions,1081Python files, API26 loader/strong-symbol closure,16KiB alignment andv2/v3signatures verified.

Limits:64Datums and64ObjectXY-attached sketches; display dimensions up to10,000mm; world coordinates within1,000,000mm; one whole same-Body plane/frame support; manual Datum placement; no offsets, external geometry or expressions in attached sketches. Existing FlatFace workflows remain separate. Other attachment/Datum modes, axis/point supports, Gui/Assembly/full FreeCAD/Rhino parity remain NOT_COMPLETE. Physical Android1.21 execution is NOT_RUN. F-Droid NOT_SUBMITTED. Private key and continuation excluded from public assets.
