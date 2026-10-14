# FreeCAD Mobile Lab 1.15

Full release of the current mobile feature set, Android code41. Signed non-debuggable ARM64 APK with the retained compatible update certificate. Comprehensive FreeCAD/Rhino and phone qualification remain incomplete.

Four original PartDesign Body finishing tools:
- Linked fillet with explicit current edge selections and editable radius.
- Linked equal-distance chamfer with explicit edges and unit-aware size.
- Planar draft about the original Body local Z axis, with a source neutral face.
- Inward skin/arc thickness with selected open faces and actual material-removal validation.

Commands BodyFillet, BodyChamfer, BodyDraft and BodyThickness, touch forms, EN/TR/DE guides and742reviewed Turkish/German entries are included. Native ownership, source/current Tip, topology selections, rollback/history, saved parameter/mode/origin-role guards are retained. Member feature placement follows Body history; whole Body placement works. PartDesign is exposed in the original API browser and Python console.

Verification:612real PartDesignJNI checks;2324Sketcher,269Part,88App,62Python regressions;527locale/command checks;3resource and10packaging checks. Actual APK proof verifies65JNI/69Python ARM64 libraries/extensions,1078Python assets,16KiB/API26 loader/strong-symbol closure, v2/v3 signatures and compatible certificate. Physical Android1.15 execution is NOT_RUN.

Limits:1–32 explicit finishing edges;1–16 faces; positive lengths below the minimum source extent. Inward thickness is below half the minimum extent and must retain one closed connected solid while removing material. Draft is planar, positive up to45degrees, with a different neutral plane perpendicular to local Z. Other modes/axes, variable radii, patterns, arbitrary workbench/addon FCStd, Gui/Assembly and manufacturing/device qualification remain pending. STEP transfers geometry, not native history. F-Droid NOT_SUBMITTED. Private keys/continuation are excluded from public assets/Actions.
