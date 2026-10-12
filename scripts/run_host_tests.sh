#!/usr/bin/env bash
# Runs the same CAD JNI implementation with a matching host OCCT 7.9.2 build.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OCCT_HOST_ROOT="${OCCT_HOST_ROOT:-${PROJECT_ROOT}/../occt-host}"
JAVA_HOME="${JAVA_HOME:?Set JAVA_HOME to JDK 17}"
JSON_JAR="${JSON_JAR:?Set JSON_JAR to org.json:json:20240303 for host-only tests}"
cmake -S "${PROJECT_ROOT}/app/src/main/cpp" -B "${PROJECT_ROOT}/host-build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DOCCT_HOST_ROOT="${OCCT_HOST_ROOT}"
cmake --build "${PROJECT_ROOT}/host-build" --parallel "${BUILD_JOBS:-2}"
mkdir -p "${PROJECT_ROOT}/host-test-classes"
"${JAVA_HOME}/bin/javac" --release 8 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/Worksheet.java" "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/LayerTools.java" "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/Expressions.java" "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/PrecisionTools.java" -classpath "${JSON_JAR}" -d "${PROJECT_ROOT}/host-test-classes" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/NativeCad.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ArchiveIO.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/FeatureModel.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ProjectStore.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ProjectSchema.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ReleaseInfo.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/JewelleryCatalog.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ParametricGraph.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/FcstdImporter.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/MeshFrame.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/RenderSettings.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/StudioLighting.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/SoftwareRasterizer.java" \
    "${PROJECT_ROOT}/tests/LargeModelRegression.java" \
    "${PROJECT_ROOT}/tests/HostRegression.java" \
    "${PROJECT_ROOT}/tests/FreeformRegression.java"
LD_LIBRARY_PATH="${PROJECT_ROOT}/host-build:${OCCT_HOST_ROOT}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}" \
    "${JAVA_HOME}/bin/java" -Xcheck:jni -Djava.library.path="${PROJECT_ROOT}/host-build" \
    -Dfreecad.evidence.directory="${PROJECT_ROOT}/docs" \
    -cp "${PROJECT_ROOT}/host-test-classes:${JSON_JAR}" org.freecad.mobilelab.HostRegression

LD_LIBRARY_PATH="${PROJECT_ROOT}/host-build:${OCCT_HOST_ROOT}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}" \
    "${JAVA_HOME}/bin/java" -Xcheck:jni -Djava.library.path="${PROJECT_ROOT}/host-build" \
    -cp "${PROJECT_ROOT}/host-test-classes:${JSON_JAR}" org.freecad.mobilelab.FreeformRegression
