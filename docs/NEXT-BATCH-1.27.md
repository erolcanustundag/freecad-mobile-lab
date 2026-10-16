# Adaptive native mass analysis and original ellipsoid features

Preserve sealed1.26/code52. Select1.27/code53 before future application edits.

Candidate scopes: bounded adaptive BRep volume/centroid analysis, original AdditiveEllipsoid, original SubtractiveEllipsoid and native ellipsoid latitude/azimuth controls. Mobile integration remains NOT_IMPLEMENTED; Android execution is NOT_RUN.

The original FreeCAD1.1.4 TopoShapePyImp.cpp Volume getter uses the nonadaptive BRepGProp overload. A verified host C++ research probe compares that output with the original OCCT adaptive overload, Eps1e-10. For the native ellipsoid with polar radius2 and equatorial radii1, default volume8.37391650358653 differs from ideal8.377580409572781. Adaptive volume8.377580538266674 improves the observed error by more than1000x; residual ideal-volume discrepancy1.28694e-7mm³ and native shape tolerance2e-7mm are recorded. The reported quadrature error does not describe ideal-geometry conversion error. No exact-geometry or Android qualification is claimed.

Before exposure, build the same bounded native adapter on host and ARM64; verify real entrypoints, linker/API26 closure,16KiB alignment and matching source/runtime hashes. Keep the serialized BRep/input, face/edge, integration-tolerance and coordinate budgets explicit. Qualify volume sign, one closed solid, centroid/world transforms, original source/dimension/angle updates, positive material/no-op checks, true FCStd/cold restoration and STEP. Reconcile default-versus-adaptive volume wherever the new native ellipsoid workflow validates material; do not compare inconsistent integration methods or silently relabel approximate values as exact. Benchmark bounded BSpline surfaces and failure handling.

Then add native ellipsoid factories/dimension/angle guards, safe conservative world bounds, dedicated commands/forms, EN/TR/DE guides and original JNI/cold/malformed tests. Re-run the existing serial suites, build/sign/verify/seal/save the compatible APK and publish a full release after four workflows qualify. Full Gui/Assembly/FreeCAD/Rhino parity and F-Droid remain open.
