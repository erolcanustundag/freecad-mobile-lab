// SPDX-License-Identifier: LGPL-2.1-or-later
#include <BRep_Builder.hxx>
#include <BRepTools.hxx>
#include <BRepGProp.hxx>
#include <GProp_GProps.hxx>
#include <TopoDS_Shape.hxx>
#include <Standard_Failure.hxx>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){
 if(argc!=2)return 2;
 try{
  TopoDS_Shape s;BRep_Builder b;
  if(!BRepTools::Read(s,argv[1],b)||s.IsNull())return 3;
  GProp_GProps coarse,fine;BRepGProp::VolumeProperties(s,coarse);
  double error=BRepGProp::VolumeProperties(s,fine,1e-10,true,false);
  auto c=fine.CentreOfMass();
  std::cout<<std::setprecision(17)<<"{\"default_volume\":"<<coarse.Mass()<<",\"adaptive_volume\":"<<fine.Mass()<<",\"estimated_relative_error\":"<<error<<",\"centroid\":["<<c.X()<<","<<c.Y()<<","<<c.Z()<<"]}\n";
 }catch(Standard_Failure const&){return 4;}
}
