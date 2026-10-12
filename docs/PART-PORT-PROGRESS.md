# Original Part port prerequisite

Product1.1 is published and contains the language/recovery update only. Original Part is not staged into that APK.

The original sketch roadmap requires native Part first. An isolated source build now adds genuine OCCT7.9.2 TKFeat, TKExpress, TKBin, TKBinL, TKMeshVS, TKRWMesh and TKDEGLTF against the retained ARM64 toolkit binaries. All seven pass ARM64,16KiB ELF and loader-name closure checks. The build uses real upstream sources, including the C expression-parser sources; no geometry functions are substituted. Optional RapidJSON is disabled, so this does not establish native GLTF import/export.

The original FreeCAD1.1.4 Part target also depends on Materials. build_freecad_android_core.py --part enables both with GUI/other workbenches disabled and an explicit complete OCCT header/library prefix. The default core-only build path remains separate. HostCPython3.13 code generation is restored. Original source/toolchain hashes and dependencies remain frozen.

Pending: complete Part/Materials compilation; strong-symbol/load checks; builtin Python registration; real geometry/document round-trip fixtures; bounded renderer integration and Android execution. B05 and subsequent workbenches remainPENDING. Do not claim native Part capability from successful prerequisite libraries alone.
