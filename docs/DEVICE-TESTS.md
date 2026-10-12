# Android verification — not yet passed

Export existing projects first. The smoke test starts an empty workspace (keeping a recovery copy), creates models and intentionally crashes the CAD process. Run on a controlled ARM64 Android 8+ device.

```bash
python3 scripts/build_android_smoke.py
python3 scripts/run_android_checks.py --serial DEVICE_SERIAL
```

Install the recorded candidate (or build --prebuilt --reproduce and install that separate file). The instrumentation APK must use the retained development signing identity. It checks actual Android JNI kernel diagnostics, recovery startup, empty software CAD workspace, UI Box creation, command Box/Rename/Undo/Redo, offline Guide and recovery after a forced CAD-process crash. Compilation alone is not a pass.

The full gate also requires: reported-phone crash trace and verified resolution; 20 cold starts and 50 background/resume cycles; project save/open/STL and STEP export through actual Storage Access Framework pickers; cancellation/denial; rotation/process recreation; corrupt/legacy autosaves; dense mesh and low-memory measurements; minimum API and contemporary Android; at least two GPU vendors; 4 KiB and 16 KiB page environments where available; and prototype-to-production project migration. Record model/OS/ABI/GPU and exact APK digest with results.

Current result: NOT_RUN. No connected Android test surface/ADB or KVM is available here. Earlier software-emulator framework failures are retained as historical evidence, not app test results. User phone instant-crash cause remains unknown.
