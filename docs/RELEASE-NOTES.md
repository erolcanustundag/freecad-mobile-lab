# FreeCAD Mobile Lab 1.18

Full release of the current mobile feature set, Android code44. Signed non-debuggable ARM64 APK retains the compatible update certificate. Comprehensive FreeCAD/Rhino and device qualification remain incomplete.

Four original PartDesign extrusion scopes:
- Native PadUpToFace linked to one preceding-solid planar face.
- Native PadUpToLast with automatic original-kernel stopping.
- Native PocketUpToFirst in either cut direction.
- Independent two-sided Length/Length2 for Pad and Pocket.

PadFace, PadLast, PocketFirst, PadTwo and PocketTwo commands, touch forms and EN/TR/DE guides are included. A stopping Pad must add material to the previous solid; ineffective/disconnected results roll back. Face stopping requires a parallel source plane ahead in the extrusion direction. Automatic first/last sources are bounded to64faces/256edges. Two sides uses positive separate lengths with total up to1,000,000mm and fixed direction; Length2 accepts units. All stopping extents have no editable Length. Pre-restoration native history, mode, second-side, total-length and stopping references are validated before generation.

1,509real PartDesignJNI checks;2,324Sketcher,269Part,88App,62Python regressions;527locale,3resource,10packaging checks.764reviewed TR/DE entries/4localized guides. Native geometry/source/profile/body-placement updates, Undo/Redo, atomic rollback, leaf deletion, no-op/complexity/reference guards, FCStd and STEP are tested. The actual APK passes65JNI/69Python ARM64 libraries/extensions,1078Python assets,16KiB/API26 loader/strong-symbol closure, v2/v3 signatures and compatible certificate. Physical Android1.18 execution NOT_RUN.

Limits: one connected solid, whole owned unused profiles, last solid Tip, positive bounded lengths, zero taper/offset and sketch-normal directions. Named native face references can become invalid after topology changes. Arbitrary second-side stopping, curved/external explicit stopping references, other modes, Pipe/Helix/Hole/Datum/general patterns, full Gui/workbench/Assembly/Rhino/addon qualification remain pending. Four next original Pipe/Helix host prototypes and analytical reference volumes are recorded; mobile integration remains pending. F-Droid NOT_SUBMITTED. Private signing key/continuation excluded from public assets.
