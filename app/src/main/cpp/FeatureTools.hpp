// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
#include <TopoDS_Shape.hxx>
#include <string>
#include <vector>
TopoDS_Shape detailModel(const std::string&,const std::vector<TopoDS_Shape>&,const std::vector<double>&);
std::string topologyData(const TopoDS_Shape&);
std::string surfacePoles(const TopoDS_Shape&);
TopoDS_Shape changeSurfacePole(const TopoDS_Shape&,const std::vector<double>&);
std::string curveCurvature(const TopoDS_Shape&);
std::string sampledThickness(const TopoDS_Shape&,double);
