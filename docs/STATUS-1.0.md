# Product 1.0 and remaining qualification

Product **1.0 / code21** releases the current mobile feature set. Full desktop parity and the original comprehensive stable-1.0 qualification milestone remain **NOT COMPLETE**. See RELEASE-SCOPE-1.0.md and RHINO-GAPS.md. Release packaging is non-debuggable and retains the RC7 development certificate for upgrades.

The user reported on 12 October 2026: "it works on my phone". This is one user-reported startup result with no phone/OS/APK details or structured workflow logs. Android automation has not run. Crash diagnosis, repeated lifecycle/SAF/process recreation, upgrade testing, device/GPU/memory/page-size coverage and manufacturing calibration remain open. The original instant-crash root cause is unknown.

The 1.0 build changes version metadata, About text and packaging mode. Native binaries and mobile Python modules remain unchanged from RC7. The complete feature comparison and pending workbench batches are preserved. Static verification and release publication are recorded in RELEASE-GATES.json / GITHUB-PUBLICATION.json after completion.

## Historical candidate evidence

The FreeCAD 1.1.4 parity plan is `ROADMAP.md`, tracked in `FREECAD-PARITY-BATCHES.json`. B01/rc3, B02/rc4, B03/rc5 and B04/rc6 each implement four bounded engineering scopes. Rc5 adds an isolated upstream Base/App editor with typed properties, units, live expressions, native transactions/groups/links and App-only FCStd save/open. Its JNI protocol passes 88 host checks; the APK has 54 JNI libraries and 69 Python extensions, all passing static ARM64/16 KiB/loader/strong-symbol checks. Android execution has not run. Rc6 adds a persistent Python console, saved/recorded macros, available App API browser and one portable QuantityDriver scripted metadata feature, with 62 additional host checks and 88 adapter regressions passed. Part, Sketcher, PartDesign, arbitrary FCStd/addon proxy restoration, workbench/Gui bindings and the remaining modules are pending. `PARITY-B03.md` records the current boundary; the main custom fcml/OCCT workspace stays independent.

| Area | Implemented candidate scope | Open release work |
| --- | --- | --- |
| Reliability | Separate recovery launcher, software default, serial transactions, autosave backups, bounded diagnostics | Reporting-phone crash reproduction and verified fix; 20 cold starts/50 resumes; file pickers/process recreation; second device |
| Editing | Commands, Redo, orthographic views/cube, type/topology selection, bounds alignment, names/layers/lock, draft pole snaps, pivot transforms and fit selected | Device touch validation; broad constraints, rotation/scale handles and operation previews |
| Precision/data | Scalar expressions, saved variables, exact distance/numeric-angle queries, bounded worksheet and CSV | Native FreeCAD Spreadsheet/expression semantics, live CAD bindings and persistent dimensions |
| Jewellery | Templates, system-font text solids, seats/cutters, curve arrays, presets, mass/casting estimates and reference models | Independent CAD comparison, Android fonts/workflows and print/casting calibration |
| CAD history | Exact persistent operation DAG, selected-edge/face guards, curves and rectangular UV trims | General surface-loop trims/blends, advanced continuity displays and general SubD cage/conversion |
| Graphs | 40 typed kinds/80 nodes, bounded lists/points, live exact regeneration, recipes and variants | Reusable subgraphs, list mapping/filtering, cross-evaluation caches, separate lightweight preview and device verification |
| Fabrication | Restricted 3MF/GLB, DXF curves, print envelope/bed, thickness samples, planar hole caps, A4 overall-dimension sheets | Global mesh intersections, volumetric wrapping, general annotations/sheets and broader formats |
| Rendering | Software/GLES, roughness/metallic studio preview, zebra/wireframe, uncapped Z clipping, transparent PNG | Phone GPU/context/memory matrix, texture UV/environment maps/shadows and measured budgets |
| Release | Offline guides/examples, project v2 migration, input digests, repeat packaging, external-key signing path | Production identity/update migration, complete device coverage and support validation |

## Evidence

Static APK verification passed for this candidate: API 26–35/ARM64, 54 native libraries plus69 Python extensions, dependency closure, 16 KiB ELF and ZIP alignment, retained development v2/v3 signing, corrected shader and larger STL limit. APK reuses verified 0.9 native libraries; Java/assets were rebuilt with official SDK tools. JDK in the recovered environment is 17.0.20, compiled with --release 8.

For rc4 the rebuilt matching-host JNI suite passed: 25,694 baseline assertions, the 1,441,792-triangle STL fixture and 459 freeform assertions. Focused suites passed organisation65, precision math11562/native38, command180, feature44, rendering4762, mobile517 and candidate59 assertions, plus software rendering checks. The candidate checks include v1-v2 migration without source rewriting, future-version rollback, five editable sample solids/exports, two graph recipes, numeric curve/revolve/material commands, selected export-ID remapping and A4 sheets/XML rejection. The prior rc2 checkpoint also passed editing36, jewellery126, graph29, formats29 and planar-hole repair9; these unchanged workflows retain their historical evidence rather than a new device pass.

At rc2, 25 portable schema/routing and six disposable signing checks passed. Independent trimesh reads verified all five sample STL files are watertight with consistent winding; independent XML reads verified A4 units, and rendered sheets were visually checked. Current rc6 signature/alignment/native closure checks passed. Rc5 preserves the 31 mobile libraries and their rc4 native regression evidence; its new adapter passes 88 checks and organisation regression65 passed again. Repeated packaging is checked separately from runtime.

The actual production identity and Android update migration remain pending. Host tests do not prove Android process recreation or file-picker behaviour. Historical GLES tests remain historical: no new phone GPU pass is claimed.

The candidate smoke instrumentation compiled. No Android device test ran: this environment has no connected Android test surface/ADB or KVM. Earlier software emulator attempts failed before app execution; see android-smoke-results.txt.

GitHub source and the signed RC7 experimental prerelease are published. Source CI and the release workflow passed; all four asset sizes/SHA256 values match. GITHUB-PUBLICATION.json records the canonical URLs and evidence. Android/device and full parity gates remain incomplete. The retained prototype certificate is not a production identity; keys are excluded from public source. This candidate does not close all roadmap milestone gates and does not claim full Rhino features.

RC7: six portable preflight regressions pass for a stale embedded Python module, module list, JAR or native core library. All822 Python archive entries pass CRC/hash/source concordance. The isolated document lab adds a restart action that closes unsaved lab documents and returns to recovery, leaving saved files intact. Macro import errors show the actual bound. Dependency source/notices and guarded runtime restoration are packaged. These UI/process changes are compiled but not phone-tested; the unchanged native set retains earlier strong-symbol evidence, with fresh RC7 signature/loader-name/alignment checks.
