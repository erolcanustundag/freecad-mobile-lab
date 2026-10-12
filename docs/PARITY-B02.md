# B02 — document organisation (1.0-rc4)

Four implemented feature scopes: bounded mobile spreadsheet/editor/CSV exchange; bounding-box alignment; fit selected; layer visibility/locking. The worksheet persists in fcml/autosave and Undo/Redo, accepts cell/document-variable formulas, and supplies evaluated numeric command arguments. It does not implement native FreeCAD Spreadsheet or live model bindings. See `BATCH02-USER-GUIDE.md` for commands and limits.

Fixed: restoring project metadata now synchronises the native workspace before a later Undo/Redo; empty quoted command arguments can clear a cell; GPU picking uses the current scene-frame centre after updates. Alignment translates exact native CAD and regenerates custom dependants. Layer actions preserve individual object properties. Focus shares immutable mesh/material arrays rather than duplicating geometry.

Host verification with matching OCCT 7.9.2:

| Suite | Result |
| --- | --- |
| Worksheet/CSV/persistence/Undo, alignment/layers/focus | 65 assertions passed |
| Precision math / native integration | 11,562 / 38 passed |
| Command integration | 180 passed |
| Candidate integration | 59 passed |
| Feature graph | 44 passed |
| Rendering/material/clipping | 4,762 passed |
| Mobile geometry/selection math | 517 passed |
| CAD baseline | 25,694 passed, dense 1,441,792-triangle STL preserved |
| Freeform CAD | 459 passed |
| Software rasterisation/camera/picking | Passed |
| Android APK | Built; retained development certificate; v2/v3 signature, 31-library ARM64 closure, 16 KiB ELF/ZIP checks passed |
| Android instrumentation | Compiled; execution NOT_RUN |

These checks exercise host CAD and mathematical behaviour, and static APK contents. No Android phone was connected. Worksheet touch/SAF/lifecycle, focus gestures/GPU and the reported instant-crash cause remain unverified on a phone. Stable 1.0 and full desktop FreeCAD parity remain NOT_COMPLETE. Native ARM64 CAD libraries remain hash-identical to the pinned 0.9 baseline.
