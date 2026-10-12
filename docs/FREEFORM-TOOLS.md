# Mobile Lab 0.2.0 modelling tools

This is an independent experimental CAD application. It does not run Rhino, Grasshopper, Rhino plugins, or the full desktop FreeCAD framework.

## Touch curves and exact modelling

Create > Curves / profiles > Draw XY sketch opens a millimetre canvas. Tap to add points, choose a snap increment, pinch to zoom, and pan with two fingers. Choose Polyline, Interpolated curve or NURBS curve. The drawing shows the control polygon; the finalized mathematical curve is shown in the workspace. Close a Polyline or Interpolated curve for solid extrusion. An open weighted NURBS curve uses a clamped degree of up to three and supports control-point/weight editing from Edit. The numerical editor accepts X Y Z and optional weight per line. NURBS follows its control polygon rather than passing through every pole.

Circle, Ellipse and Rectangle are exact planar profiles. Helix is a bounded B-spline approximation through sampled helical points. Move/Rotate can position profiles in 3D. NURBS patch is a quadratic tensor-product NURBS surface with a 3 × 3 control cage and adjustable central pole; it is not an interactive surface sculptor.

Tools > Extrude converts a closed planar profile to a solid or sweeps the wire into an open surface. Revolve uses a user-defined point, direction and angle. Keep the profile clear of the axis for a valid solid. Loft selects 2–8 profiles in creation order and supports smooth or ruled interpolation. Use Move to separate them in space. Sweep uses the selected profile and a second rail; position the profile at the rail start and perpendicular to its tangent. Pipe along curve builds its circular profile at that start automatically.

Offsets, chamfer, shape healing, surface sewing, closed-shell solidification and hollowing use real OpenCASCADE operations. Hollow top removes the highest horizontal planar face and offsets inward, so it requires a suitable solid. Inputs are retained and normally hidden after a successful tool operation. Failed operations roll back the whole change. Tools have mobile limits and can reject unsuitable geometry.

## Jewellery and organic forms

Create > Jewellery settings provides round bezel and connected prong-gallery solids. Dimensions include the stone diameter, wall/gallery thickness, setting height, seat depth and prong count/diameter. Gemstone cutter is a conical pavilion plus cylindrical clearance tool for Boolean subtraction; it does not reproduce a particular gemstone cut.

Transform > Casting shrinkage allowance applies `1 / (1 - shrinkagePercent / 100)` uniformly about the object centre. It is optional; use your foundry's measured allowance. The app does not certify wall strength, stone fit, castability or final print dimensions.

Subdivision form applies actual Catmull–Clark subdivision to a closed six-face cage, with 1–4 levels, top-cage scaling and twist. It produces a mesh, not a NURBS solid. There is no arbitrary cage vertex sculpting, crease editor or exact SubD-to-NURBS conversion.

Linear and polar arrays produce one compound result and retain the source as a hidden object. The copy count includes the original. A 360-degree polar array closes without a duplicate endpoint. Mirror creates an independent result across a specified plane.

## Local parametric graph

Create > Parametric node graph shows connected components on a touch canvas. Tap a node, then Edit / connect. Number nodes have sliders. Components are Number, Add, Multiply, Circle, Rectangle, Box, Ring, Extrude, Move, Loft, Linear array and Polar array. Geometry and numeric ports are typed; missing connections, type mismatches and cycles are rejected. Choose geometry outputs explicitly and press Evaluate to regenerate them. Updates happen on Evaluate, not continuously during slider dragging.

Graphs and the IDs of their generated objects are saved in `.fcml` projects and remapped on reopening. Graph outputs are geometry snapshots until the next evaluation. Existing standalone geometry cannot be used as a graph input. This graph format is independent of Grasshopper; `.gh`/`.ghx` files and plugins are not supported. Undo restores native geometry; graph editor values retain the latest recipe.

## Fabrication, drawing and files

Fabrication report shows volume, area, edge/curve length, CAD validity, solid count and tessellation statistics. Mesh topology is checked up to 100,000 triangles using coordinate welding at 0.00001 mm. It reports boundary/non-manifold edges and degenerate triangles. This check does not detect self-intersections, thin walls or overlapping closed components. Larger meshes skip the topology map to keep memory bounded. Draft reports the tessellated area whose normals are too close to horizontal for the selected +Z pull-angle threshold; it does not detect every undercut or guarantee mould release.

Repair mesh removes degenerate/duplicate triangles, welds vertices by rounded coordinate buckets and fixes winding on orientable manifold components. Closed components are oriented outward. It is limited to 100,000 input triangles. It rejects non-manifold edges and does not fill holes or implement volumetric ShrinkWrap.

Section intersects a CAD object with a plane. Flatten to XY stores the resulting exact section in plane coordinates at Z=0. Export SVG or DXF from that selected curve/section. Both exports sample the curves into line segments; they are not native NURBS vector exports. SVG uses physical millimetre dimensions; DXF declares millimetres. Profiles must lie in XY at Z=0. Minimum distance measures two CAD objects; intersecting/touching solids report zero.

Files: STEP, IGES and BREP preserve CAD geometry; STL and OBJ preserve mesh geometry; `.fcml` stores the workspace. OBJ supports planar convex/concave polygon faces through triangulation, negative indices and standard vertex references. It ignores material/UV/group records and rejects non-planar polygon faces. DWG, DXF import, USD, glTF and Rhino `.3dm` are not implemented.

STL/OBJ export quality is adjustable from 0.005 to 0.5 mm linear tessellation tolerance. Original mesh inputs retain their detail; changing tolerance applies to CAD tessellation. CAD exports require hiding mesh-only objects. PNG exports a shaded 1024 × 1024 isometric software view using object colours. Gold/silver/rose-gold are colour presets, not PBR materials. There is no ray tracing, UV editing, HDR environment lighting or rendering-plugin support.

## Further development

The remaining Rhino-scale work includes surface pole/trim editing and continuity tools, general SubD cage editing/conversion, a richer graph runtime, volumetric remeshing/hole filling, drawing dimensions and layouts, additional licensed/file-format translators, PBR/rendering, and extensive Android device validation. Each needs its own implementation and tests. There are no unlimited-complexity or unlimited-size promises in this mobile build.
