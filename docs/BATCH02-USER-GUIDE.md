# B02 — document organisation

Use **Tools → Mobile spreadsheet**, or enter `Spreadsheet`. The native Android grid has 32 rows and eight columns. Tap a cell to edit its source. Number and formula cells display their evaluated value; invalid formulas display `#ERR`. Text and formulas are preserved in project saves, autosave, Undo/Redo and CSV. Import replaces the sheet in one transaction.

```
Cell A1 18
Set wall 1.6
Cell A2 =A1+2*wall
Cell B1 "Diameter (mm)"
Ring =A1 wall 3
Cell B1 ""
SheetExport
SheetImport
SheetClear
```

The cell namespace is A1:H32, case insensitive in formulas. Cell names take precedence over document variables inside worksheet formulas. Formulas support the scalar expression functions from B01. Text, empty cells, missing names, cycles and arithmetic errors cannot be used as numeric command arguments. Geometry stores evaluated numbers; there is no live worksheet-to-solid dependency. This is not a port of the upstream Spreadsheet workbench. CSV uses strict UTF-8, quoted fields and a 64 KiB limit; each cell is limited to 256 characters. Export writes source formulas rather than computed display values.

Select a source object and use **Move → Align to object**. Choose a reference, world X/Y/Z axis and matching Min/Centre/Max bounds. The command also supports different source and reference anchors:

```
Align 1 2 X Centre
Align 1 2 Z Min Max
```

IDs are in the object list. Alignment translates the selected CAD object and recomputes its custom feature dependants. Bounds centres are not centres of mass. Related source/reference features are rejected to avoid moving a changing target; locked geometry remains protected.

**Fit / view → Fit selected** (`FitSelected`) centres the camera on the selected object's bounds. `Fit` restores the full-scene camera frame. Geometry and materials are shared, rather than copied into a second scene. CPU and GPU picking use the same current camera centre. Hidden objects remain hidden.

**Fit / view → Layers / visibility / locks** (`Layers`) lists the layers and applies visibility or geometry locking to all their objects. Names are case sensitive. Examples:

```
LayerHide "Reference parts"
LayerShow "Reference parts"
LayerLock "Reference parts"
LayerUnlock "Reference parts"
```

Each layer action, alignment, CSV import or cell edit commits one Undo step. Fixed in this batch: metadata restoration now synchronises the native workspace so subsequent Undo/Redo retains restored variables and cells; empty quoted command arguments are accepted for clearing cells; GPU picking updates its camera centre after a scene-frame change. Android touch, file-picker, lifecycle and reporting-phone startup checks remain pending.
