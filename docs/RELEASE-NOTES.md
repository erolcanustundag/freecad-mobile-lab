# FreeCAD Mobile Lab 1.17

Full release of the current mobile feature set, Android code43. Signed non-debuggable ARM64 APK retains the compatible update certificate. Comprehensive FreeCAD/Rhino and device qualification remain incomplete.

Four original PartDesign extrusion scopes:
- Reversed direction for length Pad and Pocket.
- Symmetric Pad/Pocket using half the total length on each side.
- Native ThroughAll Pocket in either cut direction.
- Native UpToFace Pocket linked to one preceding-solid planar face.

Pad/Pocket commands accept optional forward/reverse/symmetric. PocketThrough and PocketFace commands, touch forms and EN/TR/DE guides are included. Stopping faces must be parallel to the sketch and ahead in the cut direction. Native ownership/history/source updates, both cut directions, body placement, Undo/Redo, leaf deletion, atomic rollback, FCStd and STEP are qualified. Through/face modes have no editable Length. Fixed the legacy saved-file guard that conflicted with the new extent modes; pre-restoration mode/second-side/taper/offset/vector/reference guards reject unsupported and foreign/cyclic selections.

1,149real PartDesignJNI checks;2,324Sketcher,269Part,88App,62Python regressions;527locale,3resource,10packaging checks.757reviewed TR/DE entries/4localized guides. Malformed fixture generation uses bounded console calls with the unchanged two-second Python tracing limit. The actual APK passes65JNI/69Python ARM64 libraries/extensions,1078Python assets,16KiB/API26 loader/strong-symbol closure, v2/v3 signatures and compatible certificate. Physical Android1.17 execution NOT_RUN.

Limits: one connected solid, whole owned unused profiles, positive lengths up to1,000,000mm; zero taper/offset, sketch-normal directions, one side or symmetric total length. Pocket stopping uses one current FaceN on the preceding owned solid; topology-changing edits can invalidate named references and are rejected. Two independent sides, curved/external stopping faces, other stopping/Pad modes, arbitrary axes, full patterns/dress-up/PartDesign/Gui/workbench/Assembly/Rhino/addon qualification remain pending. F-Droid NOT_SUBMITTED. Private signing key/continuation excluded from public assets.
