# B01 — precision access (1.0-rc3)

Four implemented feature scopes: scalar expressions/saved variables; measurement panel/commands; arbitrary-axis pivot rotation/scaling; interactive orientation cube. Native CAD kernel binaries remain hash-identical to the verified 0.9 baseline. Command examples:

```
Set bore 18
Set outer "bore+2*1.6"
Ring bore 1.6 3
Calc "sqrt(3^2+4^2)"
Variables
Measure
Measure 1 2
Distance 0 0 0 3 4 0
Angle 1 0 0 0 0 0 0 1 0
RotateAround 0 0 0 0 0 1 90
ScaleAround 0 0 0 1.1
ViewCube
```

Measurements do not mutate the model or create Undo entries. Variables persist in fcml/autosave and Undo/Redo; commands snapshot evaluated values. No automatic model-variable bindings, persistent measurement dimensions or complete FreeCAD expression/Sketcher compatibility is claimed. Arithmetic values are scalar; units convert values but do not enforce dimensional algebra. Quote command arguments containing spaces.

Build/sign/static APK checks pass. Math tests pass 11,562 assertions. Native integration tests and baseline regression are pending the host kernel rebuild. Physical Android/device tests remain pending. Stable1.0 NOT_COMPLETE.
