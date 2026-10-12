# FreeCAD Mobile Lab — app roadmap

Updated 10 October 2026. Baseline: 0.2.0-experimental, version code 5.

## Product direction

Build an offline native Android CAD app that makes precise jewellery design practical on a phone, then expand into broader freeform modelling and fabrication. Jewellery is the first complete workflow: design a ring or setting in millimetres, edit it comfortably, verify its geometry, save it, and export it for printing or casting.

Keep exact CAD geometry separate from tessellated display previews. Mesh operations must identify their mesh output explicitly. Features count as complete when their geometry, editing, persistence, Undo, export and Android interaction have all been verified.

This is a proposed sequence, not a calendar commitment. Version numbers below describe intended milestones. Larger changes can span several releases.

## Verified starting point

The delivered source archive records:

- OpenCASCADE 7.9.2 geometry and the FreeCAD PlaneGCS solver; native ARM64 Android packaging.
- Weighted NURBS curves, touch XY curve creation, basic NURBS patches, profiles, extrusion, loft, revolve, sweep and pipe.
- Booleans, fillets, chamfer, offsets, hollowing, healing, sewing and closed-shell solidification.
- Round bezel/prong settings, a gemstone cutter, casting allowance, arrays, mirror and limited Catmull–Clark forms.
- A 12-component typed graph that regenerates on Evaluate.
- STEP/IGES/BREP, STL/OBJ, project persistence, sampled SVG/DXF output and shaded PNG output.
- Host regression results: 25,694 baseline assertions plus large-model checks and 459 freeform assertions. A 1,441,792-triangle STL retained full geometry through export and project reopening.

Physical Android startup and complete Activity/file-picker workflows remain unverified. The previously reported instant crash has no confirmed device-level root cause. Host test success does not establish phone reliability.

Current limits remain explicit: STL/OBJ imports up to 2 million triangles, STL input up to 256 MiB, topology/repair analysis up to 100,000 triangles, and an independently bounded viewport. Increasing these limits requires memory measurements.

## Release sequence

| Milestone | Main work | Completion gate |
| --- | --- | --- |
| 0.2.1 — reliability | Reproduce startup failures; fix native loading, lifecycle and file operations; protect projects | Phone launch, recovery and save/reopen tests pass |
| 0.3 — comfortable mobile editing | Selection, transform handles, snapping, views, object organisation and Redo | Complete modelling session using touch controls, with reliable history |
| 0.4 — jewellery workflow | More setting shapes, editable ring shanks, stone seats, engraving and templates | Reference pieces retain dimensions through edit, save and print export |
| 0.5 — deeper CAD/freeform editing | Persistent feature history, curve/surface handles, trims, blends and analysis | Upstream edits regenerate dependants or report a recoverable failure |
| 0.6 — richer parametric design | More graph components, lists, patterns, reusable groups and controlled live previews | Pattern regeneration, graph history and saved recipes remain deterministic |
| 0.7 — fabrication and interoperability | Better mesh diagnostics/repair, thickness analysis, drawings and additional exchange formats | CAD/mesh round trips pass dimensional and topology checks |
| 0.8 — visualisation and performance | GPU validation, adaptive detail, section views, PBR materials and improved image export | Reference scenes render correctly within measured phone budgets |
| 1.0 — dependable public release | Release signing, migration, documentation, device testing and support process | Stable end-to-end workflows across the supported device matrix |

## 0.2.1: make the app dependable

Highest priority. New heavy modelling features should not displace this work.

1. Obtain a device crash report and identify the failing startup stage. Distinguish native loader failure, geometry failure, Java exception, graphics failure and memory pressure.
2. Verify the lightweight recovery launcher independently of the CAD process. Test empty workspace startup, a corrupt autosave and a forced CAD-process crash.
3. Exercise real Android open/save/export pickers, denied/cancelled operations, background/resume, rotation and process recreation.
4. Add visible progress for long operations. Reject excessive inputs before large allocations. Cancellation may be offered only where the operation can safely stop; do not advertise cancellation that merely hides a running job.
5. Verify project migration from earlier versions and preserve recovery copies on failure.
6. Measure time and peak memory for representative small CAD scenes and the existing dense STL fixture. Retain full source geometry during display simplification.

Proposed release gate: on the reporting phone, 20 cold starts and 50 background/resume cycles without an unexplained crash or ANR; recovery after a forced workspace failure; successful save/reopen/export; malformed input rejected while preserving the workspace. Repeat the core workflow on a second Android device. Check 4 KiB and 16 KiB page-size environments where available.

## 0.3: make touch editing useful

- Tap selection with an object/face/edge/point filter, multi-selection and a visible selected-object state.
- Move/rotate/scale handles with numerical entry; orthographic top/front/right views and an orientation cube.
- Endpoint, midpoint, centre and intersection snapping, alongside the existing grid snap.
- Object names, folders/layers, visibility, lock state and search.
- Redo and a readable operation history. Each command is a single transactional edit.
- Sketch actions for lines, arcs and circles; visible dimensions and incremental use of the existing constraint solver.
- Operation preview with explicit Apply/Cancel and useful messages for unsuitable inputs.

Gate: create two profiles, position them, loft them, inspect dimensions, Undo/Redo, save, reopen and export using phone controls. Verify that cancelling a preview leaves geometry and history intact.

A small public beta becomes reasonable after this workflow and the reliability gate pass, with production signing and project migration prepared.

## 0.4: jewellery that can be manufactured

Priority templates: plain/tapered rings, signet rings, solitaire settings, pendants and simple bracelet forms.

- Editable shank profiles, ring inner diameter, band width and wall thickness.
- Round, oval, rectangular and cushion setting families; bezel, prong and flush-setting construction where geometrically suitable.
- Separate stone reference geometry and seat/cutter geometry; editable seat depth, clearance and prong arrangement.
- Repeated stones along curves, with a preview of count, spacing and orientation.
- Text engraving/embossing with licensed font handling and robust outline conversion.
- Reusable templates and saved parameter presets.
- Volume and estimated mass using a user-selected material density; clearly identify these as estimates.
- Casting allowance stored as an explicit project parameter, with the original dimensions preserved.

Gate: a ring, signet and pendant reference model pass geometry validity, expected dimensions, save/reopen and STL export checks. Compare imported exported files in an independent desktop CAD/mesh tool. Print and measure a calibration piece before treating a template as ready for production. Mesh closure alone does not certify strength or castability.

## 0.5: deeper CAD and freeform editing

Introduce persistent feature recipes before expanding dependent editing. The current app stores many modelling results as geometry snapshots; a richer history must preserve input relationships and parameter changes.

- Model/feature tree with named inputs, parameters and dependency recomputation.
- Touch control-point handles for curves; surface pole editing and rational weights.
- Curve join/split/trim/extend, projection and planar region construction.
- Surface trim/untrim, more general patches and blends.
- Selected-edge fillet/chamfer instead of applying only to all edges.
- Selected-face shelling and clearer tolerance diagnostics.
- Curvature plots, surface normals and zebra-style continuity inspection.
- User-controlled approximation tolerance where conversion or fitting is involved.

Gate: resizing an upstream profile updates its extrusion and later operations. Missing or changed faces/edges produce an explicit unresolved reference rather than silently selecting a different face. Numerical fixtures check curve/surface behaviour, not only whether an operation returned a shape.

General SubD cage editing can follow stable point selection and history. Begin with vertex/edge/face manipulation and crease control. SubD-to-NURBS conversion is a separate research task with deviation checks.

## 0.6: richer parametric design

Expand the existing local graph rather than promising Grasshopper file compatibility.

- Curve division, point lists, transforms, surface evaluation, loft/sweep, Boolean and setting components.
- List mapping, ranges, filtering and reusable groups, followed by more complex list/tree behaviour if needed.
- Jewellery recipes: graduated stone arrays, twisted bands and adjustable lattice/pattern forms.
- Dependency-aware caching and debounced preview updates. Commit the exact result separately from a lightweight preview.
- Node-level errors that show the failing input and preserve the last successful geometry.
- Unified Undo/Redo for graph values, connections and generated geometry.
- Versioned recipe files, reusable presets and batch variant generation.

Gate: changing a slider regenerates the expected pattern without orphaned objects, stale results or history divergence. Cycles and type errors remain rejected. Graph save/reopen produces equivalent geometry.

## 0.7: fabrication and interoperability

- Scalable boundary/non-manifold checks, self-intersection diagnostics and thickness sampling.
- Local hole filling, normals repair and component inspection, with previews of changed areas.
- A separate experimental voxel-wrap/remeshing tool. Show the resolution, dimensional deviation and minimum-feature loss; retain the original.
- Print orientation and basic build-volume placement. Full slicing/support generation is a separate project.
- Exact sections with dimensions, annotations and basic sheet layouts; DXF import and better curve entities on export.
- 3MF for printing metadata and glTF/GLB for visual exchange, subject to implementation and round-trip tests.
- Investigate Rhino .3dm geometry interchange and translator licensing before committing to support.
- Retain STEP/IGES as precise CAD exchange paths; do not imply that polygon imports automatically become exact editable solids.

Gate: each format has fixtures for scale, coordinates, units where representable, topology, visibility and supported material data. Unsupported content is reported rather than silently discarded. Repair/remeshing must report geometric changes.

Volumetric wrapping and self-intersection repair are high-risk geometry work. They can remain experimental after other fabrication tools ship.

## 0.8: rendering and performance

- Validate GLES curves, triangles, context recreation and driver fallback on Android.
- Adaptive viewport detail based on measured frame time and memory, while exports retain source geometry.
- Wireframe/shaded modes, clipping planes and an interactive section view.
- Metallic/roughness materials, environment lighting and basic shadows.
- Higher-resolution image export with transparent-background options where supported.
- Preserve saved material settings and verify colour handling.
- Profile large scene traversal, geometry meshing and display caches.

Gate: gold, silver, stones and curved geometry display correctly in reference scenes. Performance targets are set after phone measurements. Ray tracing is a later optional renderer; evaluate quality, power, memory and licence constraints before integration.

## 1.0: release readiness

- Private production signing credentials, a documented update policy and a tested migration from the public development-key prototype.
- Independent product identity, dependency licence notices and repeatable build instructions.
- Device coverage for the supported minimum Android version, contemporary Android versions, more than one GPU vendor, memory-constrained devices and 16 KiB environments.
- No known project-loss bugs; a defined crash/ANR triage process.
- User documentation, sample projects, a short jewellery tutorial, release notes and known limits.
- Optional issue reporting with explicit user control over attached files.
- Offline modelling and local project access remain core requirements.

Before the first public binary, resolve the signing transition. Android updates rely on signing identity; switching from the prototype's published development key requires a supported migration strategy, not a promise of an ordinary in-place upgrade.

## Architectural work that supports every phase

Keep the JNI geometry operations transactional and separate them from UI code. Add a command/feature layer for parameters, dependencies and Undo/Redo. Keep curve, surface, solid and mesh classifications visible. Use versioned project schemas and migration fixtures. Run native work off the UI thread. Check input sizes before allocating large buffers. Keep performance and memory tests alongside geometry tests.

Every new tool should include: a meaningful reference fixture; incorrect-input rejection; failure rollback; Undo/Redo; save/reopen; supported export; and a real Android interaction check.

## First development batch

1. Capture and reproduce the reporting phone's startup failure.
2. Build the Android launch/recovery/save smoke-test matrix.
3. Fix any device failures before changing geometry limits.
4. Add Redo and orthographic views.
5. Add selection filters and transform handles.
6. Ship 0.2.1 only after the reliability gate passes; continue mobile editing as the next milestone.

## Longer-term research

General SubD-to-NURBS conversion, Class-A surface continuity, robust volumetric wrapping, DWG/USD translators, photorealistic ray tracing and third-party plugin compatibility require separate feasibility work. They are ambition areas, not features promised for 1.0. A full desktop FreeCAD framework, Python workbench environment or Rhino/Grasshopper compatibility is a different scope from the native mobile toolset.

## Evidence and technical references

Baseline: the delivered FreeCAD-Mobile-Lab-source.zip, version 4, especially docs/build-record.json, docs/VERIFICATION.md and docs/FREEFORM-TOOLS.md.

Android primary references:
- App signing and update identity: https://developer.android.com/studio/publish/app-signing
- Native 16 KiB compatibility and testing: https://developer.android.com/guide/practices/page-sizes

The roadmap priorities, proposed gates and milestone ordering are project planning decisions.


## Engineering progress — 11 October 2026

Current candidate: **1.0-rc2 / code 15**. Stable 1.0 is NOT COMPLETE. APK numbers identify saved engineering checkpoints; they do not establish that the milestone's phone/device gate passed.

| Checkpoint | Added scope | Remaining gate |
| --- | --- | --- |
| 0.2.1 | Command input, lifecycle callbacks/rollback, progress | Reporting-phone launch/crash and recovery workflows |
| 0.3 | Redo, views, properties, picking, move handles | Touch modelling, constraints and device history |
| 0.4 | Jewellery templates, presets, text, arrays, mass/casting copies | Independent dimensions and print/casting calibration |
| 0.5 | Persistent exact-CAD recipe DAG, selected topology guards, curves/UV/poles | Broad surfaces/blends and device editing |
| 0.6 | 40 typed graph kinds, bounded lists, live exact commit, recipes/variants | Reusable groups/cache/preview and device interaction |
| 0.7 | Restricted 3MF/GLB, DXF curves, print bed/thickness | Broader formats and fabrication/Android validation |
| 0.8 | Material previews, zebra/wireframe, clipping/transparent PNG | Phone GPU/context/memory budgets |
| 0.9 | Weighted XY draft editing/snaps, topology/multiple selection, planar hole caps | Device touch and print workflows |
| 1.0-rc1 | Numeric curve/revolve/material commands, offline guide, reference models/graphs, A4 overall-dimension sheets, project v2 metadata/migration, build provenance/signing guards | Stable Android/device and production-update gates |

The current guide/status files list exact boundaries. Arrays remain snapshots; sketch assists are not a general constraint UI; surface trims are rectangular UV intervals; hole repair is planar/bounded; sheets provide overall dimensions rather than arbitrary annotation; studio shading has no HDRI/UV texture/shadow system. The advanced research items remain research.

The recovered candidate uses saved verified 0.9 ARM64 native binaries, with rebuilt Java/assets and explicit native-source/library hashes. Native changes must use a full NDK rebuild. The original unsaved candidate was lost during workspace cleanup; current artifacts are reconstructed from the saved 0.9 source and documented implementation. Host checks are rerun where available; no lost log is presented as fresh evidence.

The next release task is Android crash/workflow validation, followed by the remaining source-only roadmap work and a tested production identity/project migration. Do not rename this candidate to stable 1.0 to hide open gates.

1.0-rc2/code15 additionally remaps a pending selected-curve export after project recovery, rejects invalid XML title characters and keeps scaled A4 dimension labels inside the sheet. Rebuilt host integration/regression, static APK and independent sample checks passed. Android runtime is NOT_RUN; stable1.0 remains NOT_COMPLETE.
