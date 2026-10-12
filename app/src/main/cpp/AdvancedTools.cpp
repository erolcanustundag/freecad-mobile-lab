// SPDX-License-Identifier: LGPL-2.1-or-later
#include "AdvancedTools.hpp"
#include "JewelleryTools.hpp"
#include "FeatureTools.hpp"
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepPrimAPI_MakeRevol.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeCone.hxx>
#include <BRepOffsetAPI_MakeThickSolid.hxx>
#include <BRepAdaptor_Surface.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <TopTools_ListOfShape.hxx>
#include <Geom_BSplineSurface.hxx>
#include <TColgp_Array2OfPnt.hxx>
#include <TColStd_Array2OfReal.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Section.hxx>
#include <BRepOffsetAPI_MakePipe.hxx>
#include <BRepOffsetAPI_ThruSections.hxx>
#include <BRepOffsetAPI_MakeOffset.hxx>
#include <BRepOffsetAPI_MakeOffsetShape.hxx>
#include <BRepBuilderAPI_Sewing.hxx>
#include <BRepFilletAPI_MakeChamfer.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepCheck_Shell.hxx>
#include <BRepBuilderAPI_MakeSolid.hxx>
#include <BRepLib.hxx>
#include <BRepBndLib.hxx>
#include <BRepGProp.hxx>
#include <BRep_Tool.hxx>
#include <BRep_Builder.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <ShapeFix_Shape.hxx>
#include <GCPnts_QuasiUniformDeflection.hxx>
#include <GeomAPI_Interpolate.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <Geom_Plane.hxx>
#include <GeomConvert.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Compound.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TColgp_HArray1OfPnt.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <TColStd_Array1OfReal.hxx>
#include <TColStd_Array1OfInteger.hxx>
#include <Poly_Triangulation.hxx>
#include <Bnd_Box.hxx>
#include <GProp_GProps.hxx>
#include <gp_Circ.hxx>
#include <gp_Elips.hxx>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Ax3.hxx>
#include <gp_Trsf.hxx>
#include <gp_Pln.hxx>
#include <map>
#include <array>
#include <set>
#include <tuple>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <locale>
#include <cmath>
#include <stdexcept>
#include <algorithm>
#include <queue>
namespace {
void require(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
void count(const std::vector<double>& p,size_t n){require(p.size()==n,"Wrong number of tool parameters");for(double x:p)require(std::isfinite(x)&&std::abs(x)<=1000000,"Invalid tool parameter");}
void size(double x){require(x>=.001&&x<=10000,"Size must be 0.001 to 10000 mm");}
int whole(double x,int low,int high){require(x==std::floor(x)&&x>=low&&x<=high,"Count or subdivision level is out of range");return int(x);}
TopoDS_Wire circular(double radius,double z=0){return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(0,0,z),gp_Dir(0,0,1)),radius)).Edge()).Wire();}
TopoDS_Wire wire(const TopoDS_Shape& s){require(curveShape(s),"Select a curve or closed profile; solid edges are not a profile");if(s.ShapeType()==TopAbs_WIRE)return TopoDS::Wire(s);TopExp_Explorer w(s,TopAbs_WIRE);if(w.More()){auto first=TopoDS::Wire(w.Current());w.Next();require(!w.More(),"Choose a single profile, not an array of profiles");return first;}BRepBuilderAPI_MakeWire b;TopTools_IndexedMapOfShape edges;TopExp::MapShapes(s,TopAbs_EDGE,edges);for(int i=1;i<=edges.Extent();i++)b.Add(TopoDS::Edge(edges(i)));require(b.IsDone(),"Section edges are disconnected; use a single closed profile");return b.Wire();}
TopoDS_Face face(const TopoDS_Shape& s){auto w=wire(s);require(w.Closed(),"Solid creation requires a closed planar profile");BRepBuilderAPI_MakeFace f(w,true);require(f.IsDone(),"Profile must be planar and closed");return f.Face();}
TopoDS_Shape fuse(const TopoDS_Shape& a,const TopoDS_Shape& b){BRepAlgoAPI_Fuse f(a,b);f.Build();require(f.IsDone(),"Jewellery parts could not be joined");return f.Shape();}
TopoDS_Shape cut(const TopoDS_Shape& a,const TopoDS_Shape& b){BRepAlgoAPI_Cut f(a,b);f.Build();require(f.IsDone(),"Jewellery cut failed");return f.Shape();}
TopoDS_Shape meshShape(const std::vector<gp_Pnt>& pts,const std::vector<std::array<int,3>>& tris){require(!pts.empty()&&!tris.empty(),"Mesh has no geometry");auto t=new Poly_Triangulation(int(pts.size()),int(tris.size()),false);for(size_t i=0;i<pts.size();i++)t->SetNode(int(i+1),pts[i]);for(size_t i=0;i<tris.size();i++)t->SetTriangle(int(i+1),Poly_Triangle(tris[i][0]+1,tris[i][1]+1,tris[i][2]+1));TopoDS_Face f;BRep_Builder b;b.MakeFace(f,t);return f;}
TopoDS_Shape repairMesh(const TopoDS_Shape& shape,double tolerance){
 require(tolerance>=1e-6&&tolerance<=.1,"Mesh welding tolerance must be 0.000001 to 0.1 mm");
 size_t sourceCount=0;for(TopExp_Explorer it(shape,TopAbs_FACE);it.More();it.Next()){TopLoc_Location loc;auto t=BRep_Tool::Triangulation(TopoDS::Face(it.Current()),loc);if(!t.IsNull())sourceCount+=t->NbTriangles();}require(sourceCount<=100000,"Mesh repair is limited to 100,000 triangles to bound mobile memory");
 std::vector<gp_Pnt> points;std::vector<std::array<int,3>> triangles;std::map<std::tuple<long long,long long,long long>,int> vertices;std::set<std::array<int,3>> unique;
 auto index=[&](const gp_Pnt& p){auto key=std::make_tuple(std::llround(p.X()/tolerance),std::llround(p.Y()/tolerance),std::llround(p.Z()/tolerance));auto [it,newVertex]=vertices.emplace(key,int(points.size()));if(newVertex)points.push_back(p);return it->second;};
 for(TopExp_Explorer it(shape,TopAbs_FACE);it.More();it.Next()){auto face=TopoDS::Face(it.Current());TopLoc_Location loc;auto t=BRep_Tool::Triangulation(face,loc);if(t.IsNull())continue;for(int i=1;i<=t->NbTriangles();i++){int a,b,c;t->Triangle(i).Get(a,b,c);if(face.Orientation()==TopAbs_REVERSED)std::swap(b,c);std::array<int,3> tri{index(t->Node(a).Transformed(loc.Transformation())),index(t->Node(b).Transformed(loc.Transformation())),index(t->Node(c).Transformed(loc.Transformation()))};if(tri[0]==tri[1]||tri[1]==tri[2]||tri[2]==tri[0])continue;if(gp_Vec(points[tri[0]],points[tri[1]]).Crossed(gp_Vec(points[tri[0]],points[tri[2]])).Magnitude()<1e-12)continue;auto sorted=tri;std::sort(sorted.begin(),sorted.end());if(unique.insert(sorted).second)triangles.push_back(tri);}}
 require(!triangles.empty(),"Mesh has no non-degenerate triangles");using Link=std::pair<int,bool>;std::map<std::pair<int,int>,std::vector<Link>> edges;
 for(size_t i=0;i<triangles.size();i++)for(int j=0;j<3;j++){int a=triangles[i][j],b=triangles[i][(j+1)%3];edges[std::minmax(a,b)].push_back({int(i),a<b});}
 for(auto& [key,links]:edges)require(links.size()<=2,"Mesh has non-manifold edges; repair needs a manifold mesh");std::vector<int> flip(triangles.size(),-1);
 for(size_t seed=0;seed<triangles.size();seed++)if(flip[seed]<0){std::queue<int> q;std::vector<int> component;bool closed=true;flip[seed]=0;q.push(int(seed));while(!q.empty()){int current=q.front();q.pop();component.push_back(current);for(int j=0;j<3;j++){int a=triangles[current][j],b=triangles[current][(j+1)%3];auto& links=edges[std::minmax(a,b)];if(links.size()==1){closed=false;continue;}auto self=links[0].first==current?links[0]:links[1],other=links[0].first==current?links[1]:links[0];int expected=flip[current]^(self.second==other.second);if(flip[other.first]<0){flip[other.first]=expected;q.push(other.first);}else require(flip[other.first]==expected,"Mesh cannot be consistently oriented");}}
 double volume=0;for(int id:component){auto t=triangles[id];if(flip[id])std::swap(t[1],t[2]);volume+=points[t[0]].XYZ().Dot(points[t[1]].XYZ().Crossed(points[t[2]].XYZ()))/6;}for(int id:component)if(flip[id]^(closed&&volume<0))std::swap(triangles[id][1],triangles[id][2]);}
 return meshShape(points,triangles);
}
std::vector<std::array<int,3>> polygonTriangles(const std::vector<int>& indices,const std::vector<gp_Pnt>& points){
 require(indices.size()>=3,"OBJ face needs at least 3 vertices");if(indices.size()==3)return {{indices[0],indices[1],indices[2]}};
 gp_XYZ normal(0,0,0);for(size_t i=0;i<indices.size();i++)normal+=points[indices[i]].XYZ().Crossed(points[indices[(i+1)%indices.size()]].XYZ());require(normal.Modulus()>1e-10,"OBJ polygon is degenerate or self-intersecting");normal.Normalize();auto origin=points[indices[0]];for(int id:indices)require(std::abs((points[id].XYZ()-origin.XYZ()).Dot(normal))<.00001,"Non-planar OBJ polygons must be triangulated before importing");int dropped=std::abs(normal.X())>std::abs(normal.Y())?(std::abs(normal.X())>std::abs(normal.Z())?0:2):(std::abs(normal.Y())>std::abs(normal.Z())?1:2);
 auto xy=[&](int id){auto p=points[id];return dropped==0?std::pair<double,double>{p.Y(),p.Z()}:dropped==1?std::pair<double,double>{p.X(),p.Z()}:std::pair<double,double>{p.X(),p.Y()};};
 auto cross=[&](int a,int b,int c){auto pa=xy(a),pb=xy(b),pc=xy(c);return (pb.first-pa.first)*(pc.second-pa.second)-(pb.second-pa.second)*(pc.first-pa.first);};double area=0;for(size_t i=0;i<indices.size();i++){auto a=xy(indices[i]),b=xy(indices[(i+1)%indices.size()]);area+=a.first*b.second-a.second*b.first;}double sign=area>0?1:-1;require(std::abs(area)>1e-12,"OBJ polygon has zero area");std::vector<int> remaining=indices;std::vector<std::array<int,3>> out;
 while(remaining.size()>3){bool clipped=false;for(size_t i=0;i<remaining.size();i++){int a=remaining[(i+remaining.size()-1)%remaining.size()],b=remaining[i],c=remaining[(i+1)%remaining.size()];if(cross(a,b,c)*sign<=1e-12)continue;bool inside=false;for(int id:remaining)if(id!=a&&id!=b&&id!=c&&cross(a,b,id)*sign>=-1e-12&&cross(b,c,id)*sign>=-1e-12&&cross(c,a,id)*sign>=-1e-12){inside=true;break;}if(inside)continue;out.push_back({a,b,c});remaining.erase(remaining.begin()+i);clipped=true;break;}require(clipped,"OBJ polygon could not be triangulated; check duplicate vertices or self-intersections");}out.push_back({remaining[0],remaining[1],remaining[2]});return out;
}
TopoDS_Shape subdivision(const std::vector<double>& p){
 count(p,6);for(int i=0;i<3;i++)size(p[i]);int levels=whole(p[3],1,4);require(p[4]>=.1&&p[4]<=3,"Top scale must be 0.1 to 3");require(std::abs(p[5])<=180,"Cage twist must be within +/- 180 degrees");
 std::vector<gp_Pnt> v;for(int z=0;z<2;z++)for(auto xy:std::vector<std::array<int,2>>{{-1,-1},{1,-1},{1,1},{-1,1}}){double x=xy[0]*p[0]/2,y=xy[1]*p[1]/2,a=z*p[5]*M_PI/180,scale=z?p[4]:1;v.emplace_back(scale*(x*std::cos(a)-y*std::sin(a)),scale*(x*std::sin(a)+y*std::cos(a)),z*p[2]);}
 std::vector<std::vector<int>> faces{{0,3,2,1},{4,5,6,7},{0,1,5,4},{1,2,6,5},{2,3,7,6},{3,0,4,7}};
 for(int iteration=0;iteration<levels;iteration++){
  struct Edge {int a,b,index=-1;std::vector<int> fs;};std::map<std::pair<int,int>,Edge> edges;std::vector<gp_XYZ> fp;std::vector<std::vector<int>> vf(v.size());
  for(size_t fi=0;fi<faces.size();fi++){gp_XYZ sum(0,0,0);for(int x:faces[fi]){sum+=v[x].XYZ();vf[x].push_back(int(fi));}fp.push_back(sum/double(faces[fi].size()));for(size_t k=0;k<faces[fi].size();k++){int a=faces[fi][k],b=faces[fi][(k+1)%faces[fi].size()];auto key=std::minmax(a,b);auto& edge=edges[key];edge.a=key.first;edge.b=key.second;edge.fs.push_back(int(fi));}}
  std::vector<gp_Pnt> next(v.size());for(size_t i=0;i<v.size();i++){gp_XYZ f(0,0,0),r(0,0,0);int n=0;for(int fi:vf[i])f+=fp[fi];for(auto& [key,e]:edges)if(e.a==int(i)||e.b==int(i)){r+=(v[e.a].XYZ()+v[e.b].XYZ())/2;n++;}require(n>=3,"Invalid subdivision cage");next[i]=gp_Pnt((f/double(vf[i].size())+r*(2./n)+v[i].XYZ()*(n-3))/n);}
  for(auto& [key,e]:edges){require(e.fs.size()==2,"Subdivision cage must be closed");e.index=int(next.size());next.emplace_back((v[e.a].XYZ()+v[e.b].XYZ()+fp[e.fs[0]]+fp[e.fs[1]])/4);}
  std::vector<int> faceIds;for(auto& f:fp){faceIds.push_back(int(next.size()));next.emplace_back(f);}std::vector<std::vector<int>> nf;
  for(size_t fi=0;fi<faces.size();fi++)for(size_t k=0;k<faces[fi].size();k++){int a=faces[fi][k],b=faces[fi][(k+1)%faces[fi].size()],c=faces[fi][(k+faces[fi].size()-1)%faces[fi].size()];nf.push_back({a,edges[std::minmax(a,b)].index,faceIds[fi],edges[std::minmax(c,a)].index});}
  v=std::move(next);faces=std::move(nf);
 }
 std::vector<std::array<int,3>> tris;for(auto& f:faces){tris.push_back({f[0],f[1],f[2]});tris.push_back({f[0],f[2],f[3]});}return meshShape(v,tris);
}
}
bool curveShape(const TopoDS_Shape& s){return !s.IsNull()&&!TopExp_Explorer(s,TopAbs_FACE).More()&&TopExp_Explorer(s,TopAbs_EDGE).More();}
bool advancedMeshPrimitive(const std::string& kind){return kind=="Subdivision form";}
TopoDS_Shape pointCurve(const std::string& kind,const std::vector<double>& p,bool closed){
 require(p.size()%4==0&&p.size()>=8&&p.size()<=256,"Enter 2 to 64 points, each with X Y Z weight");int n=int(p.size()/4);
 for(int i=0;i<n;i++){for(int j=0;j<3;j++)require(std::isfinite(p[i*4+j])&&std::abs(p[i*4+j])<=10000,"Curve coordinates exceed 10,000 mm");require(std::isfinite(p[i*4+3])&&p[i*4+3]>=.001&&p[i*4+3]<=1000,"NURBS weights must be 0.001 to 1000");if(i)require(gp_Pnt(p[i*4],p[i*4+1],p[i*4+2]).Distance(gp_Pnt(p[(i-1)*4],p[(i-1)*4+1],p[(i-1)*4+2]))>1e-6,"Consecutive curve points must differ");}
 if(kind=="Polyline"){BRepBuilderAPI_MakePolygon b;for(int i=0;i<n;i++)b.Add(gp_Pnt(p[i*4],p[i*4+1],p[i*4+2]));if(closed){require(n>=3,"Closed polyline needs at least 3 points");b.Close();}require(b.IsDone(),"Invalid polyline");return b.Wire();}
 Handle(Geom_BSplineCurve) curve;
 if(kind=="Interpolated curve") {require(n>=3,"Interpolation needs at least 3 points");auto pts=new TColgp_HArray1OfPnt(1,n);for(int i=0;i<n;i++)pts->SetValue(i+1,gp_Pnt(p[i*4],p[i*4+1],p[i*4+2]));GeomAPI_Interpolate b(pts,closed,1e-6);b.Perform();require(b.IsDone(),"Spline interpolation failed");curve=b.Curve();}
 else {require(kind=="NURBS curve","Unknown curve kind");require(!closed,"For closed freeform curves choose Interpolated curve or Polyline");int degree=std::min(3,n-1),nk=n-degree+1;TColgp_Array1OfPnt poles(1,n);TColStd_Array1OfReal weights(1,n),knots(1,nk);TColStd_Array1OfInteger mults(1,nk);for(int i=1;i<=n;i++){poles(i)=gp_Pnt(p[(i-1)*4],p[(i-1)*4+1],p[(i-1)*4+2]);weights(i)=p[(i-1)*4+3];}for(int i=1;i<=nk;i++){knots(i)=double(i-1)/(nk-1);mults(i)=(i==1||i==nk)?degree+1:1;}curve=new Geom_BSplineCurve(poles,weights,knots,mults,degree,false);}
 return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(curve).Edge()).Wire();
}
TopoDS_Shape advancedPrimitive(const std::string& kind,const std::vector<double>& p){
 if(jewelleryType(kind))return jewelleryPrimitive(kind,p);
 if(kind=="NURBS patch"){count(p,3);size(p[0]);size(p[1]);require(std::abs(p[2])<=10000,"Control-point bulge exceeds 10,000 mm");TColgp_Array2OfPnt poles(1,3,1,3);TColStd_Array2OfReal weights(1,3,1,3);for(int u=1;u<=3;u++)for(int v=1;v<=3;v++){poles(u,v)=gp_Pnt((u-2)*p[0]/2,(v-2)*p[1]/2,u==2&&v==2?p[2]:0);weights(u,v)=1;}TColStd_Array1OfReal knots(1,2);knots(1)=0;knots(2)=1;TColStd_Array1OfInteger mults(1,2);mults(1)=mults(2)=3;auto surface=new Geom_BSplineSurface(poles,weights,knots,knots,mults,mults,2,2);return BRepBuilderAPI_MakeFace(surface,1e-6).Face();}
 if(kind=="Gemstone cutter"){count(p,3);for(double x:p)size(x);auto cone=BRepPrimAPI_MakeCone(.001,p[0]/2,p[1]).Shape();auto girdle=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,0,p[1]),gp_Dir(0,0,1)),p[0]/2,p[2]).Shape();return fuse(cone,girdle);}
 if(kind=="Circle"){count(p,1);size(p[0]);return circular(p[0]);}
 if(kind=="Ellipse"){count(p,2);size(p[0]);size(p[1]);require(p[0]>=p[1],"X radius must be at least Y radius");return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Elips(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(0,0,1)),p[0],p[1])).Edge()).Wire();}
 if(kind=="Rectangle"){count(p,2);size(p[0]);size(p[1]);BRepBuilderAPI_MakePolygon b;b.Add(gp_Pnt(-p[0]/2,-p[1]/2,0));b.Add(gp_Pnt(p[0]/2,-p[1]/2,0));b.Add(gp_Pnt(p[0]/2,p[1]/2,0));b.Add(gp_Pnt(-p[0]/2,p[1]/2,0));b.Close();return b.Wire();}
 if(kind=="Helix"){count(p,3);size(p[0]);size(p[1]);require(p[2]>=.1&&p[2]<=20,"Helix turns must be 0.1 to 20");int n=std::max(16,int(std::ceil(p[2]*24)));auto pts=new TColgp_HArray1OfPnt(1,n+1);for(int i=0;i<=n;i++){double t=double(i)/n,a=t*p[2]*2*M_PI;pts->SetValue(i+1,gp_Pnt(p[0]*std::cos(a),p[0]*std::sin(a),t*p[1]*p[2]));}GeomAPI_Interpolate b(pts,false,1e-6);b.Perform();require(b.IsDone(),"Helix approximation failed");return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(b.Curve()).Edge()).Wire();}
 if(kind=="Bezel setting"||kind=="Prong setting"){
  count(p,kind=="Bezel setting"?4:6);for(int i=0;i<4;i++)size(p[i]);double bore=p[0]/2,wall=p[1],h=p[2],seat=p[3];require(seat<h,"Seat depth must be less than setting height");
  auto outer=BRepPrimAPI_MakeCylinder(bore+wall,h).Shape();auto hole=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,0,h-seat),gp_Dir(0,0,1)),bore,seat+1).Shape();auto lower=BRepPrimAPI_MakeCylinder(std::max(.01,bore-wall*.6),h+1).Shape();auto base=cut(cut(outer,hole),lower);
  if(kind=="Bezel setting")return base;
  int n=whole(p[4],3,12);size(p[5]);require(p[5]<p[0],"Prong diameter must be smaller than stone diameter");
  // Lower gallery and cylinders overlap to form an actual joined solid.
  base=cut(BRepPrimAPI_MakeCylinder(bore+wall,h-seat).Shape(),BRepPrimAPI_MakeCylinder(std::max(.01,bore-wall*.6),h+1).Shape());
  for(int i=0;i<n;i++){double a=i*2*M_PI/n,r=bore+wall*.35;auto prong=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(r*std::cos(a),r*std::sin(a),0),gp_Dir(0,0,1)),p[5]/2,h).Shape();base=fuse(base,prong);}return base;
 }
 if(kind=="Subdivision form")return subdivision(p);
 throw std::runtime_error("Unsupported primitive");
}
TopoDS_Shape advancedModel(const std::string& kind,const std::vector<TopoDS_Shape>& shapes,const std::vector<double>& p){
 require(!shapes.empty(),"Select an input object");auto s=shapes[0];
 if(kind=="Repair mesh"){count(p,1);require(shapes.size()==1,"Mesh repair accepts one input");return repairMesh(s,p[0]);}
 if(kind=="Extrude solid"||kind=="Extrude surface"){count(p,3);gp_Vec v(p[0],p[1],p[2]);require(v.Magnitude()>=.001&&v.Magnitude()<=10000,"Extrusion vector must be 0.001 to 10000 mm");return BRepPrimAPI_MakePrism(kind=="Extrude solid"?TopoDS_Shape(face(s)):TopoDS_Shape(wire(s)),v).Shape();}
 if(kind=="Revolve solid"||kind=="Revolve surface"){count(p,7);gp_Vec v(p[3],p[4],p[5]);require(v.Magnitude()>1e-9,"Revolve axis cannot be zero");require(p[6]>.01&&p[6]<=360,"Revolve angle must be 0.01 to 360 degrees");return BRepPrimAPI_MakeRevol(kind=="Revolve solid"?TopoDS_Shape(face(s)):TopoDS_Shape(wire(s)),gp_Ax1(gp_Pnt(p[0],p[1],p[2]),gp_Dir(v)),p[6]*M_PI/180,true).Shape();}
 if(kind=="Loft solid"||kind=="Loft surface"){count(p,1);require(shapes.size()>=2&&shapes.size()<=8,"Loft needs 2 to 8 profiles");BRepOffsetAPI_ThruSections loft(kind=="Loft solid",p[0]!=0,1e-6);loft.CheckCompatibility(true);for(const auto& shape:shapes)loft.AddWire(wire(shape));loft.Build();require(loft.IsDone(),"Loft failed; use matching profiles at different positions");return loft.Shape();}
 if(kind=="Sweep solid"||kind=="Sweep surface"){count(p,0);require(shapes.size()==2,"Sweep needs a profile and a rail");auto rail=wire(shapes[1]);BRepOffsetAPI_MakePipe pipe(rail,kind=="Sweep solid"?TopoDS_Shape(face(s)):TopoDS_Shape(wire(s)));pipe.Build();require(pipe.IsDone(),"Sweep failed; place the profile at the start of a smooth rail, perpendicular to its tangent");return pipe.Shape();}
 if(kind=="Pipe along curve"){count(p,1);size(p[0]);auto rail=wire(s);BRepAdaptor_Curve c(TopoDS::Edge(TopExp_Explorer(rail,TopAbs_EDGE).Current()));gp_Pnt start;gp_Vec tangent;c.D1(c.FirstParameter(),start,tangent);require(tangent.Magnitude()>1e-9,"Rail has no starting tangent");auto profile=BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(start,gp_Dir(tangent)),p[0])).Edge()).Wire();BRepOffsetAPI_MakePipe pipe(rail,BRepBuilderAPI_MakeFace(profile).Face());pipe.Build();require(pipe.IsDone(),"Pipe failed; try a smaller radius or a smoother rail");return pipe.Shape();}
 if(kind=="Section"){count(p,7);gp_Vec v(p[3],p[4],p[5]);require(v.Magnitude()>1e-9,"Section plane normal cannot be zero");BRepAlgoAPI_Section section(s,gp_Pln(gp_Pnt(p[0],p[1],p[2]),gp_Dir(v)),false);section.Approximation(true);section.Build();require(section.IsDone()&&TopExp_Explorer(section.Shape(),TopAbs_EDGE).More(),"Plane does not intersect the CAD object");auto result=section.Shape();if(p[6]!=0){gp_Trsf t;t.SetTransformation(gp_Ax3(gp_Pnt(p[0],p[1],p[2]),gp_Dir(v)));result=BRepBuilderAPI_Transform(result,t,true).Shape();}return result;}
 if(kind=="Offset curve"){count(p,1);require(std::abs(p[0])>=.001&&std::abs(p[0])<=1000,"Offset must be 0.001 to 1000 mm in magnitude");BRepOffsetAPI_MakeOffset offset(wire(s),GeomAbs_Arc);offset.Perform(p[0]);require(offset.IsDone(),"Planar curve offset failed");return offset.Shape();}
 if(kind=="Offset shape"){count(p,1);require(std::abs(p[0])>=.001&&std::abs(p[0])<=1000,"Offset must be 0.001 to 1000 mm in magnitude");BRepOffsetAPI_MakeOffsetShape off;off.PerformByJoin(s,p[0],1e-5);require(off.IsDone(),"Shape offset failed; try a smaller distance");return off.Shape();}
 if(kind=="Chamfer"){count(p,1);size(p[0]);BRepFilletAPI_MakeChamfer b(s);TopTools_IndexedMapOfShape edges;TopExp::MapShapes(s,TopAbs_EDGE,edges);for(int i=1;i<=edges.Extent();i++)b.Add(p[0],TopoDS::Edge(edges(i)));b.Build();require(b.IsDone(),"Chamfer failed; try a smaller distance");return b.Shape();}
 if(kind=="Hollow top"){count(p,1);size(p[0]);TopoDS_Face top;double highest=-1e100;for(TopExp_Explorer it(s,TopAbs_FACE);it.More();it.Next()){auto f=TopoDS::Face(it.Current());BRepAdaptor_Surface surface(f);if(surface.GetType()!=GeomAbs_Plane||std::abs(surface.Plane().Axis().Direction().Z())<.999999)continue;GProp_GProps props;BRepGProp::SurfaceProperties(f,props);if(props.CentreOfMass().Z()>highest){highest=props.CentreOfMass().Z();top=f;}}require(!top.IsNull(),"Hollow top needs a solid with a horizontal planar top face");TopTools_ListOfShape removed;removed.Append(top);BRepOffsetAPI_MakeThickSolid hollow;hollow.MakeThickSolidByJoin(s,removed,-p[0],1e-5);require(hollow.IsDone(),"Hollowing failed; reduce wall thickness or simplify the body");return hollow.Shape();}
 if(kind=="Heal CAD"){count(p,1);size(p[0]);ShapeFix_Shape fix(s);fix.SetPrecision(p[0]);fix.SetMaxTolerance(p[0]);fix.Perform();return fix.Shape();}
 if(kind=="Sew surfaces"){count(p,1);require(p[0]>=1e-6&&p[0]<=1,"Sewing tolerance must be 0.000001 to 1 mm");BRepBuilderAPI_Sewing sew(p[0]);for(const auto& shape:shapes)sew.Add(shape);sew.Perform();require(!sew.SewedShape().IsNull(),"Surface sewing failed");return sew.SewedShape();}
 if(kind=="Solidify shell"){count(p,0);TopExp_Explorer shells(s,TopAbs_SHELL);require(shells.More(),"Input has no shell; sew the surfaces first");auto shell=TopoDS::Shell(shells.Current());shells.Next();require(!shells.More(),"Solidify accepts one closed shell");require(BRepCheck_Shell(shell).Closed()==BRepCheck_NoError,"Shell is open; join or cap its boundary edges first");auto solid=BRepBuilderAPI_MakeSolid(shell).Solid();require(BRepLib::OrientClosedSolid(solid),"Could not orient the closed solid");return solid;}
 auto detail=detailModel(kind,shapes,p);if(!detail.IsNull())return detail;
 throw std::runtime_error("Unknown modelling tool");
}
std::vector<std::vector<gp_Pnt>> sampleEdges(const TopoDS_Shape& s,double tolerance){
 std::vector<std::vector<gp_Pnt>> out;TopTools_IndexedMapOfShape edges;TopExp::MapShapes(s,TopAbs_EDGE,edges);require(edges.Extent()<=2000,"Drawing has too many edges for mobile export");size_t total=0;
 for(int i=1;i<=edges.Extent();i++){BRepAdaptor_Curve c(TopoDS::Edge(edges(i)));double a=c.FirstParameter(),b=c.LastParameter();if(!std::isfinite(a)||!std::isfinite(b))continue;GCPnts_QuasiUniformDeflection d(c,tolerance,a,b);int n=d.IsDone()?std::min(d.NbPoints(),1000):96;std::vector<gp_Pnt> pts;for(int k=0;k<n;k++)pts.push_back(d.IsDone()&&d.NbPoints()<=1000?d.Value(k+1):c.Value(a+(b-a)*k/(n-1)));total+=pts.size();require(total<=40000,"Drawing has too many sampled points");out.push_back(std::move(pts));}return out;
}
void exportDrawing(const TopoDS_Shape& s,const std::string& path,const std::string& format){
 require(curveShape(s),"SVG/DXF export needs curves or a Section result; project onto the XY plane first");auto edges=sampleEdges(s,.005);double x0=1e100,y0=x0,x1=-x0,y1=x1;for(auto& line:edges)for(auto& p:line){require(std::abs(p.Z())<.0001,"Drawing export requires an XY profile at Z=0. Move or rotate the section first.");x0=std::min(x0,p.X());x1=std::max(x1,p.X());y0=std::min(y0,p.Y());y1=std::max(y1,p.Y());}std::ofstream f(path);require(bool(f),"Cannot write drawing");f.imbue(std::locale::classic());f<<std::setprecision(12);
 if(format=="svg"){double w=std::max(.01,x1-x0),h=std::max(.01,y1-y0);f<<"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\""<<w<<"mm\" height=\""<<h<<"mm\" viewBox=\""<<x0<<' '<<-y1<<' '<<w<<' '<<h<<"\"><g fill=\"none\" stroke=\"black\" stroke-width=\"0.05\">";for(auto& line:edges){f<<"<polyline points=\"";for(auto& p:line)f<<p.X()<<','<<-p.Y()<<' ';f<<"\"/>";}f<<"</g></svg>";}
 else{f<<"0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n";for(auto& line:edges)for(size_t i=1;i<line.size();i++)f<<"0\nLINE\n8\n0\n10\n"<<line[i-1].X()<<"\n20\n"<<line[i-1].Y()<<"\n30\n0\n11\n"<<line[i].X()<<"\n21\n"<<line[i].Y()<<"\n31\n0\n";f<<"0\nENDSEC\n0\nEOF\n";}require(bool(f),"Drawing export failed");
}
void writeObj(const TopoDS_Shape& s,const std::string& path,double tolerance){
 BRepMesh_IncrementalMesh m(s,tolerance,false,.50,false);std::ofstream f(path);require(bool(f),"Cannot write OBJ");f.imbue(std::locale::classic());f<<std::setprecision(12)<<"# FreeCAD Mobile Lab; millimetres\n";int offset=0;size_t triangles=0;
 for(TopExp_Explorer it(s,TopAbs_FACE);it.More();it.Next()){auto face=TopoDS::Face(it.Current());TopLoc_Location loc;auto t=BRep_Tool::Triangulation(face,loc);if(t.IsNull())continue;triangles+=t->NbTriangles();require(triangles<=2000000,"OBJ exceeds 2,000,000 triangles");for(int i=1;i<=t->NbNodes();i++){auto p=t->Node(i).Transformed(loc.Transformation());f<<"v "<<p.X()<<' '<<p.Y()<<' '<<p.Z()<<'\n';}for(int i=1;i<=t->NbTriangles();i++){int a,b,c;t->Triangle(i).Get(a,b,c);if(face.Orientation()==TopAbs_REVERSED)std::swap(b,c);f<<"f "<<a+offset<<' '<<b+offset<<' '<<c+offset<<'\n';}offset+=t->NbNodes();}require(triangles>0,"OBJ export needs surfaces or a mesh");require(bool(f),"OBJ export failed");
}
TopoDS_Shape readObj(const std::string& path){
 std::ifstream f(path,std::ios::ate);require(bool(f),"Cannot open OBJ");require(f.tellg()<=256*1024*1024,"OBJ exceeds 256 MiB");f.seekg(0);std::vector<gp_Pnt> pts;std::vector<std::array<int,3>> tris;char buffer[65537];
 while(f.getline(buffer,sizeof(buffer))){std::string line(buffer);std::istringstream s(line);s.imbue(std::locale::classic());std::string kind;s>>kind;if(kind=="v"){double x,y,z;require(bool(s>>x>>y>>z),"Invalid OBJ vertex");for(double d:{x,y,z})require(std::isfinite(d)&&std::abs(d)<=1000000,"Invalid OBJ coordinates");require(pts.size()<2000000,"OBJ has too many vertices");pts.emplace_back(x,y,z);}else if(kind=="f"){std::vector<int> indices;std::string token;while(s>>token){require(indices.size()<256,"OBJ polygon has too many vertices");auto n=token.substr(0,token.find('/'));size_t consumed=0;long k=std::stol(n,&consumed);require(consumed==n.size()&&k!=0,"Invalid OBJ face index");long index=k>0?k-1:long(pts.size())+k;require(index>=0&&size_t(index)<pts.size(),"OBJ face index is out of range");indices.push_back(int(index));}require(indices.size()>=3,"OBJ face needs 3 vertices");for(auto triangle:polygonTriangles(indices,pts)){require(tris.size()<2000000,"OBJ exceeds 2,000,000 triangles");tris.push_back(triangle);}}}
 require(f.eof(),"OBJ line is too long or the file could not be read");return meshShape(pts,tris);
}
std::string inspectShape(const TopoDS_Shape& s,bool meshOnly,double draft){
 require(std::isfinite(draft)&&draft>=0&&draft<=89,"Draft threshold must be 0 to 89 degrees");GProp_GProps volume,area,length;BRepGProp::VolumeProperties(s,volume);BRepGProp::SurfaceProperties(s,area);BRepGProp::LinearProperties(s,length);TopTools_IndexedMapOfShape faces,edges,solids;TopExp::MapShapes(s,TopAbs_FACE,faces);TopExp::MapShapes(s,TopAbs_EDGE,edges);TopExp::MapShapes(s,TopAbs_SOLID,solids);
 BRepMesh_IncrementalMesh m(s,.025,false,.13,false);using Key=std::tuple<long long,long long,long long>;std::map<Key,int> vertices;std::map<std::pair<int,int>,int> uses;size_t triangles=0,degenerate=0;double meshVolume=0,meshArea=0,nearVertical=0;
 size_t total=0;for(TopExp_Explorer it(s,TopAbs_FACE);it.More();it.Next()){TopLoc_Location loc;auto t=BRep_Tool::Triangulation(TopoDS::Face(it.Current()),loc);if(!t.IsNull())total+=t->NbTriangles();}bool topologyChecked=total<=100000;
 auto index=[&](const gp_Pnt& p){Key k{std::llround(p.X()*100000),std::llround(p.Y()*100000),std::llround(p.Z()*100000)};auto [it,inserted]=vertices.emplace(k,int(vertices.size()));return it->second;};
 for(TopExp_Explorer it(s,TopAbs_FACE);it.More();it.Next()){auto face=TopoDS::Face(it.Current());TopLoc_Location loc;auto t=BRep_Tool::Triangulation(face,loc);if(t.IsNull())continue;require(triangles+size_t(t->NbTriangles())<=2000000,"Analysis exceeds mobile triangle limit");for(int i=1;i<=t->NbTriangles();i++){int a,b,c;t->Triangle(i).Get(a,b,c);if(face.Orientation()==TopAbs_REVERSED)std::swap(b,c);auto pa=t->Node(a).Transformed(loc.Transformation()),pb=t->Node(b).Transformed(loc.Transformation()),pc=t->Node(c).Transformed(loc.Transformation());auto n=gp_Vec(pa,pb).Crossed(gp_Vec(pa,pc));double ar=n.Magnitude()/2;triangles++;if(ar<1e-12){degenerate++;continue;}meshArea+=ar;if(std::abs(n.Z())/n.Magnitude()<std::sin(draft*M_PI/180))nearVertical+=ar;meshVolume+=pa.XYZ().Dot(pb.XYZ().Crossed(pc.XYZ()))/6;if(topologyChecked){int x=index(pa),y=index(pb),z=index(pc);for(auto e:std::vector<std::pair<int,int>>{{x,y},{y,z},{z,x}})uses[std::minmax(e.first,e.second)]++;}}}
 size_t boundary=0,nonmanifold=0;for(auto& [edge,n]:uses){if(n==1)boundary++;else if(n!=2)nonmanifold++;}std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(9)<<"{\"validCAD\":"<<(!meshOnly&&BRepCheck_Analyzer(s).IsValid()?"true":"false")<<",\"solids\":"<<solids.Extent()<<",\"faces\":"<<faces.Extent()<<",\"edges\":"<<edges.Extent()<<",\"volume\":"<<(meshOnly?std::abs(meshVolume):solids.Extent()?std::abs(volume.Mass()):0)<<",\"area\":"<<(meshOnly?meshArea:area.Mass())<<",\"length\":"<<length.Mass()<<",\"triangles\":"<<triangles<<",\"boundaryEdges\":"<<boundary<<",\"nonManifoldEdges\":"<<nonmanifold<<",\"degenerateTriangles\":"<<degenerate<<",\"topologyChecked\":"<<(topologyChecked?"true":"false")<<",\"watertightMesh\":"<<(topologyChecked&&triangles&&boundary==0&&nonmanifold==0&&degenerate==0?"true":"false")<<",\"draftNearVerticalAreaPercent\":"<<(meshArea?nearVertical*100/meshArea:0)<<",\"draftDegrees\":"<<draft<<"}";return out.str();
}
