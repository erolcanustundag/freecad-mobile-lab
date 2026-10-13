# Native Sketcher checkpoint

1.2-rc2 / code25 is in preparation. Original FreeCAD1.1.4 Sketcher App and PlaneGCS compile alongside genuine Part/Materials. BUILD_GUI stays off; the headless integration scopes the GUI-only SWIG/Pivy configuration check accordingly. No geometry or solver implementation is stubbed.

Four bounded feature scopes: native entities/solver-aware point movement/deletion; rational B-splines and construction geometry; native constraints/dimensions/DOF with failed-edit rollback; supported Sketcher FCStd persistence and a sampled XY preview. Commands, numeric forms and English/Turkish/German guides are included.

Host JNI validation and ARM64 APK verification are pending for this checkpoint. It must not be described as shipped or device-tested until the corresponding evidence is saved.

B05/B06/B07 remain PENDING at their full roadmap scope. Face/plane attachment UI, external-reference editing, general sketch trim/fillet/array tools, spline pole handles, touch constraint editing and the desktop GUI remain pending. Native module availability is a prerequisite, not full workbench parity. PartDesign is next after the missing sketch workflows.
