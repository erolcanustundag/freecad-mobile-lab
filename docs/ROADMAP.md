# FreeCAD Mobile Lab — complete desktop parity roadmap

Updated 12 October 2026. Product release: **1.1 / code22, current mobile feature set**. B01–B04 remain the completed bounded engineering scopes. The user reports startup works on their phone. **Full desktop parity and the original comprehensive stable-1.0 milestone are NOT COMPLETE.** Version 1.0 is the first public mobile feature release; it does not close that larger milestone. 1.1 adds Turkish/German UI, persistent locale choice, command aliases and recovery-role repair; it does not close a native workbench batch. See LANGUAGES.md, RHINO-GAPS.md and RELEASE-SCOPE-1.0.md.

## Baseline and scope

Freeze the target at **FreeCAD 1.1.4**, the latest non-prerelease reported by the official GitHub releases API on 11 October 2026, published 28 September 2026. Release: https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4 . This roadmap covers the upstream application, bundled/optional modules, file formats, document semantics, scripting and desktop workflows. It does not silently equate our similarly named tools with ports of the original workbenches.

The source-level inventory is `FREECAD-COMMAND-INVENTORY.csv` / `.json`, with a separate `FREECAD-DYNAMIC-REGISTRATIONS.csv`. It contains 1,106 literal command declarations across26 module groups and791 dynamic registration sites. All literal rows have initial module-based batch routes, but command-specific acceptance fixtures remain UNASSESSED. The scanner records source locations; dynamic registrations, optional dependencies, duplicate registration sites and non-command capabilities require runtime reconciliation. The inventory is not a claim that every upstream function has already been individually reviewed. Map every row to detailed acceptance tests before closing parity. All source modules are included in the audit, even where not enabled in a standard build.

External community add-ons form an open-ended ecosystem. The parity goal includes the Python API, addon loading, dependency handling and explicit compatibility reporting. A pinned addon catalogue/test set must be established; arbitrary future third-party addons cannot have a finite completion date. Built-in functionality takes priority. Obsolete desktop workbenches are audited against the frozen release rather than reinstated automatically. Rhino/Grasshopper/SubD/jewellery ambitions remain in `ROADMAP-JEWELLERY-LEGACY.md` and are additional goals, not features claimed as part of upstream FreeCAD.

## Architecture required for real compatibility

The main CAD workspace uses a custom Android UI around OCCT 7.9.2 and extracted FreeCAD PlaneGCS, with a limited custom recipe graph. Rc5 also packages an opt-in upstream FreeCAD Base/App document lab with CPython, typed properties, native expressions/transactions/groups/links and App-only FCStd restoration. The JNI adapter passes 88 host checks; its 123 packaged libraries/extensions pass static alignment/closure checks. Automated Android execution has not run; the user separately reports startup works on one phone. The upstream lab is separate from the main fcml graph and has no Part/Sketcher/PartDesign/Gui workbenches yet. Rc6 adds a console, saved/recorded Python macros, available-API inspection and one portable scripted QuantityDriver metadata feature, with 62 additional host checks. General addon proxy support remains pending. Stored BREP import in the main workspace is still not editing the original FreeCAD feature model. `FREECAD-CORE-PORT.md` and `PARITY-B03.md` distinguish these boundaries.

The compatibility track must build and expose the upstream FreeCAD document core and Python bindings on Android, retaining native CAD geometry. A mobile command/task/property adapter replaces desktop interaction. Qt/Coin/Python GUI dependencies require an explicit Android integration strategy and independent build proofs; precompiled desktop libraries cannot be placed in an Android APK. Keep the current renderer and usable custom tools while the core adapter is developed. FreeCAD documents require native recompute, object types, property units, expressions, links, feature proxies and dependency semantics. Avoid reimplementing isolated buttons and calling the result a complete workbench.

## Release cadence

Use **four functional feature scopes per engineering batch**, then build/sign/verify/save an APK and matching source/continuation checkpoint. Continue to the next batch without routine approval requests. A single large scope can require multiple four-feature sub-batches; do not count aliases, help entries, stubs or four fragments of one unfinished workflow as four completed features. Repair regressions before sealing a checkpoint. Preserve every APK and give it an increasing Android version code. Current candidates remain development-signed; stable production signing and prototype migration are separate release gates.

The batch ledger `FREECAD-PARITY-BATCHES.json` stores the four scopes, implementation/test status, APK and evidence. It is an ordered dependency plan, not a claim that all 144 broad scopes fit in 36 builds or a calendar promise.

## Planned batches

| Batch | Area | Four feature scopes |
| --- | --- | --- |
| B01 | Precision access | Scalar expressions and saved variables; Object / CAD-distance / point-angle measurement; Arbitrary-axis pivot rotation and scaling; Interactive orientation cube |
| B02 | Document organisation | Bounded spreadsheet editor and CSV exchange; Bounding-box object alignment; Fit selected object; Layer visibility / locking controls |
| B03 | Document core | Port FreeCAD Base/App dependency build; Native document/property/recompute adapter; Transactions, Undo/Redo and expression dependencies; Native FCStd read/write round-trip |
| B04 | Python runtime | Embedded CPython Android runtime; FreeCAD Python bindings; Python console and recorded macros; Scripted feature proxy restore/recompute |
| B05 | Sketch geometry | General sketch entity model; Line/arc/circle/ellipse editing; B-splines and construction geometry; Plane/face attachment and external references |
| B06 | Sketch constraints | Coincident / horizontal / vertical / distance; Tangent / perpendicular / parallel / angle; Equal / symmetry / radius / diameter; Solver diagnosis, DOF display and conflicting constraints |
| B07 | Sketch workflows | Trim/extend/fillet and split geometry; Sketch arrays / mirror / clone; Projection/intersection and reference geometry; Constraint editing, drag solving and saved sketches |
| B08 | PartDesign foundation | Bodies, local coordinates, Tip and multiple bodies; Datum planes/axes/points and attachment modes; ShapeBinder/SubShapeBinder references; Face-attached sketches and cumulative feature tree |
| B09 | PartDesign solids | Full Pad/Pocket and extent options; Revolution/Groove and additive/subtractive lofts; Additive/subtractive pipe and helix; Hole feature, taper and thread options |
| B10 | PartDesign finishing | Selected fillet/chamfer/draft/thickness parity; Associative linear/polar/mirror/scaled patterns; MultiTransform, suppression and feature reordering; Body Boolean/clone and cross-body workflows |
| B11 | Part primitives and queries | All primitive families and parameter editing; Compound/compsolid/fuse/cut/common parity; Shape builder, explode and conversions; Exact geometry validation/refine/tolerance tools |
| B12 | Part advanced tools | Full extrude/revolve/loft/sweep options; General offsets, shell and section tools; Split/slice/fragments and Boolean pipelines; Curve/surface domain operations and continuity |
| B13 | Draft creation | Working planes and plane proxies; Full line/polyline/arc/conic/B-spline geometry; Text/shape-string/hatch/dimension objects; Draft wires/faces and conversion tools |
| B14 | Draft editing | Working-plane grid and complete snap modes; Move/rotate/scale/offset/trim/stretch tools; Associative arrays/clones/links and path arrays; Draft style/layer overrides and editable annotations |
| B15 | Spreadsheet/expressions parity | Full cells, aliases, units and formatting; Model property references and dependencies; VarSet/property-expression completion; Cross-document formula references and CSV workflows |
| B16 | Surface workbench | Boundary/filling surfaces with arbitrary loops; Ruled/Gordon and supported surface construction; Edge extension/curve-on-surface tools; Pole/weight editing and continuity analysis |
| B17 | Mesh and MeshPart | Full STL/OBJ/PLY/3MF mesh data model; Evaluate/repair and self-intersection tools; Decimate/refine/smooth/remesh workflows; Mesh/CAD conversions and tessellation settings |
| B18 | Points/reverse engineering/inspection | Point-cloud import/edit/section tools; Supported curve/surface fitting workflows; Deviation comparisons and inspection reports; CAD/mesh/point-derived geometry validation |
| B19 | Assembly foundation | Assembly containers, insertion and component links; Grounding, placements and coordinate connectors; Fixed/revolute/slider/ball joint families; Constraint solve and conflict diagnosis |
| B20 | Assembly completion | Remaining joints and motion limits; Joint animation and simulation; Bill of Materials and component metadata; Cross-document assemblies and large-model instancing |
| B21 | TechDraw layouts | Templates, editable title fields and page formats; Projected multi-view / axonometric groups; Sections / complex sections / detail / broken views; Page layout, view alignment and printing |
| B22 | TechDraw annotation | Linked linear/angular/radius/diameter dimensions; Chain/coordinate/extent dimensions and repair; Hatches, symbols, balloons, leaders and rich text; SVG/DXF/PDF export and manufacturing notation |
| B23 | CAM setup | Job/stock/fixture/work-coordinate model; Toolbit library and cutting parameters; Facing/profile/pocket/drilling operations; Toolpath preview, ordering and collision review |
| B24 | CAM complete workflow | Remaining machining and multi-pass operations; Dressups, holding tabs and feed/speed handling; Post-processors and G-code output; Stock-removal simulation and reference machining checks |
| B25 | FEM setup | Analysis containers and material assignment; Loads, boundary conditions and mesh regions; Gmsh/Netgen integration or verified alternative; Solver export, execution and process isolation |
| B26 | FEM results | Supported structural/thermal/electrostatic analyses; Result field/unit handling and probes; Deformation/contour/glyph views and animation; Solver concordance and project/result persistence |
| B27 | BIM structure | Project/site/building/storey spatial hierarchy; Walls, columns, beams, slabs and structural objects; Windows/doors/stairs/roof/reinforcement workflows; BIM properties, classifications and quantities |
| B28 | BIM interoperability | Native IFC import/export and editable mapping; BIM section/elevation/plan views; Site/sun/georeferencing tools; Schedules, quantities and cross-document BIM links |
| B29 | Material system | Material cards and material libraries; Physical/appearance properties with unit handling; Material assignment and reuse across workbenches; Material file import/export and linked-property updates |
| B30 | Additional bundled capabilities | OpenSCAD CSG import/export and history repair; Robot trajectory/robot model workflows where supported; IDF/Plot/Import and optional bundled integrations; Inspection/ReverseEngineering/legacy optional module audit |
| B31 | Std/UI parity | Document tree/property/task panels and search; Selection clarification, filters and measure overlays; Navigation/view/draw-style/transform preferences; Images, annotations, groups, links and standard utilities |
| B32 | Formats and metadata | Complete bundled format import/export matrix; Assembly transforms, units, materials and names; Loss reporting and unsupported-feature preservation; Malformed-file and archive-isolation regression matrix |
| B33 | Extension ecosystem | Addon Manager catalogue and dependency model; Workbench Python command adapter; Binary/Qt-dependent addon compatibility reporting; Pinned addon fixture suite and update/rollback handling |
| B34 | Rendering and device optimisation | Desktop-equivalent view modes and material shading; Instancing/LOD/progressive tessellation and caches; GPU context recovery, large meshes and measured budgets; External Render-workbench adapter feasibility |
| B35 | Accessibility and support | Touch/keyboard/stylus/tablet workflows; Accessibility and localization; Offline workbench help and sample projects; Licences, source offers and upgrade/recovery support |
| B36 | Parity closure | Runtime command inventory vs static source reconciliation; Desktop/native document and numeric reference matrix; Android device/startup/lifecycle/SAF/upgrade matrix; Close every command/capability gap or retain explicit pending status |

## Acceptance rules for every feature

1. Match the frozen desktop behaviour on at least one nominal and one edge/error fixture, including numeric/unit tolerances, object types and dependencies. Preserve source fixture and expected result provenance.
2. Expose a usable mobile workflow and command input. Show operation errors without losing the prior document. Do not create false geometry results on failure.
3. Verify save/reopen, native/custom document ID remapping, Undo/Redo, model recompute, dependency changes, unsupported versions and export. A snapshot must be labelled as a snapshot rather than associative history.
4. Verify the real Android interaction, lifecycle and memory cost. Host math/kernel tests and signature checks cover their tested scope only.
5. Record status precisely: PENDING, IN_PROGRESS, ENGINEERING_VERIFIED_DEVICE_PENDING, or PARITY_VERIFIED. Only the last closes a desktop compatibility row. Record limitations and missing options, not a guessed completion percentage.

## Existing mobile coverage

| Desktop area | Current mobile coverage | Gap to parity |
| --- | --- | --- |
| Base/App/Std | Main custom scene plus opt-in native App metadata editor, dimensional properties, expressions, groups/links, transactions and App-only FCStd | Geometry workbench integration, broader scripted proxies/properties, GUI task semantics and device concordance |
| Part/PartDesign | Exact solids, booleans, extrude/revolve/loft/sweep, selected fillet/chamfer/shell and custom recipes | Full Body, datum/attachment/reference infrastructure, options, patterns, suppression and stable upstream document semantics |
| Sketcher/Draft | Weighted XY pole drafting, limited snaps, numeric curves and constrained rectangular pad | General sketch entity/constraint editor, attachments, DOF/conflict feedback and full drafting objects |
| Surface | Rational poles, simple patch and rectangular UV trims | Complete workbench plus general loops, surface construction/editing and continuity workflows |
| Spreadsheet/expressions | B01 scalar variables, B02 bounded worksheet/CSV, B03 native App property expressions | Full native Spreadsheet objects/aliases, main CAD bindings and Android concordance |
| Measure/Inspection | Existing geometry analysis; B01 adds unified measure/distance/angle access | Persistent measurements, selection overlays, deviation and full workbench commands |
| Assembly | Object organisation and numeric transformations | Native assemblies, joints, solving, BOM, animation and links |
| TechDraw | Limited A4 overall-dimension SVG from XY contours | Native pages/views/dimensions/projections/sections/hatches/annotations/PDF |
| Mesh/MeshPart | Bounded STL/OBJ, simple planar repair, native display decimation and restricted 3MF/GLB | Full mesh editing, repair/remesh/conversion and metadata interoperability |
| Points/ReverseEngineering | No native workbench | Point clouds, fitting/conversions and comparative geometry |
| CAM | No toolpath/postprocessor engine | Complete job/tool/stock/operations/simulation and G-code workflows |
| FEM | No solver/analysis runtime | Analysis/meshing/materials/boundaries/solvers/results and concordance |
| BIM | No BIM/IFC objects | Spatial hierarchy, building elements, IFC, quantities and views |
| Material | Saved metallic/roughness and supplied-density mass estimates | Native material cards/properties/units and cross-workbench use |
| OpenSCAD/Robot/optional modules | No desktop module compatibility | CSG history, robot trajectories, optional modules and dependency availability |
| Python/Addons | Embedded CPython, upstream App/Base bindings, console, saved/recorded macros, API browser and one portable FeaturePython proxy | General addon proxies, workbench/Gui bindings and addon compatibility matrix |
| Formats | Exact STEP/IGES/BREP, meshes, fcml/cadgraph, sampled SVG/DXF, restricted BREP/3MF/GLB and native App-only FCStd | Geometry/workbench FCStd, complete format/assembly/material/property preservation and runtime checks |
| Rendering/UI | CPU/GLES preview, studio/zebra/wireframe, clipping and PNG | Desktop interaction parity, large-model instances, supported device budget and external renderer integration |

## B01 boundaries

Scalar expressions support arithmetic, powers, unary math functions, pi/e, explicit length-unit conversions and degree-to-radian conversion. Saved variables can refer to other variables with cycle/depth limits. Command arguments evaluate once; changing a variable does not automatically edit existing solids. These are scalar calculations, not dimensionally checked FreeCAD expressions. Older candidates can preserve the saved geometry while ignoring the new variable metadata.

Measurement reports use exact CAD minimum distance for two CAD objects, numeric point distance and three-point angle. They do not expose CAD vertex coordinates or persistent measurement annotations yet. Bounding-box centre is not centre of mass. Pivot transformations commit one Undo step and regenerate existing custom dependants; rotated primitive snapshots follow the native adapter's existing conversion rules. The cube chooses orthographic faces and ISO; device touch/accessibility tests are pending.

## Gates that cannot be closed by APK packaging

B02 adds a custom bounded A1:H32 worksheet with scalar formulas and CSV exchange, bounds alignment, fit selected and layer-wide controls. The worksheet supplies evaluated command arguments but does not bind existing CAD parameters or restore native Spreadsheet objects. This closes the four B02 mobile scopes, not B15 upstream Spreadsheet parity. `PARITY-B02.md` records verification and `BATCH02-USER-GUIDE.md` records limits.

The user reports that the app now works on their phone (12 October 2026); no device details or test log were supplied. The earlier instant-crash root cause remains uncaptured. Retain software rendering by default, independent recovery UI, autosave backups and diagnostic export. The original comprehensive qualification milestone requires 20 cold starts / 50 resumes, file-picker cancellation and process recreation, low-memory recovery, schema upgrades, prototype/private-signing migration, ARM64 API/OS coverage and a second supported device. The current environment has no connected Android device; do not label host verification as a physical-phone pass.

Manufacturing needs independent CAD dimensional checks and physical print/casting calibration. FEM requires trusted solver concordance. CAM needs reference toolpath/simulation checks; generating a file does not certify a safe machining process. Large-file limits require measured Android memory budgets before expansion. No public publication is implied by this development request.

## Next action

B01–B04 bounded scopes have signed APK checkpoints. B03 contains the real upstream App metadata editor; host JNI 88 checks and packaged static checks passed, with Android/device validation pending. Port Part and missing OCCT/OCAF/exchange toolkits and connect native TopoShape output to the renderer. Expand Python/workbench bindings and proxy compatibility alongside the actual module ports. Part backend is a prerequisite for native Sketcher and PartDesign: satisfy that dependency before their feature batches, regardless of scope-group numbering. Arbitrary FCStd models, all workbenches and the original comprehensive qualification milestone remain unfinished. Preserve source, APK and continuation checkpoints; do not count unverified placeholders as workbench parity.

## Primary references

- Frozen release/source: https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4 and https://github.com/FreeCAD/FreeCAD/tree/1.1.4
- Workbench index: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Workbenches.md (archived documentation; reconcile against release source)
- PartDesign: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/PartDesign_Workbench.md
- FCStd format: https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/File_Format_FCStd.md
- Sketcher/Spreadsheet/TechDraw documentation in the same official repository.

## Original Part prerequisite checkpoint —1.2-rc1

P-PART adds four bounded foundations before B05: original Part/Materials runtime; native parametric solids/expressions/transactions/linked booleans; whitelisted native Part FCStd and STEP shape exchange; bounded genuine tessellation in the software viewport.270 real host JNI geometry/format/preview checks,88 document regressions and62 Python-tool regressions pass. Required default materials/models are bundled after an actual feature-creation failure identified the missing data. The new ARM64 runtime is built and statically checked; physical Android execution remainsNOT_RUN. B05 and later broad workbench scopes stayPENDING. Next: original Sketcher module and the general entity/edit/attachment infrastructure, followed by native PartDesign.


## Original Sketcher checkpoint —1.2-rc3

P-SKETCHER adds four bounded feature scopes: native sketch entity edits and solver-aware movement/deletion; rational B-splines/construction; native constraints, dimension units, DOF and rollback; supported Sketcher FCStd persistence and sampled XY preview.955 genuine JNI assertions and269/88/62 Part/document/Python regressions pass. The embedded-runtime fault-handler defect is fixed with an explicit integration patch and a real VM handler probe. Turkish/German controls and guides extend1.1 localization. B05/B06/B07 remain PENDING for their complete scope; Android execution is NOT_RUN.

Next four-feature sub-batch: explicit sketch plane placement; native face attachment with reference validation; external edge references; persistence/dependency/Undo-Redo validation for those attachments. Then expand trim/split/fillet and constraint editing before PartDesign. Publish a signed engineering APK after each validated four-feature subset, without marking entire broad batches complete from a module import.

###13 October2026 — attachment/reference sub-batch

1.2-rc4/code27 builds on published1.2-rc3. Four additional bounded native scopes are engineering-verified on the host: sketch planes/arbitrary placement; single planar face attachment/offset/detach; original projected external edges/constraints; dependency-safe FCStd and native history.1236 Sketcher checks cover the actual APIs and64-reference boundary. Android execution remainsNOT_RUN; full B05/B06/B07 stayPENDING. Next four scopes are original trim, extend, fillet and split workflows with geometry/constraint/reference/history fixtures. No PartDesign or full workbench parity is claimed.

###1.2 full mobile release — editing sub-batch

Four native editing scopes are host-verified: trim, line extension/shortening, connected-line corner fillet and curve split. Full B05/B06/B07 remainPENDING at comprehensive/device scope. Next four scopes: native mirror, geometry array, symmetry constraints and reference/driving constraint controls, with native persistence/history checks.1.2 is a full GitHub/mobile feature release as requested, not a declaration of full desktop parity.

###1.3 full mobile release — pattern/dimension sub-batch

Four bounded native scopes are host-verified: mirror copies; rectangular arrays/optional spacing constraints; axis/point symmetry; driving/reference measurements.1438 Sketcher checks pass. Full B05/B06/B07 and device gates remainPENDING. Next four scopes: point-on-object constraints, horizontal/vertical coordinate dimensions, Block/fixed geometry, and active/inactive constraint controls, with native history/FCStd tests and another full release.

### 1.4 full mobile release — native constraint sub-batch

Four bounded native scopes are host-verified: PointOnObject, signed DistanceX/Y forms, Block/fixed geometry and active/inactive constraints. 1613 Sketcher checks pass; full B05/B06/B07 and device gates remain PENDING. Next four scopes: constraint names, dimensional expression binding, solver constraint/DOF inspection, and fully constrained profile handoff to original Part extrusion/revolve with native history/FCStd fixtures. F-Droid clean source-build integration remains a separate pending distribution task.

###1.5 checkpoint — native profile sub-batch
Constraint naming, dimensional expression binding, read-only solver/reference inspection and linked original Part extrusion/revolution are host-verified with1717 checks. Native PartDesign/full-workbench/device gates stay pending. Next: extrusion extent modes, revolution axis/extent editing, native placement and exact shape measurements with solid fixtures.

###1.6 — native solid control sub-batch
1785 native Sketcher/profile/solid checks pass, covering exact volume/area/unique edge lengths/centroids, native extent modes, plane-normal dependency, placement, history and FCStd. Full workbench/device gates stay pending. Next four: selected-edge native fillet, chamfer, refinement and solid-to-surface section tools with topology/reference fixtures.
