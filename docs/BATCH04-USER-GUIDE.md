# Native App Python tools — rc6

Open the **FreeCAD document lab** from the workspace menu or recovery screen. The Python, Macros, API and Script feature buttons are inside its scrollable document panel. Its command input remains below that panel.

Try these commands:

```
Python print(App.Version())
Python print(App.Vector(1, 2, 3).Length)
Api App.Vector
Api App.Units
```

The Python button opens a multiline editor. `App` and `FreeCAD` refer to the original upstream module. Variables stay available during the current document-process session. Output/errors appear below the property panel. Source/request and output are bounded; Python tracing stops long Python loops after two seconds. A native call can take longer. Python can alter or close documents; save models before experimenting with code. Workbench modules such as Part and Gui are not available yet.

Macros supports new, edit, run, record, save recording and `.py` file import/export. Imports are saved without running them. Syntax errors leave an existing saved macro intact. Private macros persist across APK upgrades. The complete JSON command payload must fit 64 KiB; source is also capped at 64 KiB, so heavily escaped text can reach the payload limit sooner.

Record a new native metadata model:

```
Record
NewDoc MacroModel
Add Source Feature
AddProperty Source Width Length
Set Source.Width 2 cm
StopRecord Model.py
Close
RunMacro Model.py
```

The recorder captures successful document edits as App Python code, including native edit transactions and typed numeric/boolean assignments. Use a fresh document or a NewDoc command when creating a replayable model. Failed operations are not recorded. Open/save file operations are not recorded with private device paths. Python console code can also be recorded. Exported basic App macros can run on a desktop with a compatible FreeCAD installation.

For a scripted feature, create Source with a Width Length property, then:

```
Proxy Scaled Source.Width 2
Set Source.Width 32 mm
Save Scripted.FCStd
Close
Open Scripted.FCStd
Set Source.Width 21 mm
```

Scaled.Output becomes 64 mm, survives native FCStd restoration, then recomputes to 42 mm. The Script feature button provides the same inputs in a dialog. This is an actual FeaturePython QuantityDriver with a native dependency. It computes dimensional metadata; Part geometry comes with the Part port. The packaged registry currently permits this class only. Its `mobile_features.py` source is in the source archive; install that module too when using its FCStd/macros on desktop. General addon proxy classes remain pending.

The API browser reads members/docstrings of available App/Base objects. It helps discover installed APIs, and does not add absent workbenches. No Android runtime/UI/picker test has run. Rc6 remains a development-signed engineering candidate, not stable1.0 or complete desktop FreeCAD.
