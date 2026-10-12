# FreeCAD Mobile Lab 1.0-rc2 / code 15

Retains the 1.0-rc1 command tools, reference models/graphs, offline guide, A4 drawings, project schema/migration and build/signing safeguards.

Fixes a selected drawing-export recovery bug: project loading remaps native object IDs, so the pending Storage Access Framework export now remaps its selected curve too. If recovery cannot restore that object, export fails clearly instead of writing a different object. This path is covered by host project/drawing fixtures; actual Android process recreation/picker interaction remains pending.

Drawing title/notes now reject invalid XML control characters. Height dimension labels rotate along the dimension line so scaled drawings stay inside the A4 sheet. The guide clarifies contour sampling caps. No native CAD binaries changed; the candidate reuses the verified 0.9 ARM64 kernel. Stable 1.0, reported-phone crash resolution, full Android/device coverage and production update migration remain open.
