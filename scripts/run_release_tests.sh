#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAVA_HOME="${JAVA_HOME:?Set JAVA_HOME}"
JSON_JAR="${JSON_JAR:-${PROJECT_ROOT}/host-test-deps/json.jar}"
mkdir -p "${PROJECT_ROOT}/host-test-classes"
sources=(Worksheet LayerTools Expressions PrecisionTools NativeCad ArchiveIO FeatureModel ProjectStore ProjectSchema ReleaseInfo JewelleryCatalog ParametricGraph MeshFrame CameraMath RenderSettings StudioLighting SoftwareRasterizer RecipeFiles CommandLine SampleCatalog DrawingSheet)
files=()
for source in "${sources[@]}"; do files+=("${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/${source}.java"); done
"${JAVA_HOME}/bin/javac" --release 8 -classpath "${JSON_JAR}" -d "${PROJECT_ROOT}/host-test-classes" "${files[@]}" "${PROJECT_ROOT}/tests/ReleaseRegression.java"
LD_LIBRARY_PATH="${PROJECT_ROOT}/host-build:${PROJECT_ROOT}/../occt-host/lib" \
 "${JAVA_HOME}/bin/java" -Xcheck:jni -Djava.library.path="${PROJECT_ROOT}/host-build" -cp "${PROJECT_ROOT}/host-test-classes:${JSON_JAR}" org.freecad.mobilelab.ReleaseRegression "${PROJECT_ROOT}/release-fixtures-${RELEASE_VERSION:-candidate}"
