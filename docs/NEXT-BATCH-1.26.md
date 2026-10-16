# Original Body wedges and cone/sphere angular controls

Preserve sealed1.25/code51. Select1.26/code52 before application edits.

Four candidate scopes: original AdditiveWedge/SubtractiveWedge and native cone azimuth / sphere latitude-and-azimuth controls. The native prototype checks analytic tapered rectangular wedges, cone sectors, spherical segments, upstream source/dimension edits, native history, Undo, Body pose and true FCStd reopening. Mobile integration remains NOT_IMPLEMENTED; Android execution is NOT_RUN.

Wedges use ten native PropertyDistance fields Xmin/Xmax/Ymin/Ymax/Zmin/Zmax/X2min/X2max/Z2min/Z2max. Qualify finite ordered endpoint rectangles, possible triangular degeneracies separately, and conservative world bounds before native recomputation. Preserve source, topology, count, positive material, single-solid, manual mapping and history guards. Cone Angle is azimuth; Sphere uses Angle1/Angle2 latitude and Angle3 azimuth. Only qualified numeric ranges and dedicated operations should change these modes; update saved-file and regression fixtures deliberately when formerly restricted modes become supported.

Add actual JNI/cold geometry/units/history/rollback/FCStd/malformed/STEP checks and EN/TR/DE command/forms/guides. Build/sign/verify/seal/save another APK and publish a full release after four workflows qualify. Ellipsoid accuracy, arbitrary mapped/expressed primitives, Gui/Assembly/full FreeCAD/Rhino parity and F-Droid remain open.

## Integration checkpoint

Implemented in1.26 with204actualJNI+6cold-JVM checks, bounded native history/geometry/restoration and localized controls. See native-partdesign-wedge-sector-results.json. Physical Android execution remains NOT_RUN; earlier notes describe the pre-integration checkpoint.
