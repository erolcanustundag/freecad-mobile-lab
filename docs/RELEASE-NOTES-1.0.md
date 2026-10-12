# FreeCAD Mobile Lab 1.0

First full GitHub release of the **current mobile feature set**. Native offline ARM64 Android CAD, minimum Android8/API26, targetAPI35, version code21. Independent project with selected FreeCAD functionality; full desktop FreeCAD/Rhino parity remains NOT_COMPLETE. See RELEASE-SCOPE-1.0.md and RHINO-GAPS.md.

Available: OCCT solid/profile/freeform tools with persistent recipes and Undo/Redo; Rhino-style command input, variables/measurements, layers/alignment and bounded worksheets/node graphs; jewellery helpers and limited printing/mesh analysis; software/optional GLES previews and bounded geometry exchange/A4 SVG. STL import retains the original mesh up to2,000,000 triangles/256MiB with reduced preview detail. The optional upstream FreeCAD Base/App lab supports metadata documents, expressions/transactions/groups/links, App-only FCStd, Python console/macros and one scripted metadata template. Original Part/Sketcher/PartDesign and other workbenches remain pending.

Changes from RC7: version21 release packaging disables Android debugging, updates scope/help/about and records the user's report that startup works on their phone. Existing recovery, document-lab restart, stale-runtime packaging guards and macro-bound fixes are retained. No new native geometry capability or crash root cause is claimed. Native bytes are unchanged from RC7.

The APK retains the RC7 development certificate for compatible upgrades; a dedicated production identity/signing migration remains future work. Back up projects before uninstalling, downgrading or changing certificates. No signing key is published.

Validation: rebuilt Java/DEX/resources; signaturev2/v3 and matching retained certificate;54 ARM64 JNI libraries, dependency closure,16KiB ELF/ZIP alignment, non-debuggable manifest and no network permission; portable packaging regressions and embedded Python/source concordance. Earlier matching-host CAD/core regressions remain historical evidence. One user-reported phone startup works; automated Android tests, device matrix, update/lifecycle/file-picker workflows and manufacturing calibration remain unverified.

Assets: signedAPK, full mobile public source ZIP including frozen Boost/Eigen headers, pinned native-runtime ZIP and corresponding upstream/dependency source archives. Build instructions, patches and third-party notices accompany the source. RC7 remains available separately.
