# FreeCAD Mobile Lab 1.19

Full release of the current mobile feature set, Android code 45. The signed ARM64 APK keeps the compatible update certificate.

Four new original PartDesign workflows:

- Additive Pipe with an owned circular section and line or circular-arc path.
- Subtractive Pipe with material-removal and closed-solid checks.
- Additive Helix around the original Body Z axis.
- Subtractive Helix with editable pitch and height.

Use BodyAddPipe, BodySubPipe, BodyAddHelix and BodySubHelix in the command bar, or the Original PartDesign touch forms. English, Turkish and German controls and guides are included. Pipes retain original profile and Edge1 spine references in Standard/Transformed/Constant mode. Helices retain the owned circle profile and original axis; Set Helix.Pitch 4 mm and Set Helix.Height 9 mm accept units.

The path tools require separate unused sketches with one geometry each and no external references or expressions. A pipe circle must be centered at the path start, normal to its tangent. Arcs are limited to 180 degrees with radius greater than twice the section radius. Helix circles lie in the XZ meridian plane entirely on positive X. Pitch must exceed the section diameter; height/pitch is limited to 16 turns. Current helix mode is forward/right-handed with zero cone angle. Stock is bounded to 64 faces/256 edges. Single-solid, positive addition/removal, ownership, history and reference checks apply; invalid operations roll back. Live sketch parameters are checked before feature recomputation, and saved scalars/modes/links before restoration.

Validation: 310 new native path JNI checks plus 1,509 existing PartDesign checks; 2,324 Sketcher, 269 Part, 88 App and 62 Python regressions; 527 language/command, 3 resource and 10 packaging checks. Analytic curved and straight sweeps, helix volumes, source/dimension/body placement updates, Undo/Redo, transactions, FCStd, STEP and malformed saved references/modes are covered. 772 reviewed Turkish/German entries and four guide types. APK verification passes 134 ARM64 libraries/extensions, 1,079 Python files, API26 loader/strong-symbol closure, 16KiB alignment and v2/v3 signatures.

Physical Android 1.19 execution is NOT_RUN. Full FreeCAD/Rhino, Gui, Assembly, workbench and addon parity remain NOT_COMPLETE. General sections, multi-edge/auxiliary paths, other helix modes, Hole and Datum workflows remain pending. F-Droid is NOT_SUBMITTED. Private signing material and continuation notes are excluded from public assets.
