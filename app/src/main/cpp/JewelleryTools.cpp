// SPDX-License-Identifier: LGPL-2.1-or-later
#include "JewelleryTools.hpp"
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepPrimAPI_MakeRevol.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAdaptor_CompCurve.hxx>
#include <GCPnts_UniformAbscissa.hxx>
#include <BRep_Builder.hxx>
#include <BRepBndLib.hxx>
#include <Bnd_Box.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Compound.hxx>
#include <gp_Elips.hxx>
#include <gp_Circ.hxx>
#include <gp_Ax1.hxx>
#include <gp_Trsf.hxx>
#include <cmath>
#include <algorithm>
#include <stdexcept>
namespace {
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
void dims(const std::vector<double>& p,size_t n){need(p.size()==n,"Wrong number of jewellery dimensions");for(double x:p)need(std::isfinite(x)&&x>=.001&&x<=10000,"Jewellery dimensions must be 0.001 to 10000 mm");}
TopoDS_Shape cut(const TopoDS_Shape&a,const TopoDS_Shape&b){BRepAlgoAPI_Cut op(a,b);op.Build();need(op.IsDone(),"Jewellery cut failed");return op.Shape();}
TopoDS_Shape fuse(const TopoDS_Shape&a,const TopoDS_Shape&b){BRepAlgoAPI_Fuse op(a,b);op.Build();need(op.IsDone(),"Jewellery join failed");return op.Shape();}
TopoDS_Wire ellipse(double w,double d,double x=0,double y=0){gp_Ax2 axes(gp_Pnt(x,y,0),gp_Dir(0,0,1),gp_Dir(w>=d?1:0,w>=d?0:1,0));return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(gp_Elips(axes,std::max(w,d)/2,std::min(w,d)/2))).Wire();}
TopoDS_Wire rectangle(double w,double d,double r){if(r<1e-5){BRepBuilderAPI_MakePolygon b;b.Add(gp_Pnt(-w/2,-d/2,0));b.Add(gp_Pnt(w/2,-d/2,0));b.Add(gp_Pnt(w/2,d/2,0));b.Add(gp_Pnt(-w/2,d/2,0));b.Close();return b.Wire();}need(r<std::min(w,d)/2,"Corner radius must be smaller than half the narrow side");BRepBuilderAPI_MakeWire b;
 auto line=[&](double a,double c,double x,double y){if(std::hypot(x-a,y-c)>1e-8)b.Add(BRepBuilderAPI_MakeEdge(gp_Pnt(a,c,0),gp_Pnt(x,y,0)).Edge());};
 auto arc=[&](double x,double y,double a){b.Add(BRepBuilderAPI_MakeEdge(gp_Circ(gp_Ax2(gp_Pnt(x,y,0),gp_Dir(0,0,1)),r),a,a+M_PI/2).Edge());};
 line(-w/2+r,-d/2,w/2-r,-d/2);arc(w/2-r,-d/2+r,-M_PI/2);line(w/2,-d/2+r,w/2,d/2-r);arc(w/2-r,d/2-r,0);line(w/2-r,d/2,-w/2+r,d/2);arc(-w/2+r,d/2-r,M_PI/2);line(-w/2,d/2-r,-w/2,-d/2+r);arc(-w/2+r,-d/2+r,M_PI);need(b.IsDone(),"Rounded profile failed");return b.Wire();}
TopoDS_Shape pad(const TopoDS_Wire&w,double h,double z=0){auto s=BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(w,true).Face(),gp_Vec(0,0,h)).Shape();if(z!=0){gp_Trsf t;t.SetTranslation(gp_Vec(0,0,z));s=BRepBuilderAPI_Transform(s,t).Shape();}return s;}
TopoDS_Shape band(double inner,double wall,double width){return cut(BRepPrimAPI_MakeCylinder(inner/2+wall,width).Shape(),BRepPrimAPI_MakeCylinder(inner/2,width).Shape());}
double area(const std::vector<gp_Pnt>& p){double a=0;for(size_t i=0;i<p.size();i++){const auto& q=p[(i+1)%p.size()];a+=p[i].X()*q.Y()-q.X()*p[i].Y();}return a/2;}
bool inside(const gp_Pnt&q,const std::vector<gp_Pnt>& p){bool in=false;for(size_t i=0,j=p.size()-1;i<p.size();j=i++){auto a=p[i],b=p[j];if((a.Y()>q.Y())!=(b.Y()>q.Y())&&q.X()<(b.X()-a.X())*(q.Y()-a.Y())/(b.Y()-a.Y())+a.X())in=!in;}return in;}
TopoDS_Wire polygon(std::vector<gp_Pnt> p,bool outer){if((area(p)>0)!=outer)std::reverse(p.begin(),p.end());BRepBuilderAPI_MakePolygon b;for(auto q:p)b.Add(q);b.Close();need(b.IsDone(),"Text contour has invalid segments");return b.Wire();}
}
bool jewelleryType(const std::string& k){return k=="Oval bezel"||k=="Rectangle bezel"||k=="Cushion bezel"||k=="Oval prongs"||k=="Comfort ring"||k=="Signet ring"||k=="Pendant frame"||k=="Bangle";}
TopoDS_Shape jewelleryPrimitive(const std::string& k,const std::vector<double>& p){
 if(k=="Oval bezel"||k=="Rectangle bezel"||k=="Cushion bezel"||k=="Oval prongs"){
  bool prong=k=="Oval prongs",oval=k=="Oval bezel"||prong;dims(p,prong?7:k=="Cushion bezel"?6:5);double w=p[0],d=p[1],wall=p[2],h=p[3],seat=p[4],r=k=="Cushion bezel"?p[5]:0;need(seat<h&&wall<std::min(w,d)/3,"Seat must be shallower than height, and wall smaller than the stone");
  auto profile=[&](double a,double b,double corner){return oval?ellipse(a,b):rectangle(a,b,corner);};
  auto outer=pad(profile(w+2*wall,d+2*wall,r>0?r+wall:0),h);auto aperture=pad(profile(w-wall,d-wall,r>0?std::max(.001,r-wall/2):0),h);auto base=cut(outer,aperture);base=cut(base,pad(profile(w,d,r),seat,h-seat));
  if(!prong)return base;int count=int(p[5]);need(p[5]==count&&count>=3&&count<=16,"Prong count must be 3 to 16");need(p[6]<std::min(w,d)/2,"Prong diameter is too large");base=cut(base,pad(ellipse(w+2*wall+.2,d+2*wall+.2),seat*.85,h-seat*.85));
  for(int i=0;i<count;i++){double a=2*M_PI*i/count;gp_Ax2 axis(gp_Pnt((w/2+wall*.45)*std::cos(a),(d/2+wall*.45)*std::sin(a),h-seat-.1),gp_Dir(0,0,1));base=fuse(base,BRepPrimAPI_MakeCylinder(axis,p[6]/2,seat+.1).Shape());}return base;
 }
 if(k=="Comfort ring"){dims(p,4);double r=p[0]/2,t=p[1],w=p[2],bevel=p[3];need(bevel<std::min(t,w)/2,"Comfort bevel is too large");BRepBuilderAPI_MakePolygon b;for(auto q:std::vector<gp_Pnt>{{r+bevel,0,0},{r+t,0,0},{r+t,0,w},{r+bevel,0,w},{r,0,w-bevel},{r,0,bevel}})b.Add(q);b.Close();return BRepPrimAPI_MakeRevol(BRepBuilderAPI_MakeFace(b.Wire()).Face(),gp_Ax1(gp_Pnt(0,0,0),gp_Dir(0,0,1)),2*M_PI).Shape();}
 if(k=="Signet ring"){dims(p,6);need(p[3]<p[0]+2*p[1],"Signet face is too wide for this shank");return fuse(band(p[0],p[1],p[2]),BRepPrimAPI_MakeBox(gp_Pnt(-p[3]/2,p[0]/2+p[1]*.4,(p[2]-p[4])/2),p[3],p[1]*.6+p[5],p[4]).Shape());}
 if(k=="Bangle"){dims(p,4);need(p[2]<std::min(p[0],p[1])/4,"Bangle wall is too large");return cut(pad(ellipse(p[0]+2*p[2],p[1]+2*p[2]),p[3]),pad(ellipse(p[0],p[1]),p[3]));}
 if(k=="Pendant frame"){dims(p,5);need(p[2]<std::min(p[0],p[1])/4,"Pendant wall is too large");auto frame=cut(pad(ellipse(p[0],p[1]),p[3]),pad(ellipse(p[0]-2*p[2],p[1]-2*p[2]),p[3]));double centre=p[1]/2+p[4]*.7;auto bail=cut(pad(ellipse(p[4]*2,p[4]*2,0,centre),p[3]),pad(ellipse(p[4],p[4],0,centre),p[3]));return fuse(frame,bail);}
 throw std::runtime_error("Unknown jewellery template");
}
TopoDS_Shape textContours(const std::vector<double>& xy,const std::vector<int>& counts,double depth){
 need(depth>=.001&&depth<=100,"Text depth must be 0.001 to 100 mm");need(!counts.empty()&&counts.size()<=256&&xy.size()<=32768,"Text outlines exceed mobile limits");std::vector<std::vector<gp_Pnt>> loops;size_t pos=0;for(int n:counts){need(n>=3&&n<=1024&&pos+2*n<=xy.size(),"Invalid text contour");std::vector<gp_Pnt> points;for(int i=0;i<n;i++){need(std::abs(xy[pos])<=10000&&std::abs(xy[pos+1])<=10000,"Text coordinates exceed mobile limits");gp_Pnt q(xy[pos],xy[pos+1],0);pos+=2;if(points.empty()||points.back().Distance(q)>1e-7)points.push_back(q);}if(points.size()>2&&points.front().Distance(points.back())<1e-7)points.pop_back();need(points.size()>=3&&std::abs(area(points))>1e-9,"Degenerate text contour");loops.push_back(points);}need(pos==xy.size(),"Text contour length mismatch");
 std::vector<int> level(loops.size());for(size_t i=0;i<loops.size();i++)for(size_t j=0;j<loops.size();j++)if(i!=j&&std::abs(area(loops[j]))>std::abs(area(loops[i]))&&inside(loops[i][0],loops[j]))level[i]++;
 BRep_Builder b;TopoDS_Compound result;b.MakeCompound(result);for(size_t i=0;i<loops.size();i++)if(level[i]%2==0){BRepBuilderAPI_MakeFace face(polygon(loops[i],true),true);for(size_t j=0;j<loops.size();j++)if(level[j]==level[i]+1&&inside(loops[j][0],loops[i]))face.Add(polygon(loops[j],false));need(face.IsDone(),"Text face failed");b.Add(result,BRepPrimAPI_MakePrism(face.Face(),gp_Vec(0,0,depth)).Shape());}return result;
}
TopoDS_Shape alongCurve(const TopoDS_Shape&source,const TopoDS_Shape&rail,int count,bool orient){
 need(count>=2&&count<=100,"Curve array count must be 2 to 100");need(rail.ShapeType()==TopAbs_WIRE,"Curve array rail must be a single wire");auto wire=TopoDS::Wire(rail);BRepAdaptor_CompCurve c(wire,true);bool closed=wire.Closed();GCPnts_UniformAbscissa samples(c,count+(closed?1:0),c.FirstParameter(),c.LastParameter(),1e-6);need(samples.IsDone(),"Curve sampling failed");Bnd_Box bounds;BRepBndLib::AddOptimal(source,bounds,false,false);need(!bounds.IsVoid(),"Source has no bounds");double a,d,e,x,y,z;bounds.Get(a,d,e,x,y,z);gp_Pnt start((a+x)/2,(d+y)/2,e);BRep_Builder b;TopoDS_Compound result;b.MakeCompound(result);for(int i=1;i<=count;i++){double u=samples.Parameter(i);gp_Pnt q;gp_Vec tangent;c.D1(u,q,tangent);gp_Trsf rotation,move;if(orient&&std::hypot(tangent.X(),tangent.Y())>1e-9)rotation.SetRotation(gp_Ax1(start,gp_Dir(0,0,1)),std::atan2(tangent.Y(),tangent.X()));move.SetTranslation(gp_Vec(start,q));b.Add(result,BRepBuilderAPI_Transform(source,move*rotation,true).Shape());}return result;
}
