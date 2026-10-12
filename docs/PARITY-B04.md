# B04 — upstream App Python tooling (1.0-rc6)

Four additional functional tools now use the embedded upstream App runtime: a persistent Python console; a saved macro editor/recorder with file import/export; a portable scripted QuantityDriver feature; and an App API browser. B03 supplied the interpreter/App binding foundation. This batch extends that foundation; it does not claim Part/Gui or all addon bindings.

The console captures output and traceback, keeps variables between calls in the same process and updates the active native document. Python tracing has a two-second budget and output is capped at 64 KiB. Native calls can run longer, and the console is not a sandbox. The interpreter stays in the separate opt-in document process.

Macros persist in a stable private folder outside interpreter-version assets. Source is compiled before atomic replacement. Import never runs a file automatically. Successful native document commands can be recorded as Python using real App object/property and transaction methods. Syntax failures preserve the previous macro. Recording stops with a readable message if its buffer fills. Saved recordings can be edited and replayed.

QuantityDriver uses the actual FeaturePython execution mechanism, a native PropertyLink dependency, a Length input, Float multiplier and Length output. Its module/class and validated JSON state restore through FCStd. The imported-file registry permits this packaged class and null proxies. Arbitrary addon/console proxy classes remain unsupported until their portability contracts are implemented. This template computes metadata, not a geometric Part solid.

The API browser lists public members and documentation from available App/Base binding objects. It does not pretend that missing workbenches exist.

| Check | Result |
| --- | --- |
| Python tooling host suite | 62 passed: persistent namespace, Unicode output, traceback, loop budget, output bound, native API introspection, macro recording/replay, typed values/transactions, atomic failed save, proxy recompute/Undo/Redo, FCStd class/state restoration and path/type rejection |
| B03 adapter regression | 88 passed |
| Actual APK | 54 JNI libraries + 69 Python extensions; ARM64, 16 KiB ELF/ZIP, loader/API26 strong-symbol availability passed; 822 Python asset hashes matched |
| Signing | Retained development identity; v2/v3 verified |
| Expanded Android instrumentation | Compiled, includes console/API/proxy FCStd workflow; execution NOT_RUN |

Fixed: Float text commands now convert to finite native numbers; macro defaults/regex/newline escaping; UTF8 BOM import; export filename instance-state restoration; native documents/config/macros persist separately from interpreter assets.

No Android device test ran. Host uses Qt5/Python3.12; target uses Qt6/Python3.13. Phone startup, UI, file-picker/lifecycle, native initialization and the reporting-phone instant crash remain unverified. Stable1.0 and full desktop parity remain incomplete. Original 31 mobile CAD libraries are unchanged; their prior native regression evidence remains applicable to those bytes.
