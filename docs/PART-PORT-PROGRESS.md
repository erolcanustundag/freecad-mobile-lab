# Original Part prerequisite —1.2-rc1

This candidate connects genuine FreeCAD1.1.4 Part/Materials to the isolated document lab. Product1.1 remains the latest full release and has no original Part runtime. The main custom mobile CAD scene remains independent.

Four bounded scopes: original Part/Materials builtin runtime; native parametric primitives, expressions, transactions and linked booleans; whitelisted native Part FCStd plus STEP shape exchange; genuine tessellation displayed in the software viewport. They are engineering verified with Android execution stillNOT_RUN. They do not complete the whole Part workbench, B05 or the full FreeCAD/Rhino milestone.

| Evidence | Result |
| --- | --- |
| Original ARM64 and Linux Part/Materials/bridge compilation | PASS |
| Real JNI geometry, analytic volumes, expression/recompute, Undo/Redo, rollback, Unicode FCStd, STEP and preview winding/rendering |270 PASS |
| Existing document JNI and Python-tool regressions with Part loaded |88 and62 PASS |
| Locale/command/fallback/Unicode checks |527 PASS;3 resource tests |
| Runtime packaging boundary |7 PASS, including rejection of missing native material data |
| Packaged ARM64 loader/symbol/alignment checks |See core-apk-verification.json; executionNOT_RUN |

The port adds real OCCT7.9.2 TKFeat, TKExpress, TKBin, TKBinL, TKMeshVS, TKRWMesh and TKDEGLTF against the retained toolkit binaries. The original expression-parser C sources compile as C. No geometry implementations are stubbed. Default core-only build paths remain separate; --part enables original Part and its Materials dependency with GUI/other workbenches disabled.

Actual tests caught Material not found when creating a native box. The fix bundles251 unchanged upstream material/model resources and registers their versioned paths through native module-library preferences. It preserves upstream default UUIDs and data. Code24 replaces any earlier code23 prototype interpreter cache. Material data retains its original author/license notices, including GPL2 default cards; a GPL2 license copy is included. Full material editing, GUI task semantics and other workbench resources remain pending.

Preview is limited to30,000 triangles,0.05–2mm tolerance and coordinates within±1,000,000mm. Native parsers/tessellation can allocate before the display limit is checked; device memory budgets remain unmeasured. FCStd is limited to documented App metadata/proxy and Part primitive/feature/boolean types. STEP exchanges shape geometry; history, assemblies, colours/materials are not preserved by the shape-only adapter. Optional RapidJSON/FreeType are disabled: no new native GLTF/font-curve capability is claimed. Physical Android launch, recovery, lifecycle, language switching and file pickers require execution tests.

Next: the original Sketcher module and B05 general entities/editing/attachments, then native PartDesign. See PART-USER-GUIDE.md and FREECAD-PARITY-BATCHES.json.
