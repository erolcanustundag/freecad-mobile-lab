# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded original PartDesign Body/Pad/Pocket workflows, never baked Part recipes."""
import math
import sys
from pathlib import Path
import FreeCAD as App
import mobile_part
import mobile_sketch

PartDesign = None
if '_PartDesign' in sys.builtin_module_names:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'resources/Mod'))
    import PartDesign

TYPES = {'PartDesign::Body', 'PartDesign::FeatureBase', 'PartDesign::Pad', 'PartDesign::Pocket', 'PartDesign::Revolution', 'PartDesign::Groove', 'PartDesign::AdditiveLoft', 'PartDesign::SubtractiveLoft'}
FRAMES = {'App::Origin', 'App::Line', 'App::Plane', 'App::Point'}
DRESSUP={'PartDesign::Fillet','PartDesign::Chamfer','PartDesign::Draft','PartDesign::Thickness'}
TYPES.update(DRESSUP)
FEATURES = TYPES - {'PartDesign::Body'}
PROFILE_FEATURES=FEATURES-DRESSUP-{'PartDesign::FeatureBase'}
SCALARS={'PartDesign::Fillet':'Radius','PartDesign::Chamfer':'Size','PartDesign::Draft':'Angle','PartDesign::Thickness':'Value'}

def available():
    return PartDesign is not None

def require():
    if not available():raise ValueError('Original PartDesign module is unavailable')

def body(obj):
    require()
    if obj is None or obj.TypeId != 'PartDesign::Body':raise ValueError('Choose an original PartDesign Body')
    return obj

def owner(obj):
    owners = [o for o in obj.Document.Objects if o.TypeId == 'PartDesign::Body' and obj in o.Group]
    if len(owners)>1:raise ValueError('A feature cannot belong to multiple Bodies')
    return owners[0] if owners else None

def solids(b):
    return [o for o in b.Group if o.TypeId in FEATURES]

def positive(value):
    value = mobile_sketch.number(value)
    if not 1e-7 < value <= 1000000:raise ValueError('Use a positive length within1,000,000mm')
    return value

def angle(value):
    value=mobile_sketch.number(value,360)
    if not 1e-7<value<=360:raise ValueError('Use a positive revolution angle up to360degrees')
    return value

def closed(obj):
    mobile_part.profile(obj)
    for edge in obj.Shape.Edges:mobile_part.curve_budget(edge)
    return obj

def solid(obj):
    mobile_part.solid_source(obj)
    if len(obj.Shape.Faces)>1024:raise ValueError('Body features are limited to1,024 faces')
    return obj

def fresh(doc, name, count=1):
    if doc.getObject(name) is not None:raise ValueError('Object name already exists')
    if len(doc.Objects)+count>1000:raise ValueError('Body origin and features exceed the1,000-object budget')

def selection(source, names, kind):
    import re
    maximum=16 if kind=='Face' else 32
    elements=source.Shape.Faces if kind=='Face' else source.Shape.Edges
    if not isinstance(names,list) or not 1<=len(names)<=maximum or len(names)!=len(set(names)):raise ValueError('Use unique current native selections within the limit')
    ids=[]
    for name in names:
        match=re.fullmatch(kind+r'([1-9][0-9]{0,5})',name) if isinstance(name,str) else None
        if not match or not 1<=int(match.group(1))<=len(elements):raise ValueError('Choose current native '+kind+'N elements from the last Body solid')
        ids.append(int(match.group(1)))
    if kind=='Edge' and any(elements[i-1].Length<=1e-7 for i in ids):raise ValueError('Choose nonzero native edges')
    return ids

def z_axis(b):
    axes=[o for o in b.Origin.OriginFeatures if o.TypeId=='App::Line' and o.Role=='Z_Axis']
    if len(axes)!=1:raise ValueError('Body must have its original Z axis')
    return axes[0]

def dressup_parameters(kind,source,names,amount,b,neutral=None):
    solid(source);positive(amount)
    selected='Edge' if kind in ('PartDesign::Fillet','PartDesign::Chamfer') else 'Face'
    ids=selection(source,names,selected)
    box=source.Shape.BoundBox;minimum=min(box.XLength,box.YLength,box.ZLength)
    if kind=='PartDesign::Draft':
        if amount>45:raise ValueError('Draft angle must be greater than0 and at most45degrees')
        n=selection(source,[neutral],'Face')[0]
        if n in ids:raise ValueError('Neutral face must differ from the drafted faces')
        if any(not isinstance(source.Shape.Faces[i-1].Surface,mobile_part.Part.Plane) for i in ids+[n]):raise ValueError('This draft tool supports planar faces only')
        normal=source.Shape.Faces[n-1].normalAt(0,0)
        if abs(normal.z)<1-1e-7:raise ValueError('Neutral plane must be perpendicular to the Body local Z axis')
        z_axis(b)
    elif kind=='PartDesign::Thickness':
        if len(ids)>=len(source.Shape.Faces) or amount>=minimum/2:raise ValueError('Retain at least one face and use inward wall thickness below half the minimum shape extent')
    elif amount>=minimum:raise ValueError('Finishing amount must be below the minimum shape extent')

def edit(doc, e, get, identifier):
    require();op=e['op']
    if op=='body_create':
        name=identifier(e['name']);source=get(e['source']) if e.get('source') else None
        fresh(doc,name,10 if source else 9)
        if source is not None:
            solid(source)
            if source.TypeId in TYPES or owner(source) is not None:raise ValueError('Base source must be independent native Part geometry')
        b=doc.addObject('PartDesign::Body',name);b.AllowCompound=False
        if source is not None:b.BaseFeature=source
    elif op=='body_sketch':
        b=body(get(e['body']));name=identifier(e['name']);obj=doc.getObject(name)
        if obj is None:
            fresh(doc,name);b.newObject('Sketcher::SketchObject',name)
        else:
            mobile_sketch.require(obj)
            if owner(obj) is not None:raise ValueError('Sketch already belongs to a Body')
            if any(o.TypeId in FEATURES for o in obj.InList):raise ValueError('Choose an unused native sketch')
            if b in obj.OutListRecursive:raise ValueError('Sketch references would create a Body dependency cycle')
            b.addObject(obj)
    elif op=='body_tip':
        b=body(get(e['body']));feature=get(e['feature'])
        if feature not in solids(b):raise ValueError('Tip must be a solid feature owned by this Body')
        solid(feature);b.Tip=feature
    elif op=='body_remove_feature':
        b=body(get(e['body']));feature=get(e['feature']);history=solids(b)
        if not history or history[-1]!=feature or b.Tip!=feature or feature.TypeId=='PartDesign::FeatureBase':raise ValueError('Remove only the current last supported Body feature; select the last Tip first')
        if any(o!=b for o in feature.InList):raise ValueError('Remove dependent features or sketch references first')
        b.Tip=history[-2] if len(history)>1 else None
        b.removeObject(feature);doc.removeObject(feature.Name)
    elif op in ('body_fillet','body_chamfer','body_draft','body_thickness'):
        b=body(get(e['body']));name=identifier(e['name']);fresh(doc,name);doc.recompute();history=solids(b)
        if not history or b.Tip!=history[-1]:raise ValueError('Select the last Body solid Tip before creating a finishing feature')
        source=history[-1];kind='PartDesign::'+{'body_fillet':'Fillet','body_chamfer':'Chamfer','body_draft':'Draft','body_thickness':'Thickness'}[op]
        amount=positive(e['amount']);names=e['elements'];neutral=e.get('neutral')
        dressup_parameters(kind,source,names,amount,b,neutral)
        obj=b.newObject(kind,name);obj.Base=(source,names)
        if kind=='PartDesign::Fillet':obj.Radius=amount;obj.UseAllEdges=False
        elif kind=='PartDesign::Chamfer':obj.ChamferType='Equal distance';obj.Size=amount;obj.UseAllEdges=False
        elif kind=='PartDesign::Thickness':obj.Value=amount;obj.Reversed=True;obj.Intersection=False;obj.Mode=0;obj.Join=0
        else:obj.Angle=amount;obj.NeutralPlane=(source,[neutral]);obj.PullDirection=(z_axis(b),['']);obj.Reversed=False
        b.Tip=obj
    elif op in ('body_pad','body_pocket','body_revolve','body_groove','body_add_loft','body_sub_loft'):
        b=body(get(e['body']));s=get(e['profile']);name=identifier(e['name']);fresh(doc,name)
        subtractive=op in ('body_pocket','body_groove','body_sub_loft')
        if owner(s)!=b:raise ValueError('Profile must be a sketch owned by this Body; use BodySketch to adopt it')
        doc.recompute();closed(s)
        history=solids(b)
        if history and b.Tip!=history[-1]:raise ValueError('Select the last solid Tip before appending a feature')
        if any(o.TypeId in FEATURES for o in s.InList):raise ValueError('Use a separate sketch for each Body feature')
        if subtractive and not history:raise ValueError('Subtractive Body feature needs an existing solid')
        if history:solid(history[-1])
        if op in ('body_pad','body_pocket'):length=positive(e['length'])
        elif op in ('body_revolve','body_groove'):
            amount=angle(e['angle']);axis=e['axis']
            if axis not in ('H','V'):raise ValueError('Use the profile horizontal H or vertical V axis')
        else:
            section=get(e['section'])
            if section==s or owner(section)!=b:raise ValueError('Loft needs two different sketches owned by this Body')
            closed(section)
            if any(o.TypeId in FEATURES for o in section.InList):raise ValueError('Choose an unused owned loft section')
            # Ruled two-profile lofts only: no silent approximation of arbitrary loft UI.
        kind={'body_pad':'Pad','body_pocket':'Pocket','body_revolve':'Revolution','body_groove':'Groove','body_add_loft':'AdditiveLoft','body_sub_loft':'SubtractiveLoft'}[op]
        obj=b.newObject('PartDesign::'+kind,name);obj.Profile=(s,[])
        if op in ('body_pad','body_pocket'):obj.Type='Length';obj.SideType='One side';obj.Length=length
        elif op in ('body_revolve','body_groove'):
            obj.Type='Angle';obj.Midplane=False;obj.Reversed=False;obj.Angle2=0
            obj.ReferenceAxis=(s,['H_Axis' if axis=='H' else 'V_Axis']);obj.Angle=amount
        else:obj.Sections=[(section,[''])];obj.Ruled=True;obj.Closed=False
        b.Tip=obj
    else:raise ValueError('Unknown Body operation')

def protected(obj):
    return obj.TypeId in TYPES|FRAMES or owner(obj) is not None

def editable(obj,name):
    if obj.TypeId in FRAMES:return name=='Label'
    if obj.TypeId in TYPES:return name=='Label' or obj.TypeId in DRESSUP and name==SCALARS[obj.TypeId] or obj.TypeId in FEATURES-{'PartDesign::FeatureBase'} and name=='Refine' or obj.TypeId in ('PartDesign::Pad','PartDesign::Pocket') and name=='Length' or obj.TypeId in ('PartDesign::Revolution','PartDesign::Groove') and name=='Angle'
    return True

def validate_edit(obj,name,value):
    if not editable(obj,name):raise ValueError('Use Body tools for native ownership, Tip and profile links; this feature mode is read-only')
    if obj.TypeId in DRESSUP and name==SCALARS[obj.TypeId]:
        source,names=obj.Base;b=body(owner(obj));neutral=obj.NeutralPlane[1][0] if obj.TypeId=='PartDesign::Draft' else None
        dressup_parameters(obj.TypeId,source,names,value,b,neutral)
    if obj.TypeId in ('PartDesign::Pad','PartDesign::Pocket') and name=='Length':positive(value)
    if obj.TypeId in ('PartDesign::Revolution','PartDesign::Groove') and name=='Angle':angle(value)

def summary(b):
    if b.TypeId!='PartDesign::Body':return None
    return {'origin':b.Origin.Name, 'origin_features':[o.Name for o in b.Origin.OriginFeatures],
        'members':[o.Name for o in b.Group], 'solid_history':[o.Name for o in solids(b)],
        'tip':b.Tip.Name if b.Tip else None, 'base_source':b.BaseFeature.Name if b.BaseFeature else None,
        'single_solid':not b.AllowCompound}

def validate_document(doc):
    if not available():return
    if len(doc.Objects)>1000:raise ValueError('Document exceeds1,000 objects including origin frames')
    frames=set();owned=set()
    for b in doc.Objects:
        if b.TypeId!='PartDesign::Body':continue
        if b.AllowCompound:raise ValueError('Mobile Bodies currently support a single connected solid')
        origin=b.Origin
        if origin is None or origin.TypeId!='App::Origin':raise ValueError('Body origin is missing')
        children=list(origin.OriginFeatures)
        if len(children)!=7 or sorted(o.TypeId for o in children)!=sorted(['App::Line']*3+['App::Plane']*3+['App::Point']):raise ValueError('Body origin frames are incomplete')
        these=set([origin]+children)
        if frames & these:raise ValueError('Bodies cannot share origin frames')
        frames.update(these)
        members=list(b.Group)
        if len(members)!=len(set(members)) or owned & set(members):raise ValueError('Body members must have unique ownership')
        owned.update(members)
        if any(o.TypeId not in FEATURES|mobile_sketch.TYPES for o in members):raise ValueError('This Body contains an unsupported feature type')
        history=solids(b)
        if b.Tip is not None and b.Tip not in history:raise ValueError('Body Tip must be an owned solid feature')
        if history and b.Tip is None:raise ValueError('Body with solid history needs a Tip')
        bases=[o for o in history if o.TypeId=='PartDesign::FeatureBase']
        if b.BaseFeature is not None:
            solid(b.BaseFeature)
            if b.BaseFeature.TypeId in TYPES or owner(b.BaseFeature) is not None or len(bases)!=1 or history[0]!=bases[0] or bases[0].BaseFeature!=b.BaseFeature:raise ValueError('Body BaseFeature must link an independent solid')
        elif bases:raise ValueError('Orphan Body base feature')
        previous=None
        for feature in history:
            solid(feature)
            if feature.TypeId in DRESSUP:
                source,names=feature.Base
                if source!=previous or feature.BaseFeature!=previous or source not in members:raise ValueError('Body finishing source must be the preceding owned solid')
                amount=getattr(feature,SCALARS[feature.TypeId]).Value
                neutral=None
                if feature.TypeId=='PartDesign::Draft':
                    plane,neutral_names=feature.NeutralPlane;axis,axis_names=feature.PullDirection
                    if plane!=source or len(neutral_names)!=1 or axis!=z_axis(b) or list(axis_names)!=[''] or feature.Reversed:raise ValueError('Draft supports a source neutral face and the Body Z axis only')
                    neutral=neutral_names[0]
                elif feature.TypeId=='PartDesign::Chamfer':
                    if feature.ChamferType!='Equal distance' or feature.UseAllEdges:raise ValueError('Chamfer supports explicit equal-distance edge selections only')
                elif feature.TypeId=='PartDesign::Fillet':
                    if feature.UseAllEdges:raise ValueError('Fillet requires explicit bounded edge selections')
                else:
                    if not feature.Reversed or feature.Intersection or feature.Mode!='Skin' or feature.Join!='Arc':raise ValueError('Thickness supports inward skin/arc mode only')
                dressup_parameters(feature.TypeId,source,names,amount,b,neutral)
                if feature.TypeId=='PartDesign::Thickness' and not 1e-7<abs(source.Shape.Volume)-abs(feature.Shape.Volume)<abs(source.Shape.Volume):raise ValueError('Thickness must remove interior material and retain a closed single solid')
            elif feature.TypeId in PROFILE_FEATURES:
                profile,sub=feature.Profile
                if sub or profile not in members or profile.TypeId not in mobile_sketch.TYPES:raise ValueError('Pad/Pocket needs a whole sketch owned by its Body')
                closed(profile)
                if feature.TypeId in ('PartDesign::Pad','PartDesign::Pocket'):
                    if feature.Type!='Length' or feature.SideType!='One side':raise ValueError('Pad/Pocket currently supports one-sided length mode only')
                    positive(feature.Length.Value)
                elif feature.TypeId in ('PartDesign::Revolution','PartDesign::Groove'):
                    ref,axis=feature.ReferenceAxis
                    if ref!=profile or axis not in (['H_Axis'],['V_Axis']) or feature.Type!='Angle' or feature.Midplane or feature.Reversed or feature.Angle2.Value!=0:raise ValueError('Revolution/Groove supports one forward angle about its sketch H/V axis only')
                    angle(feature.Angle.Value)
                else:
                    sections=feature.Sections
                    if len(sections)!=1 or sections[0][0]==profile or sections[0][0] not in members or list(sections[0][1])!=[''] or sections[0][0].TypeId not in mobile_sketch.TYPES or not feature.Ruled or feature.Closed:raise ValueError('Body loft supports two different owned whole sketches in open ruled mode')
                    closed(sections[0][0])
                if feature.BaseFeature!=previous:raise ValueError('Body solid history is branched or out of order')
                if feature.TypeId in ('PartDesign::Pocket','PartDesign::Groove','PartDesign::SubtractiveLoft'):
                    if previous is None:raise ValueError('Subtractive feature needs a base solid')
                    before=abs(previous.Shape.Volume);after=abs(feature.Shape.Volume)
                    if not 1e-7 < before-after < before:raise ValueError('Subtractive feature must remove material and retain one solid')
            previous=feature
        if b.Tip is not None:
            solid(b)
            if not math.isclose(abs(b.Shape.Volume),abs(b.Tip.Shape.Volume),rel_tol=1e-7,abs_tol=1e-6):raise ValueError('Body shape does not agree with its Tip')
    for obj in doc.Objects:
        if obj.TypeId in FRAMES and obj not in frames:raise ValueError('Origin frames must belong to a Body')
        if obj.TypeId in FEATURES and obj not in owned:raise ValueError('PartDesign feature must belong to a Body')


def validate_fcstd(tree):
    """Validate Body reference/origin budgets before native restoration can generate objects."""
    if not available():return
    types={o.get('name'):o.get('type') for o in tree.findall('./Objects/Object')}
    data={o.get('name'):o for o in tree.findall('./ObjectData/Object')}
    frames=set();owned=set()
    def node(name,prop,tag):
        d=data.get(name)
        return d.find("./Properties/Property[@name='"+prop+"']/"+tag) if d is not None else None
    def link(name,prop):
        n=node(name,prop,'Link')
        return n.get('value') if n is not None else None
    def links(name,prop):
        n=node(name,prop,'LinkList')
        if n is None:raise ValueError('Missing saved Body ownership/origin list')
        result=[c.get('value') for c in n.findall('Link')]
        if str(len(result))!=n.get('count') or len(result)!=len(set(result)):raise ValueError('Saved Body ownership list is inconsistent')
        return result
    for name,kind in types.items():
        if kind!='PartDesign::Body':continue
        origin=link(name,'Origin')
        if types.get(origin)!='App::Origin':raise ValueError('Saved Body must reference its complete origin')
        children=links(origin,'OriginFeatures')
        if len(children)!=7 or sorted(types.get(n,'') for n in children)!=sorted(['App::Line']*3+['App::Plane']*3+['App::Point']):raise ValueError('Saved Body origin frames are incomplete')
        these=set([origin]+children)
        if frames & these:raise ValueError('Saved Bodies cannot share origin frames')
        frames.update(these)
        members=links(name,'Group')
        if owned & set(members) or any(types.get(n) not in FEATURES|mobile_sketch.TYPES for n in members):raise ValueError('Saved Body feature ownership is invalid')
        owned.update(members)
        tip=link(name,'Tip')
        if tip and (tip not in members or types.get(tip) not in FEATURES):raise ValueError('Saved Tip must be an owned solid feature')
        for feature in members:
            if types.get(feature) in DRESSUP:
                kind=types[feature];base=node(feature,'Base','LinkSub');names=[c.get('value') for c in base.findall('Sub')] if base is not None else []
                import re
                selected='Edge' if kind in ('PartDesign::Fillet','PartDesign::Chamfer') else 'Face'
                maximum=32 if selected=='Edge' else 16
                if base is None or base.get('value') not in members or types.get(base.get('value')) not in FEATURES or base.get('value')==feature or str(len(names))!=base.get('count') or not 1<=len(names)<=maximum or len(names)!=len(set(names)) or any(not re.fullmatch(selected+r'([1-9][0-9]{0,5})',n or '') for n in names):raise ValueError('Saved finishing selections must reference an owned solid with bounded current names')
                scalar=node(feature,SCALARS[kind],'Float')
                if scalar is None:raise ValueError('Missing saved finishing amount')
                amount=positive(float(scalar.get('value','nan')))
                if kind=='PartDesign::Draft':
                    if amount>45:raise ValueError('Saved draft angle exceeds45degrees')
                    plane=node(feature,'NeutralPlane','LinkSub');axis=node(feature,'PullDirection','LinkSub')
                    if plane is None or plane.get('value')!=base.get('value') or plane.get('count')!='1' or len(plane.findall('Sub'))!=1 or not re.fullmatch(r'Face([1-9][0-9]{0,5})',plane.find('Sub').get('value','')):raise ValueError('Saved draft needs one source neutral face')
                    if axis is None or axis.get('count')!='1' or len(axis.findall('Sub'))!=1 or axis.find('Sub').get('value')!='' or axis.get('value') not in links(origin,'OriginFeatures'):raise ValueError('Saved draft axis must belong to this Body origin')
                for prop,(tag,value) in ({'UseAllEdges':('Bool','false')} if kind=='PartDesign::Fillet' else {'UseAllEdges':('Bool','false'),'ChamferType':('Integer','0')} if kind=='PartDesign::Chamfer' else {'Reversed':('Bool','false')} if kind=='PartDesign::Draft' else {'Reversed':('Bool','true'),'Intersection':('Bool','false'),'Mode':('Integer','0'),'Join':('Integer','0')}).items():
                    n=node(feature,prop,tag)
                    if n is None or n.get('value')!=value:raise ValueError('Saved finishing mode is unsupported')
                continue
            if types.get(feature) not in PROFILE_FEATURES:continue
            profile=node(feature,'Profile','LinkSub')
            if profile is None or profile.get('value') not in members or types.get(profile.get('value')) not in mobile_sketch.TYPES or profile.get('count')!='0':raise ValueError('Saved Body profile must be a whole owned sketch')
            if types[feature] in ('PartDesign::AdditiveLoft','PartDesign::SubtractiveLoft'):
                section=node(feature,'Sections','LinkSubList')
                children=section.findall('Link') if section is not None else []
                if len(children)!=1 or section.get('count')!='1' or children[0].get('sub')!='' or children[0].get('obj') not in members or children[0].get('obj')==profile.get('value') or types.get(children[0].get('obj')) not in mobile_sketch.TYPES:raise ValueError('Saved loft section must be a different whole owned sketch')
    if any(kind in FRAMES and name not in frames or kind in FEATURES and name not in owned for name,kind in types.items()):raise ValueError('Saved native frames/features need Body ownership')
