// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
#include <TopoDS_Shape.hxx>
#include <vector>
#include <cstddef>

struct PreviewVertex {float x,y,z,nx=0,ny=0,nz=0;};
struct MeshPreview {
    size_t budget=0,originalTriangles=0;
    bool coarse=false;
    std::vector<PreviewVertex> vertices;
    std::vector<unsigned int> indices;
};
MeshPreview makePreview(const TopoDS_Shape& shape,size_t budget);
