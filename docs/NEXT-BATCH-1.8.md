# Next native batch1.8/code34

Resume only after1.7 publication records are verified and app inputs remain sealed.
Select a new version before modifying app inputs. Keep all earlier APKs unchanged.

1. Native planar section helper: confirm Part::Plane fields in frozen1.1.4/runtime;
   create a bounded parametric face centered at the requested world origin with
   normalized nonzero normal and finite size. Link Part::Section to the chosen
   source and plane. Test analytic box/cylinder cross-sections, plane translation,
   empty/cyclic/deleting-source rollback and FCStd. Do not claim all section modes.
2. World wire preview: discretize actual native section/shape edges with explicit
   curve/sample/point budgets. Render world XYZ through an orthographic camera;
   orbit/zoom/pan need Android validation. Preserve stored native curves; preview
   sampling is display only. Host-check coordinate projection and data limits.
3. Current face/edge inspection: numbered native sub-elements, exact edge length,
   bounds/endpoints or face area/surface type. Distinguish face area centroid from
   a point evaluated on the surface; report normal at that evaluated point.
   Test known analytic primitives and outward orientation, not generic assumptions.
4. Finishing selection/radius edits: reuse native Part::Fillet/Chamfer Base link
   and Edges tuples;1–32 unique current1-based edges. Atomic native recompute,
   rollback/Undo/Redo/FCStd and parent topology failures must be tested. Names are
   current selections, not a guarantee of full desktop topology-reference parity.

Full B05/B06/B07/Part/PartDesign/device parity stays pending. Source Git is
canonical; save signed APK plus private continuation after the four verified scopes.
Use full GitHub release channel unless the user changes that preference. Never put
private keys or private continuation in public source/assets/Actions.
