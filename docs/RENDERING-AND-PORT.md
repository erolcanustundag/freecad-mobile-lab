# Rendering alternatives and remaining desktop port

| Approach | Evidence and tradeoff | Result here |
| --- | --- | --- |
| Keep Coin3D and adapt desktop OpenGL | Upstream Coin has an open GLES support issue. FreeCAD's CMake currently requires GLU, and its entry point is a desktop executable. | Inspected; not a direct Android build. |
| Coin3D through GL4ES | GL4ES supports Android and translates legacy OpenGL into GLES. Its own README documents limitations in selection, feedback, and framebuffer behaviour. Coin's context integration, GLU, and picking still need verification. | Considered as a future compatibility route; not built or validated in this APK. |
| OpenCASCADE's native GLES/AIS viewer | OCCT supports Android and offers a `USE_GLES2` / TKOpenGles driver. It can retain CAD-aware selection but needs viewer lifecycle, EGL, font resources, and touch integration. | Confirmed in source/docs; modelling kernel built without the viewer. |
| Qt Quick 3D | Qt offers a mobile-compatible scene renderer and custom geometry. It adds Qt/QML deployment and has GPLv3/commercial licensing for this module. It does not automatically provide FreeCAD workbenches. | Considered; not included. |
| Android OpenGL ES directly | Render OpenCASCADE tessellation in a GLSurfaceView. Fewer dependencies and a direct Android lifecycle; CAD-aware face/edge picking would need new work. | Implemented and packaged. |
| Java software rasterizer | Perspective projection, a depth buffer, and interpolated lighting of the actual native CAD mesh; no EGL/GL startup dependency. CPU rendering is slower for large meshes. | Default in 0.1.2; bounded 640-pixel viewport, gestures and shared native geometry. |

The chosen implementation keeps BREP modelling in native C++, uses the real
FreeCAD PlaneGCS constraint solver, and feeds face meshes/normals to the software
renderer or optional GLES renderer. The
geometry operations, tessellation, and file exports are computed locally; the
scene is not a decorative mockup.

Version 0.1.3 adds meshoptimizer 1.0 to cache bounded display meshes, while
retaining the original native STL triangulation for geometry transforms,
project saving and export. This decouples viewport cost from STL detail.
The simplifier is linked statically under MIT and adds no graphics/runtime
dependency. Its source is pinned in `versions.lock`.

The launcher and CAD Activity now use separate Android processes. Recovery
does not load the CAD native libraries or create a GLES surface. It records
startup progress and can export available Android exit history/native traces.
This is a recovery mechanism, not evidence that the unidentified physical-phone
crash has been fixed.

## What is still needed for the full desktop application

The full FreeCAD Base/App framework must still be cross-compiled, with Android
Qt Core, CPython, Boost and remaining dependencies. Python extension loading and
resources need Android packaging. The document framework and Part/Sketcher
bindings then need to connect to a mobile UI. A new renderer does not remove
these dependencies or automatically port workbench commands.

Full FCStd feature-history loading/recomputation depends on that framework and
on the relevant Python workbenches. This prototype can import stored Part BREP
geometry from FCStd archives, but does not recreate the original parametric tree.

## Primary sources

- FreeCAD source, checked out and inspected:
  https://github.com/FreeCAD/FreeCAD
- Coin GLES issue: https://github.com/coin3d/coin/issues/449
- GL4ES capabilities/limits: https://github.com/ptitSeb/gl4es
- OCCT Android/GLES build options:
  https://occt3d.com/dev/doc/overview/html/build_upgrade__building_occt.html
- Qt Android: https://doc.qt.io/qt-6/android.html
- Qt Quick 3D: https://doc.qt.io/qt-6/qtquick3d-index.html
- CPython Android embedding: https://docs.python.org/3/using/android.html
