# Original Part document lab — 1.8

The current mobile feature set connects the original FreeCAD1.1.4 Part/Materials modules to the isolated document lab. It is separate from the main mobile CAD recipe workspace. Android execution and broader desktop parity remain pending.

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
ImportStep Imported NativeModel.step
```

The preview uses genuine Part tessellation and the software viewport. One finger orbits, pinch zooms, two fingers pan. Tolerance must be0.05–2mm. The display is bounded to30,000 triangles and coordinates within±1,000,000mm; increasing tolerance can reduce display detail. This does not alter the saved BRep. Native tessellation may allocate memory before the display limit can be checked; no global Android memory guarantee is claimed. Wires without faces cannot use this triangle preview.

FCStd save/open preserves native whitelisted geometry, properties, expressions, links and supported metadata. Supported geometry types: Part::Feature, Box, Cylinder, Sphere, Cone, Torus, Cut, Fuse, Common, Plane, Extrusion, Revolution, Fillet, Chamfer and Section, plus supported Sketcher::SketchObject profiles. Other types, including PartDesign objects and arbitrary addon proxies, are rejected before restore. The existing QuantityDriver metadata proxy remains the sole supported scripted proxy. FCStd input remains128MiB, expanded ZIP256MiB, Document.xml16MiB and2,000 entries. This is not a general desktop FCStd editor.

Import Part STEP opens the Android file picker and imports up to128MiB into a native Part::Feature. Create a document first. STEP shape transforms are carried by the imported BRep; document history, source labels/assembly tree, colours and materials are not preserved by this shape-only reader. Import is a native transaction with Undo/Redo. The native parser can use memory before a shape is returned; device budgets remain unmeasured.

ExportStep writes the selected original Part object through native Part.export, then opens Android's save picker. Export uses a plain.step/.stp filename. Files do not transfer the whole document/history/materials. The Python console exposes the loaded original Part API; try Api Part.makeBox or Python print(Part.makeBox(20,10,5).Volume). Gui and other workbench APIs remain pending. Macros have the existing tracing budget; native operations can take longer and Recovery/Restart remains available. Save FCStd before restarting.

Turkish: Workspace → Language → Türkçe, or Dil in the main workspace. Native Part menu captions have Turkish and German resources. Canonical object/property/API names and native diagnostics remain unchanged; command numbers use decimal points.

## Sections, wires and measurements


SECTIONS AND EDGE INSPECTION (1.8)
SectionPlane Solid Slice 0 0 5 0 0 1 100 creates a native finite Part plane centred at world XYZ (0,0,5), with normal (0,0,1) and size100mm, and a linked native section. Slice_Plane is the editable helper; PartPlacement changes its world placement. The plane has local UV bounds0..size; its placement offsets those bounds about the requested centre. The source and helper stay as dependencies. Empty/invalid sections and out-of-bounds helper planes roll back together.
WirePreview Slice samples actual world-space native edges for display. Drag to orbit, pinch to zoom, two fingers to pan; Fit resets the view. Edge numbers are current1-based indices. At most128 edges/8192 points; straight edges use2 points, curves65. Tiny/pole edges at or below1e-7mm are skipped for drawing. Sampling changes display detail only; native geometry and STEP exports retain their exact curves. Touch gestures have not been independently tested on Android.
ElementInfo Solid Edge1 reports exact length, bounds, raw curve parameter range and endpoint coordinates. ElementInfo Solid Face1 reports native area/surface type, area centroid and a point/normal evaluated at the middle of the surface parameter range. The area centroid need not lie on the surface; the evaluated point need not lie within every trimmed face. Units are mm/mm²; curve/UV parameters retain native units. Below-tolerance edges report that flag rather than claiming they are topologically degenerate.
FinishSettings Rounded 1,2 2 updates current edge selections and equal radius/distance in mm on a native fillet/chamfer. Native recompute, Undo/Redo and FCStd preserve the edit. Use1–32 unique current1-based edges. This is not a guarantee of stable selections across arbitrary topology changes. Inspect and retry if native geometry fails.
