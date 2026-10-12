# Upstream FreeCAD document-core port checkpoint

Target: the frozen FreeCAD **1.1.4** source, SHA256 `b95270a74a26dbdde331c6ff8e764289da6c77713e2b2d4e0c0041dfe1950f3f`. This is a genuine build of upstream Base/App and its Python entrypoint, separate from the custom mobile OCCT adapter. All workbench modules and the desktop GUI are disabled in this first reference build. **Rc5 packages this core in an opt-in isolated document lab. JNI integration is implemented and host-tested; Android execution has not run. Rc4 and earlier retain the custom mobile runtime.**

## Verified progress

| Proof | Result |
| --- | --- |
| Upstream headless host Base/App, CLI and Python module | Built, FreeCAD reports 1.1.4 |
| Native document reference fixture | 28 checks passed: typed length properties, units, live expressions, graph direction, transaction Undo/Redo/abort, groups, links and FCStd restoration/recompute |
| CPython 3.13.16 ARM64/API26 | Cross-built with upstream Android tooling; 82 shared libraries checked for 16 KiB alignment; device NOT_RUN |
| Qt 6.8.3 Core/XML/Concurrent/Network ARM64/API26 | Built from source with NDK27c; all four libraries have 16 KiB LOAD alignment |
| Boost 1.87 program_options/regex/thread/date_time | Cross-built, ARM64/16 KiB verified |
| ICU74.2, Xerces3.2.5, fmt11.1.4, yaml-cpp0.8, pybind11 headers | Cross-built/installed into the isolated Android prefix |
| Upstream Base/App and FreeCAD.so ARM64 | Cross-built successfully |
| Combined static core/dependency verification | 92 unique shared libraries: ARM64, 16 KiB, loader-name closure and strong-symbol availability against the provided libraries/API26 stubs passed |
| Rc5 JNI adapter and readable commands | 88 host checks passed; ARM64 bridge built |
| Rc5 actual packaged runtime | 54 JNI libraries + 69 Python extensions, 820 assets; static architecture/16 KiB/loader/strong-symbol checks passed |
| Retained mobile libc++ versus restored NDK | Same 2,336 dynamic exports; differing file digests are not used as an ABI-equivalence claim |

Static symbol availability is checked across the supplied library set. Qt Java/JNI context, isolated PyConfig, private assets and serialized document calls are implemented, but their target namespace/initialization/runtime behaviour still needs Android execution. The adapter registers the upstream PyInit_FreeCAD entrypoint as a built-in Python module; staging renames FreeCAD.so to libFreeCADPython.so with matching SONAME/bridge dependency. Host proof and packaging do not establish a working phone port.

The reference fixture and JSON expectations are in `samples/upstream-core/`. The saved file contains Width25/Driven50 mm; the post-restoration edit to Width32 mm must recompute Driven64 mm. It contains App objects, not Part solids. It does not establish native geometry workbench or arbitrary FCStd compatibility.

## Build repairs and dependency decisions

- Even `BUILD_GUI=OFF` requires Qt Core/Concurrent/Network/XML. Base/App also generate translations, but upstream Qt setup initially requested LinguistTools only with GUI enabled. `vendor/freecad-core-patches/0001-headless-linguist-tools.patch` makes the translation tools available in both configurations.
- CPython's Android tooling defaults to NDK27d. Patch0002 permits an explicit verified standalone `ANDROID_NDK_ROOT`, so this app uses its pinned27c without presenting it as another SDK version. API26 and 16 KiB linker flags are retained.
- The actual Android Base link failed on `-lpthread`. Patch0003 stops appending that Unix DSO on Android; pthread functions are supplied by Bionic libc. Compiler/thread flags remain intact.
- Official Qt6.8.3 ARM64 binaries were inspected and have 4 KiB LOAD alignment. They are excluded from APK inputs. The Qt source rebuild provides the required alignment. Official matching Linux host tools need their bundled ICU73 runtime; this is host-only and kept apart from Android ICU74.
- ICU's generated Unix SONAMEs end in `.so.74`. `normalise_android_icu.py` rewrites only the isolated Android ICU loader names to `lib*.so`, preserves the versioned function ABI, and checks 16 KiB alignment afterward. Run this before linking Xerces/Core; rerun their links after any ICU normalization.
- Xerces builds with ICU transcoding and network access disabled. No host x86_64 library is a target dependency. Ubuntu snapshot development packages are used only for the Linux reference.
- The primary-runtime Python shared-library symlink was broken in this environment. The host script resolves the real matching `.so.1.0`, and explicitly supplies matching headers/library/interpreter. Qt host-tool archives need executable permissions restored for trusted ELF/script files.

## Reproduce

Use Python3.12+ for archive extraction. Install CMake/Ninja, py7zr and patchelf. JDK17 must provide java/javac/jar/keytool; SDK35 and NDK27.2.12479018 must be restored. `FREECAD-ANDROID-TOOLCHAINS.json` pins all source/archive checksums and `FREECAD-HOST-DEPENDENCIES.json` pins the separate Ubuntu host prefix. Source builds/toolchains are outside the APK/source-package application inputs.

```
python3 scripts/fetch_freecad_core_sources.py
python3 scripts/prepare_freecad_host.py
python3 scripts/build_freecad_host_core.py
python3 scripts/prepare_qt_android.py
python3 scripts/build_qt_android_core.py
python3 scripts/build_cpython_android.py
python3 scripts/build_boost_android.py
python3 scripts/build_icu_android.py
python3 scripts/normalise_android_icu.py
python3 scripts/build_cmake_android_dependencies.py
python3 scripts/build_cmake_android_dependencies.py --xerces
python3 scripts/build_freecad_android_core.py
python3 scripts/verify_freecad_android_core.py
```

Provide absolute JAVA_HOME and prepend its bin and CMake/Ninja to PATH. The host OCCT7.9.2 reference must exist (or restore its checkpoint). The Base/App target only needs its architecture-independent OCCT headers for configuration; **Part/OCAF toolkits are not all available for the future workbench build**. Android source fetching resets upstream files; apply the checked-in patches through the build scripts afterward. Do not fetch/extract over a source tree while a build is running.

For the host fixture, use `PYTHONPATH=../freecad-core-host/lib` and LD_LIBRARY_PATH with the matching host Python lib first, isolated host prefix lib second and host OCCT lib third. Run `tests/FreeCADCoreReference.py --output samples/upstream-core`. Logs are `freecad-core-host-final-build.txt`, `freecad-core-reference.txt`, `freecad-core-android-build.txt`, dependency logs and static-verification JSON. Failed probes are retained as scoped evidence, not runtime passes.

## Adapter and continuation

Rc5 adds native metadata documents, property dialogs, readable commands, expression/recompute, native transactions and App-only FCStd save/open. Its recovery and main CAD processes remain independent. See PARITY-B03.md and BATCH03-USER-GUIDE.md for exact scope. Limits reject unknown geometry/workbench types and unregistered scripted proxies before native FCStd restoration (rc6 permits the packaged QuantityDriver). The adapter does not silently turn arbitrary documents into empty scenes.

Build with build_core_bridge.py [--android], run_core_adapter_tests.py, prepare_core_apk.py, build_apk.py --prebuilt --upstream-core, verify_apk.py and verify_core_apk.py. Prepare/stage only before selecting/sealing a new APK; existing milestone inputs are immutable. App documents/configuration persist outside the interpreter version directory. Python deliberately lives until isolated-process exit.

1. Run Android core concordance, Qt/Python startup, task/command UI, process recreation and file-picker scenarios. The compiled smoke instrumentation includes units, expressions, Undo/Redo and FCStd restoration, but execution is NOT_RUN.
2. Rc6 supplies console, saved/recorded macros, API browser and one portable QuantityDriver proxy, with 62 host checks plus adapter88 regressions. Broader proxy and workbench/Gui bindings require actual module ports.
3. Build Part and missing OCCT/OCAF/exchange toolkits and connect original TopoShape data to the renderer. This backend is required before native Sketcher/PartDesign. Test geometric FCStd restore/recompute and preserve fcml originals during migration.
4. Complete remaining modules/formats/API and command-specific fixtures from the full roadmap.

Every four functional scopes require a signed APK checkpoint. Rc3/B01, rc4/B02, rc5/B03 and rc6/B04 are completed bounded engineering checkpoints. Stable1.0, reporting-phone crash verification, Android lifecycle/pickers, production signing/migration, manufacturing and full desktop parity remain incomplete.

The two reusable development archives core-build-host.zip and core-build-android.zip preserve prefixes/upstream outputs and generated headers from the earlier core build. Restore BOTH alongside the source project, preserve executable modes, fetch pinned sources/NDK/JDK/SDK separately and rebuild the small JNI adapter. They are not Android installers.

Primary build guidance: https://doc.qt.io/qt-6.8/android-building.html , https://doc.qt.io/qt-6.8/android-getting-started.html , https://docs.python.org/3.13/using/android.html and pinned CPython `Android/README.md`. Upstream dependency requirements and the three fixes were checked against the frozen FreeCAD/CPython source and actual build failures.
