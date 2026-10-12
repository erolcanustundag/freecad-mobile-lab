// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
#include <TopoDS_Shape.hxx>
#include <gp_Pnt.hxx>
#include <string>
#include <vector>
TopoDS_Shape advancedPrimitive(const std::string&,const std::vector<double>&);
TopoDS_Shape pointCurve(const std::string&,const std::vector<double>&,bool);
TopoDS_Shape advancedModel(const std::string&,const std::vector<TopoDS_Shape>&,const std::vector<double>&);
std::vector<std::vector<gp_Pnt>> sampleEdges(const TopoDS_Shape&,double tolerance=.025);
std::string inspectShape(const TopoDS_Shape&,bool meshOnly,double draftDegrees);
void exportDrawing(const TopoDS_Shape&,const std::string&,const std::string&);
void writeObj(const TopoDS_Shape&,const std::string&,double tolerance=.015);
TopoDS_Shape readObj(const std::string&);
bool curveShape(const TopoDS_Shape&);
bool advancedMeshPrimitive(const std::string&);
