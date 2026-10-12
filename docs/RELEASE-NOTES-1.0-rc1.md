# FreeCAD Mobile Lab 1.0-rc1 / code 14

This engineering candidate extends 0.9-preview with numeric line/arc/polyline/weighted NURBS/interpolation/revolve/material commands; five editable reference models and two graphs; bundled offline tutorials; A4 overall-dimension SVG sheets; and versioned project v2 metadata with legacy in-memory migration and autosave recovery copies.

Command Undo/Redo/Select now clear a stale indexed topology selection. Java 8 source compatibility is consistent between Gradle and SDK packaging. Build/source input digests, native prebuilt provenance checks, immutable checkpoint/reproduce outputs and an external private signing path make builds reviewable. Separate Android instrumentation covers command entry/Undo/Redo/guide and uses a numeric CAD process PID for its forced crash.

Native geometry code/libraries match saved 0.9. The 2,000,000-triangle STL limit, binary-STL reader correction and planar hole repair are retained. No new device-crash root cause is established.

Stable 1.0 is pending Android crash, lifecycle, SAF/device/GPU/memory and production migration tests. See STATUS-1.0.md and RELEASE-GATES.json for exact scope. The APK remains signed with the public development key for prototype updates.
