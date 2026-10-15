# SPDX-License-Identifier: LGPL-2.1-or-later
"""Qualified original PartDesign sweeps; geometry remains in upstream FreeCAD."""
import math
import FreeCAD as App
import mobile_part
import mobile_sketch

PIPES={'PartDesign::AdditivePipe','PartDesign::SubtractivePipe'}
HELICES={'PartDesign::AdditiveHelix','PartDesign::SubtractiveHelix'}
TYPES=PIPES|HELICES

def sketch(obj):
    mobile_sketch.require(obj)
    if obj.GeometryCount!=1 or obj.getConstruction(0) or obj.ExternalGeometry or obj.ExpressionEngine:
        raise ValueError('Path tools require one nonconstruction geometry with no external references or expressions')
    return obj.Geometry[0]

def circle(obj):
    curve=sketch(obj)
    if not isinstance(curve,mobile_part.Part.Circle):raise ValueError('Path profile must be a single native sketch circle')
    radius=mobile_sketch.number(curve.Radius)
    if radius<=1e-7:raise ValueError('Use a positive circular section radius')
    center=obj.Placement.multVec(curve.Center)
    normal=obj.Placement.Rotation.multVec(curve.Axis)
    return center,normal,radius

def bounded_source(source):
    if source is not None:
        mobile_part.solid_source(source)
        if len(source.Shape.Faces)>64 or len(source.Shape.Edges)>256:raise ValueError('Path feature stock is limited to64faces/256edges')

def pipe_parameters(profile,path,edge):
    if profile==path or edge!='Edge1':raise ValueError('Use a separate owned single-edge path sketch and Edge1')
    center,normal,radius=circle(profile);curve=sketch(path)
    if isinstance(curve,mobile_part.Part.LineSegment):
        start=curve.StartPoint;tangent=curve.EndPoint-start;length=tangent.Length
    elif isinstance(curve,mobile_part.Part.ArcOfCircle):
        sweep=curve.LastParameter-curve.FirstParameter
        if not 1e-7<sweep<=math.pi or curve.Radius<=2*radius:raise ValueError('Circular path angle must be at most180degrees and its radius greater than twice the section radius')
        start=curve.value(curve.FirstParameter);tangent=curve.tangent(curve.FirstParameter)[0];length=curve.Radius*sweep
    else:raise ValueError('Pipe path supports one native line or circular arc')
    if not 1e-7<length<=1000000:raise ValueError('Pipe path length must be positive and within1,000,000mm')
    start=path.Placement.multVec(start);tangent=path.Placement.Rotation.multVec(tangent);tangent.normalize()
    if (center-start).Length>1e-6 or abs(normal.dot(tangent))<1-1e-7:raise ValueError('Circle must be centered at the path start and normal to its initial tangent')
    for v in (center.x,center.y,center.z):
        if abs(v)+length+radius>1000000:raise ValueError('Sweep exceeds the coordinate budget')

def helix_parameters(profile,pitch,height):
    import mobile_partdesign as pd
    pitch=pd.positive(pitch);height=pd.positive(height)
    center,normal,radius=circle(profile)
    if abs(abs(normal.y)-1)>1e-7 or abs(center.y)>1e-6 or center.x<=radius+1e-7:
        raise ValueError('Helix circle must lie in the Body XZ meridian plane, entirely on the positive radial X side')
    if pitch<=2*radius+1e-7:raise ValueError('Helix pitch must exceed the section diameter to prevent adjacent-turn overlap')
    if not 1e-7<height/pitch<=16:raise ValueError('Helix supports at most16turns')
    if center.x+radius>1000000 or abs(center.z)+height+radius>1000000:raise ValueError('Helix exceeds the coordinate budget')

def references(feature):
    import mobile_partdesign as pd
    b=pd.owner(feature)
    if b is None:raise ValueError('Path feature must belong to a Body')
    if feature.Profile is None:raise ValueError('Path feature requires its owned circle profile')
    profile,subs=feature.Profile
    if subs or pd.owner(profile)!=b:raise ValueError('Path profile must be a whole sketch owned by the same Body')
    if feature.TypeId in PIPES:
        if feature.Spine is None:raise ValueError('Pipe requires its owned path sketch')
        path,names=feature.Spine
        if pd.owner(path)!=b or list(names)!=['Edge1']:raise ValueError('Pipe spine must be Edge1 of a sketch owned by the same Body')
        pipe_parameters(profile,path,'Edge1')
    else:
        if feature.ReferenceAxis is None or feature.ReferenceAxis[0]!=pd.z_axis(b) or list(feature.ReferenceAxis[1])!=['']:
            raise ValueError('Helix must reference its original Body Z axis')
        helix_parameters(profile,feature.Pitch.Value,feature.Height.Value)
    return profile

def validate_modes(feature):
    if feature.Midplane or feature.Reversed or feature.Suppressed or not feature.AllowMultiFace or feature.FuzzyTolerance!=-1 or feature.ExpressionEngine:
        raise ValueError('Path features support the forward unsuppressed default-tolerance mode only')
    if feature.UpToFace is not None or feature.UpToFace2 is not None or feature.UpToShape or feature.UpToShape2:
        raise ValueError('Path stopping references are unsupported')
    if feature.TypeId in PIPES:
        if feature.Mode!='Standard' or feature.Transition!='Transformed' or feature.Transformation!='Constant' or feature.Sections or feature.AuxiliarySpine is not None or feature.SpineTangent or feature.AuxiliarySpineTangent or not feature.AuxiliaryCurvilinear or feature.Binormal.Length>1e-7:
            raise ValueError('Pipe supports Standard/Transformed/Constant mode without auxiliary paths or sections')
    elif feature.Mode!='pitch-height-angle' or feature.Angle.Value!=0 or feature.LeftHanded or feature.Outside or not feature.HasBeenEdited or feature.Tolerance!=0.1:
        raise ValueError('Helix supports edited forward right-handed pitch/height mode with zero cone angle')

def preflight(doc):
    """Use live solved sketch geometry before heavy native feature recomputation."""
    for feature in doc.Objects:
        if feature.TypeId in TYPES:
            validate_modes(feature);references(feature)

def validate(feature,previous):
    validate_modes(feature);references(feature);bounded_source(previous)
    if feature.TypeId.startswith('PartDesign::Additive') and previous is not None and abs(feature.Shape.Volume)-abs(previous.Shape.Volume)<=1e-7:
        raise ValueError('Additive path feature must add material to the preceding solid')

def create(doc,e,get,identifier):
    import mobile_partdesign as pd
    b=pd.body(get(e['body']));s=get(e['profile']);name=identifier(e['name']);pd.fresh(doc,name)
    if pd.owner(s)!=b:raise ValueError('Path profile must belong to this Body')
    if any(o.TypeId in pd.FEATURES for o in s.InList):raise ValueError('Use an unused separate profile sketch')
    preflight(doc);doc.recompute();pd.closed(s);history=pd.solids(b)
    if history and b.Tip!=history[-1]:raise ValueError('Select the last solid Tip before appending a path feature')
    previous=history[-1] if history else None;bounded_source(previous)
    kinds={'body_add_pipe':'AdditivePipe','body_sub_pipe':'SubtractivePipe','body_add_helix':'AdditiveHelix','body_sub_helix':'SubtractiveHelix'}
    kind='PartDesign::'+kinds[e['op']]
    if kind.startswith('PartDesign::Subtractive') and previous is None:raise ValueError('Subtractive path feature requires an existing solid')
    if kind in PIPES:
        path=get(e['path'])
        if pd.owner(path)!=b or any(o.TypeId in pd.FEATURES for o in path.InList):raise ValueError('Use a separate unused path sketch owned by this Body')
        pipe_parameters(s,path,e.get('edge','Edge1'))
    else:helix_parameters(s,e['pitch'],e['height'])
    obj=b.newObject(kind,name)
    if kind in HELICES:obj.HasBeenEdited=True
    obj.Profile=(s,[])
    if kind in PIPES:
        obj.Spine=(path,['Edge1']);obj.Mode='Standard';obj.Transition='Transformed';obj.Transformation='Constant'
    else:
        obj.ReferenceAxis=(pd.z_axis(b),['']);obj.Mode='pitch-height-angle'
        # Increase pitch first if needed so transient onChanged calculations stay bounded.
        obj.Pitch=max(e['pitch'],obj.Pitch.Value);obj.Height=e['height'];obj.Pitch=e['pitch'];obj.Angle=0
    b.Tip=obj

def validate_fcstd(node,types,members,feature,children):
    """Scalar/mode/link guards run before native restoration, including turn budgets."""
    def value(prop,tag):
        n=node(feature,prop,tag)
        if n is None:raise ValueError('Missing saved path property: '+prop)
        return n.get('value')
    def empty(prop,tag):
        n=node(feature,prop,tag)
        if n is None or n.get('value') or n.get('count')!='0' or list(n):raise ValueError('Unsupported saved path reference: '+prop)
    for prop,tag,v in [('Midplane','Bool','false'),('Reversed','Bool','false'),('Suppressed','Bool','false'),('AllowMultiFace','Bool','true'),('FuzzyTolerance','Float','-1')]:
        actual=value(prop,tag)
        if (float(actual)!=float(v)) if tag=='Float' else actual!=v:raise ValueError('Unsupported saved path mode: '+prop)
    for prop in ('UpToFace','UpToFace2'):empty(prop,'LinkSub')
    for prop in ('UpToShape','UpToShape2'):empty(prop,'LinkSubList')
    if types[feature] in PIPES:
        for prop,v in [('Mode','0'),('Transition','0'),('Transformation','0')]:
            if value(prop,'Integer')!=v:raise ValueError('Unsupported saved pipe mode')
        for prop,v in [('SpineTangent','false'),('AuxiliarySpineTangent','false'),('AuxiliaryCurvilinear','true')]:
            if value(prop,'Bool')!=v:raise ValueError('Unsupported saved pipe tangent mode')
        empty('Sections','LinkSubList');empty('AuxiliarySpine','LinkSub')
        vector=node(feature,'Binormal','PropertyVector')
        if vector is None or any(float(vector.get(a,'nan'))!=0 for a in ('valueX','valueY','valueZ')):raise ValueError('Saved pipe binormal must be zero')
        spine=node(feature,'Spine','LinkSub');profile=node(feature,'Profile','LinkSub')
        if spine is None or spine.get('value') not in members or spine.get('value')==profile.get('value') or types.get(spine.get('value')) not in mobile_sketch.TYPES or spine.get('count')!='1' or [n.get('value') for n in spine.findall('Sub')]!=['Edge1']:raise ValueError('Saved pipe needs one owned Edge1 path')
    else:
        import mobile_partdesign as pd
        pitch=pd.positive(float(value('Pitch','Float')));height=pd.positive(float(value('Height','Float')))
        if height/pitch>16 or not 1e-7<float(value('Turns','Float'))<=16:raise ValueError('Saved helix exceeds16turns')
        if value('Mode','Integer')!='0' or float(value('Angle','Float'))!=0 or float(value('Tolerance','Float'))!=0.1 or value('HasBeenEdited','Bool')!='true' or value('LeftHanded','Bool')!='false' or value('Outside','Bool')!='false':raise ValueError('Unsupported saved helix mode')
        axis=node(feature,'ReferenceAxis','LinkSub');role=node(axis.get('value'),'Role','String') if axis is not None else None
        if axis is None or axis.get('value') not in children or axis.get('count')!='1' or [n.get('value') for n in axis.findall('Sub')]!=[''] or role is None or role.get('value')!='Z_Axis':raise ValueError('Saved helix must use its original Body Z axis')
