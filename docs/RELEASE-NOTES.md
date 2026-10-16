# FreeCAD Mobile Lab 1.25

Full release of the current mobile feature set, Android code51. Signed ARM64 APK retains the compatible update certificate.

Four original PartDesign Body workflows:

- AdditivePrism and SubtractivePrism: linked regular polygonal stock and cuts, with3–32 sides.
- AdditiveTorus and SubtractiveTorus: linked ring-shaped stock and channels.

Use `BodyAddPrism` / `BodySubPrism BODY NAME SIDES CIRCUMRADIUS HEIGHT` and `BodyAddTorus` / `BodySubTorus BODY NAME MAJOR_RADIUS MINOR_RADIUS`, optionally followed by `X Y Z YAW PITCH ROLL`. Touch forms and native guides support English, Turkish and German, with822 reviewed Turkish/German UI entries. `Set` accepts length units; Polygon requires an integer. `BodyPrimitivePose` moves the original feature.

229 actual JNI checks plus6 fresh-JVM checks qualify analytic volumes, native source/radius/polygon/unit edits, original history, Undo/Redo, atomic rollback,22 malformed FCStd cases, original reopening and STEP. Saved integer validation rejects fractional and exponential text before native restoration. Ring torus radii require major>minor>0; prisms retain straight end angles. Additions must add connected material; cuts must remove material and retain one closed solid. Source64faces/256edges,64primitives and1,000,000mm world budgets remain enforced.

APK static verification:134 ARM64 libraries/extensions,1083 Python assets, API26 native dependency/strong-symbol closure,16KiB alignment and compatible v2/v3 signatures. Physical Android1.25 execution is NOT_RUN. Full desktop FreeCAD/Rhino/Gui/Assembly parity is NOT COMPLETE; F-Droid submission remains pending. Next wedge/cone-sector/sphere-segment native proofs are recorded; they are not mobile features in1.25. Ellipsoid measurement accuracy remains under investigation.

All existing native regressions pass:227round/280primitive/268attachment/299Datum/302Hole/310path/1509PartDesign/2324Sketcher/269Part/88App/62Python plus527locale/3resource/10packaging checks.
