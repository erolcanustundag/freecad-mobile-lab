// SPDX-License-Identifier: LGPL-2.1-or-later
#include "MeshPreview.hpp"
#include <meshoptimizer.h>
#include <BRep_Tool.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Face.hxx>
#include <gp_Pnt.hxx>
#include <Poly_Triangulation.hxx>
#include <array>
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <limits>

MeshPreview makePreview(const TopoDS_Shape& shape,size_t budget) {
    MeshPreview result;result.budget=budget;
    std::vector<std::array<float,3>> positions;
    std::vector<unsigned int> input;
    for(TopExp_Explorer it(shape,TopAbs_FACE);it.More();it.Next()) {
        auto face=TopoDS::Face(it.Current());TopLoc_Location location;
        auto tri=BRep_Tool::Triangulation(face,location);if(tri.IsNull())continue;
        if(positions.size()+tri->NbNodes()>12000000||input.size()/3+tri->NbTriangles()>4000000)
            throw std::runtime_error("Model is too large for a mobile preview");
        unsigned int offset=positions.size();auto t=location.Transformation();
        for(int i=1;i<=tri->NbNodes();++i){auto p=tri->Node(i).Transformed(t);for(double v:{p.X(),p.Y(),p.Z()})if(!std::isfinite(v)||std::abs(v)>1000000)throw std::runtime_error("Mesh coordinates must be finite and within +/- 1,000,000 mm");positions.push_back({float(p.X()),float(p.Y()),float(p.Z())});}
        bool reversed=face.Orientation()==TopAbs_REVERSED;
        for(int i=1;i<=tri->NbTriangles();++i){int a,b,c;tri->Triangle(i).Get(a,b,c);if(reversed)std::swap(b,c);for(int j:{a,b,c}){if(j<1||j>tri->NbNodes())throw std::runtime_error("Invalid mesh triangle");input.push_back(offset+j-1);}}
    }
    result.originalTriangles=input.size()/3;
    if(input.empty()||budget==0)return result;
    std::vector<unsigned int> reduced;
    if(input.size()/3>budget) {
        reduced.resize(input.size());float error=0;
        size_t n=meshopt_simplify(reduced.data(),input.data(),input.size(),positions.front().data(),positions.size(),sizeof(positions[0]),budget*3,.005f,meshopt_SimplifyLockBorder,&error);
        reduced.resize(n);
        if(n/3>budget||n==0) {
            // Some disconnected/non-manifold meshes cannot reach the budget while
            // preserving topology. This fallback changes ONLY the display copy.
            const auto& source=n?reduced:input;std::vector<unsigned int> coarse(source.size());
            size_t target=budget*3;
            for(int attempt=0;attempt<4;++attempt){n=meshopt_simplifySloppy(coarse.data(),source.data(),source.size(),positions.front().data(),positions.size(),sizeof(positions[0]),nullptr,target,1.f,&error);if(n>0&&n/3<=budget)break;target=std::max(size_t(3),target/2);}
            if(n>0&&n/3<=budget){coarse.resize(n);reduced=std::move(coarse);}
            else {
                // Emergency display for pathological facets; full source remains
                // intact for export. Deterministic coverage keeps a visible proxy.
                reduced.clear();for(size_t j=0;j<budget;++j){size_t i=(j*(input.size()/3)/budget)*3;reduced.insert(reduced.end(),input.begin()+i,input.begin()+i+3);}
            }
            result.coarse=true;
        }
    }else reduced=std::move(input);
    result.indices=std::move(reduced);
    std::vector<unsigned int> remap(positions.size(),std::numeric_limits<unsigned int>::max());
    for(auto& i:result.indices){if(remap[i]==std::numeric_limits<unsigned int>::max()){remap[i]=result.vertices.size();auto p=positions[i];result.vertices.push_back({p[0],p[1],p[2]});}i=remap[i];}
    // Area-weighted smooth normals of the reduced mesh. Original geometry is never modified.
    for(size_t i=0;i<result.indices.size();i+=3){auto& a=result.vertices[result.indices[i]];auto& b=result.vertices[result.indices[i+1]];auto& c=result.vertices[result.indices[i+2]];double ux=b.x-a.x,uy=b.y-a.y,uz=b.z-a.z,vx=c.x-a.x,vy=c.y-a.y,vz=c.z-a.z;float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;for(auto j:{result.indices[i],result.indices[i+1],result.indices[i+2]}){auto& v=result.vertices[j];v.nx+=nx;v.ny+=ny;v.nz+=nz;}}
    for(auto& v:result.vertices){double l=std::sqrt(double(v.nx)*v.nx+double(v.ny)*v.ny+double(v.nz)*v.nz);if(l>1e-20){v.nx/=l;v.ny/=l;v.nz/=l;}else{v.nx=0;v.ny=0;v.nz=1;}}
    return result;
}
