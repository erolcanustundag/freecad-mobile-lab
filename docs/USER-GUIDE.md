# FreeCAD Mobile Lab 1.0 candidate guide

## Start

GETTING STARTED
All model dimensions are millimetres. The app uses the native OCCT 7.9.2 CAD kernel and the FreeCAD PlaneGCS solver.

Type commands in the bar above the tools, then press Run or the keyboard action. Empty input repeats the last command. Help opens the command list, Help Box shows one command. Case, commas and the leading underscore are accepted.

Try Box 20 10 4, Rename "My box", Move 0 0 0, Fit. Select by tapping geometry or an object chip. Object IDs appear on chips; Select 3 selects ID 3. Undo and Redo recover completed operations during this session.

One finger orbits, pinch zooms, two fingers pan. Top, Front, Right and Isometric choose standard views. Objects searches names/layers/IDs; Selection sets object or topology filters. The primary selected object is highlighted. Multiple-selection controls affect the chosen set.

Save exports a .fcml project. Autosave is private to the app; export a backup before uninstalling. Open imports supported files. Export opens the format chooser.

Guide, Samples and Drawing are available from the command bar; Guide and Samples also appear in the Workspace menu.

## Jewellery

JEWELLERY TUTORIAL
Try ComfortRing 18 1.6 3 0.4. This creates an 18 mm inner diameter ring with a 1.6 mm wall and 3 mm band. Edit changes template dimensions. Rename "My comfort ring", Color 0.83 0.64 0.25, Material 0.25 0.85, Studio.

Templates includes oval, rectangular and cushion bezels, oval prongs, comfort and signet rings, pendant frames and bangles. Dimensions are explicit; inspect the result with Info and Analyze before export. Samples inserts editable examples, including a signet seat and a plate with feature history.

Text creates a solid from a system font outline. Position the text and use Cut to engrave or Union to emboss. Font availability and outline complexity vary by phone.

Mass estimates weight from solid volume and the density you enter; it excludes stones, solder and process losses. Allowance makes a compensated copy and preserves the original. Calibrate casting percentage with your alloy and casting process.

PrintPrep checks a bed envelope and places/orients the model. Thickness is a bounded sample report, not proof of minimum wall thickness everywhere. Export STL, STEP or other supported formats after checking geometry. Physical print/casting calibration remains a release gate.

## Curves

CURVES AND FEATURE HISTORY
Line 0 0 0 10 0 0 creates an exact straight line. Arc 0 0 0 5 0 90 creates a quarter circle in XY. Polyline accepts XYZ triples, NURBSCurve accepts XYZW control poles and InterpCurve accepts XYZ through-points. Each command accepts 2 to 16 points/poles. Positive rational weights affect the curve shape.

Example: NURBSCurve 0 0 0 1 5 8 0 2 10 0 0 1. Sketch opens touch XY drafting, weighted pole editing, local draft Undo and snapping. Snaps/intersections refer to draft points and straight control segments; this is not a general sketch constraint editor.

Rectangle 20 12 then Extrude 3 creates an exact pad. Revolve uses an axis point, direction and angle. Loft joins 2 to 8 profiles; Sweep uses profile/rail IDs. FeatureHistory displays saved CAD operation recipes. Editing a hidden root regenerates its dependants, or rolls back and reports the failure. Detach converts a recipe output to a snapshot.

Join, TrimCurve, ExtendLine, ProjectCurve, Region and selected-index Fillet/Chamfer/Shell extend exact CAD editing. Selected topology is guarded against changed edge/face numbering. TrimPatch supports rectangular UV intervals. SurfacePoints edits NURBS patch poles. General surface-loop trims, blends and touch surface handles remain pending.

Native arrays and curve-array copies are snapshots rather than a persistent associative pattern feature. Limited subdivision forms do not provide a general SubD editor or exact SubD-to-NURBS conversion.

## Graph

PARAMETRIC GRAPHS
Graph opens the local visual component editor. Components have typed ports for numbers, lists, points and CAD geometry. Connect inputs, choose geometry outputs, then Evaluate. There are 40 component kinds and a limit of 80 nodes.

Samples includes a ring graph and a bezel pattern. Change a Number node to regenerate the pattern. Graph samples replace prior graph-owned outputs while preserving other workspace objects, subject to dependency guards.

Live Apply is optional and debounced by 450 ms; it commits exact CAD results and can be expensive. Evaluation memoizes nodes only within one evaluation. Group labels organise components; they are not reusable subgraphs.

GraphFiles saves/opens versioned .cadgraph recipes. Batch variants exports 2 to 10 single-output STL/recipe variants while preserving the live scene and Redo state. Lists and point series are bounded. No Grasshopper plug-ins or arbitrary code execution are provided.

## Printing

PRINTING AND FILES
STL/OBJ imports are bounded to 2,000,000 triangles; STL input up to 256 MiB. Viewport detail is separately bounded, so display reduction preserves full imported geometry for save/export. The old 200,000-triangle rejection is removed. Malformed or larger files still report a limit or format error.

Formats: STEP, IGES and BREP exact geometry; STL/OBJ meshes; .fcml projects; restricted .FCStd saved Part geometry; sampled SVG/DXF curve output. DXF import accepts exact ASCII lines, arcs, circles and straight lightweight polylines with explicit supported units.

3MF import supports up to 500,000 triangles in one untransformed object/build. GLB supports up to 2,000,000 triangles in one baked mesh/scene primitive; coordinate conversion uses metres and Y-up. Unsupported assemblies/transforms/extensions are rejected. .3dm, DWG, USD and full desktop FreeCAD document execution are not implemented.

FillHoles creates a separate repaired mesh copy for simple planar boundary loops, up to 100,000 triangles, 512 boundary edges and 128 vertices per loop. Branched/non-manifold, inconsistent, non-planar or self-crossing boundary loops are rejected. Global mesh self-intersection checking and volumetric shrink-wrap remain pending.

Drawing exports an A4 SVG for a selected XY curve or Section result at Z=0. It adds overall width/height dimensions, title and notes. Dimensions use CAD bounds; contours target 0.005 mm sampling, capped at 1,000 points per edge and 40,000 points total. Larger profiles scale down. Print at 100%, disable page fit. This is not a general dimension editor or multi-view sheet system.

PNG exports 512 to 2048 pixels with optional transparency. Studio shading previews roughness/metallic; zebra shows normal stripes. Clipping hides pixels above a world-Z plane without a section cap. Environment maps, UV texture materials and shadows remain pending.

## Recovery

RECOVERY AND PROJECT VERSIONS
The recovery launcher runs separately from the native CAD process, and software rendering is the default. If CAD fails, reopen the recovery screen and export the crash report and recovery copy. Device-level instant-crash cause remains unverified without a captured phone report.

Project version 2 records writer version, minimum reader and OCCT kernel metadata. Version 1 files are migrated in memory on open; the chosen source file is not rewritten. On startup, a legacy version 1 autosave is backed up before autosave is upgraded. Workspace > Export recovery copy retrieves it. Version 2 projects cannot be opened by the old 0.9 APK.

A corrupt autosave is preserved as a recovery copy. Starting empty preserves the previous autosave too. Opening a project or failing an operation uses engine transactions and rolls back CAD/recipe state. Export backups regularly; uninstalling removes app-private storage.

Retained development signing permits prototype updates with the same signing identity. Production signing uses a separate private key; a different certificate does not provide a normal in-place prototype upgrade. Production migration and device tests remain pending.

A pending selected-curve export is remapped to the restored project object after Activity recreation. If the selected object is missing after recovery, export reports an error and asks you to select again. Actual Android picker/process-recreation verification is still pending.

## Status

1.0 RELEASE CANDIDATE STATUS
Version 1.0-rc2 is an engineering candidate, not a completed stable 1.0 release. It is signed with the retained public development key and supports ARM64 Android API 26–35.

Implemented: native exact CAD/feature history, bounded meshes, jewellery templates, command bar, typed graph tools, software/GLES preview modes, project persistence, recovery launcher, sample models, offline help and A4 overall-dimension sheets.

Open gates: reported phone crash reproduction/fix verification, physical startup/lifecycle/file-picker tests, supported-device/GPU/memory matrix, project-upgrade checks on Android, private production signing/update migration, independent dimensional checks and physical print/casting calibration. Remaining roadmap tools are listed in the source documentation.

Host tests and static APK signature/alignment checks are evidence for their tested scope; they do not prove Android phone reliability. No full Rhino, Grasshopper or desktop FreeCAD parity is claimed. Public publication has not happened.

