#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OCCT_HOST_ROOT="${OCCT_HOST_ROOT:-${PROJECT_ROOT}/../occt-host}"
JAVA_HOME="${JAVA_HOME:?Set JAVA_HOME to JDK 17}"
mkdir -p "${PROJECT_ROOT}/host-test-classes"
"${JAVA_HOME}/bin/javac" --release 8 -d "${PROJECT_ROOT}/host-test-classes" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/NativeCad.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/MeshFrame.java" \
    "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/RenderSettings.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/StudioLighting.java" \
 "${PROJECT_ROOT}/app/src/main/java/org/freecad/mobilelab/SoftwareRasterizer.java" \
    "${PROJECT_ROOT}/tests/SoftwareRendererTest.java"
LD_LIBRARY_PATH="${PROJECT_ROOT}/host-build:${OCCT_HOST_ROOT}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}" \
    "${JAVA_HOME}/bin/java" -Xcheck:jni -Djava.library.path="${PROJECT_ROOT}/host-build" \
    -cp "${PROJECT_ROOT}/host-test-classes" org.freecad.mobilelab.SoftwareRendererTest \
    "${PROJECT_ROOT}/docs/software-native-ring.ppm"
