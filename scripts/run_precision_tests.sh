#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAVA_HOME="${JAVA_HOME:?Set JAVA_HOME}"
JSON_JAR="${JSON_JAR:-${PROJECT_ROOT}/host-test-deps/json.jar}"
sources=(Worksheet LayerTools NativeCad ArchiveIO FeatureModel ProjectStore ProjectSchema ReleaseInfo JewelleryCatalog ParametricGraph MeshFrame CameraMath RenderSettings StudioLighting SoftwareRasterizer RecipeFiles CommandLine SampleCatalog DrawingSheet Expressions PrecisionTools ViewCubeMath)
files=();for source in "${sources[@]}";do files+=("${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/${source}.java");done
mkdir -p "${PROJECT_ROOT}/host-test-classes"
"${JAVA_HOME}/bin/javac" --release 8 -cp "${JSON_JAR}" -d "${PROJECT_ROOT}/host-test-classes" "${files[@]}" "${PROJECT_ROOT}/tests/PrecisionMathRegression.java" "${PROJECT_ROOT}/tests/PrecisionCadRegression.java"
"${JAVA_HOME}/bin/java" -cp "${PROJECT_ROOT}/host-test-classes:${JSON_JAR}" org.freecad.mobilelab.PrecisionMathRegression
if [[ "${1:-}" != "--math-only" ]];then
 LD_LIBRARY_PATH="${PROJECT_ROOT}/host-build:${PROJECT_ROOT}/../occt-host/lib" "${JAVA_HOME}/bin/java" -Xcheck:jni -Djava.library.path="${PROJECT_ROOT}/host-build" -cp "${PROJECT_ROOT}/host-test-classes:${JSON_JAR}" org.freecad.mobilelab.PrecisionCadRegression
fi
