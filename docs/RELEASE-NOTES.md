# FreeCAD Mobile Lab 1.14

Full release of the current mobile feature set, Android code40. The signed non-debuggable ARM64 APK retains the existing update certificate. This independent project has not completed comprehensive FreeCAD/Rhino or phone qualification.

Four additional original PartDesign workflows in Document Lab:
- Linked Revolution about the owned profile's horizontal or vertical axis, with editable forward angle.
- Linked Groove that removes material through the same bounded native rotational workflow.
- Original additive ruled Loft between exactly two different owned closed sketches.
- Original subtractive ruled Loft that retains one connected solid after actual material removal.

Commands: BodyRevolve, BodyGroove, BodyAddLoft and BodySubLoft. Touch forms and English/Turkish/German guides are included. Tip, safe last-feature removal, native history, source updates, FCStd and STEP also cover these features. Saved origin/ownership lists, angular modes and loft sections are validated before native restoration.

Verification:436 original PartDesignJNI checks;2324Sketcher,269Part,88App,62Python regressions;527locale/command/fallback checks;3resource and10packaging checks.734reviewed Turkish/German entries and4localized guides. The actual APK passes v2/v3 signature/update-certificate,65JNI/69Python ARM64 libraries/extensions,16KiB and API26 loader/strong-symbol checks. Android1.14 execution is NOT_RUN; historical startup feedback was unversioned.

Limits: one connected closed solid per Body; forward one-sided rotational angles greater than0 and at most360degrees; sketch H/V axes only; exactly two whole sketches in open ruled loft mode. Source profiles are bounded, origin objects count toward1000objects, and features are limited to1024faces. Multi-section/smooth lofts, other directions/extents, history reorder, dress-up/patterns, Gui/Assembly/other workbenches and arbitrary addon FCStd remain pending. STEP transfers geometry rather than parametric history. F-Droid remains NOT_SUBMITTED. Private keys and continuation are excluded from public assets and Actions.
