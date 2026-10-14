# FreeCAD Mobile Lab 1.16

Full release of the current mobile feature set, Android code42. Signed non-debuggable ARM64 APK retains the compatible update certificate. Comprehensive FreeCAD/Rhino and device qualification remain incomplete.

Four original PartDesign pattern tools:
- Mirrored about an owned original Body XY/XZ/YZ plane.
- Forward LinearPattern with one total extent along an original Body X/Y/Z axis.
- Forward PolarPattern with a bounded total angle about an original Body axis.
- Scaled pattern growing about the native additive source centre of mass.

Commands BodyMirror, BodyLinear, BodyPolar and BodyScaled, touch forms and EN/TR/DE guides are included. Patterns transform one last owned Pad/Revolution/AdditiveLoft in original Features mode. Counts2–16, growth factors greater than1 up to4 and source complexity are checked before native generation/restoration. Copies must remain one connected solid. Native source updates, owned Tip/history/removal, rollback, FCStd and STEP are tested.

796real PartDesignJNI checks;2324Sketcher,269Part,88App,62Python regressions;527locale,3resource,10packaging checks.751reviewed TR/DE entries/4localized guides. The large Sketcher run initially timed out under concurrent work and completed on isolated retry; progress markers are retained. The actual APK passes65JNI/69Python ARM64 libraries/extensions,1078Python assets,16KiB/API26 loader/strong-symbol closure, v2/v3 signatures and compatible certificate. Physical Android1.16 execution NOT_RUN.

Limits: one supported owned additive source up to64faces/256edges; explicit whole Body origin references; forward extent modes; one linear direction;2–16 occurrences including original; scale growth>1≤4. Multi-source, subtractive/dress-up/pattern sources, arbitrary directions, spacing/second directions, general MultiTransform and other modes remain pending. Full Gui/workbench/Assembly/Rhino/device qualification and arbitrary addon FCStd remain pending. F-Droid NOT_SUBMITTED. Private signing key/continuation excluded from public assets.
