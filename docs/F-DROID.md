# F-Droid inclusion preparation

Status: **PREPARATION_ONLY — NOT_SUBMITTED / NOT_PUBLISHED** (13 October 2026).
The owner requested F-Droid distribution. GitHub release 1.3 is available;
that does not mean the app is accepted by the official F-Droid repository.

## Completed preparation

- Public application source, LGPL-2.1-or-later license declaration and version tag v1.3.
- Store text and version-code 29 changelogs under fastlane/metadata/android for en-US, tr-TR and de-DE.
- Disabled descriptive metadata draft in fdroid/org.freecad.mobilelab.yml. It intentionally has no build block or binary-scan exemptions.
- An unsigned, non-debuggable, aligned packaging option: build_apk.py --unsigned.
  This does not create or use a signing key and writes a separate unsigned APK;
  it does not overwrite the signed release APK or its sealed input record.

## Remaining admission work

1. Produce one clean, pinned source-build recipe for the complete runtime:
   OCCT, FreeCAD Base/App/Part/Materials/Sketcher, Qt and its Android JAR,
   CPython and native extensions, Boost, ICU, Xerces, fmt, yaml-cpp and other
   bundled dependencies. Existing source/build scripts are starting points,
   not evidence of a successful F-Droid clean build. See FREECAD-CORE-PORT.md,
   source manifests, THIRD-PARTY.md and the corresponding-source release asset.
2. Replace dependence on bootstrap_release_runtime.py and the prebuilt runtime
   ZIP for official F-Droid builds. Supplying source beside binaries does not
   establish that F-Droid has built those binaries. Do not use scanignore to
   bypass this work. The local --prebuilt unsigned check tests packaging only.
3. Verify archive hashes, patch application, Qt host tools and CPython extension
   recipes in F-Droid's actual build environment. Record source provenance and
   licenses for every resulting library/JAR; review redistribution obligations.
4. Define and test an fdroiddata build block with those source dependencies,
   pinned SDK/NDK and the separate unsigned output. Run fdroid lint and build.
   No full fdroidserver lint/build or clean native rebuild has run here.
5. Add the real application icon and current device screenshots. Do not use
   fabricated screenshots or historical crash screenshots as store previews.
6. Choose F-Droid signing or independently verified reproducible upstream
   signatures. Reproducible builds are encouraged, not mandatory. A differently
   signed installation cannot update our existing APK in place; document export
   and migration. Never upload a private signing key to the submission.
7. Submit an inclusion request or tested fdroiddata merge request and respond
   to maintainers. No GitLab submission capability is available in this session.

## Submission text (prepare after the build blockers are resolved)

App: FreeCAD Mobile Lab
Package: org.freecad.mobilelab
Source: https://github.com/erolcanustundag/freecad-mobile-lab
Release: https://github.com/erolcanustundag/freecad-mobile-lab/releases/tag/v1.3
License: LGPL-2.1-or-later application; upstream dependencies retain their licenses.
Purpose: independent native Android CAD with commands, supported file import/export,
bounded original FreeCAD Part/Sketcher operations and English/Turkish/German UI.
Architecture/minimum: arm64-v8a, Android 8/API26.
Author approval: repository owner requested inclusion.
Build readiness: pending clean source-build integration; do not represent this
preparation as an already-tested F-Droid build.

Official references:
- https://f-droid.org/docs/Submitting_to_F-Droid_Quick_Start_Guide/
- https://f-droid.org/docs/Inclusion_Policy/
- https://f-droid.org/docs/FAQ_-_App_Developers/
