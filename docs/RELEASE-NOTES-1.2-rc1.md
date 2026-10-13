# FreeCAD Mobile Lab1.2-rc1

Signed ARM64 Android8+ engineering candidate, minAPI26/target35, code24. The original full desktop FreeCAD/Rhino parity milestone remains NOT_COMPLETE.1.1 remains the latest full release.

Four Part prerequisite scopes connect genuine FreeCAD1.1.4 Part/Materials to the isolated document lab:

1. Original Part/Materials builtin runtime with seven additional real OCCT7.9.2 toolkits.
2. Native Box/Cylinder/Sphere/Cone/Torus, editable dimensions, dimensional expressions, native transactions, Undo/Redo and linked Cut/Fuse/Common objects.
3. Whitelisted native Part FCStd save/open and original STEP shape import/export. Import supports native transaction Undo/Redo; STEP exchanges shape geometry rather than the complete document/history/materials.
4. Genuine Part tessellation in the software viewport, bounded to30,000 preview triangles and0.05–2mm tolerance; saved BRep geometry stays exact.

Use Workspace → Document lab → New → Original Part. Quick commands include Add Solid Box, Set Solid.Length 30 mm, Cut Result Solid Tool, Preview Result 0.2, ImportStep Imported Model.step and ExportStep Result Model.step. The original Part API is available in the lab Python console/browser. The main mobile CAD recipe workspace remains independent.

English/Turkish/German support continues, now with634 reviewed Turkish/German entries, including Part/STEP menus and common errors. Use Workspace → Language → Türkçe or Dil in the main workspace. Canonical properties, APIs, numeric storage and model names remain intact. Advanced technical output can use English fallback.

Static verification passes63 packaged ARM64 native libraries plus69 Python extensions, API26 loader/strong-symbol availability, real Part/Materials entrypoints,16KiB ELF/ZIP alignment,823 Python asset hashes and retained-certificate v2/v3 signatures. The desktop reference passes270 real JNI/FCStd/STEP/parametric geometry and preview assertions. A missing-default-material failure was fixed by packaging251 unchanged upstream material/model resources and configuring their native module-library paths. Physical Android startup, language switching, geometry workflows, lifecycle and file-picker tests for this candidate remain NOT_RUN.

FCStd restoration supports documented App metadata/proxy types and Part::Feature/Box/Cylinder/Sphere/Cone/Torus/Cut/Fuse/Common only. Native Sketcher, PartDesign, Gui and other workbench/addon objects remain pending. Native material/model resources are bundled; a full material editor and complete Part task/UI semantics remain pending. Optional RapidJSON/FreeType support is disabled in this headless build; no new native GLTF or font-curve support is claimed. Native import/tessellation can allocate memory before display bounds are checked; Android memory budgets remain unmeasured. The retained development signing key stays private and was not deleted or published.
