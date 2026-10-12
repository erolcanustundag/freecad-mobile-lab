# FreeCAD Mobile Lab1.1

Native offline ARM64 Android CAD, minAPI26/target35, version code22. Current mobile feature set; original desktop FreeCAD/Rhino parity remains NOT_COMPLETE.

Adds English/Turkish/German language selection, automatic phone-language detection and English fallback.597 translated core UI entries per language cover recovery/workspace/document controls, fixed menus, fields and common validation. Start, jewellery and recovery guides have Turkish/German editions. Advanced technical diagnostics/reference prose can remain English. The preference persists across all three processes without restarting the CAD kernel. Open Workspace → Language or use Language/Dil/Sprache.

Adds Turkish/German command aliases, including Kutu/Küre/Silindir/Yardim and Quader/Kugel/Zylinder/Hilfe. English commands remain available; numeric command input keeps a decimal point. Model names, saved expressions and geometry are unchanged by locale selection. Dropdown kinds remain canonical despite translated captions.

Fixes document-lab Help/Restart/Recovery actions while busy. Their availability and callbacks use stable role metadata, independent of displayed button text. Existing laboratory restart still closes unsaved lab documents.

Validation:527 portable language/fallback/command/Unicode-name assertions;3 resource/placeholder regressions;6 runtime-packaging regressions; Java/DEX/resource build and signature/native-alignment checks. Physical switching, layout and lifecycle coverage remain pending. The earlier user-reported phone startup is separate evidence. Native/Python runtime bytes remain unchanged from1.0; the retained development certificate preserves the update identity. No private key is published.

The next original sketch scopes still depend on porting native Part and required OCCT/Boost/Python infrastructure. This language update does not mark those workbenches complete.
