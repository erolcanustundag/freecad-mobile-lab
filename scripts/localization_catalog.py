#!/usr/bin/env python3
"""Generate resource catalogues from reviewed translations; --check rejects drift."""
import argparse,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def literals(source):
    i=0
    while i<len(source):
        if source.startswith('//',i):
            j=source.find('\n',i);i=len(source) if j<0 else j+1;continue
        if source.startswith('/*',i):
            j=source.find('*/',i+2);i=len(source) if j<0 else j+2;continue
        if source[i] in ('"',"'"):
            quote=source[i];start=i;i+=1
            while i<len(source):
                if source[i]=='\\':i+=2;continue
                if source[i]==quote:i+=1;break
                i+=1
            if quote=='"':
                try:yield json.loads(source[start:i])
                except ValueError:pass
            continue
        i+=1
def key(source):return 'ui_'+hashlib.sha1(source.encode()).hexdigest()[:12]
def android(value):
    return '"'+value.replace('\\','\\\\').replace('"','\\"').replace("'","\\'").replace('\n','\\n').replace('\t','\\t')+'"'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    catalog={}
    for number,row in enumerate((ROOT/'docs/i18n/ui.tsv').read_text().splitlines(),1):
        if not row:continue
        fields=row.split('|')
        if len(fields)!=3:raise ValueError('Expected English|Turkish|German: line '+str(number))
        en,tr,de=[v.replace('\\n','\n') for v in fields]
        if en in catalog:raise ValueError('Duplicate source: '+en)
        if not tr or not de:raise ValueError('Empty translation: '+en)
        catalog[en]={'tr':tr,'de':de}
    sources=set(catalog)
    for path in (ROOT/'app/src/main/java/org/freecad/mobilelab').glob('*.java'):
        for value in literals(path.read_text()):
            if re.search('[A-Za-z]',value) and len(value)<4000 and (re.search(r'\s',value) or re.fullmatch(r'[A-Z][A-Za-z]+',value)) and not value.startswith(('uniform ','attribute ','precision ','void ','#version ','<','{')):sources.add(value)
    keys={key(s):s for s in sources}
    if len(keys)!=len(sources):raise ValueError('Resource key collision')
    for language,folder in [('en','values'),('tr','values-tr'),('de','values-de')]:
        root=ET.Element('resources')
        for source in sorted(sources):
            if language!='en' and source not in catalog:continue
            ET.SubElement(root,'string',name=key(source),formatted='false').text=android(source if language=='en' else catalog[source][language])
        ET.indent(root);text=ET.tostring(root,encoding='unicode')+'\n';path=ROOT/'app/src/main/res'/folder/'strings.xml'
        if args.check:
            if not path.exists() or path.read_text()!=text:raise ValueError('Resource catalogue differs: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(exist_ok=True);path.write_text(text)
    print('PASS: English fallback',len(sources),'keys; Turkish/German',len(catalog),'reviewed entries each')
if __name__=='__main__':main()
