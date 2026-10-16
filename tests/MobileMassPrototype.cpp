// SPDX-License-Identifier: LGPL-2.1-or-later
// Experimental CPython/OCCT adapter. Not packaged or exposed by mobile 1.26.
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <BRep_Builder.hxx>
#include <BRepTools.hxx>
#include <BRepGProp.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepBndLib.hxx>
#include <Bnd_Box.hxx>
#include <GProp_GProps.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS_Shape.hxx>
#include <Standard_Failure.hxx>
#include <cmath>
#include <sstream>
#include <stdexcept>
namespace {
PyObject* measure(PyObject*,PyObject* args){
 const char* bytes=nullptr;Py_ssize_t length=0;double eps=1e-8;
 if(!PyArg_ParseTuple(args,"y#|d",&bytes,&length,&eps))return nullptr;
 if(length<=0||length>4*1024*1024){PyErr_SetString(PyExc_ValueError,"Use a nonempty BRep up to4MiB");return nullptr;}
 if(!std::isfinite(eps)||eps<1e-10||eps>1e-4){PyErr_SetString(PyExc_ValueError,"Relative integration tolerance must be between1e-10 and1e-4");return nullptr;}
 try{
  TopoDS_Shape shape;BRep_Builder builder;std::istringstream input(std::string(bytes,static_cast<size_t>(length)));BRepTools::Read(shape,input,builder);
  if(shape.IsNull()||shape.ShapeType()!=TopAbs_SOLID)throw std::runtime_error("Choose one original closed solid");
  TopTools_IndexedMapOfShape faces,edges;TopExp::MapShapes(shape,TopAbs_FACE,faces);TopExp::MapShapes(shape,TopAbs_EDGE,edges);
  if(faces.Extent()>64||edges.Extent()>256)throw std::runtime_error("Mass analysis supports at most64faces and256edges");
  if(!BRepCheck_Analyzer(shape).IsValid())throw std::runtime_error("Solid BRep is invalid");
  Bnd_Box box;BRepBndLib::Add(shape,box,false);double x0,y0,z0,x1,y1,z1;box.Get(x0,y0,z0,x1,y1,z1);
  for(double value:{x0,y0,z0,x1,y1,z1})if(!std::isfinite(value)||std::abs(value)>1000000)throw std::runtime_error("Solid bounds exceed1,000,000mm");
  GProp_GProps props;double error=BRepGProp::VolumeProperties(shape,props,eps,true,false);double signedVolume=props.Mass();auto centre=props.CentreOfMass();
  for(double value:{error,signedVolume,centre.X(),centre.Y(),centre.Z()})if(!std::isfinite(value))throw std::runtime_error("Mass integration produced a nonfinite result");
  if(error<0||signedVolume==0)throw std::runtime_error("Mass integration did not produce a closed volume");
  return Py_BuildValue("{s:d,s:d,s:(ddd),s:d,s:d,s:i,s:i}","volume",std::abs(signedVolume),"signed_volume",signedVolume,"centroid",centre.X(),centre.Y(),centre.Z(),"estimated_relative_integration_error",error,"requested_relative_tolerance",eps,"faces",faces.Extent(),"edges",edges.Extent());
 }catch(const Standard_Failure& e){PyErr_SetString(PyExc_RuntimeError,e.GetMessageString()?e.GetMessageString():"Native mass integration failed");return nullptr;}
 catch(const std::exception& e){PyErr_SetString(PyExc_ValueError,e.what());return nullptr;}
}
PyMethodDef methods[]={{"measure",measure,METH_VARARGS,"Adaptive OCCT volume/centroid for a bounded serialized single solid; geometry tolerance remains separate."},{nullptr,nullptr,0,nullptr}};
PyModuleDef module={PyModuleDef_HEAD_INIT,"_mobile_gprops",nullptr,-1,methods};
}
PyMODINIT_FUNC PyInit__mobile_gprops(){return PyModule_Create(&module);}
