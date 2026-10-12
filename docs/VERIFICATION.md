# Current verification

Current candidate is 1.0-rc2/code15. See STATUS-1.0.md, RELEASE-GATES.json, build-record.json and current per-version logs. Host/static package checks passed; Android runtime is NOT_RUN and stable1.0 is NOT_COMPLETE. The record below is historical evidence for 0.2.0.

# Verification record — 0.2.0

The earlier shader fix did not stop the reporting phone's instant crash. No
phone crash trace is available, so the device's root cause is still unknown.
The 0.1.3 update retained the software 3D viewport, recovery launcher, startup-stage
logging and bounded crash-report export, and added larger STL support plus
resize/rotation/duplication. **Physical
Android startup and complete file-picker workflows remain unverified.**

## Immediate startup failure

Version 0.1.0 used `uniform bool flat;` in its fragment shader. `flat` is a
reserved GLSL ES interpolation qualifier. A GLES 3 compiler rejects it with
`'flat': syntax error`. The old renderer threw the shader error uncaught on the
GL thread, which closes the application. This is a confirmed bug, but the
continuing report after 0.1.1 means it was not the complete explanation.

Version 0.1.1 names the uniform `unlit`. The actual packaged app vertex and
fragment shaders compile and link in a real SwiftShader OpenGL ES 3 context.
Lit and unlit VBO/VAO triangle draws produce the expected nonzero pixels without
a GL error. Shader compilation, program linking, upload and draw failures are
now caught and posted to the UI. See `gles-results.txt` and `tests/gles_test.py`.
These tests use a host EGL pbuffer, not an Android Activity or the phone's GPU.

EGL configuration/context creation can fail before the renderer receives a
callback. The optional GL viewport now uses a matching RGBA8888 surface/config
and a process uncaught-exception route for GL-thread failures. The default
software viewport avoids EGL entirely; it uses the same real native triangle
mesh, a depth buffer and interpolated face lighting. A host check renders the
actual native ring with its open bore and verifies depth, camera gestures,
translated geometry and input rejection. See `software-render-results.txt`
and `software-native-ring.png`; the image is a host render, not a phone screen.

## Checks completed

| Check | Result |
| --- | --- |
| Android ARM64 OCCT 7.9.2 and upstream FreeCAD PlaneGCS | Compiled |
| Updated JNI adapter and Android Java sources | Compiled; Java 8 core API target |
| Native geometry and JNI with matching host OCCT 7.9.2 | Passed, with JVM `-Xcheck:jni` |
| Default startup ring | Correct dimensions/volume; finite display mesh and unit normals |
| FreeCAD solver | Constrained sketch pad passed; previous three rectangle scale tests passed |
| Solid operations | Union, cut, intersection, unique-edge fillet and Undo passed |
| CAD files | Binary BREP fallback and STEP/STL round-trips passed |
| Project persistence | Primitives, translated BREP, hidden STL, movement after reopen passed |
| Import transactions | Late geometry failure restores original workspace and Undo; import uses one Undo |
| Bounded IO | Archive path, per-entry/expanded-size, cumulative copy and unit rejection passed |
| Save failure | Staging cleaned; a failed replacement preserves the destination |
| FCStd stored geometry | Synthetic saved Part archive and visibility passed; missing part/DTD rejected |
| STL restrictions | Solid-operation/STEP/BREP export rejection and triangle-count preflight passed |
| GLES 3 shader and triangle drawing | Passed in SwiftShader EGL pbuffer |
| Software mesh rendering | Passed actual native ring, depth order, orbit/pan/zoom, fit and invalid-input checks |
| Native tombstone decoding | Passed synthetic schema fixture, unknown-field and truncated-input checks |
| Large STL IO | 1,441,792 triangles / 72 MB; import, full-detail export and >64 MiB project entry/reopen passed |
| Display simplification | 9,998 / 50,000 / 150,000 triangles for respective budgets; full source unchanged; torus bore preserved |
| New transforms | Solid and dense STL resize, rotation, duplication, Undo and persistence passed |
| Malformed STL | Binary size mismatch, invalid coordinates and over-limit input rejected before native reading |
| Android x86-64 native QA core and separate instrumentation APK (0.1.2 attempt) | Compiled; Android framework failure prevented installation/runtime checks |
| APK version | Code 5 / 0.2.0-experimental, same package and development key |
| APK v2/v3 signatures and 16 KiB ZIP alignment | Passed |
| Native dependency closure and ELF alignment | Passed for all 31 ARM64 libraries |
| Physical phone launch, gestures, lifecycle and SAF file picker | Not tested here |

The host tests compile the same `cad.cpp`, FreeCAD PlaneGCS sources and Java
project/import classes with OCCT 7.9.2. They use host JNI and host `org.json`;
they do not validate Android's dynamic loader, framework JSON implementation,
graphics driver or file picker. Their output is in `host-regression-results.txt`.
`apk-verification-results.txt` and `build-record.json` describe the delivered APK.

## Startup and data handling fixes

The recovery Activity runs in the application process; native modelling and
its viewport run in `:cad`. The recovery screen never loads NativeCad or opens
an EGL context. First launch normally opens the software workspace; after a
detected crash it stays at recovery. Starting empty copies the previous
autosave before replacing it. Android may still terminate multiple processes
under memory pressure; process separation is not an absolute guarantee.

Engine loading occurs on a shared serial worker. Software rasterization runs
on a coalescing worker with a bounded 640-pixel image. The optional GL renderer
uses VBOs/VAOs and restores saved meshes after EGL context loss. Display meshes
are validated and bounded to 200,000 triangles before allocating direct buffers.
GPU allocation is deferred until the GPU renderer actually needs it.

STL import/export now uses an independent 2,000,000-triangle limit and a
256 MiB input-file limit. STL coordinates and binary lengths are checked
before calling the native reader. The unchanged source triangulation is
retained for export and project saving. Display meshes use cached meshoptimizer
edge-collapse simplification; topology-constrained/non-manifold cases may
fall back to a coarse display copy. The viewport explicitly reports original
and preview counts. Display never overwrites the source mesh.

The real JNI regression suite creates a closed, 1,441,792-triangle torus STL,
checks 10k/50k/150k scene budgets, renders its open bore, and verifies the full
triangle count through STL export and project reopen. Its 72,089,684-byte
STL also exercises the expanded 128 MiB project-shape allowance. Rotated/scaled
copies retain full detail while the source stays unchanged. Solid resize and
rotated BREP snapshots retain volume, dimensions and placement through project
reopen. See `host-regression-results.txt` and `large-stl-preview.png`.

Startup stages and Java exceptions are written to app-private records.
Android 11+ process exit history supplies available reason/signal information;
available native tombstone protobufs are decoded into a short backtrace and
retained in exported ZIPs. Older Android versions still retain app stage/Java
records. Decoder input, report size and exported traces are bounded. Copy and
export are explicit user actions; nothing is uploaded automatically.

Model edits/imports are transactional. Rejected imports leave the previous
geometry and Undo intact. Project saves use a completed, synced temporary ZIP
and atomic replacement where supported. Corrupt startup autosaves are copied
to private recovery files before a fresh workspace is saved. Use Workspace >
Export recovery copy to retrieve the preserved bytes. ZIP extraction is bounded
and cleaned, including FCStd import failures. JNI null arrays, nonfinite values
and invalid positions report exceptions instead of calling JNI with null data.

## Android runtime verification

The available host has no `/dev/kvm`. The earlier Android 11/API 30 x86-64 image
ran under software CPU emulation with ARM64 translation. One earlier APK
installed, but Android repeatedly killed processes for exceeding its attachment
deadline. Later installation timed out while the system showed a System UI ANR.
The retained `emulator-failure.png` and `emulator-startup-excerpt.txt` document
that older attempt. For the 0.1.2 recovery update, OCCT and the same FreeCAD solver/JNI adapter
were additionally built for Android x86-64, avoiding ARM translation for QA.
The emulator-only package uses the same app DEX, resources and manifest as the
ARM64 deliverable. The separate smoke instrumentation checks actual Android
JNI diagnostics, recovery, an empty software workspace, Box creation, and
recovery after a forced CAD-process crash. Its runtime result is recorded in
`build-record.json`; compilation alone is not a runtime pass.

This attempt did not reach app execution: the emulator's Android zygote/system
framework restarted and its package/settings services became unavailable.
The smaller x86-only QA APK pushed successfully, but installation returned
`Can't find service: package`. Earlier installation also timed out. See
`android-smoke-results.txt` and `emulator-0.1.2-excerpt.txt`. These are emulator
failures, not a reproduced crash of the delivered ARM64 app.

## On-device checks

Install version 0.2.0 over the earlier APK on an ARM64 Android 8.0+ device.
If recovery appears, choose Start empty workspace and create a Box. Verify
orbit/pan/zoom and resume after backgrounding. Run Workspace > Run kernel tests.
Also create/edit a model, use
Undo, save/reopen a project and import/export a CAD file.
Open a detailed STL, switch Display detail, resize to a chosen longest side,
rotate and duplicate it. Reopen the project and check exported STL geometry.

For a remaining crash, reopen the app and use Copy crash report or Save crash
report (.zip). A computer can also capture logs with the development-signed APK:

```bash
adb install -r FreeCAD-Mobile-Lab-0.2.0-arm64.apk
adb logcat -c
adb shell am force-stop org.freecad.mobilelab
adb shell am start -n org.freecad.mobilelab/.StartupActivity --ez diagnostics_only true
# Open the workspace using its recovery buttons; run kernel tests from Workspace.
adb logcat -d -s CAD_STARTUP CAD_CRASH CAD_ENGINE CAD_SELFTEST CAD_RENDERER AndroidRuntime libc DEBUG
adb shell run-as org.freecad.mobilelab cat files/diagnostics/cad-stage.txt
adb shell run-as org.freecad.mobilelab cat files/selftest.txt
```

The in-app kernel tests are diagnostics. This is a selected-functionality
native prototype; full desktop workbenches, Python and FCStd recomputation are
not included.

## 0.2.0 feature verification

The native expansion compiles for Android ARM64, including OCCT's matching IGES toolkit. The Java UI, touch sketch and typed node graph compile against SDK 35 with a Java 8 core API target. Signing and all 31 libraries are checked by `scripts/verify_apk.py`. `tests/FreeformRegression.java` passed 459 assertions with matching host OCCT 7.9.2 and JVM `-Xcheck:jni`. These check native modelling against analytic dimensions/volumes, rational weights, curve-only software drawing, closed-shell solidification, mesh repair, file formats, graph regeneration/Undo and new project object types. Its completed results are in `freeform-regression-results.txt`. See `FREEFORM-TOOLS.md` for the exact feature boundaries and mobile limits.

Bug fixes in this expansion include scrolling long dimension forms; curve-only camera bounds and software/GLES line rendering; preserving full mesh geometry through transforms and exports; treating count/angle parameters separately from uniform dimensional scaling; retaining object colours across saved projects; remapping graph object IDs on reopening; and native graph ownership to prevent orphaned outputs after Undo followed by graph regeneration. The export-quality regression caught an angular tessellation setting that masked the selected linear tolerance; a 0.50-radian ceiling now permits the tested fine/coarse STL settings to produce different detail. Section flattening supports drawing exports in millimetres. OBJ polygons are triangulated with concavity support; malformed indexes, excessive lines, non-planar polygons and oversized meshes are rejected. Mesh topology/repair maps are limited to 100,000 triangles to bound memory.

Physical Android launch, touch gestures, graph/sketch dialogs, lifecycle and SAF file picking remain unverified in this environment. The latest APK is development-signed with the retained key to support upgrading the previous app. It is not a production Play Store signing setup.
