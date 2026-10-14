# FreeCAD Mobile Lab 1.13

Full release of the current mobile feature set, Android code39. The non-debuggable ARM64 APK retains the existing update certificate. This is an independent Android CAD project; comprehensive FreeCAD/Rhino parity is NOT_COMPLETE.

Four original PartDesign workflows in Document Lab:
- Native Body with protected origin frames, sketch ownership and linked independent BaseFeature.
- Owned Tip selection and dependency-safe last Pad/Pocket deletion with native history/rollback.
- Linked original Pad from one valid closed owned sketch, using one-sided Length mode.
- Linked original Pocket that removes real material and retains one connected solid.

Touch controls, quick commands (Body, BodyFrom, BodySketch, Pad, Pocket, BodyTip, RemoveBodyFeature, BodyInfo) and English/Turkish/German guides are included. Native origin objects count toward the1000-object limit. Saved Pad/Pocket lengths and unsupported modes are rejected before restore/recompute. The APK embeds the genuine original ARM64 PartDesign module and unchanged Python wrapper.

Verification:213 real PartDesignJNI checks;2324Sketcher,269Part,88App,62Python regressions;527language command/fallback checks;3resource and10packaging checks. Actual APK static proof covers65JNI libraries/69Python extensions,16KiB alignment, API26 strong-symbol/dependency closure, v2/v3 signatures and compatible certificate. Physical Android1.13 execution is NOT_RUN; historical startup feedback was unversioned.

Current limits: single connected solid per Body; one closed wire/profile up to256edges; feature up to1024faces; positive length up to1,000,000mm; one-sided Length mode only. Full PartDesign modes, reorder, patterns/dress-up, Gui/Assembly/other workbenches and arbitrary addon FCStd remain pending. Native topology edits may change face names. STEP transfers shape geometry, not parametric history. F-Droid remains NOT_SUBMITTED pending clean native source integration. Private keys are excluded from public assets and Actions.
