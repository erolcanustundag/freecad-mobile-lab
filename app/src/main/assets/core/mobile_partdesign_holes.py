# SPDX-License-Identifier: LGPL-2.1-or-later
"""Bounded unthreaded original PartDesign Hole modes."""
import math
import mobile_partdesign_paths as paths

TYPE='PartDesign::Hole'
BOOLS={'Threaded':False,'ModelThread':False,'UseCustomThreadClearance':False,'DrillForDepth':False,'Midplane':False,'Reversed':False,'Suppressed':False,'Tapered':False,'AllowMultiFace':True}
ENUMS={'DrillPoint':'Flat','ThreadType':'None','ThreadClass':'None','ThreadSize':'---','ThreadDirection':'Right','ThreadFit':'-','ThreadDepthType':'Hole Depth'}

def parameters(diameter,depth,extent,cut,head=0,head_depth=0):
    import mobile_partdesign as pd
    diameter=pd.positive(diameter);depth=pd.positive(depth)
    if extent not in ('Dimension','ThroughAll') or cut not in ('None','Counterbore','Countersink') or extent=='ThroughAll' and cut!='None':raise ValueError('Hole supports blind/through-all flat holes or dimensioned counterbore/countersink')
    if cut=='None':
        if head!=0 or head_depth!=0:raise ValueError('Plain holes have no head cut dimensions')
    else:
        head=pd.positive(head)
        if head<=diameter+1e-7:raise ValueError('Head diameter must exceed the main hole diameter')
        if cut=='Counterbore':
            if not 1e-7<pd.positive(head_depth)<depth:raise ValueError('Counterbore depth must be positive and smaller than the main depth')
        else:
            if not 1e-7<(head-diameter)/2<depth:raise ValueError('The90degree countersink must fit within the main hole depth')
            if not math.isfinite(head_depth) or not 0<=head_depth<=1000000:raise ValueError('Invalid inactive head depth')

def profile_parameters(profile,diameter,depth,head):
    center,normal,_=paths.circle(profile)
    if normal.z<1-1e-7:raise ValueError('Hole profile must be one circle in a Body XY plane facing positive Z')
    radius=max(diameter,head)/2
    if max(abs(center.x)+radius,abs(center.y)+radius,abs(center.z)+depth)>1000000:raise ValueError('Hole exceeds the coordinate budget')

def values(f):
    return [f.Diameter.Value,f.Depth.Value,f.DepthType,f.HoleCutType,f.HoleCutDiameter.Value,f.HoleCutDepth.Value]

def validate_modes(f):
    if f.ExpressionEngine or any(getattr(f,k)!=v for k,v in BOOLS.items()) or any(getattr(f,k)!=v for k,v in ENUMS.items()):raise ValueError('Only flat, forward, unthreaded Hole modes are supported')
    if f.FuzzyTolerance!=-1 or f.DrillPointAngle.Value!=118 or f.TaperedAngle.Value!=90 or f.HoleCutCountersinkAngle.Value!=90 or f.CustomThreadClearance.Value!=0:raise ValueError('Unsupported Hole tolerance, taper or drill settings')
    if f.HoleCutCustomValues!=(f.HoleCutType!='None'):raise ValueError('Head cuts require custom dimensions; plain holes do not')
    if f.UpToFace is not None or f.UpToFace2 is not None or f.UpToShape or f.UpToShape2:raise ValueError('Hole stopping references are unsupported')
    parameters(*values(f))
    import mobile_partdesign as pd
    pd.positive(f.ThreadDepth.Value);pd.positive(f.ThreadDiameter.Value)

def references(f):
    import mobile_partdesign as pd
    if f.Profile is None:raise ValueError('Hole requires a whole owned circle sketch')
    b=pd.owner(f);profile,subs=f.Profile
    if b is None or pd.owner(profile)!=b or subs or any(o!=f and o.TypeId in pd.FEATURES for o in profile.InList):raise ValueError('Hole requires a separate whole sketch owned by its Body')
    profile_parameters(profile,f.Diameter.Value,f.Depth.Value,f.HoleCutDiameter.Value)

def preflight(doc):
    for f in doc.Objects:
        if f.TypeId==TYPE:validate_modes(f);references(f)

def validate(f,previous):
    if previous is None:raise ValueError('Hole needs a preceding Body solid')
    paths.bounded_source(previous);validate_modes(f);references(f)

def editable(f,name):
    return name in ('Label','Refine','Diameter') or name=='Depth' and f.DepthType=='Dimension' or name=='HoleCutDiameter' and f.HoleCutType!='None' or name=='HoleCutDepth' and f.HoleCutType=='Counterbore'

def validate_edit(f,name,value):
    if not editable(f,name):raise ValueError('This Hole mode/property is read-only; use the bounded Hole tools')
    v=values(f)
    for i,p in enumerate(['Diameter','Depth','DepthType','HoleCutType','HoleCutDiameter','HoleCutDepth']):
        if name==p:v[i]=value
    parameters(*v);profile_parameters(f.Profile[0],v[0],v[1],v[4])

def create(doc,e,get,identifier):
    import mobile_partdesign as pd
    b=pd.body(get(e['body']));s=get(e['profile']);name=identifier(e['name']);pd.fresh(doc,name)
    if pd.owner(s)!=b or any(o.TypeId in pd.FEATURES for o in s.InList):raise ValueError('Hole profile must be a separate unused sketch owned by this Body')
    diameter=pd.positive(e['diameter']);depth=pd.positive(e.get('depth',5));extent=e.get('extent','Dimension');cut=e.get('cut','None');head=e.get('head',0);head_depth=e.get('head_depth',0)
    parameters(diameter,depth,extent,cut,head,head_depth);profile_parameters(s,diameter,depth,head)
    pd.preflight(doc);doc.recompute();pd.closed(s);history=pd.solids(b)
    if not history or b.Tip!=history[-1]:raise ValueError('Select an existing last Body solid Tip before creating a Hole')
    paths.bounded_source(history[-1])
    f=b.newObject(TYPE,name);f.Profile=(s,[]);f.Threaded=False;f.ThreadType='None';f.ModelThread=False;f.DrillPoint='Flat'
    f.DepthType=extent;f.Diameter=diameter;f.Depth=depth;f.HoleCutType=cut
    if cut!='None':f.HoleCutCustomValues=True;f.HoleCutDiameter=head;f.HoleCutDepth=head_depth;f.HoleCutCountersinkAngle=90
    b.Tip=f

def validate_fcstd(node,feature):
    def value(prop,tag):
        n=node(feature,prop,tag)
        if n is None:raise ValueError('Missing saved Hole property: '+prop)
        return n.get('value')
    def scalar(prop):return float(value(prop,'Float'))
    for k,v in BOOLS.items():
        if value(k,'Bool')!=str(v).lower():raise ValueError('Unsupported saved Hole boolean: '+k)
    for k in ENUMS:
        if value(k,'Integer')!='0':raise ValueError('Unsupported saved Hole enumeration: '+k)
    for k,v in {'FuzzyTolerance':-1,'DrillPointAngle':118,'TaperedAngle':90,'HoleCutCountersinkAngle':90,'CustomThreadClearance':0}.items():
        if scalar(k)!=v:raise ValueError('Unsupported saved Hole scalar: '+k)
    extent=value('DepthType','Integer');cut=value('HoleCutType','Integer')
    if extent not in ('0','1') or cut not in ('0','1','2'):raise ValueError('Unsupported saved Hole extent/head cut')
    if value('HoleCutCustomValues','Bool')!=('false' if cut=='0' else 'true'):raise ValueError('Invalid saved Hole custom head dimensions')
    parameters(scalar('Diameter'),scalar('Depth'),'Dimension' if extent=='0' else 'ThroughAll',{'0':'None','1':'Counterbore','2':'Countersink'}[cut],scalar('HoleCutDiameter'),scalar('HoleCutDepth'))
    import mobile_partdesign as pd
    pd.positive(scalar('ThreadDepth'));pd.positive(scalar('ThreadDiameter'))
    for prop,tag in [('UpToFace','LinkSub'),('UpToFace2','LinkSub'),('UpToShape','LinkSubList'),('UpToShape2','LinkSubList')]:
        n=node(feature,prop,tag)
        if n is None or n.get('value') or n.get('count')!='0' or list(n):raise ValueError('Saved Hole has unsupported stopping references')
