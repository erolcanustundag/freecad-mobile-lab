# SPDX-License-Identifier: LGPL-2.1-or-later
"""Original non-solid Datum references and finite viewport guides."""
import math
import FreeCAD as App

ENGINES={'PartDesign::Plane':'Plane','PartDesign::Line':'Line','PartDesign::Point':'Point','PartDesign::CoordinateSystem':'3D'}
TYPES=set(ENGINES)
ATTACHABLE={'PartDesign::Plane','PartDesign::CoordinateSystem'}
MAXIMUM=64

def is_reference(obj):
    source=obj.getLinkedObject(True) if obj.TypeId.startswith('App::Link') else obj
    return source is not None and source.TypeId in TYPES

def identity(p):
    return p.Base.Length<1e-9 and p.Rotation.Angle<1e-9

def size(value):
    import mobile_sketch
    value=mobile_sketch.number(value,10000)
    if value<=1e-7:raise ValueError('Construction guide size must be positive and at most10,000mm')
    return value

def datum(obj):
    import mobile_partdesign as pd
    if obj is None or obj.TypeId not in TYPES or pd.owner(obj) is None:raise ValueError('Choose an original Datum owned by a Body')
    if obj.TypeId=='PartDesign::Line' and 'Transient' not in obj.getPropertyStatus('Shape'):obj.setPropertyStatus('Shape','Transient')
    if obj.MapMode!='Deactivated' or obj.AttachmentSupport or not identity(obj.AttachmentOffset) or obj.MapReversed or obj.MapPathParameter!=0 or obj.ExpressionEngine or obj.AttacherType!='Attacher::AttachEngine'+ENGINES[obj.TypeId]:raise ValueError('Datums support manual unbound placement without attachment, expressions or offsets')
    if obj.TypeId in ('PartDesign::Plane','PartDesign::Line'):
        if obj.ResizeMode!='Manual':raise ValueError('Datum guides require Manual sizing')
        size(obj.Length.Value)
        if obj.TypeId=='PartDesign::Plane':size(obj.Width.Value)
    pose=obj.Placement
    if any(not math.isfinite(v) or abs(v)>1000000 for v in pose.Base) or any(not math.isfinite(v) for v in pose.Rotation.Q):raise ValueError('Datum placement must be finite and bounded')
    return obj

def support(sketch):
    import mobile_partdesign as pd
    links=sketch.AttachmentSupport
    if sketch.MapMode!='ObjectXY' or len(links)!=1 or list(links[0][1])!=['']:raise ValueError('ObjectXY requires one whole original Datum plane or coordinate system')
    source=datum(links[0][0])
    if source.TypeId not in ATTACHABLE or pd.owner(sketch)!=pd.owner(source):raise ValueError('Attach to a plane/frame owned by the same Body')
    if sketch.MapReversed or sketch.MapPathParameter!=0 or not identity(sketch.AttachmentOffset) or sketch.AttacherType!='Attacher::AttachEnginePlane' or sketch.ExternalGeometry or sketch.ExpressionEngine:raise ValueError('Datum sketch attachment supports ObjectXY without offsets, external geometry or expressions')
    return source

def sketch_pose(sketch):
    return support(sketch).Placement if sketch.MapMode=='ObjectXY' else sketch.Placement

def check_sketch(sketch):
    source=support(sketch);pose=source.getGlobalPlacement()
    if sketch.GeometryCount>256 or sketch.ConstraintCount>256:raise ValueError('Attached sketch exceeds256entities/constraints')
    for g in sketch.Geometry:
        box=g.toShape().BoundBox
        for x in (box.XMin,box.XMax):
            for y in (box.YMin,box.YMax):
                for z in (box.ZMin,box.ZMax):
                    p=pose.multVec(App.Vector(x,y,z))
                    if any(not math.isfinite(v) or abs(v)>1000000 for v in p):raise ValueError('Attached sketch geometry would exceed the coordinate budget')

def preview(obj):
    datum(obj);pose=obj.getGlobalPlacement();curves=[]
    def line(points,label):
        world=[list(pose.multVec(App.Vector(*p))) for p in points]
        if any(not math.isfinite(v) or abs(v)>1000000 for p in world for v in p):raise ValueError('Construction preview must stay within1,000,000mm')
        curves.append(dict(index=len(curves)+1,label=label,points=world))
    if obj.TypeId=='PartDesign::Plane':
        a=obj.Length.Value/2;b=obj.Width.Value/2
        line([[-a,-b,0],[a,-b,0],[a,b,0],[-a,b,0],[-a,-b,0]],'XY')
        line([[0,0,0],[min(a,20),0,0]],'X');line([[0,0,0],[0,min(b,20),0]],'Y');line([[0,0,0],[0,0,20]],'Z')
    elif obj.TypeId=='PartDesign::Line':
        half=obj.Length.Value/2;line([[0,0,-half],[0,0,half]],'Z')
    elif obj.TypeId=='PartDesign::Point':
        line([[-1,0,0],[1,0,0]],'X');line([[0,-1,0],[0,1,0]],'Y');line([[0,0,-1],[0,0,1]],'Z')
    else:
        for axis,label in [([20,0,0],'X'),([0,20,0],'Y'),([0,0,20],'Z')]:line([[0,0,0],axis],label)
    return dict(object=obj.Name,construction=True,curves=curves,point_count=sum(len(c['points']) for c in curves),coordinates='world XYZ mm',scope='Finite viewport guides for original non-solid references; no material mesh or boundary edges')

def info(obj):
    datum(obj);pose=obj.getGlobalPlacement();preview(obj)
    result=dict(object=obj.Name,type=obj.TypeId,construction=True,origin_mm=list(pose.Base),axes={n:list(pose.Rotation.multVec(App.Vector(*v))) for n,v in [('X',(1,0,0)),('Y',(0,1,0)),('Z',(0,0,1))]},map_mode=obj.MapMode,material_volume_mm3=None)
    if obj.TypeId in ('PartDesign::Plane','PartDesign::Line'):result['display_length_mm']=obj.Length.Value
    if obj.TypeId=='PartDesign::Plane':result['display_width_mm']=obj.Width.Value
    return result

def preflight(doc):
    objects=[o for o in doc.Objects if o.TypeId in TYPES]
    attached=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject' and o.MapMode=='ObjectXY']
    if len(objects)>MAXIMUM or len(attached)>MAXIMUM:raise ValueError('Document supports at most64Datums and64attached sketches')
    for o in objects:preview(o)
    for o in attached:check_sketch(o)

def validate_document(doc):
    preflight(doc)
    for o in doc.Objects:
        if o.TypeId not in TYPES:continue
        shape=o.Shape
        if shape.isNull() or not shape.isValid():raise ValueError('Datum native geometry is invalid: '+o.Name+' null='+str(shape.isNull())+' state='+str(o.State))
        if o.TypeId in ATTACHABLE:
            if len(shape.Faces)!=1 or shape.Edges:raise ValueError('Datum plane/frame must retain its original analytic plane')
        elif o.TypeId=='PartDesign::Line':
            if len(shape.Edges)!=1 or shape.Vertexes:raise ValueError('Datum axis must retain its original analytic line')
        elif len(shape.Vertexes)!=1 or shape.Edges or shape.Faces:raise ValueError('Datum point must retain its original native point')

def editable(obj,name):
    return name=='Label' or name=='Length' and obj.TypeId in ('PartDesign::Plane','PartDesign::Line') or name=='Width' and obj.TypeId=='PartDesign::Plane'

def edit(doc,e,get,identifier):
    import mobile_partdesign as pd
    import mobile_sketch
    b=pd.body(get(e['body']));op=e['op']
    if op=='body_datum_create':
        kind='PartDesign::'+e['kind']
        if kind not in TYPES:raise ValueError('Choose original Plane, Line, Point or CoordinateSystem')
        name=identifier(e['name']);pd.fresh(doc,name);pose=mobile_sketch.placement(e.get('values',[0]*6))
        if sum(o.TypeId in TYPES for o in doc.Objects)>=MAXIMUM:raise ValueError('Datum limit is64')
        length=size(e.get('length',100));width=size(e.get('width',100))
        obj=b.newObject(kind,name);obj.Placement=pose
        # Infinite-edge BRep serialization clears the upstream axis on restore.
        # Keep this derived cache transient; the original native constructor
        # recreates its analytic line and the saved Placement positions it.
        if kind=='PartDesign::Line':obj.setPropertyStatus('Shape','Transient')
        if kind in ('PartDesign::Plane','PartDesign::Line'):obj.ResizeMode='Manual';obj.Length=length
        if kind=='PartDesign::Plane':obj.Width=width
    elif op=='body_datum_pose':
        obj=datum(get(e['object']))
        if pd.owner(obj)!=b:raise ValueError('Datum belongs to another Body')
        obj.Placement=mobile_sketch.placement(e['values'])
    elif op=='body_datum_remove':
        obj=datum(get(e['object']))
        if pd.owner(obj)!=b or any(o!=b for o in obj.InList):raise ValueError('Detach/remove Datum dependents before removing this owned reference')
        b.removeObject(obj);doc.removeObject(obj.Name)
    elif op=='body_datum_sketch':
        source=datum(get(e['datum']));name=identifier(e['name']);obj=doc.getObject(name)
        if source.TypeId not in ATTACHABLE or pd.owner(source)!=b:raise ValueError('Use a whole plane/frame owned by this Body')
        if obj is None:pd.fresh(doc,name);obj=b.newObject('Sketcher::SketchObject',name)
        else:
            mobile_sketch.require(obj)
            if pd.owner(obj)!=b or any(o.TypeId in pd.FEATURES for o in obj.InList) or obj.MapMode not in ('Deactivated','ObjectXY'):raise ValueError('Use an unused owned sketch; detach other supports first')
        obj.AttachmentSupport=[(source,[''])];obj.AttachmentOffset=App.Placement();obj.MapReversed=False;obj.MapPathParameter=0;obj.MapMode='ObjectXY'
    else:raise ValueError('Unknown Datum operation')

def validate_fcstd(tree):
    types={o.get('name'):o.get('type') for o in tree.findall('./Objects/Object')};data={o.get('name'):o for o in tree.findall('./ObjectData/Object')};owners={}
    def node(name,prop,tag):
        obj=data.get(name)
        return obj.find("./Properties/Property[@name='"+prop+"']/"+tag) if obj is not None else None
    def value(name,prop,tag):
        n=node(name,prop,tag)
        if n is None:raise ValueError('Missing saved Datum/attachment property: '+prop)
        return n.get('value')
    def place(name,prop,zero=False):
        p=node(name,prop,'PropertyPlacement')
        if p is None:raise ValueError('Missing saved placement')
        xyz=[float(p.get(k,'nan')) for k in ('Px','Py','Pz')];q=[float(p.get('Q'+str(i),'nan')) for i in range(4)]
        if any(not math.isfinite(v) or abs(v)>1000000 for v in xyz) or any(not math.isfinite(v) for v in q) or not math.isclose(sum(v*v for v in q),1,abs_tol=1e-6):raise ValueError('Saved placement must be finite, bounded and normalized')
        if zero and (any(abs(v)>1e-9 for v in xyz+q[:3]) or abs(abs(q[3])-1)>1e-9):raise ValueError('Saved attachment offset must be identity')
    for name,kind in types.items():
        if kind=='PartDesign::Body':
            n=node(name,'Group','LinkList')
            if n is not None:
                for c in n.findall('Link'):owners[c.get('value')]=name
    if sum(t in TYPES for t in types.values())>MAXIMUM:raise ValueError('Saved Datum count exceeds64')
    attached=0
    for name,kind in types.items():
        if kind in TYPES:
            if name not in owners or value(name,'MapMode','Integer')!='0' or value(name,'AttacherType','String')!='Attacher::AttachEngine'+ENGINES[kind]:raise ValueError('Saved Datum must be an owned manual original reference')
            n=node(name,'AttachmentSupport','LinkSubList')
            if n is None or n.get('count')!='0' or list(n):raise ValueError('Saved Datum attachment is unsupported')
            place(name,'Placement');place(name,'AttachmentOffset',True)
            if kind=='PartDesign::Line' and data[name].find("./Properties/Property[@name='Shape']") is not None:raise ValueError('Saved Datum axis must use a transient native geometry cache')
            if value(name,'MapReversed','Bool')!='false' or float(value(name,'MapPathParameter','Float'))!=0:raise ValueError('Unsupported saved Datum mapping')
            if kind in ('PartDesign::Plane','PartDesign::Line'):
                if value(name,'ResizeMode','Integer')!='1':raise ValueError('Saved Datum guide sizing must be Manual')
                size(float(value(name,'Length','Float')))
                if kind=='PartDesign::Plane':size(float(value(name,'Width','Float')))
        if kind!='Sketcher::SketchObject':continue
        for prop,tag,maximum in [('Geometry','GeometryList',256),('Constraints','ConstraintList',256),('ExternalGeometry','LinkSubList',64)]:
            n=node(name,prop,tag)
            if n is None or not n.get('count','').isdigit() or not 0<=int(n.get('count'))<=maximum or len(list(n))!=int(n.get('count')):raise ValueError('Saved sketch entity/constraint/reference count is inconsistent or oversized')
        mode=value(name,'MapMode','Integer');refs=node(name,'AttachmentSupport','LinkSubList');links=list(refs) if refs is not None else []
        if mode!='2' and not any(types.get(c.get('obj')) in TYPES for c in links):continue
        attached+=1
        if mode!='2' or refs is None or refs.get('count')!='1' or len(links)!=1 or links[0].get('sub')!='' or types.get(links[0].get('obj')) not in ATTACHABLE or name not in owners or owners.get(links[0].get('obj'))!=owners[name]:raise ValueError('Saved ObjectXY must reference one whole same-Body Datum plane/frame')
        if value(name,'AttacherType','String')!='Attacher::AttachEnginePlane' or value(name,'MapReversed','Bool')!='false' or float(value(name,'MapPathParameter','Float'))!=0:raise ValueError('Unsupported saved ObjectXY mapping')
        place(name,'AttachmentOffset',True);place(name,'Placement')
        if node(name,'ExternalGeometry','LinkSubList').get('count')!='0' or data[name].findall("./Properties/Property[@name='ExpressionEngine']//Expression"):raise ValueError('Saved Datum sketches cannot have external geometry or expressions')
    if attached>MAXIMUM:raise ValueError('Saved attached sketch count exceeds64')
