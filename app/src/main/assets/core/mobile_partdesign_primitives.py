# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded original Body primitive features; no baked Part substitutes."""
import math
import FreeCAD as App
import mobile_sketch
import mobile_partdesign_supports as supports

FIELDS={'PartDesign::AdditiveBox':('Length','Width','Height'),
        'PartDesign::SubtractiveBox':('Length','Width','Height'),
        'PartDesign::AdditiveCylinder':('Radius','Height'),
        'PartDesign::SubtractiveCylinder':('Radius','Height'),
        'PartDesign::AdditiveCone':('Radius1','Radius2','Height'),
        'PartDesign::SubtractiveCone':('Radius1','Radius2','Height'),
        'PartDesign::AdditiveSphere':('Radius',),
        'PartDesign::SubtractiveSphere':('Radius',),
        'PartDesign::AdditivePrism':('Polygon','Circumradius','Height'),
        'PartDesign::SubtractivePrism':('Polygon','Circumradius','Height'),
        'PartDesign::AdditiveTorus':('Radius1','Radius2'),
        'PartDesign::SubtractiveTorus':('Radius1','Radius2'),
        'PartDesign::AdditiveWedge':('Xmin','Xmax','Ymin','Ymax','Zmin','Zmax','X2min','X2max','Z2min','Z2max'),
        'PartDesign::SubtractiveWedge':('Xmin','Xmax','Ymin','Ymax','Zmin','Zmax','X2min','X2max','Z2min','Z2max')}
TYPES=set(FIELDS)
SUBTRACTIVE={kind for kind in TYPES if 'Subtractive' in kind}
MAXIMUM=64

def dimensions(kind, values):
    import mobile_partdesign as pd
    result={}
    for name in FIELDS[kind]:
        value=float(values[name])
        if kind.endswith('Wedge'):
            if not math.isfinite(value) or abs(value)>1000000:raise ValueError('Wedge coordinates must be finite and within1,000,000mm')
            result[name]=value
        elif name=='Polygon':
            if not math.isfinite(value) or value!=int(value) or not 3<=value<=32:raise ValueError('Body prism sides must be an integer between3 and32')
            result[name]=int(value)
        elif kind.endswith('Cone') and name in ('Radius1','Radius2'):
            if not math.isfinite(value) or not 0<=value<=1000000:raise ValueError('Cone radii must be finite and between0 and1,000,000mm')
            result[name]=value
        else:result[name]=pd.positive(value)
    if kind.endswith('Cone') and max(result['Radius1'],result['Radius2'])<=1e-7:raise ValueError('A cone needs at least one positive radius above1e-7mm')
    if kind.endswith('Torus') and result['Radius1']-result['Radius2']<=1e-7:raise ValueError('Ring torus needs Radius1 greater than Radius2, both positive')
    if kind.endswith('Wedge'):
        for low,high in [('Xmin','Xmax'),('Ymin','Ymax'),('Zmin','Zmax'),('X2min','X2max'),('Z2min','Z2max')]:
            if not 1e-7<result[high]-result[low]<=1000000:raise ValueError('Wedge endpoint rectangle dimensions must be positive and bounded')
    return result

def bounds(kind, values, pose, body_pose):
    supports.finite_pose(pose);supports.finite_pose(body_pose)
    world=body_pose.multiply(pose)
    if kind.endswith('Box'):axes=[(0,values['Length']),(0,values['Width']),(0,values['Height'])]
    elif kind.endswith('Wedge'):
        axes=[(min(values['Xmin'],values['X2min']),max(values['Xmax'],values['X2max'])),(values['Ymin'],values['Ymax']),(min(values['Zmin'],values['Z2min']),max(values['Zmax'],values['Z2max']))]
    elif kind.endswith('Torus'):
        radius=values['Radius1']+values['Radius2'];axes=[(-radius,radius),(-radius,radius),(-values['Radius2'],values['Radius2'])]
    elif kind.endswith('Prism'):
        radius=values['Circumradius'];axes=[(-radius,radius),(-radius,radius),(0,values['Height'])]
    else:
        radius=max(values['Radius1'],values['Radius2']) if kind.endswith('Cone') else values['Radius']
        axes=[(-radius,radius),(-radius,radius),(-radius,radius) if kind.endswith('Sphere') else (0,values['Height'])]
    for x in axes[0]:
        for y in axes[1]:
            for z in axes[2]:
                point=world.multVec(App.Vector(x,y,z))
                if any(not math.isfinite(v) or abs(v)>1000000 for v in point):raise ValueError('Primitive bounds must remain within1,000,000mm in world coordinates')

def values(obj, name=None, value=None):
    return {p:value if p==name else getattr(getattr(obj,p),'Value',getattr(obj,p)) for p in FIELDS[obj.TypeId]}

def angles(kind):
    if kind.endswith('Torus'):return {'Angle1':-180,'Angle2':180,'Angle3':360}
    if kind.endswith('Prism'):return {'FirstAngle':0,'SecondAngle':0}
    if kind.endswith('Sphere'):return {'Angle1':-90,'Angle2':90,'Angle3':360}
    if kind.endswith('Cone'):return {'Angle':360}
    if kind.endswith('Cylinder'):return {'Angle':360,'FirstAngle':0,'SecondAngle':0}
    return {}

def check_angles(kind, values):
    expected=angles(kind)
    if set(values)!=set(expected):raise ValueError('Use the native angle fields for this primitive')
    result={p:float(values[p]) for p in expected}
    if any(not math.isfinite(v) for v in result.values()):raise ValueError('Primitive angles must be finite')
    if kind.endswith('Cone'):
        if not 1e-7<result['Angle']<=360:raise ValueError('Cone azimuth must be positive and at most360degrees')
    elif kind.endswith('Sphere'):
        if not -90<=result['Angle1']<result['Angle2']<=90 or result['Angle2']-result['Angle1']<=1e-7 or not 1e-7<result['Angle3']<=360:raise ValueError('Use ordered sphere latitudes within-90..90 and positive azimuth up to360degrees')
    elif result!=expected:raise ValueError('This primitive requires its full native angular defaults')
    return result

def modes(obj):
    import mobile_partdesign_datums as datums
    if obj.MapMode!='Deactivated' or obj.AttachmentSupport or not datums.identity(obj.AttachmentOffset) or obj.MapReversed or obj.MapPathParameter!=0 or obj.AttacherType!='Attacher::AttachEngine3D' or obj.ExpressionEngine or obj.Suppressed or obj.FuzzyTolerance!=-1:raise ValueError('Body primitives require original manual unsuppressed default-tolerance mapping without expressions')
    check_angles(obj.TypeId,{p:getattr(obj,p).Value for p in angles(obj.TypeId)})

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
    if e['op']=='body_primitive_angles':
        obj=get(e['object'])
        if obj.TypeId not in TYPES or not obj.TypeId.endswith(('Cone','Sphere')) or pd.owner(obj)!=b:raise ValueError('Choose an owned original cone or sphere')
        modes(obj);requested=check_angles(obj.TypeId,e['angles'])
        for field,value in requested.items():setattr(obj,field,value)
        return
    if e['op']=='body_primitive_pose':
        obj=get(e['object'])
        if obj.TypeId not in TYPES or pd.owner(obj)!=b:raise ValueError('Choose an original primitive owned by this Body')
        modes(obj);pose=mobile_sketch.placement(e['values'])
        bounds(obj.TypeId,dimensions(obj.TypeId,values(obj)),pose,b.getGlobalPlacement());obj.Placement=pose
        return
    kind='PartDesign::'+e['kind']
    if kind not in TYPES:raise ValueError('Choose a supported original additive or subtractive Body primitive')
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
    dims=dimensions(kind,{p:int(raw(p,'Integer')) if p=='Polygon' else float(raw(p,'Float')) for p in FIELDS[kind]})
    if raw('MapMode','Integer')!='0' or raw('AttacherType','String')!='Attacher::AttachEngine3D' or raw('MapReversed','Bool')!='false' or float(raw('MapPathParameter','Float'))!=0 or raw('Suppressed','Bool')!='false' or float(raw('FuzzyTolerance','Float'))!=-1:raise ValueError('Unsupported saved primitive mapping or mode')
    links=node(name,'AttachmentSupport','LinkSubList')
    if links is None or links.get('count')!='0' or list(links):raise ValueError('Saved primitive attachment is unsupported')
    check_angles(kind,{p:float(raw(p,'Float')) for p in angles(kind)})
    def pose(obj,prop,identity=False):
        n=node(obj,prop,'PropertyPlacement')
        if n is None:raise ValueError('Missing saved primitive/Body placement')
        xyz=[float(n.get(k,'nan')) for k in ('Px','Py','Pz')];q=[float(n.get('Q'+str(i),'nan')) for i in range(4)]
        if any(not math.isfinite(v) or abs(v)>1000000 for v in xyz) or any(not math.isfinite(v) for v in q) or not math.isclose(sum(v*v for v in q),1,abs_tol=1e-6):raise ValueError('Saved primitive placement must be finite, bounded and normalized')
        if identity and (any(abs(v)>1e-9 for v in xyz+q[:3]) or abs(abs(q[3])-1)>1e-9):raise ValueError('Saved primitive attachment offset must be identity')
        return App.Placement(App.Vector(*xyz),App.Rotation(*q))
    pose(name,'AttachmentOffset',True);bounds(kind,dims,pose(name,'Placement'),pose(body_name,'Placement'))
    if kind in SUBTRACTIVE and previous is None:raise ValueError('Saved subtractive primitive needs a preceding solid')

