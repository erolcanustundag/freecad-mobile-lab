#!/usr/bin/env python3
"""Concordance fixture for the real upstream Base/App host build.

Run with the matching Python runtime and PYTHONPATH=<core-build>/lib.
This proves host document semantics only; the Android adapter must later
restore this fixture and match its results before claiming compatibility.
"""
import json
from pathlib import Path
import tempfile
import zipfile
import FreeCAD as App

count = 0
def check(condition, message):
    global count
    if not condition:
        raise AssertionError(message)
    count += 1

def near(value, expected, message):
    check(abs(float(value)-expected) < 1e-8, message)

def run(directory):
    document = App.newDocument('MobileCoreReference')
    document.UndoMode = 1
    source = document.addObject('App::FeaturePython', 'Dimensions')
    source.addProperty('App::PropertyLength', 'Width', 'Dimensions')
    source.addProperty('App::PropertyLength', 'Height', 'Dimensions')
    source.Width = '2 cm'
    source.Height = '7 mm'
    source.Label = 'Source dimensions'
    target = document.addObject('App::FeaturePython', 'Driven')
    target.addProperty('App::PropertyLength', 'Width', 'Dimensions')
    target.addProperty('App::PropertyLength', 'Height', 'Dimensions')
    target.addProperty('App::PropertyLink', 'Source', 'References')
    target.addProperty('App::PropertyString', 'Note', 'Documentation')
    target.Source = source
    target.Note = 'Android concordance fixture'
    target.setExpression('Width', 'Dimensions.Width * 2')
    target.setExpression('Height', 'Dimensions.Height + 3 mm')
    document.recompute()
    near(source.Width.Value, 20, 'Unit conversion')
    near(target.Width.Value, 40, 'Initial expression recompute')
    near(target.Height.Value, 10, 'Dimensional expression')
    check(target.Source == source, 'PropertyLink')
    check(source in target.OutList and target in source.InList, 'Dependency graph direction')

    document.openTransaction('Change driving dimension')
    source.Width = '25 mm'
    document.recompute()
    document.commitTransaction()
    near(target.Width.Value, 50, 'Live expression propagation')
    document.undo()
    document.recompute()
    near(source.Width.Value, 20, 'Transaction Undo')
    near(target.Width.Value, 40, 'Dependent Undo recompute')
    document.redo()
    document.recompute()
    near(source.Width.Value, 25, 'Transaction Redo')
    near(target.Width.Value, 50, 'Dependent Redo recompute')

    document.openTransaction('Cancelled dimension')
    source.Height = '100 mm'
    document.abortTransaction()
    document.recompute()
    near(source.Height.Value, 7, 'Aborted transaction restored source')
    near(target.Height.Value, 10, 'Aborted transaction restored expression')

    group = document.addObject('App::DocumentObjectGroup', 'DimensionsGroup')
    group.addObject(source)
    group.addObject(target)
    check(len(group.Group) == 2, 'Group membership')
    link = document.addObject('App::Link', 'Instance')
    link.setLink(target)
    check(link.LinkedObject == target, 'Native linked instance')
    target.Label = 'Derived dimensions'
    original_name = target.Name
    check(original_name == 'Driven', 'Name remains stable after label edit')

    fixture = directory/'FreeCAD-1.1.4-core-reference.FCStd'
    document.recompute()
    document.saveAs(str(fixture))
    with zipfile.ZipFile(fixture) as archive:
        check('Document.xml' in archive.namelist(), 'Native FCStd document XML')
        check(archive.testzip() is None, 'FCStd ZIP integrity')
        xml = archive.read('Document.xml')
        check(b'App::PropertyExpressionEngine' in xml, 'Native expression engine persisted')
        check(b'App::PropertyLink' in xml, 'Native object link persisted')
    App.closeDocument(document.Name)
    restored = App.openDocument(str(fixture))
    restored_source = restored.getObject('Dimensions')
    restored_target = restored.getObject('Driven')
    restored.recompute()
    near(restored_source.Width.Value, 25, 'FCStd source value restored')
    near(restored_target.Width.Value, 50, 'FCStd dependent restored')
    check(restored_target.Label == 'Derived dimensions', 'FCStd label restored')
    check(restored_target.Source == restored_source, 'FCStd link identity restored')
    check(restored.getObject('Instance').LinkedObject == restored_target, 'FCStd instance restored')
    check(len(restored.getObject('DimensionsGroup').Group) == 2, 'FCStd group restored')
    check(len(restored_target.ExpressionEngine) == 2, 'FCStd formula definitions restored')
    restored_source.Width = '32 mm'
    restored.recompute()
    near(restored_target.Width.Value, 64, 'Live recompute after FCStd restore')
    check(restored_target.Note == 'Android concordance fixture', 'String property restored')
    report = {'runtime': 'upstream host reference, not Android', 'version': App.Version(),
        'assertions': count, 'fixture': fixture.name,
        'saved_values_mm': {'Dimensions.Width':25.0,'Driven.Width':50.0,'Driven.Height':10.0},
        'post_restore_edit':{'object':'Dimensions','property':'Width','value':'32 mm',
            'expected_values_mm':{'Driven.Width':64.0,'Driven.Height':10.0}},
        'android_adapter': 'NOT_IMPLEMENTED'}
    (directory/'FreeCAD-core-reference-results.json').write_text(json.dumps(report, indent=2)+'\n')
    App.closeDocument(restored.Name)
    print('PASS:', count, 'upstream core reference assertions; Android concordance pending')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        run(args.output.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix='freecad-core-reference-') as temp:
            run(Path(temp))
