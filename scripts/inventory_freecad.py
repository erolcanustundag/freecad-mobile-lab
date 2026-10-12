#!/usr/bin/env python3
"""Inventory literal upstream command declarations; preserve unresolved registrations for audit.

This is a static source inventory, not a runtime list or a declaration of mobile compatibility.
Use a release source archive, not an evolving checkout. Regenerate on baseline updates.
"""
import argparse,csv,hashlib,json,re
from collections import defaultdict
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('--tag',default='1.1.4');args=parser.parse_args()
root=Path(__file__).resolve().parents[1];docs=root/'docs';docs.mkdir(exist_ok=True)
rows={};unresolved=[]
batch_routes={
    'Assembly':'B19/B20','BIM':'B27/B28','CAM':'B23/B24','Cloud':'B30',
    'Draft':'B13/B14','Fem':'B25/B26','Import':'B32','Inspection':'B18',
    'Material':'B29','Measure':'B31','Mesh':'B17','MeshPart':'B17',
    'OpenSCAD':'B30','Part':'B11/B12','PartDesign':'B08/B09/B10',
    'Points':'B18','ReverseEngineering':'B18','Robot':'B30',
    'Sketcher':'B05/B06/B07','Spreadsheet':'B15','Start':'B31',
    'Std/Core':'B03/B04/B31/B32/B33/B34/B35/B36','Surface':'B16',
    'TechDraw':'B21/B22','Test':'B36',
}
literal=re.compile(r'(?:addCommand|\bCommand)\s*\(\s*[\"\']([A-Za-z][A-Za-z0-9_]*)[\"\']')
for path in sorted((args.source/'src').rglob('*')):
    if path.suffix not in ('.py','.cpp','.h','.cxx'):continue
    relative=path.relative_to(args.source);parts=relative.parts
    module=parts[2] if len(parts)>2 and parts[:2]==('src','Mod') else 'Std/Core'
    if module in ('TemplatePyMod','Sandbox','Tux'):continue
    text=path.read_text(errors='replace')
    for match in literal.finditer(text):
        name=match.group(1)
        if name in ('Command','Cmd'):continue
        line=text.count('\n',0,match.start())+1
        key=(module,name)
        row=rows.setdefault(key,{'module':module,'command':name,'mobile_status':'UNASSESSED','locations':[],'release_batch':batch_routes.get(module,'B36'),'acceptance':'PROVISIONAL: compare upstream behaviour and options; verify mobile UI, persistence, Undo/Redo, export and device workflow; define command-specific fixtures before closing parity'})
        row['locations'].append(f'{relative}:{line}')
    for i,line in enumerate(text.splitlines(),1):
        if re.search(r'\baddCommand\s*\(',line) and not re.search(r'\baddCommand\s*\(\s*[\"\']',line):
            unresolved.append({'module':module,'source':str(relative),'line':i,'registration':line.strip()[:240],'status':'REVIEW_DYNAMIC'})
ordered=sorted(rows.values(),key=lambda r:(r['module'],r['command']))
record={'baseline':{'project':'FreeCAD','tag':args.tag,'source_url':f'https://github.com/FreeCAD/FreeCAD/tree/{args.tag}', 'snapshot_date':'2026-10-11'},'scope':'Literal command declarations in upstream src, including optional modules; not a complete runtime registration list. Dynamic registrations are tracked separately. External add-ons are a separate compatibility scope. Initial batch routing is based on module, not a completed command-specific acceptance audit. No mobile command is marked as a port merely because an equivalent tool exists.','commands':ordered,'dynamic_registrations':unresolved}
(docs/'FREECAD-COMMAND-INVENTORY.json').write_text(json.dumps(record,indent=2)+'\n')
with (docs/'FREECAD-COMMAND-INVENTORY.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['module','command','mobile_status','locations','release_batch','acceptance']);w.writeheader()
    for row in ordered:w.writerow({**row,'locations':' | '.join(row['locations'])})
with (docs/'FREECAD-DYNAMIC-REGISTRATIONS.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['module','source','line','registration','status']);w.writeheader();w.writerows(unresolved)
counts=defaultdict(int)
for row in ordered:counts[row['module']]+=1
print(json.dumps({'literal_commands':len(ordered),'dynamic_registration_sites':len(unresolved),'by_module':dict(counts)},indent=2))
