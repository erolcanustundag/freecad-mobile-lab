# FreeCAD Mobile Lab 1.20

Full release of the current mobile feature set, Android code46. The signed ARM64 APK keeps the compatible update certificate.

Four new original PartDesign Hole workflows:

- Flat-bottom blind hole with editable diameter and depth.
- Flat through-all hole with editable diameter.
- Custom counterbore with editable hole and head dimensions.
- Custom 90degree countersink with editable hole depth/diameter and head diameter.

Use BodyHole, BodyHoleThrough, BodyCounterbore and BodyCountersink in the command bar, or Original PartDesign touch forms. English, Turkish and German controls and guides are included. A separate unused owned circle sketch supplies the hole center; actual Hole.Diameter is independent of sketch radius. The native forward cut goes down Body Z. ThroughAll removes material below the profile plane, so move the plane to the new stock top after increasing stock height. Counterbore depth or derived 90degree countersink depth must fit within the main depth; head diameter must exceed hole diameter.

Native feature modes, dimensions, dormant thread values, owned profiles and preceding source/history are validated. Invalid, nonremoving and empty results roll back. Source circles cannot carry external references or expressions. Hole profiles face positive Z in a Body XY plane. Current stock limit:64faces/256edges; dimensions are finite, positive and bounded. Threading, modelled threads, taper, angled drill points, reverse, counterdrill and other modes remain pending.

Validation:302new Hole JNI checks,310path checks and1509existing PartDesign checks;2324Sketcher,269Part,88App,62Python regressions;527language/command,3resource and10packaging checks. Analytic volumes, units, diameter/depth/head edits, source/profile/body placement updates, Undo/Redo, transactions, leaf deletion,19malformedFCStd variants, validFCStd and STEP roundtrips are covered.780reviewed TR/DE entries andfour guide types. The APK passes134ARM64 libraries/extensions,1080Python assets, API26 loader/strong-symbol closure,16KiB alignment andv2/v3signatures.

Physical Android1.20 execution is NOT_RUN. Full FreeCAD/Rhino, Gui, Assembly, workbench and addon parity remain NOT_COMPLETE. Datum construction/attachment and broader native modes remain pending. F-Droid is NOT_SUBMITTED. Private signing material and continuation notes are excluded from public assets.
