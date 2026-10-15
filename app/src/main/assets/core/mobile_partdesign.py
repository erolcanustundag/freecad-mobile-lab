# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded original PartDesign Body/Pad/Pocket workflows, never baked Part recipes."""
import math
import sys
from pathlib import Path
import FreeCAD as App
import mobile_part
import mobile_sketch
import mobile_partdesign_paths as paths
import mobile_partdesign_holes as holes
import mobile_partdesign_datums as datums
DATUMS=datums.TYPES

PartDesign = None
if '_PartDesign' in sys.builtin_module_names:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'resources/Mod'))
    import PartDesign

TYPES = {'PartDesign::Body', 'PartDesign::FeatureBase', 'PartDesign::Pad', 'PartDesign::Pocket', 'PartDesign::Revolution', 'PartDesign::Groove', 'PartDesign::AdditiveLoft', 'PartDesign::SubtractiveLoft'}
FRAMES = {'App::Origin', 'App::Line', 'App::Plane', 'App::Point'}
DRESSUP={'PartDesign::Fillet','PartDesign::Chamfer','PartDesign::Draft','PartDesign::Thickness'}
PATTERNS={'PartDesign::Mirrored','PartDesign::LinearPattern','PartDesign::PolarPattern','PartDesign::Scaled'}
PATTERN_SOURCES={'PartDesign::Pad','PartDesign::Revolution','PartDesign::AdditiveLoft'}
TYPES.update(DRESSUP|PATTERNS|paths.TYPES|{holes.TYPE}|DATUMS)
FEATURES = TYPES - {'PartDesign::Body'} - DATUMS
PROFILE_FEATURES=FEATURES-DRESSUP-PATTERNS-{'PartDesign::FeatureBase'}
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

def frame(b,role):
    items=[o for o in b.Origin.OriginFeatures if o.Role==role]
    if len(items)!=1:raise ValueError('Choose an original Body origin axis/plane')
    return items[0]

def occurrences(value):
    if type(value) is not int or not 2<=value<=16:raise ValueError('Pattern occurrences must be integer2–16 including the original')
    return value

def pattern_parameters(kind,source,count=2,amount=None):
    solid(source)
    if source.TypeId not in PATTERN_SOURCES or len(source.Shape.Faces)>64 or len(source.Shape.Edges)>256:raise ValueError('Pattern source must be one bounded owned Pad/Revolution/AdditiveLoft feature')
    occurrences(count)
    if kind=='PartDesign::LinearPattern':positive(amount)
    elif kind=='PartDesign::PolarPattern':angle(amount)
    elif kind=='PartDesign::Scaled':
        amount=mobile_sketch.number(amount,4)
        if not 1+1e-7<amount<=4:raise ValueError('Scaled patterns currently support growth factor greater than1 and at most4')
        if any(abs(v)*amount>1000000 for v in mobile_part.summary(source)['bounds']):raise ValueError('Scaled geometry would exceed the coordinate budget')

def extent_parameters(kind,profile,source,mode,side,reverse,length,face=None,length2=None):
    modes=('Length','UpToFace','UpToLast') if kind=='PartDesign::Pad' else ('Length','ThroughAll','UpToFace','UpToFirst')
    if mode not in modes:raise ValueError('Unsupported native extrusion extent')
    if side not in ('One side','Symmetric','Two sides') or side!='One side' and mode!='Length':raise ValueError('Symmetric and two-sided extrusions support length extents only')
    if type(reverse) is not bool or side!='One side' and reverse:raise ValueError('Use a boolean direction; symmetric/two-sided extent has fixed direction')
    positive(length)
    if side=='Two sides':
        positive(length2)
        if length+length2>1000000:raise ValueError('Combined two-sided length exceeds1,000,000mm')
    elif length2 is not None:raise ValueError('Second length applies to Two sides only')
    if mode in ('UpToFirst','UpToLast'):
        if source is None:raise ValueError('Automatic stopping needs the preceding owned Body solid')
        solid(source)
        if len(source.Shape.Faces)>64 or len(source.Shape.Edges)>256:raise ValueError('Automatic stopping source is limited to64faces/256edges')
    if mode=='UpToFace':
        if source is None:raise ValueError('Face stopping needs the preceding owned Body solid')
        index=selection(source,[face],'Face')[0];surface=source.Shape.Faces[index-1]
        if not isinstance(surface.Surface,mobile_part.Part.Plane):raise ValueError('Stopping currently supports a planar source face')
        normal=profile.Placement.Rotation.multVec(App.Vector(0,0,1))
        if abs(surface.normalAt(0,0).dot(normal))<1-1e-7:raise ValueError('Stopping face must be parallel to the sketch plane')
        direction=(-1 if reverse else 1) if kind=='PartDesign::Pad' else (1 if reverse else -1)
        distance=(surface.CenterOfMass-profile.Shape.Vertexes[0].Point).dot(normal)*direction
        if not 1e-7<distance<=1000000:raise ValueError('Choose a source face ahead of the extrusion direction within the extent budget')
    elif face is not None:raise ValueError('A stopping face applies to UpToFace only')

def validate_extent(feature,profile,source):
    if feature.UseCustomVector or not feature.AlongSketchNormal or feature.ReferenceAxis is not None or feature.Type2!='Length' or feature.Midplane or feature.UpToFace2 is not None or feature.UpToShape or feature.UpToShape2 or any(getattr(feature,p).Value!=0 for p in ('TaperAngle','TaperAngle2','Offset','Offset2')):raise ValueError('Extrusions support the sketch normal, length/qualified stopping extents and zero taper/offset only')
    face=None
    if feature.Type=='UpToFace':
        ref,names=feature.UpToFace if feature.UpToFace is not None else (None,[])
        if ref!=source or len(names)!=1:raise ValueError('Stopping face must belong to the preceding owned solid')
        face=names[0]
    elif feature.UpToFace is not None:raise ValueError('This extent has no stopping-face reference')
    extent_parameters(feature.TypeId,profile,source,feature.Type,feature.SideType,feature.Reversed,feature.Length.Value,face,feature.Length2.Value if feature.SideType=='Two sides' else None)
    if feature.TypeId=='PartDesign::Pad' and feature.Type!='Length':
        if source is None or abs(feature.Shape.Volume)-abs(source.Shape.Volume)<=1e-7:raise ValueError('A stopping Pad must add material to the preceding solid')

def preflight(doc):
    if available():datums.preflight(doc,True);paths.preflight(doc);holes.preflight(doc)

def edit(doc, e, get, identifier):
    require();op=e['op']
    if op.startswith('body_datum_'):
        datums.edit(doc,e,get,identifier)
    elif op=='body_hole':
        holes.create(doc,e,get,identifier)
    elif op in ('body_add_pipe','body_sub_pipe','body_add_helix','body_sub_helix'):
        paths.create(doc,e,get,identifier)
    elif op=='body_create':
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
    elif op in ('body_mirror','body_linear','body_polar','body_scaled'):
        b=body(get(e['body']));name=identifier(e['name']);fresh(doc,name);doc.recompute();history=solids(b)
        if not history or b.Tip!=history[-1]:raise ValueError('Select the last solid Tip before creating a pattern')
        source=history[-1];kind='PartDesign::'+{'body_mirror':'Mirrored','body_linear':'LinearPattern','body_polar':'PolarPattern','body_scaled':'Scaled'}[op]
        count=occurrences(e['count']) if kind!='PartDesign::Mirrored' else 2
        amount=e.get('amount');pattern_parameters(kind,source,count,amount)
        if kind=='PartDesign::Mirrored':
            plane=e['plane']
            if plane not in ('XY','XZ','YZ'):raise ValueError('Use an original Body XY/XZ/YZ mirror plane')
            reference=frame(b,plane+'_Plane')
        elif kind in ('PartDesign::LinearPattern','PartDesign::PolarPattern'):
            axis=e['axis']
            if axis not in ('X','Y','Z'):raise ValueError('Use an original Body X/Y/Z axis')
            reference=frame(b,axis+'_Axis')
        obj=b.newObject(kind,name);obj.Originals=[source];obj.TransformMode='Features'
        if kind=='PartDesign::Mirrored':obj.MirrorPlane=(reference,[''])
        elif kind=='PartDesign::LinearPattern':
            obj.Direction=(reference,['']);obj.Mode='Extent';obj.Reversed=False;obj.Direction2=None;obj.Occurrences2=1;obj.Length=positive(amount);obj.Occurrences=count
        elif kind=='PartDesign::PolarPattern':obj.Axis=(reference,['']);obj.Mode='Extent';obj.Reversed=False;obj.Angle=angle(amount);obj.Occurrences=count
        else:obj.Factor=amount;obj.Occurrences=count
        b.Tip=obj
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
        if op in ('body_pad','body_pocket'):
            length=positive(e.get('length',5));mode=e.get('extent','Length');side=e.get('side','One side');reverse=e.get('reverse',False);face=e.get('face');length2=positive(e['length2']) if 'length2' in e else None
            extent_parameters('PartDesign::Pad' if op=='body_pad' else 'PartDesign::Pocket',s,history[-1] if history else None,mode,side,reverse,length,face,length2)
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
        if op in ('body_pad','body_pocket'):
            obj.Type=mode;obj.Type2='Length';obj.SideType=side;obj.Reversed=reverse;obj.Length=length
            if side=='Two sides':obj.Length2=length2
            if mode=='UpToFace':obj.UpToFace=(history[-1],[face])
        elif op in ('body_revolve','body_groove'):
            obj.Type='Angle';obj.Midplane=False;obj.Reversed=False;obj.Angle2=0
            obj.ReferenceAxis=(s,['H_Axis' if axis=='H' else 'V_Axis']);obj.Angle=amount
        else:obj.Sections=[(section,[''])];obj.Ruled=True;obj.Closed=False
        b.Tip=obj
    else:raise ValueError('Unknown Body operation')

def protected(obj):
    return obj.TypeId in TYPES|FRAMES or owner(obj) is not None

def editable(obj,name):
    if obj.TypeId in DATUMS:return datums.editable(obj,name)
    if obj.TypeId in FRAMES:return name=='Label'
    if obj.TypeId==holes.TYPE:return holes.editable(obj,name)
    if obj.TypeId in paths.HELICES:return name in ('Label','Refine','Pitch','Height')
    if obj.TypeId in TYPES:return name=='Label' or obj.TypeId in PATTERNS and (name=='Occurrences' and obj.TypeId!='PartDesign::Mirrored' or name=={'PartDesign::LinearPattern':'Length','PartDesign::PolarPattern':'Angle','PartDesign::Scaled':'Factor'}.get(obj.TypeId)) or obj.TypeId in DRESSUP and name==SCALARS[obj.TypeId] or obj.TypeId in FEATURES-{'PartDesign::FeatureBase'} and name=='Refine' or obj.TypeId in ('PartDesign::Pad','PartDesign::Pocket') and (name=='Length' and obj.Type=='Length' or name=='Length2' and obj.Type=='Length' and obj.SideType=='Two sides' or name=='Reversed' and obj.SideType=='One side') or obj.TypeId in ('PartDesign::Revolution','PartDesign::Groove') and name=='Angle'
    return True

def validate_edit(obj,name,value):
    if not editable(obj,name):raise ValueError('Use Body tools for native ownership, Tip and profile links; this feature mode is read-only')
    if obj.TypeId in DATUMS:
        if name in ('Length','Width'):datums.size(value)
        return
    if obj.TypeId==holes.TYPE:holes.validate_edit(obj,name,value)
    if obj.TypeId in paths.HELICES:
        paths.helix_parameters(obj.Profile[0],value if name=='Pitch' else obj.Pitch.Value,value if name=='Height' else obj.Height.Value)
    if obj.TypeId in PATTERNS and obj.TypeId!='PartDesign::Mirrored':
        source=obj.Originals[0];field={'PartDesign::LinearPattern':'Length','PartDesign::PolarPattern':'Angle','PartDesign::Scaled':'Factor'}[obj.TypeId]
        count=value if name=='Occurrences' else obj.Occurrences
        amount=value if name==field else getattr(obj,field)
        pattern_parameters(obj.TypeId,source,count,float(amount.Value) if hasattr(amount,'Value') else amount)
    if obj.TypeId in DRESSUP and name==SCALARS[obj.TypeId]:
        source,names=obj.Base;b=body(owner(obj));neutral=obj.NeutralPlane[1][0] if obj.TypeId=='PartDesign::Draft' else None
        dressup_parameters(obj.TypeId,source,names,value,b,neutral)
    if obj.TypeId in ('PartDesign::Pad','PartDesign::Pocket'):
        profile=obj.Profile[0];face=obj.UpToFace[1][0] if obj.UpToFace is not None else None
        extent_parameters(obj.TypeId,profile,obj.BaseFeature,obj.Type,obj.SideType,value if name=='Reversed' else obj.Reversed,value if name=='Length' else obj.Length.Value,face,(value if name=='Length2' else obj.Length2.Value) if obj.SideType=='Two sides' else None)
    if obj.TypeId in ('PartDesign::Revolution','PartDesign::Groove') and name=='Angle':angle(value)

def summary(b):
    if b.TypeId!='PartDesign::Body':return None
    return {'origin':b.Origin.Name, 'origin_features':[o.Name for o in b.Origin.OriginFeatures],
        'members':[o.Name for o in b.Group], 'solid_history':[o.Name for o in solids(b)],
        'tip':b.Tip.Name if b.Tip else None, 'base_source':b.BaseFeature.Name if b.BaseFeature else None,
        'single_solid':not b.AllowCompound,'datums':[o.Name for o in b.Group if o.TypeId in DATUMS]}

def validate_document(doc):
    if not available():return
    if len(doc.Objects)>1000:raise ValueError('Document exceeds1,000 objects including origin frames')
    datums.validate_document(doc)
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
        if any(o.TypeId not in FEATURES|DATUMS|mobile_sketch.TYPES for o in members):raise ValueError('This Body contains an unsupported feature type')
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
            if feature.TypeId in PATTERNS:
                if list(feature.Originals)!=[previous] or feature.BaseFeature!=previous or feature.TransformMode!='Features':raise ValueError('Pattern must transform the preceding owned additive feature')
                count=feature.Occurrences if feature.TypeId!='PartDesign::Mirrored' else 2
                amount=feature.Length.Value if feature.TypeId=='PartDesign::LinearPattern' else feature.Angle.Value if feature.TypeId=='PartDesign::PolarPattern' else feature.Factor if feature.TypeId=='PartDesign::Scaled' else None
                pattern_parameters(feature.TypeId,previous,count,amount)
                if feature.TypeId=='PartDesign::Mirrored':reference,names=feature.MirrorPlane;roles=['XY_Plane','XZ_Plane','YZ_Plane']
                elif feature.TypeId=='PartDesign::LinearPattern':
                    reference,names=feature.Direction;roles=['X_Axis','Y_Axis','Z_Axis']
                    if feature.Mode!='Extent' or feature.Reversed or feature.Direction2 is not None or feature.Occurrences2!=1:raise ValueError('Linear pattern supports one forward extent direction only')
                elif feature.TypeId=='PartDesign::PolarPattern':
                    reference,names=feature.Axis;roles=['X_Axis','Y_Axis','Z_Axis']
                    if feature.Mode!='Extent' or feature.Reversed:raise ValueError('Polar pattern supports forward extent angle only')
                if feature.TypeId!='PartDesign::Scaled' and (reference not in origin.OriginFeatures or reference.Role not in roles or list(names)!=['']):raise ValueError('Pattern reference must be a whole original Body axis/plane')
            elif feature.TypeId in DRESSUP:
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
                if feature.TypeId==holes.TYPE:
                    holes.validate(feature,previous)
                elif feature.TypeId in paths.TYPES:
                    paths.validate(feature,previous)
                elif feature.TypeId in ('PartDesign::Pad','PartDesign::Pocket'):
                    validate_extent(feature,profile,previous)
                elif feature.TypeId in ('PartDesign::Revolution','PartDesign::Groove'):
                    ref,axis=feature.ReferenceAxis
                    if ref!=profile or axis not in (['H_Axis'],['V_Axis']) or feature.Type!='Angle' or feature.Midplane or feature.Reversed or feature.Angle2.Value!=0:raise ValueError('Revolution/Groove supports one forward angle about its sketch H/V axis only')
                    angle(feature.Angle.Value)
                else:
                    sections=feature.Sections
                    if len(sections)!=1 or sections[0][0]==profile or sections[0][0] not in members or list(sections[0][1])!=[''] or sections[0][0].TypeId not in mobile_sketch.TYPES or not feature.Ruled or feature.Closed:raise ValueError('Body loft supports two different owned whole sketches in open ruled mode')
                    closed(sections[0][0])
                if feature.BaseFeature!=previous:raise ValueError('Body solid history is branched or out of order')
                if feature.TypeId in ('PartDesign::Pocket','PartDesign::Groove','PartDesign::SubtractiveLoft','PartDesign::SubtractivePipe','PartDesign::SubtractiveHelix','PartDesign::Hole'):
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
    datums.validate_fcstd(tree)
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
        roles={'X_Axis':'App::Line','Y_Axis':'App::Line','Z_Axis':'App::Line','XY_Plane':'App::Plane','XZ_Plane':'App::Plane','YZ_Plane':'App::Plane','Origin':'App::Point'}
        saved_roles=[]
        for child in children:
            role=node(child,'Role','String')
            if role is None or roles.get(role.get('value'))!=types.get(child):raise ValueError('Saved origin frame roles are invalid')
            saved_roles.append(role.get('value'))
        if set(saved_roles)!=set(roles):raise ValueError('Saved Body origin roles must be unique')
        these=set([origin]+children)
        if frames & these:raise ValueError('Saved Bodies cannot share origin frames')
        frames.update(these)
        members=links(name,'Group')
        if owned & set(members) or any(types.get(n) not in FEATURES|DATUMS|mobile_sketch.TYPES for n in members):raise ValueError('Saved Body feature ownership is invalid')
        owned.update(members)
        tip=link(name,'Tip')
        if tip and (tip not in members or types.get(tip) not in FEATURES):raise ValueError('Saved Tip must be an owned solid feature')
        previous=None
        for feature in members:
            if types.get(feature) in PATTERNS:
                kind=types[feature]
                if links(feature,'Originals')!=[previous] or types.get(previous) not in PATTERN_SOURCES or link(feature,'BaseFeature')!=previous:raise ValueError('Saved pattern needs the preceding owned additive source')
                n=node(feature,'TransformMode','Integer')
                if n is None or n.get('value')!='0':raise ValueError('Saved pattern supports Features mode only')
                if kind!='PartDesign::Mirrored':
                    n=node(feature,'Occurrences','Integer')
                    if n is None:raise ValueError('Missing saved pattern count')
                    occurrences(int(n.get('value','0')))
                    field={'PartDesign::LinearPattern':'Length','PartDesign::PolarPattern':'Angle','PartDesign::Scaled':'Factor'}[kind]
                    n=node(feature,field,'Float')
                    if n is None:raise ValueError('Missing saved pattern amount')
                    amount=float(n.get('value','nan'))
                    if kind=='PartDesign::LinearPattern':positive(amount)
                    elif kind=='PartDesign::PolarPattern':angle(amount)
                    elif not math.isfinite(amount) or not 1+1e-7<amount<=4:raise ValueError('Saved scale growth factor outside1–4')
                if kind!='PartDesign::Scaled':
                    prop={'PartDesign::Mirrored':'MirrorPlane','PartDesign::LinearPattern':'Direction','PartDesign::PolarPattern':'Axis'}[kind]
                    n=node(feature,prop,'LinkSub');roles=['XY_Plane','XZ_Plane','YZ_Plane'] if kind=='PartDesign::Mirrored' else ['X_Axis','Y_Axis','Z_Axis']
                    role=node(n.get('value'),'Role','String') if n is not None else None
                    if n is None or n.get('value') not in links(origin,'OriginFeatures') or n.get('count')!='1' or len(n.findall('Sub'))!=1 or n.find('Sub').get('value')!='' or role is None or role.get('value') not in roles:raise ValueError('Saved pattern must reference a whole owned origin axis/plane')
                if kind in ('PartDesign::LinearPattern','PartDesign::PolarPattern'):
                    for prop,tag,value in [('Mode','Integer','0'),('Reversed','Bool','false')]+([('Occurrences2','Integer','1')] if kind=='PartDesign::LinearPattern' else []):
                        n=node(feature,prop,tag)
                        if n is None or n.get('value')!=value:raise ValueError('Saved pattern mode is unsupported')
                    if kind=='PartDesign::LinearPattern':
                        n=node(feature,'Direction2','LinkSub')
                        if n is None or n.get('value'):raise ValueError('Saved second pattern direction is unsupported')
                previous=feature;continue
            if types.get(feature) in DRESSUP:
                kind=types[feature];base=node(feature,'Base','LinkSub');names=[c.get('value') for c in base.findall('Sub')] if base is not None else []
                import re
                selected='Edge' if kind in ('PartDesign::Fillet','PartDesign::Chamfer') else 'Face'
                maximum=32 if selected=='Edge' else 16
                if base is None or base.get('value') not in members or types.get(base.get('value')) not in FEATURES or base.get('value')==feature or str(len(names))!=base.get('count') or not 1<=len(names)<=maximum or len(names)!=len(set(names)) or any(not re.fullmatch(selected+r'([1-9][0-9]{0,5})',n or '') for n in names):raise ValueError('Saved finishing selections must reference an owned solid with bounded current names')
                if base.get('value')!=previous or link(feature,'BaseFeature')!=previous:raise ValueError('Saved finishing source must be the preceding owned solid')
                previous=feature
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
            if types.get(feature)=='PartDesign::FeatureBase':previous=feature;continue
            if types.get(feature) not in PROFILE_FEATURES:continue
            source=previous;previous=feature
            if (link(feature,'BaseFeature') or None)!=source:raise ValueError('Saved extrusion/profile history must reference the preceding owned solid')
            profile=node(feature,'Profile','LinkSub')
            if profile is None or profile.get('value') not in members or types.get(profile.get('value')) not in mobile_sketch.TYPES or profile.get('count')!='0':raise ValueError('Saved Body profile must be a whole owned sketch')
            if types[feature] in ('PartDesign::Pad','PartDesign::Pocket'):
                def scalar(prop,tag):
                    n=node(feature,prop,tag)
                    if n is None:raise ValueError('Missing saved extrusion property: '+prop)
                    return n.get('value')
                mode=scalar('Type','Integer');side=scalar('SideType','Integer');reverse=scalar('Reversed','Bool')
                if mode not in (['0','1','3'] if types[feature]=='PartDesign::Pad' else ['0','1','2','3']) or side not in ['0','1','2'] or side!='0' and (mode!='0' or reverse!='false') or reverse not in ['true','false']:raise ValueError('Saved extrusion extent/direction is unsupported')
                length=positive(float(scalar('Length','Float')));length2=positive(float(scalar('Length2','Float')))
                if side=='1' and length+length2>1000000:raise ValueError('Saved combined two-sided length exceeds the budget')
                for prop,tag,value in [('Type2','Integer','0'),('UseCustomVector','Bool','false'),('AlongSketchNormal','Bool','true'),('Midplane','Bool','false')]:
                    if scalar(prop,tag)!=value:raise ValueError('Saved extrusion has unsupported side or direction properties')
                for prop in ('TaperAngle','TaperAngle2','Offset','Offset2'):
                    if float(scalar(prop,'Float'))!=0:raise ValueError('Saved tapered/offset extrusion is unsupported')
                for prop in ('ReferenceAxis','UpToFace2'):
                    n=node(feature,prop,'LinkSub')
                    if n is None or n.get('value') or n.get('count')!='0' or list(n):raise ValueError('Saved extrusion contains an unsupported reference')
                for prop in ('UpToShape','UpToShape2'):
                    n=node(feature,prop,'LinkSubList')
                    if n is None or n.get('count')!='0' or list(n):raise ValueError('Saved extrusion contains an unsupported stopping shape')
                if ((types[feature]=='PartDesign::Pad' and mode=='1') or (types[feature]=='PartDesign::Pocket' and mode=='2')) and types.get(source) not in FEATURES:raise ValueError('Saved automatic stopping needs an owned preceding solid')
                face=node(feature,'UpToFace','LinkSub')
                if mode=='3':
                    import re
                    if face is None or face.get('value')!=source or types.get(source) not in FEATURES or link(feature,'BaseFeature')!=source or face.get('count')!='1' or len(face.findall('Sub'))!=1 or not re.fullmatch(r'Face([1-9][0-9]{0,5})',face.find('Sub').get('value','')):raise ValueError('Saved stopping face must reference the preceding owned Body solid')
                elif face is None or face.get('value') or face.get('count')!='0' or list(face):raise ValueError('Saved extrusion unexpectedly contains a stopping face')
            if types[feature]==holes.TYPE:holes.validate_fcstd(node,feature)
            if types[feature] in paths.TYPES:paths.validate_fcstd(node,types,members,feature,children)
            if types[feature] in ('PartDesign::AdditiveLoft','PartDesign::SubtractiveLoft'):
                section=node(feature,'Sections','LinkSubList')
                children=section.findall('Link') if section is not None else []
                if len(children)!=1 or section.get('count')!='1' or children[0].get('sub')!='' or children[0].get('obj') not in members or children[0].get('obj')==profile.get('value') or types.get(children[0].get('obj')) not in mobile_sketch.TYPES:raise ValueError('Saved loft section must be a different whole owned sketch')
    if any(kind in FRAMES and name not in frames or kind in FEATURES and name not in owned for name,kind in types.items()):raise ValueError('Saved native frames/features need Body ownership')
