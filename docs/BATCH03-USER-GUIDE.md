# FreeCAD document lab — rc5

Open **Workspace → FreeCAD document lab**, or use the button on the recovery screen. This experimental editor uses the original FreeCAD App document engine. The existing CAD workspace retains its 3D tools and Rhino-style command bar.

Create a native metadata document with these commands, one per line:

```
NewDoc MobileDocument
Add Source Feature
AddProperty Source Width Length
Set Source.Width 2 cm
Add Driven Feature
AddProperty Driven Width Length
Expression Driven.Width Source.Width * 2
```

Source.Width is 20 mm and Driven.Width is 40 mm. `Set Source.Width 32 mm` updates Driven.Width to 64 mm. `Undo` restores the previous values, and `Redo` reapplies the edit. `Begin "Edit dimensions"`, several edits, then `Commit` combine changes into one native transaction. `Abort` cancels it. A failed edit batch also cancels the active transaction.

Use `Save Model.FCStd`, `Close`, and `Open Model.FCStd` to verify native restoration. **Save before closing the app**: the document lab does not silently autosave unsaved documents. The Save FCStd button also offers export through Android's file picker. Canceling that export keeps the private saved copy. Open FCStd can import a file or open a private copy. Private documents persist separately from versioned interpreter assets across APK upgrades.

Other commands:

```
Add GroupName Group
Group GroupName Source
Add Instance Link
Link Instance Driven
Add Variables VarSet
Set Source.Label "Source dimensions"
Expression Driven.Width ""
Remove Instance
Activate MobileDocument
Recompute
State
```

Property kinds: Length, Angle, Area, Volume, Float, Integer, String, Bool and Link. Object kinds: Feature, Group, Link and VarSet. Properties, objects and expressions also have dialogs. Quotes preserve spaces; names use letters, digits and underscores. For a Link property, Set takes a target object name; an empty quoted value clears it. Bool accepts true/false; Integer accepts a 32-bit integer. Dimensional properties use native FreeCAD units.

This batch opens **supported App-only metadata FCStd documents**. Part solids, sketches, PartDesign bodies, assemblies and other workbench objects require their actual module ports. Scripted feature proxies remain pending. The lab reports unsupported types and preserves the imported copy. Its initial limits are eight open documents, 1,000 created objects, 256 properties per created object, 100 edits per batch and 128 MiB FCStd input, with protected XML/archive limits. It does not promise desktop-unlimited size.

The command field stays available below the scrollable property panel. Core calls run on a serialized worker in a separate process. The main workspace and recovery screen remain available while the core port is validated. Android device execution and picker/lifecycle checks have not run; this is a development-signed engineering candidate.
