# FreeCAD Mobile Lab 1.26

Full release of the current mobile feature set, Android code52. Signed ARM64 APK retains the compatible update certificate.

Four original PartDesign Body workflows:

- AdditiveWedge and SubtractiveWedge with signed/slanted native endpoint rectangles.
- Cone sector azimuth control through `BodyConeAngle BODY FEATURE ANGLE`.
- Sphere latitude/azimuth control through `BodySphereAngles BODY FEATURE LOWER_LAT UPPER_LAT AZIMUTH`.

`BodyAddWedge` / `BodySubWedge BODY NAME XMIN XMAX YMIN YMAX ZMIN ZMAX X2MIN X2MAX Z2MIN Z2MAX` accepts optional `X Y Z YAW PITCH ROLL`. `Set` accepts length units for wedge coordinates. Endpoint rectangles must have positive dimensions; cone azimuth is positive up to360degrees; sphere latitudes are ordered within-90..90 and azimuth is positive up to360degrees. Dedicated angle controls preserve original native features and history. Touch forms and native guides support English, Turkish and German, with839 reviewed Turkish/German entries.

204 actual JNI checks plus6 fresh-JVM checks qualify analytic wedge/sector volumes, source clipping and swallowing/no-op rollback, native dimension/units/history, Undo/Redo, atomic rollback,17 malformed FCStd cases, original reopening and STEP. Source64faces/256edges,64primitives, one connected closed solid, positive material change and1,000,000mm world budgets remain enforced.

APK static verification:134 ARM64 libraries/extensions,1083 Python assets, API26 native dependency/strong-symbol closure,16KiB alignment and compatible v2/v3 signatures. Physical Android1.26 execution is NOT_RUN. Full desktop FreeCAD/Rhino/Gui/Assembly parity is NOT COMPLETE; F-Droid submission remains pending. Adaptive volume/ellipsoid host research is saved for the next batch and is not a mobile feature in1.26.

All existing native regressions pass:229torus/prism/227round/280primitive/268attachment/299Datum/302Hole/310path/1509PartDesign/2324Sketcher/269Part/88App/62Python plus527locale/3resource/10packaging checks.
