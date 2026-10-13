# SPDX-License-Identifier: LGPL-2.1-or-later
"""Console, saved macros, recording and App API inspection for the native lab."""
import contextlib
import io
import json
from pathlib import Path
import re
import sys
import time
import traceback
import FreeCAD as App
import mobile_part
import mobile_sketch

scope = {"App": App, "FreeCAD": App, "__name__": "__mobile_console__"}
if mobile_part.available():
    scope["Part"] = mobile_part.Part
if mobile_sketch.available():
    scope["Sketcher"] = mobile_sketch.Sketcher
console = {"output": "", "error": ""}
api = None
recording = False
record = []
folder = None


def configure(root):
    global folder
    folder = Path(root).resolve() / "macros"
    folder.mkdir(parents=True, exist_ok=True)


def macro_path(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9-]{0,79}\.py", name):
        raise ValueError("Use a plain Python filename such as MyMacro.py")
    path = (folder / name).resolve()
    if path.parent != folder:
        raise ValueError("Macro path must stay in the macro directory")
    return path


class Output(io.StringIO):
    def write(self, text):
        left = max(0, 65536 - self.tell())
        super().write(text[:left])
        return len(text)


def run(code, filename="<mobile-console>"):
    global console
    if not isinstance(code, str) or len(code.encode("utf-8")) > 65536 or "\x00" in code:
        raise ValueError("Python source exceeds 64 KiB or contains NUL")
    output = Output()
    errors = ""
    deadline = time.monotonic() + 2.0
    previous_trace = sys.gettrace()

    def trace(frame, event, arg):
        if time.monotonic() > deadline:
            raise RuntimeError("Python execution exceeded the two-second tracing budget")
        return trace

    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            sys.settrace(trace)
            exec(compile(code, filename, "exec"), scope, scope)
            if App.ActiveDocument is not None:
                App.ActiveDocument.recompute()
    except BaseException:
        errors = traceback.format_exc(limit=8)[-8192:]
    finally:
        sys.settrace(previous_trace)
    console = {"output": output.getvalue(), "error": errors}
    return console


def save(name, code):
    if not isinstance(code, str) or len(code.encode("utf-8")) > 65536:
        raise ValueError("Macro source exceeds 64 KiB")
    compile(code, name, "exec")
    path = macro_path(name)
    if not path.exists() and len(list(folder.glob("*.py"))) >= 100:
        raise ValueError("Maximum 100 saved macros")
    temporary = path.with_suffix(".tmp")
    temporary.write_text(code, encoding="utf-8")
    temporary.replace(path)


def read(name):
    path = macro_path(name)
    if path.stat().st_size > 65536:
        raise ValueError("Macro exceeds 64 KiB")
    return path.read_text(encoding="utf-8")


def inspect(target):
    global api
    if not isinstance(target, str) or len(target) > 160:
        raise ValueError("Invalid API target")
    parts = target.split(".")
    modules = {"App": App, "FreeCAD": App}
    if mobile_part.available():
        modules["Part"] = mobile_part.Part
    if mobile_sketch.available():
        modules["Sketcher"] = mobile_sketch.Sketcher
    if parts[0] not in modules or any(not re.fullmatch(r"[A-Za-z][A-Za-z_0-9]*", p) for p in parts):
        raise ValueError("Use an App API target such as App.Vector or App.Units")
    value = modules[parts[0]]
    for name in parts[1:]:
        value = getattr(value, name)
    api = {"target": target, "doc": (getattr(value, "__doc__", None) or "")[:8192],
        "members": sorted(n for n in dir(value) if not n.startswith("_"))[:500]}


def start_recording():
    global recording, record
    if recording:
        raise ValueError("Recording is already active")
    recording = True
    record = ["import FreeCAD as App", ""]


def add_record(request, manual_transaction=False):
    global recording, console
    if not recording:
        return
    op = request.get("op", "state")
    lines = []
    if op == "new":
        lines = ["App.newDocument(" + repr(request.get("name", "MobileDocument")) + ")", "App.ActiveDocument.UndoMode = 1"]
    elif op == "activate":
        lines = ["App.setActiveDocument(" + repr(request["name"]) + ")"]
    elif op in ("undo", "redo", "recompute", "commit", "abort", "begin"):
        method = {"commit": "commitTransaction", "abort": "abortTransaction", "begin": "openTransaction"}.get(op, op)
        args = repr(request.get("label", "Mobile edit")) if op == "begin" else ""
        lines = ["App.ActiveDocument." + method + "(" + args + ")"]
    elif op == "batch":
        if not manual_transaction:
            lines += ["App.ActiveDocument.openTransaction('Recorded edit')"]
        for edit in request["edits"]:
            action = edit["op"]
            obj = "App.ActiveDocument.getObject(" + repr(edit.get("object", "")) + ")"
            if action == "add":
                lines += ["_feature = App.ActiveDocument.addObject(" + repr(edit.get("type", "App::FeaturePython")) + ", " + repr(edit["name"]) + ")", "_feature.Label = " + repr(edit.get("label", edit["name"]))]
            elif action == "property":
                lines += [obj + ".addProperty(" + repr(edit["type"]) + ", " + repr(edit["name"]) + ", 'Mobile')"]
            elif action == "set":
                value = edit.get("value")
                feature = App.ActiveDocument.getObject(edit["object"])
                kind = feature.getTypeIdOfProperty(edit["property"])
                if kind == "App::PropertyBool":
                    value = value.lower() == "true" if isinstance(value, str) else value
                elif kind == "App::PropertyInteger":
                    value = int(value)
                elif kind == "App::PropertyFloat":
                    value = float(value)
                expression = "App.ActiveDocument.getObject(" + repr(value) + ")" if kind == "App::PropertyLink" and value else repr(None if kind == "App::PropertyLink" else value)
                lines += [obj + "." + edit["property"] + " = " + expression]
            elif action == "expression":
                lines += [obj + ".setExpression(" + repr(edit["property"]) + ", " + repr(edit["expression"] or None) + ")"]
            elif action == "remove":
                lines += ["App.ActiveDocument.removeObject(" + repr(edit["object"]) + ")"]
            elif action == "group":
                lines += ["App.ActiveDocument.getObject(" + repr(edit["group"]) + ").addObject(" + obj + ")"]
            elif action == "link":
                lines += [obj + ".setLink(App.ActiveDocument.getObject(" + repr(edit["target"]) + "))"]
            elif action == "proxy":
                lines += ["from mobile_features import QuantityDriver", "_feature = App.ActiveDocument.addObject('App::FeaturePython', " + repr(edit["name"]) + ")",
                    "QuantityDriver(_feature, App.ActiveDocument.getObject(" + repr(edit["source"]) + "), " + repr(edit["property"]) + ", " + repr(float(edit.get("factor", 1))) + ")"]
        lines += ["App.ActiveDocument.recompute()"]
        if not manual_transaction:
            lines += ["App.ActiveDocument.commitTransaction()"]
    elif op == "python":
        lines += [request["code"]]
    if len("\n".join(record + lines).encode("utf-8")) > 65536:
        recording = False
        console = {"output": "", "error": "Recording reached 64 KiB. The latest edit was applied but not recorded; save the captured portion."}
        return
    record.extend(lines)


def stop_recording(name):
    global recording
    if not record:
        raise ValueError("No recording is active")
    save(name, "\n".join(record) + "\n")
    recording = False


def metadata():
    return {"console": console, "api": api, "recording": recording,
        "macros": sorted(p.name for p in folder.glob("*.py"))}
