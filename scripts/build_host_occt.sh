#!/usr/bin/env bash
# Optional Linux OCCT build for the JNI regression suite; does not enter the APK.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OCCT_SOURCE="${OCCT_SOURCE:-${PROJECT_ROOT}/../occt-source}"
OCCT_HOST_ROOT="${OCCT_HOST_ROOT:-${PROJECT_ROOT}/../occt-host}"
BUILD_DIR="${PROJECT_ROOT}/../occt-host-build"
cmake -S "${OCCT_SOURCE}" -B "${BUILD_DIR}" -G Ninja \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.10 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG" -DCMAKE_INSTALL_PREFIX="${OCCT_HOST_ROOT}" \
  -DINSTALL_DIR_LIB=lib -DINSTALL_DIR_INCLUDE=include/opencascade \
  -DBUILD_LIBRARY_TYPE=Shared -DBUILD_SOVERSION_NUMBERS=0 \
  -DBUILD_MODULE_FoundationClasses=OFF -DBUILD_MODULE_ModelingData=OFF \
  -DBUILD_MODULE_ModelingAlgorithms=OFF -DBUILD_MODULE_Visualization=OFF \
  -DBUILD_MODULE_ApplicationFramework=OFF -DBUILD_MODULE_DataExchange=OFF \
  -DBUILD_MODULE_DETools=OFF -DBUILD_MODULE_Draw=OFF \
  "-DBUILD_ADDITIONAL_TOOLKITS=TKPrim TKBO TKBool TKFillet TKOffset TKMesh TKDESTEP TKDESTL TKDEIGES" \
  -DUSE_FREETYPE=OFF -DUSE_OPENGL=OFF -DUSE_GLES2=OFF -DUSE_XLIB=OFF \
  -DUSE_TBB=OFF -DUSE_RAPIDJSON=OFF -DBUILD_DOC_Overview=OFF
cmake --build "${BUILD_DIR}" --parallel "${BUILD_JOBS:-4}"
cmake --install "${BUILD_DIR}"
