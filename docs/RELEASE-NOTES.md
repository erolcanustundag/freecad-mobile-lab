# FreeCAD Mobile Lab1.2-rc3 — original Sketcher candidate

Signed ARM64 Android8+ engineering candidate, code26. Latest full release remains1.1. This is an independent project; full FreeCAD/Rhino desktop parity and device qualification remain NOT_COMPLETE.

Four new bounded modeling scopes in the isolated Document Lab:
- Original Sketcher lines/circles/arcs/ellipses with native solver movement and deletion.
- Rational B-splines and construction geometry.
- Eleven native constraint kinds, unit-aware datum editing, DOF and atomic conflict/redundancy rollback.
- Supported Sketcher FCStd save/open and sampled local XY preview with pan/pinch/fit.

Includes the previously verified original Part/Materials prerequisite: parametric primitives, expressions, linked booleans, STEP shape import/export and genuine tessellation. The unpublished rc1 APK was lost during workspace cleanup; its source/evidence remain preserved, and this replacement is rebuilt/tested/signed independently.

Turkish/German controls now include657 reviewed strings each and a native sketch guide. English fallback remains available. Sketch/Eskiz/Skizze creation aliases work; command names/geometry data remain canonical. Read the in-app Sketch guide or docs/SKETCHER-USER-GUIDE.md.

A host integration defect replaced the JVM SIGSEGV handler during FreeCAD initialization. The explicit embedded-build policy preserves VM handlers; a real JNI probe passes before/after500 repeated snapshots. Native hidden/read-only/internal properties are protected. These checks do not establish the cause of earlier phone crashes.

Validation:955 genuine Sketcher JNI/solver/geometry/FCStd assertions;269 Part,88 document and62 Python regressions;527 locale/command checks;3 resource and9 packaging tests. The APK passes retained-certificate v2/v3 signing,64 JNI libraries plus69 Python extensions,16KiB ZIP/ELF alignment and API26 strong-symbol/loader closure.1,075 runtime files are CRC/hash/source checked.

Limits:256 sketch entities/constraints;64 spline poles;8,192 preview points;coordinates within±1,000,000mm. Native work can allocate/block before adapter bounds. Preview is sampled local XY, with numeric forms/commands for editing. Attachments/external-reference UI, broader constraint variants, trim/fillet, spline handles, PartDesign and other workbenches remain pending. Arbitrary desktop/addon FCStd documents are unsupported. STEP exchanges shape geometry without modeling history/assemblies/materials.

Android execution of this candidate is NOT_RUN. Phone startup, language/gestures, lifecycle/recovery, file pickers, memory budgets and broader device coverage require testing. The candidate is debuggable and uses the retained development identity for compatible updates; no signing key is supplied in public Git/assets. Save/export projects before uninstalling or downgrading.

Four public assets: signed APK, matching native runtime, application source, and frozen corresponding upstream sources. SHA256 values are in docs/RELEASE-ASSETS.json. Publication is verified independently after upload.

APK packaging stages source assets only; generated Python cache files are excluded and explicitly rejected by verification.1.2-rc2 was never published and is superseded by1.2-rc3.
