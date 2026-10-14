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

TYPES = {'PartDesign::Body', 'PartDesign::FeatureBase', 'PartDesign::Pad', 'PartDesign::Pocket'}
FRAMES = {'App::Origin', 'App::Line', 'App::Plane', 'App::Point'}
FEATURES = TYPES - {'PartDesign::Body'}

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

def solid(obj):
    mobile_part.solid_source(obj)
    if len(obj.Shape.Faces)>1024:raise ValueError('Body features are limited to1,024 faces')
    return obj

def fresh(doc, name, count=1):
    if doc.getObject(name) is not None:raise ValueError('Object name already exists')
    if len(doc.Objects)+count>1000:raise ValueError('Body origin and features exceed the1,000-object budget')

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
        if not history or history[-1]!=feature or b.Tip!=feature or feature.TypeId=='PartDesign::FeatureBase':raise ValueError('Remove only the current last Pad/Pocket; select the last Tip first')
        if any(o!=b for o in feature.InList):raise ValueError('Remove dependent features or sketch references first')
        b.Tip=history[-2] if len(history)>1 else None
        b.removeObject(feature);doc.removeObject(feature.Name)
    elif op in ('body_pad','body_pocket'):
        b=body(get(e['body']));s=get(e['profile']);name=identifier(e['name']);length=positive(e['length']);fresh(doc,name)
        if owner(s)!=b:raise ValueError('Profile must be a sketch owned by this Body; use BodySketch to adopt it')
        doc.recompute();mobile_part.profile(s)
        history=solids(b)
        if history and b.Tip!=history[-1]:raise ValueError('Select the last solid Tip before appending a feature')
        if any(o.TypeId in FEATURES for o in s.InList):raise ValueError('Use a separate sketch for each Pad/Pocket')
        if op=='body_pocket' and not history:raise ValueError('Pocket needs an existing Body solid')
        if history:solid(history[-1])
        obj=b.newObject('PartDesign::Pad' if op=='body_pad' else 'PartDesign::Pocket',name)
        obj.Profile=(s,[]);obj.Type='Length';obj.SideType='One side';obj.Length=length
        b.Tip=obj
    else:raise ValueError('Unknown Body operation')

def protected(obj):
    return obj.TypeId in TYPES|FRAMES or owner(obj) is not None

def editable(obj,name):
    if obj.TypeId in FRAMES:return name=='Label'
    if obj.TypeId in TYPES:return name=='Label' or obj.TypeId in ('PartDesign::Pad','PartDesign::Pocket') and name in ('Length','Refine')
    return True

def validate_edit(obj,name,value):
    if not editable(obj,name):raise ValueError('Use Body tools for native ownership, Tip and profile links; this feature mode is read-only')
    if obj.TypeId in ('PartDesign::Pad','PartDesign::Pocket') and name=='Length':positive(value)

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
            if feature.TypeId in ('PartDesign::Pad','PartDesign::Pocket'):
                profile,sub=feature.Profile
                if sub or profile not in members or profile.TypeId not in mobile_sketch.TYPES:raise ValueError('Pad/Pocket needs a whole sketch owned by its Body')
                mobile_part.profile(profile)
                if feature.Type!='Length' or feature.SideType!='One side':raise ValueError('Pad/Pocket currently supports one-sided length mode only')
                positive(feature.Length.Value)
                if feature.BaseFeature!=previous:raise ValueError('Body solid history is branched or out of order')
                if feature.TypeId=='PartDesign::Pocket':
                    if previous is None:raise ValueError('Pocket needs a base solid')
                    before=abs(previous.Shape.Volume);after=abs(feature.Shape.Volume)
                    if not 1e-7 < before-after < before:raise ValueError('Pocket must remove material and retain one solid')
            previous=feature
        if b.Tip is not None:
            solid(b)
            if not math.isclose(abs(b.Shape.Volume),abs(b.Tip.Shape.Volume),rel_tol=1e-7,abs_tol=1e-6):raise ValueError('Body shape does not agree with its Tip')
    for obj in doc.Objects:
        if obj.TypeId in FRAMES and obj not in frames:raise ValueError('Origin frames must belong to a Body')
        if obj.TypeId in FEATURES and obj not in owned:raise ValueError('PartDesign feature must belong to a Body')
