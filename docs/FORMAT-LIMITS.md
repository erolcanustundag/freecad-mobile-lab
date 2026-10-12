# Geometry interchange checkpoint

STL retains the original import up to 2,000,000 triangles / 256 MiB. Preview detail is independent.

3MF export writes one welded triangle mesh, millimetre units and OPC content-type/start-part relationships. It is bounded to 500,000 triangles because vertex welding requires an additional map. Import supports one model part, one mesh object and one untransformed build item; components and required extensions are rejected. Explicit units are converted to mm. XML is streamed with a 128 MiB limit; DTD/entity declarations and non-UTF-8 data are rejected. Geometry import does not preserve materials or print-process settings. Independent trimesh tests verify a cube's dimensions, volume and shared topology.

GLB export writes a static triangle mesh, float positions/normals, metre units and a right-handed Y-up frame: CAD (x,y,z) becomes (x,z,-y)/1000. Vertices are a triangle soup; coincident vertices can be welded by a downstream tool. Import supports one baked static mesh/primitive/scene, dense float VEC3 positions and optional unsigned integer triangle indices. Node transforms, required extensions, skinning and morphs are rejected. Colours/textures/animations are not imported. Both paths are bounded to 2,000,000 triangles and import containers to 256 MiB. Independent reader tests verify dimensions, oriented volume and coordinate-welded topology.

ASCII DXF import supports modelspace LINE, CIRCLE, ARC and straight LWPOLYLINE entities, at most 2,000 curve segments / 16 MiB. $INSUNITS must declare inch, foot, mm, cm or metre units. Bulged polylines, block inserts, arbitrary extrusion directions and unsupported entities fail with an explanation. Curves retain exact line/circle/arc geometry. The current DXF exporter samples general CAD curves into LINE segments and includes mm units.

Print placement uses the world bounding box to centre a selected object on Z=0. Envelope checks list fitting axis permutations. CAD thickness uses at most 128 tessellation-distributed samples projected back to exact surfaces; inward rays find the next boundary. It is an approximate sampled report, not a global minimum-wall certificate. Existing mesh welding/winding repair remains limited to 100,000 triangles. Planar hole filling creates a separate mesh copy with a report of the number of capped loops. Limits: 100,000 input triangles, 512 boundary edges and 128 vertices per loop; only planar unbranched consistently wound loops are accepted. Self-crossing boundary loops are rejected. Global mesh self-intersection detection, nonplanar hole repair, volumetric wrap and general dimension editing remain pending. The Drawing command exports an A4 SVG with title, notes and overall width/height dimensions from CAD bounds; selected profiles must lie in XY at Z=0. Contours are sampled at 0.005 mm. Larger drawings scale down; print at 100% with page fit disabled.

## .3dm investigation

McNeel's openNURBS can serialize .3dm geometry, but its public toolkit omits important modelling operations, surface meshing and SubD-to-BRep conversion. A future translator must preserve knot vectors, rational weights, trimming loops, units, layers and instance transforms and reject unsupported object families. Start with curve/mesh fixtures, then NURBS patches and trimmed BReps, comparing results on desktop. No .3dm support is claimed in this APK.

Primary references consulted 2026-10-10:
- https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md
- https://developer.rhino3d.com/guides/opennurbs/what-is-opennurbs/
- https://developer.rhino3d.com/guides/opennurbs/reading-subdivision-surfaces/
