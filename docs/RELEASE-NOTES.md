# FreeCAD Mobile Lab 1.0-rc7

Experimental ARM64 Android 8+ candidate, Android version code20. Independent project; stable1.0 and full desktop FreeCAD parity are NOT COMPLETE.

RC7 adds a document-lab restart that remains available during failed initialization or a stuck script/native call. Restart closes unsaved lab documents. Saved lab files and the separate CAD workspace persist. Help and Recovery also remain available while the lab is busy. Android execution of this path is still pending.

Packaging now rejects edited mobile Python sources that differ from the embedded archive, missing script modules, changed Qt Java inputs and changed native core dependencies. A guarded refresh tool rebuilds the Python archive from current scripts while preserving pinned interpreter files. CPython dependency fetching now checks the frozen binary archive hashes before its upstream build helper can use them. Macro import errors report the actual file-size bound.

The source package now includes public build instructions, dependency source locks and notices, source-only CI checks, a bug-report form, runtime restoration and a guarded GitHub publishing script. Signing keys and private continuation files are excluded from the public repository/source archive.

Validation: six portable runtime-packaging regression tests; all822 embedded Python file hashes/CRC and script concordance; Java/APK compilation; APKv2/v3 signatures;54 ARM64 JNI libraries, loader-name dependency closure,16KiB ZIP/ELF alignment and no network permission. Android smoke instrumentation compiles but has NOT_RUN on Android. Native library bytes are unchanged from RC6; earlier host/core tests are historical evidence.

Candidates retain the development certificate for compatible prototype upgrades. Production signing/update migration, Android launch/crash reproduction/lifecycle/file pickers, and major native workbench ports remain open. The phone instant-crash report has not been reproduced or verified fixed. Export project backups before uninstalling or changing certificates. Part/Sketcher/PartDesign/Assembly/TechDraw/CAM/FEM/BIM and broad addon/FCStd compatibility are still incomplete.

Release assets: signed APK, pinned native runtime bundle for local builds and corresponding upstream/source dependency archives. The source repository supplies mobile code, vendor headers/solver sources and integration patches. Rebuild/install modified libraries with your own certificate; see THIRD-PARTY.md, SIGNING.md and FREECAD-CORE-PORT.md.
