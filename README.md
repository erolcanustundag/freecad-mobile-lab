# FreeCAD Mobile Lab

**Current release: 1.2 / Android version code 28, current mobile feature set.** Native CAD for ARM64 Android 8+ (min API26, target35). **Full desktop FreeCAD/Rhino parity and the original comprehensive qualification milestone are NOT COMPLETE.** This is an independent project, not an official FreeCAD Android release.

The main workspace uses OCCT 7.9.2 and the upstream FreeCAD PlaneGCS solver. An optional document lab embeds upstream FreeCAD 1.1.4 Base/App, CPython3.13 and headless Qt6.8.3. Models stay on the device; the app requests no network permission.

Engineering candidate: **1.2-rc4 / code27** adds original Part/Materials and Sketcher to the isolated document lab: native parametric solids/booleans and STEP exchange; sketch lines/circles/arcs/ellipses, rational B-splines/construction, native constraints/DOF/units, Undo/Redo, supported FCStd and sampled XY preview. This checkpoint adds free sketch planes/arbitrary placement, planar face attachment/offset/detach, projected external edges with solver constraints, and reference-safe persistence/history.1236 real Sketcher JNI checks and269/88/62 Part/document/Python regressions pass. The signed APK has64 ARM64 JNI libraries plus69 Python extensions and16KiB/static loader verification. Android execution of this candidate remainsNOT_RUN. See [Sketch guide](docs/SKETCHER-USER-GUIDE.md), [Sketch evidence](docs/SKETCHER-PORT-PROGRESS.md) and [Part guide](docs/PART-USER-GUIDE.md). The current full release1.2 includes these native scopes.

[Download the signed1.2-rc4 candidate APK](https://github.com/erolcanustundag/freecad-mobile-lab/releases/download/v1.2-rc4/FreeCAD-Mobile-Lab-1.2-rc4-arm64.apk) or open the [candidate release](https://github.com/erolcanustundag/freecad-mobile-lab/releases/tag/v1.2-rc4). The candidate is debuggable;1.2 is the current full release.

## Languages

English, Turkish and German core interface text is available. Use **Workspace → Language**, the recovery-screen Language button, or the `Language` / `Dil` / `Sprache` command. The choice applies without restarting the CAD kernel and persists across the separate processes. Automatic mode follows the phone language and falls back to English for unsupported languages. Model names, expressions, numeric storage and canonical command tokens keep their original values. Advanced kernel/Python diagnostics and untranslated technical reference text use English fallback.

## Install and start

Download the [signed1.2 APK](https://github.com/erolcanustundag/freecad-mobile-lab/releases/download/v1.2/FreeCAD-Mobile-Lab-1.2-arm64.apk) from the [1.2 full release](https://github.com/erolcanustundag/freecad-mobile-lab/releases/tag/v1.2). See [publication verification](docs/GITHUB-PUBLICATION.json). APKs belong in Releases because they exceed GitHub's regular Git file-size limit. The APK is not debuggable and retains the RC7 development certificate for compatible upgrades. A dedicated production signing identity and its migration remain future work.

Software rendering is the default. The recovery screen can open an empty workspace, retain recovery copies, and export local crash reports. OpenGL is optional. On 12 October 2026, the user reported that the app works on their phone. This is one user-reported startup result; device details, broader workflows and independent crash diagnosis remain open. RC7 adds an explicit document-lab restart for failed initialization or stuck script/native calls; unsaved lab documents close when restarted.

Try these commands in the CAD workspace:

```
Box 20 10 4
Rename "My box"
Fit
Help
```

Save `.fcml` projects and export backups before uninstalling or downgrading. In the optional document lab, try `NewDoc Model`, `Add Source Feature`, `AddProperty Source Width Length`, and `Set Source.Width 2 cm`. Save native FCStd before closing that process.

## Implemented scope

| Area | Available |
| --- | --- |
| CAD workspace | Exact primitives, booleans, profiles, extrusion/revolve/loft/sweep, bounded NURBS/patch tools, feature recipes and Undo/Redo |
| Access and organisation | Rhino-style commands, saved scalar variables, measurements, pivot transforms, view cube, bounded worksheet/CSV, alignment, fit selected and layers |
| Fabrication and display | Jewellery templates, print envelope, sampled thickness, planar mesh repair, software/GLES preview, materials/clipping/PNG and limited A4 SVG |
| Native document lab | Original App/Part/Sketcher subset: units/expressions/history, primitives/booleans, constrained sketches/attachments/external edges and whitelisted native FCStd |
| Python lab | Console, saved/recorded macros, App API browser and one portable QuantityDriver FeaturePython template |

The document lab is separate from the custom CAD recipe graph. The1.2 candidate includes the bounded native Part adapter described above; the complete Part workbench UI remains pending. The candidate includes the bounded original Sketcher adapter; its full workbench UI remains pending. It does **not** yet provide PartDesign, Assembly, TechDraw, CAM, FEM or BIM workbenches. Arbitrary FCStd and addon proxy classes are unsupported. Supported file formats and losses are documented in [FORMAT-LIMITS](docs/FORMAT-LIMITS.md). STL import is bounded to2,000,000 triangles/256MiB; display reduction preserves the stored source.

The [roadmap](docs/ROADMAP.md) covers the frozen FreeCAD1.1.4 scope in36 broad batches. Large scopes require additional batches. The [ledger](docs/FREECAD-PARITY-BATCHES.json) separates engineering evidence from device validation. Four bounded feature batches have APK checkpoints; remaining workbench batches and device gates remain pending.

See [1.0 scope](docs/RELEASE-SCOPE-1.0.md) and [Rhino/FreeCAD gaps](docs/RHINO-GAPS.md) for the next priorities. Version 1.0 freezes the current tools; it does not implement the remaining workbenches.

## Build

Required: Linux, Python3.12+, JDK17, Android SDK platform35/build-tools35.0.0. NDK27.2.12479018, CMake and Ninja are additionally needed for native source rebuilds. Git contains application/bridge/solver sources and dependency checksums. The full public source ZIP supplies the frozen Boost/Eigen header trees; the runtime ZIP supplies binaries; the corresponding-source ZIP supplies upstream sources and OCCT. All are release assets.

Use the native runtime release asset matching the release metadata. Verify its SHA256 and extract it at the repository root. The1.1 asset supplies54 ARM64 libraries; the1.2 asset supplies64. Both include Qt6Android.jar and the embedded Python archive. No signing key is included in Git or public source archives. A new local development key is generated if needed; it differs from the certificate on the published prototype APK and cannot upgrade that installation in place.

```bash
export JAVA_HOME=/path/to/jdk17
export ANDROID_SDK_ROOT=/path/to/android-sdk
python3 scripts/bootstrap_release_runtime.py --bundle /path/to/native-runtime.zip
python3 scripts/bootstrap_vendor_sources.py --bundle /path/to/FreeCAD-Mobile-Lab-1.1-public-source.zip
python3 scripts/check_core_runtime_inputs.py
# Choose a new development version before modifying sealed app inputs.
python3 scripts/set_release.py 1.2 28 '' --channel release
python3 scripts/build_apk.py --prebuilt --upstream-core
python3 scripts/verify_apk.py
```

After editing mobile Python modules, run `scripts/refresh_python_assets.py`. The build now rejects source/archive drift before packaging. `--reproduce` requires unchanged sealed inputs and a local signing identity; signature equality with the published prototype is not promised.

For full native rebuilds, read [CORE-PORT](docs/FREECAD-CORE-PORT.md), the source/toolchain manifest and the build scripts. The public corresponding-source archive includes frozen FreeCAD/Qt/Python/dependency sources, mobile OCCT/solver code and integration patches. Source fetching overwrites extracted upstream trees; apply the checked-in patches afterward. Modified libraries can be relinked and packaged with your own certificate. Export projects before replacing an installation signed with another certificate.

## Verification and bugs

Historical matching-host evidence includes25,694 CAD assertions, a1,441,792-triangle STL fixture,459 freeform checks,88 upstream JNI document checks and62 Python-tooling checks. RC7 adds packaging regressions against stale Python/JAR/native inputs. APK signatures, ARM64 dependency closure and16KiB alignment are checked independently.

**One user-reported phone startup works; broader device qualification pending.** Automated Android tests have not run. Source CI checks syntax, release metadata and portable packaging regressions. Native runtime, gestures, file pickers, process recreation and crash reproduction require Android execution. See [DEVICE-TESTS](docs/DEVICE-TESTS.md) and [STATUS](docs/STATUS-1.0.md). Report bugs with APK version, phone/Android version, steps and a redacted recovery report.

## Licences

Application source is LGPL-2.1-or-later; each upstream component retains its own licence and notices. OCCT uses LGPL2.1 with its exception; FreeCAD is LGPL2.1-or-later; Qt includes LGPL3/GPL3 notices; CPython uses the PSF licence; Boost, Eigen, meshoptimizer and Python/native dependencies have their respective licences. See [THIRD-PARTY](docs/THIRD-PARTY.md), bundled notices, exact source archives and build/patch instructions. There is no affiliation with the FreeCAD or Rhino vendors.

1.2/code28 adds original Sketcher trim, line extend/shorten, connected-line corner fillet and curve split. Native constraint updates, rollback, Undo/Redo and FCStd are covered by1,310 Sketcher checks. Full GitHub release, non-debuggable APK, retained update certificate. Device qualification and full desktop parity remain pending. Turkish/German controls and guides include669 reviewed entries each.
