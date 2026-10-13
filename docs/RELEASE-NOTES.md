# FreeCAD Mobile Lab1.2 — full mobile feature release

Full GitHub release, Android code28, ARM64 Android8+, non-debuggable APK signed with the retained update certificate. Releases the current mobile feature set; full FreeCAD/Rhino parity and broader device qualification remain NOT_COMPLETE.

Four new original Sketcher scopes in Document Lab: trim selected curve spans; line extension/shortening; connected-line corner fillets; curve splitting. Edits use original geometry/constraint algorithms, native transactions, Undo/Redo and FCStd. Invalid picks/radii/indices and failed multi-edits roll back. Preview shows actual solved curves. Driving dimensions remain authoritative during extension. Trim without intersections may delete the entire selected entity, matching upstream behavior.

Includes all prior native App/Part/Sketcher subsets: primitives/booleans/STEP, rational curves/construction,11 constraint kinds/units/DOF, planar attachments/offsets and projected external references. Turkish/German menus and guides now contain669 reviewed UI entries each. Advanced diagnostics retain English fallback.

Validation:1310 actual native Sketcher JNI checks, including geometry lengths/arc radius, constraint updates, errors, native history and save/reopen; Part/App/Python and localization regressions are recorded separately. APK signatures, retained certificate, native loader/API26 closure and16KiB ELF/ZIP checks are required before publication.

Limits remain256 sketch entities/constraints,64 external edges/64 spline poles,8192 preview points and±1Mmm. Extension exposes line segments; fillets expose a common-endpoint pair of lines. Full constraint variants, curved-corner fillets, additional extension options, touch editing, PartDesign and remaining workbenches are pending. Native memory/runtime budgets on phones are not measured.

The user previously reported startup works on their phone; this is an unversioned report. Automated Android execution for1.2 is NOT_RUN. Physical launch/lifecycle/gestures/language/SAF and wider device coverage remain qualification work. Save/export projects before uninstalling/downgrading. Signing keys are excluded from Git, release assets and Actions.
