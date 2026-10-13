# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded JSON adapter to upstream FreeCAD App, not a replacement document engine.

All calls run serially under the embedded interpreter's GIL. This first adapter
supports App metadata documents. Geometry/workbench restoration is rejected
explicitly until those modules are ported.
"""
import json
import base64
import math
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
import FreeCAD as App
import mobile_features
import mobile_python
import mobile_part
import mobile_sketch

OBJECT_TYPES = {"App::FeaturePython", "App::DocumentObjectGroup", "App::Link", "App::VarSet"}
if mobile_part.available():
    OBJECT_TYPES.update(mobile_part.TYPES)
if mobile_sketch.available():
    OBJECT_TYPES.update(mobile_sketch.TYPES)
PROPERTY_TYPES = {"App::PropertyLength", "App::PropertyAngle", "App::PropertyArea",
    "App::PropertyVolume", "App::PropertyDistance", "App::PropertyFloatConstraint", "App::PropertyFloat", "App::PropertyInteger",
    "App::PropertyString", "App::PropertyBool", "App::PropertyLink"}
_root = None
_document = None
_transaction = False


def configure(root):
    global _root
    _root = Path(root).resolve() / "documents"
    _root.mkdir(parents=True, exist_ok=True)
    mobile_part.configure()
    mobile_python.configure(Path(root).resolve())


def _text(value, limit=4096):
    if not isinstance(value, str) or len(value) > limit or "\x00" in value:
        raise ValueError("Invalid or oversized text")
    return value


def _identifier(value):
    value = _text(value, 80)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", value):
        raise ValueError("Use a name starting with a letter or underscore")
    return value


def _file(value):
    name = _text(value, 160)
    if name in (".", "..") or "/" in name or "\\" in name or not name.lower().endswith(".fcstd"):
        raise ValueError("Use a plain .FCStd filename")
    path = (_root / name).resolve()
    if path.parent != _root:
        raise ValueError("Document path must stay inside the document directory")
    return path


def _doc():
    if _document is None:
        raise ValueError("Create or open a document first")
    return _document


def _object(name):
    obj = _doc().getObject(_identifier(name))
    if obj is None:
        raise ValueError("Object does not exist: " + name)
    return obj


def _value(obj, name):
    value = getattr(obj, name)
    if hasattr(value, "Value") and hasattr(value, "Unit"):
        return {"value": value.Value, "text": str(value), "unit": str(value.Unit)}
    if hasattr(value, "Name"):
        return {"object": value.Name}
    if isinstance(value, (tuple, list)):
        return [{"object": v.Name} if hasattr(v, "Name") else str(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _editable(obj, name):
    return name!="Label2" and not name.startswith("_") and not obj.getEditorMode(name)


def snapshot():
    result = {"version": App.Version()[:3], "scope": "App/Part bounded mobile adapter" if mobile_part.available() else "App metadata; geometry workbenches pending",
        "part": mobile_part.available(),
        "sketcher": mobile_sketch.available(),
        "documents": list(App.listDocuments()), "files": sorted(p.name for p in _root.iterdir()
            if p.is_file() and p.suffix.lower() == ".fcstd"),
        "transaction": _transaction, "document": None, "python": mobile_python.metadata()}
    if _document is not None:
        d = _document
        objects = []
        for obj in d.Objects:
            props = []
            for name in obj.PropertiesList:
                kind = obj.getTypeIdOfProperty(name)
                if kind in PROPERTY_TYPES or name in ("Label", "Group", "LinkedObject"):
                    props.append({"name": name, "type": kind, "value": _value(obj, name),
                        "editable": (name == "Label" or kind in PROPERTY_TYPES) and _editable(obj,name)})
            objects.append({"name": obj.Name, "label": obj.Label, "type": obj.TypeId,
                "properties": props, "expressions": list(obj.ExpressionEngine),
                "dependencies": [o.Name for o in obj.OutList], "state": list(obj.State)})
            shape = mobile_part.summary(obj) if mobile_part.available() else None
            if shape is not None:
                objects[-1]["shape"] = shape
            sketch=mobile_sketch.summary(obj) if mobile_sketch.available() else None
            if sketch is not None:
                objects[-1]["sketch"] = sketch
        result["document"] = {"name": d.Name, "label": d.Label, "objects": objects,
            "undo": d.UndoCount, "redo": d.RedoCount}
    return result


def _edit(edit):
    action = edit.get("op")
    if isinstance(action,str) and action.startswith("sketch_"):
        mobile_sketch.edit(_object(edit["object"]),edit)
    elif action == "section_plane":
        source=_object(edit["source"]);name=_identifier(edit["name"]);plane_name=_identifier(name+"_Plane")
        info=mobile_part.shape_info(source)
        if source.TypeId not in mobile_part.TYPES or not info["valid"]:raise ValueError("Choose valid native Part geometry")
        if len(_doc().Objects)>998 or any(_doc().getObject(n) is not None for n in (name,plane_name)):raise ValueError("Choose new section and helper names within the1000-object budget")
        center=edit["origin"];normal=edit["normal"];size=mobile_sketch.number(edit["size"])
        if not isinstance(center,list) or not isinstance(normal,list) or len(center)!=3 or len(normal)!=3 or size<=1e-7:raise ValueError("Use world XYZ origin, nonzero normal and positive plane size")
        center=App.Vector(*[mobile_sketch.number(v) for v in center]);normal=App.Vector(*[mobile_sketch.number(v) for v in normal])
        if normal.Length<=1e-7:raise ValueError("Section plane normal must be nonzero")
        normal.normalize();rotation=App.Rotation(App.Vector(0,0,1),normal)
        plane=_doc().addObject("Part::Plane",plane_name);plane.Length=size;plane.Width=size
        plane.Placement=App.Placement(center-rotation.multVec(App.Vector(size/2,size/2,0)),rotation)
        obj=_doc().addObject("Part::Section",name);obj.Base=source;obj.Tool=plane
    elif action == "finish_settings":
        obj=_object(edit["object"])
        if obj.TypeId not in ("Part::Fillet","Part::Chamfer"):raise ValueError("Select a native fillet or chamfer")
        source=obj.Base;mobile_part.shape_info(source);ids=edit["edges"];amount=mobile_sketch.number(edit["amount"])
        if not isinstance(ids,list) or not 1<=len(ids)<=32 or len(set(ids))!=len(ids) or any(type(i) is not int or not 1<=i<=len(source.Shape.Edges) for i in ids):raise ValueError("Use1–32 unique current edge numbers starting at1")
        if amount<=1e-7:raise ValueError("Finishing amount must be positive")
        obj.Edges=[(i,amount,amount) for i in ids]
    elif action == "part_finish":
        source=_object(edit["source"]);name=_identifier(edit["name"]);mode=edit["mode"]
        if source.TypeId not in mobile_part.TYPES or not hasattr(source,"Shape") or source.Shape.isNull():raise ValueError("Choose a supported nonempty native Part source")
        if _doc().getObject(name) is not None or len(_doc().Objects)>=1000:raise ValueError("Choose a new name within the1000-object budget")
        info=mobile_part.shape_info(source)
        if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Finishing sources must be valid and bounded")
        if mode in ("fillet","chamfer"):
            ids=edit["edges"];amount=mobile_sketch.number(edit["amount"])
            if not isinstance(ids,list) or not 1<=len(ids)<=32 or len(set(ids))!=len(ids) or any(type(i) is not int or not 1<=i<=len(source.Shape.Edges) for i in ids):raise ValueError("Use1–32 unique current edge numbers starting at1")
            if amount<=1e-7 or len(source.Shape.Solids)!=1:raise ValueError("Use a positive edge radius/distance on one solid")
            obj=_doc().addObject("Part::Fillet" if mode=="fillet" else "Part::Chamfer",name);obj.Base=source;obj.Edges=[(i,amount,amount) for i in ids]
        elif mode=="refine":
            shape=source.Shape.removeSplitter()
            if shape.isNull() or not shape.isValid() or len(shape.Faces)>2000:raise ValueError("Refinement must produce valid bounded geometry")
            obj=_doc().addObject("Part::Feature",name);obj.Shape=shape;obj.addProperty("App::PropertyString","MobileOperation","Mobile");obj.MobileOperation="Refinement snapshot from "+source.Name;obj.setEditorMode("MobileOperation",1)
        elif mode=="section":
            tool=_object(edit["tool"])
            if tool==source or tool.TypeId not in mobile_part.TYPES or tool.Shape.isNull():raise ValueError("Choose a different native Part tool")
            obj=_doc().addObject("Part::Section",name);obj.Base=source;obj.Tool=tool
        else:raise ValueError("Use fillet, chamfer, refine or section")
    elif action == "extrusion_settings":
        obj=_object(edit["object"])
        if obj.TypeId!="Part::Extrusion":raise ValueError("Select a native Part extrusion")
        fwd=mobile_sketch.number(edit["forward"]);rev=mobile_sketch.number(edit["reverse"])
        symmetric=edit["symmetric"];reversed_=edit["reversed"]
        if min(fwd,rev)<0 or type(symmetric) is not bool or type(reversed_) is not bool or (fwd if symmetric else fwd+rev)<=1e-7:raise ValueError("Use nonnegative extents with positive total depth and boolean modes")
        obj.LengthFwd=fwd;obj.LengthRev=rev;obj.Symmetric=symmetric;obj.Reversed=reversed_
    elif action == "revolution_settings":
        obj=_object(edit["object"])
        if obj.TypeId!="Part::Revolution":raise ValueError("Select a native Part revolution")
        angle=mobile_sketch.number(edit["angle"],360);symmetric=edit["symmetric"]
        if angle<=1e-7 or type(symmetric) is not bool:raise ValueError("Use positive angle up to360 degrees and boolean symmetry")
        origin=edit["origin"];axis=edit["axis"]
        if not isinstance(origin,list) or not isinstance(axis,list) or len(origin)!=3 or len(axis)!=3:raise ValueError("Use world XYZ axis origin and direction")
        origin=App.Vector(*[mobile_sketch.number(v) for v in origin]);axis=App.Vector(*[mobile_sketch.number(v) for v in axis])
        if axis.Length<1e-7:raise ValueError("Revolution axis must be nonzero")
        axis.normalize();obj.Base=origin;obj.Axis=axis;obj.Angle=angle;obj.Symmetric=symmetric
    elif action == "part_placement":
        obj=_object(edit["object"])
        if obj.TypeId not in mobile_part.TYPES:raise ValueError("Choose a supported native Part object")
        obj.Placement=mobile_sketch.placement(edit["values"])
        _doc().recompute();info=mobile_part.shape_info(obj)
        if not info["valid"] or any(abs(v)>1000000 for v in info["bounds"]):raise ValueError("Placement must preserve valid geometry within±1,000,000mm")
    elif action == "profile_solid":
        source=mobile_part.profile(_object(edit["source"]),True)
        name=_identifier(edit["name"])
        if _doc().getObject(name) is not None or len(_doc().Objects)>=1000:raise ValueError("Choose a new object name within the1000-object budget")
        mode=edit["mode"]
        if mode not in ("extrude","revolve"):raise ValueError("Use extrude or revolve")
        amount=mobile_sketch.number(edit["amount"],360 if mode=="revolve" else 1000000)
        if amount<=1e-7:raise ValueError("Profile amount must be positive")
        if mode=="extrude":
            obj=_doc().addObject("Part::Extrusion",name);obj.Base=source;obj.Dir=source.Placement.Rotation.multVec(App.Vector(0,0,1));obj.LengthFwd=amount;obj.DirMode="Normal";obj.Solid=True
        else:
            origin=edit["origin"];axis=edit["axis"]
            if not isinstance(origin,list) or not isinstance(axis,list) or len(origin)!=3 or len(axis)!=3:raise ValueError("Provide world XYZ origin and axis vectors")
            origin=App.Vector(*[mobile_sketch.number(v) for v in origin]);axis=App.Vector(*[mobile_sketch.number(v) for v in axis])
            if axis.Length<1e-7:raise ValueError("Revolution axis must be nonzero")
            axis.normalize();obj=_doc().addObject("Part::Revolution",name);obj.Source=source;obj.Base=origin;obj.Axis=axis;obj.Angle=amount;obj.Solid=True
    elif action == "add":
        kind = edit.get("type", "App::FeaturePython")
        if kind not in OBJECT_TYPES:
            raise ValueError("Object type is not ported: " + str(kind))
        if len(_doc().Objects) >= 1000:
            raise ValueError("This mobile metadata editor supports up to 1,000 objects")
        name = _identifier(edit["name"])
        if _doc().getObject(name) is not None:
            raise ValueError("Object name already exists")
        obj = _doc().addObject(kind, name)
        obj.Label = _text(edit.get("label", name), 256)
    elif action == "remove":
        target=_object(edit["object"])
        if any(o.TypeId in mobile_sketch.TYPES|{"Part::Extrusion","Part::Revolution","Part::Fillet","Part::Chamfer","Part::Section"} for o in target.InList):
            raise ValueError("Detach sketches and remove their external references before deleting the source")
        _doc().removeObject(target.Name)
    elif action == "property":
        obj = _object(edit["object"])
        name = _identifier(edit["name"])
        kind = edit["type"]
        if kind not in PROPERTY_TYPES or name in obj.PropertiesList:
            raise ValueError("Unsupported type or existing property")
        if len(obj.PropertiesList) >= 256:
            raise ValueError("Too many properties")
        obj.addProperty(kind, name, "Mobile")
    elif action == "set":
        obj = _object(edit["object"])
        name = _identifier(edit["property"])
        if name not in obj.PropertiesList:
            raise ValueError("Property does not exist")
        kind = obj.getTypeIdOfProperty(name)
        if kind not in PROPERTY_TYPES or not _editable(obj,name):
            raise ValueError("Property is not editable in this adapter")
        value = edit.get("value")
        if kind == "App::PropertyLink":
            value = _object(value) if value else None
        elif kind == "App::PropertyString":
            value = _text(value, 4096)
        elif kind == "App::PropertyBool":
            if isinstance(value, str) and value.lower() in ("true", "false"):
                value = value.lower() == "true"
            if not isinstance(value, bool):
                raise ValueError("Boolean property needs true or false")
        elif kind == "App::PropertyInteger":
            if isinstance(value, str) and re.fullmatch(r"-?\d{1,11}", value):
                value = int(value)
            if type(value) is not int or not -2147483648 <= value <= 2147483647:
                raise ValueError("Integer outside the supported range")
        elif kind == "App::PropertyFloatConstraint":
            if obj.TypeId!="Part::Revolution" or name!="Angle":raise ValueError("This constrained scalar is read-only in the mobile adapter")
            q=App.Units.Quantity(str(value))
            value=float(q.Value if str(q.Unit)=="" else q.getValueAs("deg").Value)
            if not math.isfinite(value) or not 1e-7<value<=360:raise ValueError("Revolution angle must be greater than0 and at most360 degrees")
        elif kind == "App::PropertyFloat":
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("Use a finite floating-point value")
        elif isinstance(value, str):
            value = _text(value, 512)
        elif type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Use a finite number or a unit expression")
        setattr(obj, name, value)
        actual = getattr(obj, name)
        if hasattr(actual, "Value"):
            actual = actual.Value
        if type(actual) in (int, float) and not math.isfinite(actual):
            raise ValueError("Property value must be finite")
    elif action == "expression":
        obj = _object(edit["object"])
        name = _identifier(edit["property"])
        if obj.getTypeIdOfProperty(name) not in PROPERTY_TYPES or not _editable(obj,name):
            raise ValueError("Expression property is not editable")
        expr = _text(edit["expression"], 512)
        obj.setExpression(name, expr if expr else None)
    elif action == "group":
        group = _object(edit["group"])
        if group.TypeId != "App::DocumentObjectGroup":
            raise ValueError("Target is not a group")
        group.addObject(_object(edit["object"]))
    elif action == "link":
        link = _object(edit["object"])
        if link.TypeId != "App::Link":
            raise ValueError("Target is not a linked instance")
        link.setLink(_object(edit["target"]))
    elif action == "proxy":
        name = _identifier(edit["name"])
        if _doc().getObject(name) is not None:
            raise ValueError("Object name already exists")
        source = _object(edit["source"])
        if len(_doc().Objects) >= 1000:
            raise ValueError("This mobile editor supports up to 1,000 objects")
        input_property = _identifier(edit["property"])
        if source.getTypeIdOfProperty(input_property) != "App::PropertyLength":
            raise ValueError("QuantityDriver needs a Length source property")
        factor = float(edit.get("factor", 1))
        if not math.isfinite(factor) or abs(factor) > 1000000:
            raise ValueError("Use a finite multiplier within ±1,000,000")
        obj = _doc().addObject("App::FeaturePython", name)
        mobile_features.QuantityDriver(obj, source, input_property, factor)
    else:
        raise ValueError("Unknown edit operation")


def _validate_fcstd(path):
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("FCStd input exceeds 128 MiB")
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        if len(entries) > 2000 or sum(i.file_size for i in entries) > 256 * 1024 * 1024:
            raise ValueError("FCStd archive is too large")
        infos = [i for i in entries if i.filename == "Document.xml"]
        if len(infos) != 1 or infos[0].file_size > 16 * 1024 * 1024:
            raise ValueError("Missing or oversized Document.xml")
        xml = z.read(infos[0])
        if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
            raise ValueError("XML declarations are unsupported")
        tree = ET.fromstring(xml)
        unsupported = sorted({o.get("type") for o in tree.findall("./Objects/Object")
            if o.get("type") not in OBJECT_TYPES})
        if unsupported:
            raise ValueError("Workbenches not yet ported: " + ", ".join(str(t) for t in unsupported))
        # Scripted proxies have a separate portability contract in B04. Do not
        # silently deserialize a proxy whose class/module is not in this port.
        for prop in tree.iter("Property"):
            if prop.get("type") == "App::PropertyPythonObject":
                value = prop.find("Python")
                if value is not None and value.get("json") == "yes" and value.get("value") in ("null", "bnVsbA=="):
                    continue
                if value is None or value.get("module") != "mobile_features" or value.get("class") != "QuantityDriver" or value.get("encoded") != "yes":
                    raise ValueError("This scripted proxy is not in the portable mobile registry")
                state = base64.b64decode(value.get("value", ""), validate=True)
                if len(state) > 2048:
                    raise ValueError("Proxy state exceeds the limit")
                mobile_features.QuantityDriver.validate(json.loads(state))


def execute(request):
    global _document, _transaction
    action = request.get("op", "state")
    if action == "new":
        if _transaction:
            raise ValueError("Finish the current transaction first")
        if len(App.listDocuments()) >= 8:
            raise ValueError("Close a document before creating another")
        _document = App.newDocument(_identifier(request.get("name", "MobileDocument")))
        _document.UndoMode = 1
    elif action == "activate":
        if _transaction:
            raise ValueError("Finish the current transaction first")
        _document = App.getDocument(_identifier(request["name"]))
        App.setActiveDocument(_document.Name)
    elif action == "close":
        if _transaction:
            raise ValueError("Finish the current transaction first")
        name = _doc().Name
        _document = None
        App.closeDocument(name)
    elif action == "begin":
        if _transaction:
            raise ValueError("A transaction is already open")
        _doc().openTransaction(_text(request.get("label", "Mobile edit"), 128))
        _transaction = True
    elif action in ("commit", "abort"):
        if not _transaction:
            raise ValueError("No transaction is open")
        if action == "commit":
            _doc().recompute()
            try:
                mobile_sketch.validate_document(_doc())
                mobile_part.validate_document(_doc())
                if any("Invalid" in o.State for o in _doc().Objects):
                    raise ValueError("Document recompute failed; transaction was rolled back")
            except Exception:
                _doc().abortTransaction();_doc().recompute();_transaction=False
                raise
            _doc().commitTransaction()
        else:
            _doc().abortTransaction()
            _doc().recompute()
        _transaction = False
    elif action == "batch":
        edits = request.get("edits")
        if not isinstance(edits, list) or not 1 <= len(edits) <= 100:
            raise ValueError("Use 1 to 100 edits per transaction")
        owned = not _transaction
        if owned:
            _doc().openTransaction(_text(request.get("label", "Mobile edit"), 128))
        try:
            for edit in edits:
                _edit(edit)
            _doc().recompute()
            mobile_sketch.validate_document(_doc())
            mobile_part.validate_document(_doc())
            if any("Invalid" in o.State for o in _doc().Objects):
                raise ValueError("Recompute failed; check expressions and object references")
            if owned:
                _doc().commitTransaction()
        except Exception:
            _doc().abortTransaction()
            _transaction = False
            _doc().recompute()
            raise
    elif action in ("undo", "redo"):
        if _transaction:
            raise ValueError("Finish the current transaction first")
        getattr(_doc(), action)()
        _doc().recompute()
        mobile_sketch.validate_document(_doc())
        mobile_part.validate_document(_doc())
    elif action == "recompute":
        _doc().recompute()
        mobile_sketch.validate_document(_doc())
        mobile_part.validate_document(_doc())
    elif action == "save":
        if _transaction:
            raise ValueError("Finish the current transaction first")
        _doc().recompute()
        mobile_sketch.validate_document(_doc())
        mobile_part.validate_document(_doc())
        if any("Invalid" in o.State for o in _doc().Objects):
            raise ValueError("Document has failed features")
        _doc().saveAs(str(_file(request["file"])))
    elif action == "open":
        if _transaction:
            raise ValueError("Finish the current transaction first")
        if len(App.listDocuments()) >= 8:
            raise ValueError("Close a document before opening another")
        path = _file(request["file"])
        if any(d.FileName and Path(d.FileName).resolve()==path for d in App.listDocuments().values()):
            raise ValueError("This document file is already open; close it before reopening")
        _validate_fcstd(path)
        restored = App.openDocument(str(path))
        try:
            restored.UndoMode = 1
            restored.recompute()
            mobile_sketch.validate_document(restored)
            mobile_part.validate_document(restored)
        except Exception:
            App.closeDocument(restored.Name)
            if _document is not None:App.setActiveDocument(_document.Name)
            raise
        _document = restored
    elif action in ("python", "macro_run"):
        if _transaction:
            raise ValueError("Finish the current transaction before running Python")
        code = request["code"] if action == "python" else mobile_python.read(request["name"])
        mobile_python.run(code, "<mobile-console>" if action == "python" else request["name"])
        _document = App.ActiveDocument
        if _document is not None:
            _document.UndoMode = 1
    elif action == "macro_save":
        mobile_python.save(request["name"], request["code"])
    elif action == "macro_read":
        result = snapshot()
        result["macro_source"] = mobile_python.read(request["name"])
        result["macro_name"] = request["name"]
        return result
    elif action == "record_start":
        if _transaction:
            raise ValueError("Finish the current transaction before recording")
        mobile_python.start_recording()
    elif action == "record_stop":
        mobile_python.stop_recording(request["name"])
    elif action == "api":
        mobile_python.inspect(request.get("target", "App"))
    elif action == "part_import":
        if _transaction:
            raise ValueError("Finish the current transaction before importing geometry")
        name = _identifier(request["name"])
        if _doc().getObject(name) is not None or len(_doc().Objects) >= 1000:
            raise ValueError("Object name already exists or the document is full")
        shape = mobile_part.read_step(_root, request["file"])
        _doc().openTransaction("Import native STEP")
        try:
            obj = _doc().addObject("Part::Feature", name)
            obj.Shape = shape
            _doc().recompute()
            if "Invalid" in obj.State:
                raise ValueError("Imported STEP feature failed recompute")
            _doc().commitTransaction()
        except Exception:
            _doc().abortTransaction()
            _doc().recompute()
            raise
    elif action == "wire_preview":
        result=snapshot();result["wire_preview"]=mobile_part.wire_preview(_object(request["object"]));return result
    elif action == "element_info":
        result=snapshot();result["element_inspection"]=mobile_part.element_info(_object(request["object"]),request["kind"],request["index"]);return result
    elif action == "shape_info":
        result=snapshot();result["shape_inspection"]=mobile_part.shape_info(_object(request["object"]));return result
    elif action == "sketch_inspect":
        result=snapshot();obj=_object(request["object"]);mobile_sketch.require(obj);result["sketch_inspection"]=mobile_sketch.summary(obj);return result
    elif action == "sketch_preview":
        result=snapshot()
        result["sketch_preview"]=mobile_sketch.preview(_object(request["object"]))
        return result
    elif action == "part_preview":
        result = snapshot()
        result["preview"] = mobile_part.mesh(_object(request["object"]),float(request.get("tolerance",0.2)))
        return result
    elif action == "part_export":
        if _transaction:
            raise ValueError("Finish the current transaction before exporting geometry")
        _doc().recompute()
        result = snapshot()
        result["step_file"] = mobile_part.export_step(_object(request["object"]),_root,request["file"])
        return result
    elif action != "state":
        raise ValueError("Unknown document operation")
    return snapshot()


def dispatch(text):
    try:
        if len(text) > 65536:
            raise ValueError("Command exceeds 64 KiB")
        request = json.loads(text)
        if not isinstance(request, dict):
            raise ValueError("Command must be a JSON object")
        manual_before = _transaction
        result = execute(request)
        mobile_python.add_record(request, manual_before)
        # Recording metadata can change as a consequence of a full buffer.
        result["python"] = mobile_python.metadata()
        return json.dumps({"ok": True, "state": result}, ensure_ascii=True, allow_nan=False)
    except Exception as error:
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=True)
