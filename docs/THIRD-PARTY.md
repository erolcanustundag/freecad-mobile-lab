# Third-party components and rebuilding

This independent Android candidate contains original mobile application code and upstream components. Component licences remain applicable to those components. The app bundles complete licence texts under `assets/licenses` and `assets/core/licenses`. This inventory describes the candidate, not all future desktop FreeCAD modules.

| Component | Version/source lock | Licence/notices | Corresponding source and modifications |
| --- | --- | --- | --- |
| Mobile Java/C++ application | release.json / apk-inputs.json | LGPL-2.1-or-later | app/, scripts/, tests/; LICENSE |
| OCCT kernel/exchange | 7.9.2, versions.lock | LGPL-2.1 with OCCT exception | occt-source in the corresponding-source archive; build_occt.sh/build_iges_addon.py |
| Extracted FreeCAD PlaneGCS | versions.lock commit | LGPL-2.1-or-later | vendor/freecad/planegcs and mobile bridge; extracted compatibility headers |
| Upstream FreeCAD Base/App | 1.1.4 archive SHA256 in FREECAD-ANDROID-TOOLCHAINS.json | LGPL-2.1-or-later and embedded upstream component notices | frozen FreeCAD archive, vendor/freecad-core-patches, build_freecad_android_core.py |
| Qt headless Core/XML/Network/Concurrent and Android Java support | 6.8.3 | LGPL-3.0/GPL-3.0 texts; upstream third-party notices | frozen qtbase source archive; build_qt_android_core.py and Qt Java bootstrap adapter |
| CPython runtime/standard library/extensions | 3.13.16 | PSF licence and embedded historic/upstream notices | frozen CPython archive, standalone-NDK patch and build_cpython_android.py |
| Boost | 1.87.0 | Boost Software Licence1.0 | source archive, vendor/boost and build_boost_android.py |
| Eigen headers | 3.4.0 | MPL-2.0, individual source notices | vendor/eigen; GPL-only modules are not application build inputs |
| meshoptimizer | versions.lock 1.0 commit | MIT | vendor/meshoptimizer |
| ICU / Xerces | 74.2 /3.2.5 | Unicode/ICU notices / Apache-2.0 | frozen source archives; ICU loader normalization and CMake build scripts |
| fmt / yaml-cpp / pybind11 headers | 11.1.4 /0.8.0 /2.13.6 | respective MIT-style notices | frozen source archives and build_cmake_android_dependencies.py |
| Python bzip2 / libffi / OpenSSL / SQLite / liblzma dependencies | 1.0.8 /3.4.4 /3.5.9 /3.53.4 /5.4.6 | respective BSD-style / MIT / Apache-2.0 / public-domain / upstream XZ notices | PYTHON-DEPENDENCY-SOURCES.json pins exact source versions and frozen BeeWare Android recipes/patches; binary locks are in FREECAD-ANDROID-TOOLCHAINS.json |
| Android shared C++ runtime | retained NDK runtime input hash in versions-prebuilt.json | Apache-2.0 with LLVM exceptions and historic C++ runtime notices | standard Android NDK toolchain runtime, corresponding LLVM licence texts bundled; native scripts use pinned NDK27c |
| Android system libraries | OS-provided | Android system components | These libraries are resolved from the OS and are not copied into the APK. |

Qt's bundled third-party notice directory includes notices for its full qtbase source tree, including components disabled in this headless build. CPython dependency sources/recipes were retrieved and locked in RC7; their native binaries were not rebuilt in this checkpoint. Exact APK/runtime file digests, rather than archive names alone, identify the distributed inputs.

The corresponding-source release archive contains the pinned upstream source archives, dependency recipes and OCCT rebuild sources. The mobile source repository/archive contains all application/bridge sources, solver/header sources, patches and build scripts. Toolchain URLs and checksums are frozen in the dependency manifests; SDK/JDK/NDK build tools are not copied into the release source archive.

For native rebuilding, extract the corresponding-source archives alongside `native-cad`, fetch/verify the pinned source archives as needed, then follow FREECAD-CORE-PORT.md. Patches are applied by the build scripts. Source fetching can overwrite patched trees; do not fetch while building. For the custom CAD kernel, use build_occt.sh, build_iges_addon.py and app/src/main/cpp/CMakeLists.txt. For the App lab, build Qt/CPython/Boost/ICU/Xerces/FreeCAD, build the JNI bridge, run prepare_core_apk.py, and package with build_apk.py --prebuilt --upstream-core.

The distributed shared libraries can be replaced by rebuilt compatible versions. Modified native/Python/JAR files require updating the development input lock before packaging; this protects sealed releases and is not a prohibition on modification. Select a new development release, regenerate the appropriate runtime/prebuilt input manifests, and sign your build with your own certificate. No private production key or matching-signature requirement restricts local builds. Android will require exporting projects/uninstalling the original when certificates differ; see SIGNING.md.

The app requests no network permission. Local Android SAF files and documents stay on the device; crash reports are exported only through the user's file picker. No FreeCAD/Rhino affiliation or trademark permission is claimed.
