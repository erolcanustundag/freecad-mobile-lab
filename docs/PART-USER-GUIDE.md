# Original Part document lab — 1.2 candidate

This development candidate connects the original FreeCAD1.1.4 Part/Materials modules to the isolated document lab. It is separate from the main mobile CAD recipe workspace. Android execution and broader desktop parity remain pending.

Open Workspace → Document lab, create a document, then open Original Part. Create a native Box, Cylinder, Sphere, Cone or Torus. Set / formula edits their native dimensional properties: choose the object name, property (Length, Width, Height, Radius, Radius1 or Radius2 as applicable), and a value such as 25 mm or 2 cm. Expressions use native document property names. Undo/Redo and explicit transactions use original App semantics. Part booleans choose result name, base object and tool object; the input shapes remain document dependencies.

In the lab command input:

```
NewDoc NativeModel
Add Solid Box
Set Solid.Length 30 mm
Set Solid.Width 10 mm
Set Solid.Height 5 mm
Add Tool Cylinder
Set Tool.Radius 3 mm
Set Tool.Height 10 mm
Cut Result Solid Tool
Preview Result 0.2
Save NativeModel.FCStd
ExportStep Result NativeModel.step
```

The preview uses genuine Part tessellation and the software viewport. One finger orbits, pinch zooms, two fingers pan. Tolerance must be0.05–2mm. The display is bounded to30,000 triangles and coordinates within±1,000,000mm; increasing tolerance can reduce display detail. This does not alter the saved BRep. Native tessellation may allocate memory before the display limit can be checked; no global Android memory guarantee is claimed. Wires without faces cannot use this triangle preview.

FCStd save/open preserves native whitelisted geometry, properties, expressions, links and supported metadata. Supported geometry types: Part::Feature, Box, Cylinder, Sphere, Cone, Torus, Cut, Fuse and Common. Other types, including Sketcher/PartDesign objects and arbitrary addon proxies, are rejected before restore. The existing QuantityDriver metadata proxy remains the sole supported scripted proxy. FCStd input remains128MiB, expanded ZIP256MiB, Document.xml16MiB and2,000 entries. This is not a general desktop FCStd editor.

ExportStep writes the selected original Part object through native Part.export, then opens Android's save picker. Export uses a plain.step/.stp filename. Files do not transfer the whole document/history/materials. The Python console exposes the loaded original Part API; try Api Part.makeBox or Python print(Part.makeBox(20,10,5).Volume). Gui and other workbench APIs remain pending. Macros have the existing tracing budget; native operations can take longer and Recovery/Restart remains available. Save FCStd before restarting.

Turkish: Workspace → Language → Türkçe, or Dil in the main workspace. Native Part menu captions have Turkish and German resources. Canonical object/property/API names and native diagnostics remain unchanged; command numbers use decimal points.
