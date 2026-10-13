# Mobile release1.11/code37

Four new original Part scopes: regular polygon, ellipsoid, linked refinement, and linked orientation reversal. Each has commands, native document history, source dependency checks and FCStd persistence. These are in the isolated Document Lab; the main custom workspace remains separate.

2224 native JNI checks plus269 Part/88 App/62 Python regressions;3 locale resource and9 packaging tests. Native test execution is Linux reference only; Android launch/lifecycle/touch/SAF for1.11 areNOT_RUN. Native binaries unchanged. No full FreeCAD/Rhino/PartDesign claim.

Polygon sides3–128; XYZ ellipsoid semiaxes positive and bounded. Native Radius3=0 retains upstream legacy Y=X. Only full ellipsoids supported. Original BRep conservative bounds and finite volume integration are documented. LinkedRefine follows parent edits; old PartRefine is a labelled snapshot. Reverse flips orientation without changing material size. ShapeInfo volume sums absolute closed-solid integrals; oriented_volume_mm3 reports signed integral. Compound is aggregation, not Boolean union. Inward shell checks use positive component volume consistently; native reversed-source shell fallback is rejected.

APK staging also excludes temporary archives and partial downloads.

Numeric native dimensions and offsets are bounded before recompute; polygon side expressions unsupported and oversized stored polygons rejected before load. Expressions/complex native kernels do not have a global hard CPU/memory guarantee.

Compatible development signing identity retained and excluded from public source/assets. F-Droid remains NOT_SUBMITTED; clean reproducible source-build admission and broader device qualification are pending.
