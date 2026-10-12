# Languages in1.1 and1.2

English is the complete default resource set. Turkish and German provide597 reviewed translations for core screen controls, fixed tool menus, common fields, recovery prompts and validation messages. Additional technical output, native Python/kernel diagnostics, canonical API names and advanced reference prose retain English fallback. The start, jewellery and recovery guides have Turkish/German editions. The1.2 candidate extends the catalogue to634 Turkish/German entries, including native Part/STEP controls and common errors. No whole-FreeCAD or whole-document translation is claimed.

Open Workspace → Language or the recovery screen button. Language/Dil/Sprache open the same picker. Automatic follows the phone's primary locale (tr/de/en) and falls back to English otherwise. An atomic private preference is read on resume by every process; no native process is restarted. Existing modal dialogs can be reopened to refresh their captions. Model names, worksheet data, typed identifiers, numeric storage and English command syntax stay intact. Turkish/German convenience aliases are additional command names; use decimal points in command numbers.

UI text uses Android values/values-tr/values-de string resources. docs/i18n/ui.tsv holds English|Turkish|German translations; scripts/localization_catalog.py generates stable resource identifiers and a complete default fallback. Extend LanguagePolicy choices and add a locale catalogue when adding another language. Do not translate object identifiers, filenames, expressions or saved geometry. Tests check placeholder parity, default resource coverage, region/fallback decisions, command case folding and quoted Unicode names.

The document-lab recovery roles use stable metadata and accept clicks while busy. They no longer depend on displayed English button text. Sketch curve kinds are selected by stable indices while labels are localized.

Validation: Java/APK compilation and portable locale/alias tests; physical language switching, font layout and process resumption still need Android testing.
