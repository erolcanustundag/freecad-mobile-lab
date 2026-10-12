#pragma once
#include <TopoDS_Shape.hxx>
#include <string>
#include <vector>
bool jewelleryType(const std::string&);
TopoDS_Shape jewelleryPrimitive(const std::string&,const std::vector<double>&);
TopoDS_Shape textContours(const std::vector<double>&,const std::vector<int>&,double);
TopoDS_Shape alongCurve(const TopoDS_Shape&,const TopoDS_Shape&,int,bool);
