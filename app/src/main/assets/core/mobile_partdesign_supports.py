# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded original Datum support mapping; geometry stays in native Attacher."""
import math
import re

MODES = {'PartDesign::Plane': ('FlatFace', 'Face', 5, 64),
         'PartDesign::Line': ('Tangent', 'Edge', 24, 256),
         'PartDesign::Point': ('Vertex', 'Vertex', 39, 512)}

def finite_pose(pose):
    q = list(pose.Rotation.Q)
    if any(not math.isfinite(v) or abs(v)>1000000 for v in pose.Base) or any(not math.isfinite(v) for v in q) or not math.isclose(sum(v*v for v in q),1,abs_tol=1e-6):
        raise ValueError('Attachment placement/offset must be finite, bounded and normalized')

def candidate(obj, source, element):
    import mobile_partdesign as pd
    if obj.TypeId not in MODES:raise ValueError('Support mapping is available for Datum plane, axis or point')
    mode, kind, _, maximum = MODES[obj.TypeId]
    if source is None or source.TypeId not in pd.FEATURES or pd.owner(source)!=pd.owner(obj):raise ValueError('Datum support must be an original solid owned by the same Body')
    if source==obj or source in obj.InListRecursive:raise ValueError('Datum support would create a dependency cycle')
    match = re.fullmatch(kind+r'([1-9][0-9]{0,5})',element) if isinstance(element,str) else None
    if match is None or not 1<=int(match.group(1))<=maximum:raise ValueError('Choose one current native '+kind+'N support')
    shape = source.Shape
    if shape.isNull() or len(shape.Faces)>64 or len(shape.Edges)>256 or len(shape.Vertexes)>512:raise ValueError('Datum support is limited to64faces/256edges/512vertices')
    if 'Invalid' in source.State or not shape.isValid() or len(shape.Solids)!=1 or not shape.isClosed():raise ValueError('Datum support must retain one valid closed solid')
    elements = shape.Faces if kind=='Face' else shape.Edges if kind=='Edge' else shape.Vertexes
    index = int(match.group(1))-1
    if index>=len(elements):raise ValueError('Datum support element no longer exists')
    selected = elements[index]
    if kind=='Face' and selected.Surface.TypeId!='Part::GeomPlane':raise ValueError('Datum Plane support requires a planar face')
    if kind=='Edge' and (selected.Curve.TypeId!='Part::GeomLine' or selected.Length<=1e-7):raise ValueError('Datum Axis support requires a nonzero straight edge')
    return mode

def reference(obj):
    links = obj.AttachmentSupport
    if obj.TypeId not in MODES or len(links)!=1 or len(links[0][1])!=1:raise ValueError('Datum support requires one qualified solid element')
    source, names = links[0]
    if obj.MapMode!=candidate(obj,source,names[0]):raise ValueError('Unsupported original Datum attachment mode')
    return source

def refresh(obj):
    reference(obj)
    obj.positionBySupport()
    finite_pose(obj.Placement)

def validate_saved(tree, types, data, owners, node, value, place):
    import mobile_partdesign as pd
    def dependencies(name):
        obj = data.get(name)
        if obj is None or types.get(name)=='PartDesign::Body':return set()
        result=set()
        for prop in obj.findall('./Properties/Property'):
            for child in prop:
                if child.tag in ('Link','LinkSub') and child.get('value') in types:result.add(child.get('value'))
                elif child.tag in ('LinkList','LinkSubList'):
                    result.update(c.get('obj',c.get('value')) for c in child if c.get('obj',c.get('value')) in types)
        return result
    graph={n:dependencies(n) for n in types}
    def reaches(start, target):
        seen=set();pending=[start]
        while pending:
            name=pending.pop()
            if name==target:return True
            if name in seen:continue
            seen.add(name);pending.extend(graph.get(name,set())-seen)
        return False
    for name, kind in types.items():
        if kind not in pd.DATUMS:continue
        mode=value(name,'MapMode','Integer')
        links=node(name,'AttachmentSupport','LinkSubList')
        if links is None:raise ValueError('Saved Datum support property is missing')
        if mode=='0':
            if links.get('count')!='0' or list(links):raise ValueError('Manual Datum must have no saved support')
            continue
        if kind not in MODES or mode!=str(MODES[kind][2]) or links.get('count')!='1' or len(list(links))!=1:raise ValueError('Unsupported saved Datum attachment mode/count')
        link=list(links)[0];source=link.get('obj');element=link.get('sub','');expected=MODES[kind]
        match=re.fullmatch(expected[1]+r'([1-9][0-9]{0,5})',element)
        if match is None or not 1<=int(match.group(1))<=expected[3]:raise ValueError('Invalid saved Datum support element')
        if types.get(source) not in pd.FEATURES or owners.get(source)!=owners.get(name) or name not in owners or reaches(source,name):raise ValueError('Saved Datum support must be an acyclic same-Body original solid')

