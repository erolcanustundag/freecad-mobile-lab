# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded original Body primitive features; no baked Part substitutes."""
import math
import FreeCAD as App
import mobile_sketch
import mobile_partdesign_supports as supports

FIELDS={'PartDesign::AdditiveBox':('Length','Width','Height'),
        'PartDesign::SubtractiveBox':('Length','Width','Height'),
        'PartDesign::AdditiveCylinder':('Radius','Height'),
        'PartDesign::SubtractiveCylinder':('Radius','Height')}
TYPES=set(FIELDS)
SUBTRACTIVE={'PartDesign::SubtractiveBox','PartDesign::SubtractiveCylinder'}
MAXIMUM=64

def dimensions(kind, values):
    import mobile_partdesign as pd
    return {name:pd.positive(values[name]) for name in FIELDS[kind]}

def bounds(kind, values, pose, body_pose):
    supports.finite_pose(pose);supports.finite_pose(body_pose)
    world=body_pose.multiply(pose)
    axes=[(0,values['Length']),(0,values['Width']),(0,values['Height'])] if kind.endswith('Box') else [(-values['Radius'],values['Radius']),(-values['Radius'],values['Radius']),(0,values['Height'])]
    for x in axes[0]:
        for y in axes[1]:
            for z in axes[2]:
                point=world.multVec(App.Vector(x,y,z))
                if any(not math.isfinite(v) or abs(v)>1000000 for v in point):raise ValueError('Primitive bounds must remain within1,000,000mm in world coordinates')

def values(obj, name=None, value=None):
    return {p:value if p==name else getattr(obj,p).Value for p in FIELDS[obj.TypeId]}

def modes(obj):
    import mobile_partdesign_datums as datums
    if obj.MapMode!='Deactivated' or obj.AttachmentSupport or not datums.identity(obj.AttachmentOffset) or obj.MapReversed or obj.MapPathParameter!=0 or obj.AttacherType!='Attacher::AttachEngine3D' or obj.ExpressionEngine or obj.Suppressed or obj.FuzzyTolerance!=-1:raise ValueError('Body primitives require original manual unsuppressed default-tolerance mapping without expressions')
    if obj.TypeId.endswith('Cylinder') and (obj.Angle.Value!=360 or obj.FirstAngle.Value!=0 or obj.SecondAngle.Value!=0):raise ValueError('Body cylinders support full360degree straight primitives only')

def preflight(doc):
    import mobile_partdesign as pd
    import mobile_partdesign_paths as paths
    objects=[o for o in doc.Objects if o.TypeId in TYPES]
    if len(objects)>MAXIMUM:raise ValueError('Document supports at most64Body primitives')
    for obj in objects:
        b=pd.owner(obj)
        if b is None:raise ValueError('Original primitive must belong to a Body')
        modes(obj);bounds(obj.TypeId,dimensions(obj.TypeId,values(obj)),obj.Placement,b.getGlobalPlacement())
        if obj.BaseFeature is not None:paths.bounded_source(obj.BaseFeature)

def validate(obj, previous):
    import mobile_partdesign_paths as paths
    if obj.BaseFeature!=previous:raise ValueError('Primitive must reference the preceding owned Body solid')
    paths.bounded_source(previous)
    before=abs(previous.Shape.Volume) if previous is not None else 0
    after=abs(obj.Shape.Volume)
    if obj.TypeId in SUBTRACTIVE:
        if previous is None or not 1e-7<before-after<before:raise ValueError('Subtractive primitive must remove material and retain one closed solid')
    elif not after-before>1e-7:raise ValueError('Additive primitive must add material and retain one connected solid')

def editable(obj,name):
    return name in ('Label','Refine') or name in FIELDS[obj.TypeId]

def validate_edit(obj,name,value):
    import mobile_partdesign as pd
    if not editable(obj,name):raise ValueError('Use bounded Body primitive dimensions and dedicated placement tools')
    if name in FIELDS[obj.TypeId]:bounds(obj.TypeId,dimensions(obj.TypeId,values(obj,name,value)),obj.Placement,pd.owner(obj).getGlobalPlacement())

def edit(doc,e,get,identifier):
    import mobile_partdesign as pd
    import mobile_partdesign_paths as paths
    b=pd.body(get(e['body']))
    if e['op']=='body_primitive_pose':
        obj=get(e['object'])
        if obj.TypeId not in TYPES or pd.owner(obj)!=b:raise ValueError('Choose an original primitive owned by this Body')
        modes(obj);pose=mobile_sketch.placement(e['values'])
        bounds(obj.TypeId,dimensions(obj.TypeId,values(obj)),pose,b.getGlobalPlacement());obj.Placement=pose
        return
    kind='PartDesign::'+e['kind']
    if kind not in TYPES:raise ValueError('Choose AdditiveBox, SubtractiveBox, AdditiveCylinder or SubtractiveCylinder')
    if sum(o.TypeId in TYPES for o in doc.Objects)>=MAXIMUM:raise ValueError('Body primitive limit is64')
    name=identifier(e['name']);pd.fresh(doc,name)
    dims=dimensions(kind,e['dimensions']);pose=mobile_sketch.placement(e.get('values',[0]*6));bounds(kind,dims,pose,b.getGlobalPlacement())
    pd.preflight(doc);doc.recompute();history=pd.solids(b);previous=history[-1] if history else None
    if b.Tip!=previous:raise ValueError('Select the last solid Tip before appending a primitive')
    if kind in SUBTRACTIVE and previous is None:raise ValueError('Subtractive primitive needs a preceding solid')
    paths.bounded_source(previous)
    obj=b.newObject(kind,name)
    for field,value in dims.items():setattr(obj,field,value)
    obj.Placement=pose;b.Tip=obj

def validate_fcstd(node, name, kind, body_name, previous):
    def raw(prop,tag):
        n=node(name,prop,tag)
        if n is None:raise ValueError('Missing saved primitive property: '+prop)
        return n.get('value')
    dims=dimensions(kind,{p:float(raw(p,'Float')) for p in FIELDS[kind]})
    if raw('MapMode','Integer')!='0' or raw('AttacherType','String')!='Attacher::AttachEngine3D' or raw('MapReversed','Bool')!='false' or float(raw('MapPathParameter','Float'))!=0 or raw('Suppressed','Bool')!='false' or float(raw('FuzzyTolerance','Float'))!=-1:raise ValueError('Unsupported saved primitive mapping or mode')
    links=node(name,'AttachmentSupport','LinkSubList')
    if links is None or links.get('count')!='0' or list(links):raise ValueError('Saved primitive attachment is unsupported')
    if kind.endswith('Cylinder') and any(float(raw(p,'Float'))!=v for p,v in [('Angle',360),('FirstAngle',0),('SecondAngle',0)]):raise ValueError('Saved cylinder must retain full360degree straight defaults')
    def pose(obj,prop,identity=False):
        n=node(obj,prop,'PropertyPlacement')
        if n is None:raise ValueError('Missing saved primitive/Body placement')
        xyz=[float(n.get(k,'nan')) for k in ('Px','Py','Pz')];q=[float(n.get('Q'+str(i),'nan')) for i in range(4)]
        if any(not math.isfinite(v) or abs(v)>1000000 for v in xyz) or any(not math.isfinite(v) for v in q) or not math.isclose(sum(v*v for v in q),1,abs_tol=1e-6):raise ValueError('Saved primitive placement must be finite, bounded and normalized')
        if identity and (any(abs(v)>1e-9 for v in xyz+q[:3]) or abs(abs(q[3])-1)>1e-9):raise ValueError('Saved primitive attachment offset must be identity')
        return App.Placement(App.Vector(*xyz),App.Rotation(*q))
    pose(name,'AttachmentOffset',True);bounds(kind,dims,pose(name,'Placement'),pose(body_name,'Placement'))
    if kind in SUBTRACTIVE and previous is None:raise ValueError('Saved subtractive primitive needs a preceding solid')

