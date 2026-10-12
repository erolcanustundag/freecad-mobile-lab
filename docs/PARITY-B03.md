# B03 — upstream document core (1.0-rc5)

This batch packages the genuine upstream FreeCAD 1.1.4 Base/App runtime into an **opt-in document lab**, in an isolated Android process. It preserves the existing mobile CAD renderer and 31 native libraries. It does not port Part, Sketcher, PartDesign, GUI workbenches or arbitrary FCStd models.

The four bounded engineering scopes are:

1. ARM64/API26 Base/App and dependency runtime, embedded CPython 3.13.16, official Qt Java/JNI context and 16 KiB native libraries.
2. Native documents, typed properties, groups, linked instances and recompute, exposed through task dialogs and readable commands.
3. Native transactions, abort, Undo/Redo and live dimensional expression dependencies. Failed edit batches roll back through upstream App.
4. Native App-only FCStd save/open through private files and Android file pickers. Stored links, groups, labels and expressions remain native data. Unsupported workbench types and scripted proxies are rejected before native restoration.

The document engine is upstream App called through a serialized JNI/Python adapter. It is independent from the existing custom fcml/OCCT graph. It does not replace the main workspace automatically or migrate existing models.

| Check | Result |
| --- | --- |
| Upstream host reference fixture | 28 passed |
| Same JNI adapter against host FreeCAD | 88 passed: typed units, dependent recompute, Undo/Redo/abort, atomic rollback, groups/links, UTF16/UTF8 labels, FCStd restore, circular expression rejection, unsupported object/proxy/path rejection, cross-thread GIL reads, readable commands and typed values |
| Adapter ARM64 build | Passed |
| Packaged core static verification | 123 shared libraries/extensions, 16 KiB LOAD alignment, loader-name and API26 strong-symbol availability passed; 820 Python asset files matched their hashes |
| APK static verification | 54 JNI libraries, retained development signing identity, v2/v3 signatures, 16 KiB ELF/ZIP alignment; no network permission |
| Android instrumentation | Compiled; includes upstream lab unit/expression/Undo/Redo/native FCStd UI scenarios; execution NOT_RUN |

The host uses Python 3.12 and Qt5; the target uses Python 3.13 and Qt6. Host JNI evidence proves the adapter protocol and upstream App semantics on that platform. Static ARM64 checks prove packaging and available symbols, not Qt/Python initialization on a phone. No Android device was connected. Phone startup, process recreation, file pickers, runtime namespace behavior and the reported instant crash remain unverified. Stable 1.0 remains incomplete.

Build entry points: `build_core_bridge.py` (host / `--android`), `run_core_adapter_tests.py`, `prepare_core_apk.py`, `build_apk.py --prebuilt --upstream-core`, `verify_apk.py`, `verify_core_apk.py`. The expensive dependency checkpoints remain separate development archives. B04 console/macros/proxies and the geometry/workbench batches are still open.
