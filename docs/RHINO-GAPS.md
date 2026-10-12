# Gaps after product 1.0

Comparison reviewed 12 October 2026 against Rhino's official feature documentation and published Rhino9 highlights. McNeel's general features/download pages still describe Rhino8; its Rhino9 page says available now. The comparison uses documented capabilities rather than assuming our similarly named commands have equivalent behavior.

| Area | Our current implementation | Work still missing |
| --- | --- | --- |
| Freeform CAD | Exact OCCT solids; bounded NURBS, loft/sweep/patch and rectangular UV trims | General trim/split/untrim, multi-rail/network surfaces, edge matching and continuity, rebuild/refit and robust interactive pole editing |
| Organic modeling | Bounded subdivision primitives | General editable SubD topology/cages, creases, soft transforms and validated SubD-to-NURBS conversion |
| Parametric design | Small typed graph (40 kinds,80 nodes), recipes, variants and scalar inputs | Grasshopper-compatible components/files, data trees, reusable subgraphs, broad list operations and plugin ecosystem |
| Precision interaction | Numeric commands, measurements, selected topology, pivot transforms, alignment and some snaps | Broad object snaps/CPlanes, direct manipulators and previews, persistent associative dimensions and geometric tolerances |
| Mesh/fabrication | STL import up to2m triangles/256MiB; bounded weld/winding/planar repair, bed/envelope, sampled thickness | General volumetric wrapping, nonplanar repair and global self-intersections; validated manufacturing analysis |
| Drawings | Limited A4 SVG bounds dimensions and sampled contours | Associative multi-view sheets/sections, hidden lines, editable annotations, hatches, dimension styles and GD&T |
| Rendering | Software/GLES shaded/studio previews, simple metallic/roughness, stripes/clipping/PNG | Ray tracing, texture/UV editing, environment lighting, physically based material workflows and render plugins |
| Interchange | Bounded STL/STEP/IGES/OBJ/DXF/3MF/GLB paths | Native3DM, DWG/USD and broad exchange coverage; complete materials, assemblies, instances and metadata round trips |
| Large projects/extensions | Layers and a separate App-only Python/document lab | Full CAD scripting bindings, broad addons, blocks/worksharing and proven large-model memory/performance budgets |

Rhino9 also documents adaptive Rebuild, Global Edge Continuity, MatchSubD/Knife, UVN manipulators, live clipping drawings, GD&T and in-model AI tools. Those capabilities are not implemented here. AI is lower priority than trustworthy geometry and device reliability.

Compared with original FreeCAD, the largest structural gap is the original geometry/workbench model: Base/App is present, but native Part/Sketcher/PartDesign, Assembly, TechDraw, CAM, FEM, BIM and general addon/FCStd compatibility remain pending. Similar custom commands in our main workspace are not those original workbenches. The frozen FreeCAD1.1.4 inventory and36-batch roadmap remain the acceptance plan.

Next four-feature batches should target (1) reliable selection/snapping/preview workflows, (2) general surfaces with continuity fixtures, and (3) original Part integration before native Sketcher/PartDesign. Each needs named functional acceptance cases and an APK checkpoint. Complete the phone/lifecycle/import-export test matrix alongside those batches.

Primary references:
- https://www.rhino3d.com/en/features/
- https://www.rhino3d.com/9/
- https://www.rhino3d.com/features/file-formats/
- https://developer.rhino3d.com/guides/opennurbs/what-is-opennurbs/
- FreeCAD source snapshot/inventory: FREECAD-UPSTREAM-MANIFEST.json, FREECAD-COMMAND-INVENTORY.csv, FREECAD-PARITY-BATCHES.json.
