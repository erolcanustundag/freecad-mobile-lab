#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JAVA_HOME="${JAVA_HOME:?Set JAVA_HOME}"
JSON_JAR="${PROJECT_ROOT}/host-test-deps/json.jar"
mkdir -p "${PROJECT_ROOT}/host-test-classes"
"${JAVA_HOME}/bin/javac" --release 8 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/Worksheet.java" "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/LayerTools.java" "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/Expressions.java" "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/PrecisionTools.java" -classpath "${JSON_JAR}" -d "${PROJECT_ROOT}/host-test-classes" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/NativeCad.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ArchiveIO.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/FeatureModel.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ProjectStore.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ProjectSchema.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ReleaseInfo.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/ParametricGraph.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/JewelleryCatalog.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/MeshFrame.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/CameraMath.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/RenderSettings.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/StudioLighting.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/SoftwareRasterizer.java" \
 "${PROJECT_ROOT}/tests/MilestoneRegression.java"
LD_LIBRARY_PATH="${PROJECT_ROOT}/host-build:${PROJECT_ROOT}/../occt-host/lib" \
 "${JAVA_HOME}/bin/java" -Xcheck:jni -Djava.library.path="${PROJECT_ROOT}/host-build" \
 -cp "${PROJECT_ROOT}/host-test-classes:${JSON_JAR}" org.freecad.mobilelab.MilestoneRegression
