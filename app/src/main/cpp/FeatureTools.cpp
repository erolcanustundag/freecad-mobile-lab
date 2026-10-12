// SPDX-License-Identifier: LGPL-2.1-or-later
#include "FeatureTools.hpp"
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepFilletAPI_MakeFillet.hxx>
#include <BRepFilletAPI_MakeChamfer.hxx>
#include <BRepOffsetAPI_MakeThickSolid.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepGProp.hxx>
#include <BRep_Tool.hxx>
#include <BRepTools.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Face.hxx>
#include <Geom_BSplineSurface.hxx>
#include <Geom_Curve.hxx>
#include <Geom_Line.hxx>
#include <Geom_Plane.hxx>
#include <GeomProjLib.hxx>
#include <GeomLProp_CLProps.hxx>
#include <GProp_GProps.hxx>
#include <TopoDS.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopTools_ListOfShape.hxx>
#include <gp_Pln.hxx>
#include <sstream>
#include <iomanip>
#include <locale>
#include <cmath>
#include <stdexcept>
namespace {
void need(bool b,const char* t){if(!b)throw std::runtime_error(t);}
int index(double d,int count){need(d==std::floor(d)&&d>=1&&d<=count,"Selected topology index is out of range");return int(d);}
TopoDS_Edge singleEdge(const TopoDS_Shape& s){TopTools_IndexedMapOfShape m;TopExp::MapShapes(s,TopAbs_EDGE,m);need(m.Extent()==1,"This curve tool needs a single edge");return TopoDS::Edge(m(1));}
Handle(Geom_Curve) worldCurve(const TopoDS_Shape& s,double& a,double& b){TopLoc_Location loc;auto c=BRep_Tool::Curve(singleEdge(s),loc,a,b);need(!c.IsNull(),"Curve has no exact geometry");return Handle(Geom_Curve)::DownCast(c->Transformed(loc.Transformation()));}
Handle(Geom_BSplineSurface) patch(const TopoDS_Shape& s,TopoDS_Face& face){TopTools_IndexedMapOfShape m;TopExp::MapShapes(s,TopAbs_FACE,m);need(m.Extent()==1,"Select one NURBS surface patch");face=TopoDS::Face(m(1));TopLoc_Location loc;auto g=BRep_Tool::Surface(face,loc);auto b=Handle(Geom_BSplineSurface)::DownCast(g);need(!b.IsNull()&&b->NbUPoles()<=16&&b->NbVPoles()<=16,"Surface pole tools support B-spline patches up to 16 by 16 poles");return Handle(Geom_BSplineSurface)::DownCast(b->Transformed(loc.Transformation()));}
void point(std::ostream& s,const gp_Pnt& p){s<<'['<<p.X()<<','<<p.Y()<<','<<p.Z()<<']';}
}
std::string topologyData(const TopoDS_Shape& shape){
 std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(12)<<"{\"edges\":[";TopTools_IndexedMapOfShape m;TopExp::MapShapes(shape,TopAbs_EDGE,m);need(m.Extent()<=2000,"Too many edges for mobile topology tools");for(int i=1;i<=m.Extent();i++){if(i>1)out<<',';GProp_GProps props;BRepGProp::LinearProperties(m(i),props);BRepAdaptor_Curve c(TopoDS::Edge(m(i)));out<<"{\"id\":"<<i<<",\"length\":"<<props.Mass()<<",\"centre\":";point(out,props.CentreOfMass());out<<",\"kind\":"<<int(c.GetType())<<'}';}out<<"],\"faces\":[";m.Clear();TopExp::MapShapes(shape,TopAbs_FACE,m);need(m.Extent()<=2000,"Too many faces for mobile topology tools");for(int i=1;i<=m.Extent();i++){if(i>1)out<<',';GProp_GProps props;BRepGProp::SurfaceProperties(m(i),props);out<<"{\"id\":"<<i<<",\"area\":"<<props.Mass()<<",\"centre\":";point(out,props.CentreOfMass());out<<'}';}out<<"]}";return out.str();
}
TopoDS_Shape detailModel(const std::string& kind,const std::vector<TopoDS_Shape>& s,const std::vector<double>& p){
 need(!s.empty(),"Select an input");
 if(kind=="Selected fillet"||kind=="Selected chamfer"||kind=="Selected shell"){
  need(s.size()==1&&p.size()>=2&&p.size()<=16&&p[0]>=.001&&p[0]<=1000,"Enter a positive radius/wall and 1 to 15 topology indices");TopTools_IndexedMapOfShape m;TopExp::MapShapes(s[0],kind=="Selected shell"?TopAbs_FACE:TopAbs_EDGE,m);
  TopTools_ListOfShape picked;for(size_t i=1;i<p.size();i++){auto shape=m(index(p[i],m.Extent()));need(!picked.Contains(shape),"Repeated topology index");picked.Append(shape);}
  if(kind=="Selected shell"){BRepOffsetAPI_MakeThickSolid f;f.MakeThickSolidByJoin(s[0],picked,-p[0],1e-5);need(f.IsDone(),"Selected-face hollowing failed; reduce the wall");return f.Shape();}
  if(kind=="Selected fillet"){BRepFilletAPI_MakeFillet f(s[0]);for(auto& e:picked)f.Add(p[0],TopoDS::Edge(e));f.Build();need(f.IsDone(),"Selected-edge fillet failed; reduce radius");return f.Shape();}
  BRepFilletAPI_MakeChamfer f(s[0]);for(auto& e:picked)f.Add(p[0],TopoDS::Edge(e));f.Build();need(f.IsDone(),"Selected-edge chamfer failed; reduce distance");return f.Shape();
 }
 if(kind=="Join curves"){
  need(p.empty()&&s.size()>=2,"Join needs 2 to 8 connected curves");BRepBuilderAPI_MakeWire w;for(auto& a:s)for(TopExp_Explorer it(a,TopAbs_EDGE);it.More();it.Next()){w.Add(TopoDS::Edge(it.Current()));need(w.IsDone(),"Curves do not join within CAD tolerance; move their endpoints together");}return w.Wire();
 }
 if(kind=="Planar region"){need(s.size()==1&&p.empty(),"Planar region needs one closed planar wire");TopExp_Explorer it(s[0],TopAbs_WIRE);need(it.More(),"Select a closed profile");auto wire=TopoDS::Wire(it.Current());it.Next();need(!it.More(),"Region accepts one wire");BRepBuilderAPI_MakeFace f(wire,true);need(f.IsDone(),"Profile is open or nonplanar");return f.Face();}
 if(kind=="Trim curve"){
  need(s.size()==1&&p.size()==2&&p[0]>=0&&p[1]<=1&&p[1]-p[0]>=1e-6,"Trim needs start/end parameter fractions: 0 <= start < end <= 1");double a,b;auto c=worldCurve(s[0],a,b);BRepBuilderAPI_MakeEdge edge(c,a+(b-a)*p[0],a+(b-a)*p[1]);need(edge.IsDone(),"Curve trimming failed");return BRepBuilderAPI_MakeWire(edge.Edge()).Wire();
 }
 if(kind=="Extend line"){
  need(s.size()==1&&p.size()==2&&p[0]>=0&&p[1]>=0&&p[0]+p[1]>.0001&&p[0]+p[1]<=10000,"Line extension needs start/end lengths in mm");double a,b;auto c=worldCurve(s[0],a,b);need(!Handle(Geom_Line)::DownCast(c).IsNull(),"Extend line supports straight single-edge curves");gp_Pnt first=c->Value(a),last=c->Value(b);gp_Vec tangent(first,last);need(tangent.Magnitude()>1e-9,"Line has zero length");tangent.Normalize();return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(first.Translated(tangent*(-p[0])),last.Translated(tangent*p[1])).Edge()).Wire();
 }
 if(kind=="Project curve"){
  need(s.size()==1&&p.size()==1&&std::abs(p[0])<=10000,"Project curve needs target Z plane in mm");double a,b;auto c=worldCurve(s[0],a,b);Handle(Geom_Plane) plane=new Geom_Plane(gp_Pln(gp_Pnt(0,0,p[0]),gp_Dir(0,0,1)));auto projected=GeomProjLib::ProjectOnPlane(c,plane,gp_Dir(0,0,1),true);need(!projected.IsNull(),"Curve projection failed");BRepBuilderAPI_MakeEdge edge(projected,a,b);need(edge.IsDone(),"Curve collapsed onto the projection plane");return BRepBuilderAPI_MakeWire(edge.Edge()).Wire();
 }
 if(kind=="Trim patch"||kind=="Untrim patch"){
  TopoDS_Face face;auto b=patch(s[0],face);double u0,u1,v0,v1;b->Bounds(u0,u1,v0,v1);if(kind=="Trim patch"){need(p.size()==4&&p[0]>=0&&p[1]<=1&&p[2]>=0&&p[3]<=1&&p[1]-p[0]>1e-6&&p[3]-p[2]>1e-6,"Patch trim needs uStart uEnd vStart vEnd fractions in [0,1]");double du=u1-u0,dv=v1-v0;u1=u0+du*p[1];u0+=du*p[0];v1=v0+dv*p[3];v0+=dv*p[2];}else need(p.empty(),"Untrim patch takes no parameters");return BRepBuilderAPI_MakeFace(b,u0,u1,v0,v1,1e-6).Face();
 }
 return TopoDS_Shape();
}
std::string surfacePoles(const TopoDS_Shape& s){TopoDS_Face f;auto b=patch(s,f);std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(12)<<"{\"u\":"<<b->NbUPoles()<<",\"v\":"<<b->NbVPoles()<<",\"poles\":[";for(int u=1;u<=b->NbUPoles();u++)for(int v=1;v<=b->NbVPoles();v++){if(u!=1||v!=1)out<<',';auto p=b->Pole(u,v);out<<'['<<p.X()<<','<<p.Y()<<','<<p.Z()<<','<<b->Weight(u,v)<<']';}out<<"]}";return out.str();}
TopoDS_Shape changeSurfacePole(const TopoDS_Shape& s,const std::vector<double>& p){need(p.size()==6,"Pole edit needs uIndex vIndex x y z weight");TopoDS_Face f;auto b=patch(s,f);int u=index(p[0],b->NbUPoles()),v=index(p[1],b->NbVPoles());for(int i=2;i<5;i++)need(std::abs(p[i])<=10000,"Surface pole coordinates exceed 10,000 mm");need(p[5]>=.001&&p[5]<=1000,"Weight must be 0.001 to 1000");double a,z,c,d;b->Bounds(a,z,c,d);double fa,fz,fc,fd;BRepTools::UVBounds(f,fa,fz,fc,fd);need(std::abs(a-fa)<1e-6&&std::abs(z-fz)<1e-6&&std::abs(c-fc)<1e-6&&std::abs(d-fd)<1e-6,"Untrim the patch before editing poles");b->SetPole(u,v,gp_Pnt(p[2],p[3],p[4]),p[5]);return BRepBuilderAPI_MakeFace(b,1e-6).Face();}
std::string curveCurvature(const TopoDS_Shape& s){double a,b;auto c=worldCurve(s,a,b);std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(12)<<"{\"samples\":[";double peak=0;for(int i=0;i<=64;i++){if(i)out<<',';double t=a+(b-a)*i/64;GeomLProp_CLProps props(c,t,2,1e-9);need(props.IsTangentDefined(),"Curvature undefined at a singular curve point");double k=props.Curvature();need(std::isfinite(k),"Curve has singular curvature");peak=std::max(peak,k);out<<'['<<double(i)/64<<','<<k<<']';}out<<"],\"maxCurvature\":"<<peak<<",\"units\":\"1/mm\"}";return out.str();}
#include <BRepClass3d_SolidClassifier.hxx>
#include <GeomAPI_ProjectPointOnSurf.hxx>
#include <GeomLProp_SLProps.hxx>
#include <BRepClass_FaceClassifier.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <IntCurvesFace_ShapeIntersector.hxx>
#include <Poly_Triangulation.hxx>
#include <gp_Lin.hxx>
#include <array>
std::string sampledThickness(const TopoDS_Shape& s,double threshold){
 need(std::isfinite(threshold)&&threshold>=.001&&threshold<=1000,"Thickness threshold must be 0.001 to 1,000 mm");TopTools_IndexedMapOfShape solids;TopExp::MapShapes(s,TopAbs_SOLID,solids);need(solids.Extent()==1,"Thickness sampling requires one closed CAD solid");auto solid=solids(1);BRepMesh_IncrementalMesh mesh(solid,.05,false,.2,false);size_t total=0;for(TopExp_Explorer it(solid,TopAbs_FACE);it.More();it.Next()){TopLoc_Location loc;auto t=BRep_Tool::Triangulation(TopoDS::Face(it.Current()),loc);if(!t.IsNull())total+=t->NbTriangles();}need(total>0&&total<=2000000,"Thickness analysis mesh is empty or too large");size_t stride=std::max(size_t(1),(total+127)/128),index=0,tested=0,valid=0,thin=0;double minimum=1e100,maximum=0;BRepClass3d_SolidClassifier classifier(solid);IntCurvesFace_ShapeIntersector ray;ray.Load(solid,1e-6);
 for(TopExp_Explorer it(solid,TopAbs_FACE);it.More();it.Next()){auto face=TopoDS::Face(it.Current());TopLoc_Location loc;auto t=BRep_Tool::Triangulation(face,loc);if(t.IsNull())continue;for(int i=1;i<=t->NbTriangles();i++,index++){if(index%stride)continue;int a,b,c;t->Triangle(i).Get(a,b,c);auto pa=t->Node(a).Transformed(loc.Transformation()),pb=t->Node(b).Transformed(loc.Transformation()),pc=t->Node(c).Transformed(loc.Transformation());gp_Vec normal=gp_Vec(pa,pb).Crossed(gp_Vec(pa,pc));if(normal.Magnitude()<1e-12)continue;normal.Normalize();gp_Pnt centre((pa.XYZ()+pb.XYZ()+pc.XYZ())/3);TopLoc_Location surfaceLoc;auto localSurface=BRep_Tool::Surface(face,surfaceLoc);if(localSurface.IsNull())continue;auto surface=Handle(Geom_Surface)::DownCast(localSurface->Transformed(surfaceLoc.Transformation()));double ua,ub,va,vb;BRepTools::UVBounds(face,ua,ub,va,vb);GeomAPI_ProjectPointOnSurf projection(centre,surface,ua,ub,va,vb,1e-6);if(!projection.NbPoints())continue;double u,v;projection.LowerDistanceParameters(u,v);BRepClass_FaceClassifier faceClassifier(face,gp_Pnt2d(u,v),1e-6);if(faceClassifier.State()!=TopAbs_IN&&faceClassifier.State()!=TopAbs_ON)continue;GeomLProp_SLProps props(surface,u,v,1,1e-9);if(!props.IsNormalDefined())continue;centre=projection.NearestPoint();normal=gp_Vec(props.Normal());tested++;double best=1e100;for(double sign:{-1.,1.}){gp_Vec direction=normal*sign;auto start=centre.Translated(direction*1e-4);classifier.Perform(start,1e-6);if(classifier.State()!=TopAbs_IN)continue;ray.Perform(gp_Lin(start,gp_Dir(direction)),1e-4,20000);if(!ray.IsDone())continue;for(int hit=1;hit<=ray.NbPnt();hit++)if(ray.WParameter(hit)>1e-4)best=std::min(best,ray.WParameter(hit)+1e-4);}if(best<1e99){valid++;minimum=std::min(minimum,best);maximum=std::max(maximum,best);if(best<threshold)thin++;}}}
 std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(12)<<"{\"attempted\":"<<tested<<",\"valid\":"<<valid<<",\"belowThreshold\":"<<thin<<",\"threshold\":"<<threshold<<",\"minSampled\":"<<(valid?minimum:0)<<",\"maxSampled\":"<<maximum<<",\"approximate\":true}";return out.str();
}
