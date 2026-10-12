// SPDX-License-Identifier: LGPL-2.1-or-later
// Native Android adapter for OpenCASCADE and FreeCAD's upstream PlaneGCS solver.
#include <jni.h>
#include <map>
#include <vector>
#include <mutex>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <stdexcept>
#include <fstream>
#include <algorithm>
#include <memory>
#include <locale>
#include <limits>
#include <cstdint>
#include <cstring>
#include <array>
#include <set>
#include <unordered_set>
#include "MeshPreview.hpp"
#include "AdvancedTools.hpp"
#include "JewelleryTools.hpp"
#include "FeatureTools.hpp"
#include <IGESControl_Reader.hxx>
#include <IGESControl_Writer.hxx>
#include <Geom_BSplineCurve.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <BRepBuilderAPI_Copy.hxx>
#include <GCS.h>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <BRepPrimAPI_MakeSphere.hxx>
#include <BRepPrimAPI_MakeTorus.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Common.hxx>
#include <BRepFilletAPI_MakeFillet.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <gp_Circ.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepGProp.hxx>
#include <BRepBndLib.hxx>
#include <BRepTools.hxx>
#include <BinTools.hxx>
#include <BRep_Builder.hxx>
#include <BRep_Tool.hxx>
#include <Bnd_Box.hxx>
#include <GProp_GProps.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Compound.hxx>
#include <TopExp_Explorer.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <Poly_Triangulation.hxx>
#include <STEPControl_Reader.hxx>
#include <STEPControl_Writer.hxx>
#include <StlAPI_Writer.hxx>
#include <RWStl.hxx>
#include <OSD_Path.hxx>
#include <Standard_Failure.hxx>
#include <gp_Trsf.hxx>
#include <gp_Vec.hxx>
#include <gp_Ax1.hxx>
#include <IntCurvesFace_ShapeIntersector.hxx>
#include <gp_Lin.hxx>

namespace {
struct Object {
    int id = 0;
    std::string type;
    std::string name,layer="Default";
    bool locked=false;float roughness=.45f,metallic=0;
    std::vector<double> dims;
    TopoDS_Shape shape;
    bool visible = true;
    bool meshOnly = false;
    bool graphOwned = false;
    double x = 0, y = 0, z = 0;
    std::shared_ptr<MeshPreview> preview;
    std::array<float,3> color{.29f,.73f,.67f};
};
std::map<int, Object> scene;
struct State {std::map<int,Object> objects;std::string workspace;};
std::vector<State> history,future;
std::string workspace;
std::mutex gate;
int nextId = 1;
constexpr size_t MaxDisplayTriangles = 200000;
constexpr size_t MaxStlTriangles = 2000000;
constexpr size_t MaxStlBytes = 256 * 1024 * 1024;
constexpr size_t UndoMeshBudget = 256 * 1024 * 1024;
struct Transaction {
    std::map<int,Object> original;
    std::vector<State> undo,redo;
    std::string originalWorkspace;
    int originalNextId;
    bool recordUndo;
    bool dirty = false;
};
std::unique_ptr<Transaction> transaction;
struct PreviewState {std::map<int,Object> objects;std::string workspace;int next;bool dirty;};std::unique_ptr<PreviewState> previewState;
std::string utf(JNIEnv* e, jstring s) {
    if(!s) throw std::runtime_error("Missing string");
    const char* c=e->GetStringUTFChars(s,nullptr);
    if(!c)throw std::runtime_error("Cannot allocate string");
    std::string out;
    try {out=c;}catch(...){e->ReleaseStringUTFChars(s,c);throw;}
    e->ReleaseStringUTFChars(s,c);return out;
}
std::vector<double> doubles(JNIEnv* e, jdoubleArray a,size_t maximum=16) {
    if(!a)throw std::runtime_error("Missing dimensions");
    if(size_t(e->GetArrayLength(a))>maximum)throw std::runtime_error("Too many dimensions");
    std::vector<double> out(e->GetArrayLength(a)); if(!out.empty())e->GetDoubleArrayRegion(a,0,out.size(),out.data());
    if(e->ExceptionCheck())throw std::runtime_error("Cannot read dimensions");
    for(double x:out) if(!std::isfinite(x)) throw std::runtime_error("Dimensions must be finite");
    return out;
}
void fail(JNIEnv* e,const char* s) {
    if(e->ExceptionCheck())return;
    auto cls=e->FindClass("java/lang/IllegalArgumentException");
    if(cls){e->ThrowNew(cls,s?s:"CAD operation failed");e->DeleteLocalRef(cls);}
}
void trimHistory() {
    while(history.size()>24)history.erase(history.begin());while(future.size()>24)future.erase(future.begin());
    while(history.size()>1||future.size()>1) {
        std::unordered_set<const void*> seen;size_t bytes=0;
        auto count=[&](const std::map<int,Object>& objects){for(const auto& [id,o]:objects){for(TopExp_Explorer it(o.shape,TopAbs_FACE);it.More();it.Next()){TopLoc_Location loc;auto tri=BRep_Tool::Triangulation(TopoDS::Face(it.Current()),loc);if(!tri.IsNull()&&seen.insert(tri.get()).second)bytes+=size_t(tri->NbNodes())*36+size_t(tri->NbTriangles())*12;}if(o.preview&&seen.insert(o.preview.get()).second)bytes+=o.preview->vertices.size()*sizeof(PreviewVertex)+o.preview->indices.size()*4;}};
        count(scene);for(const auto& saved:history)count(saved.objects);for(const auto& saved:future)count(saved.objects);
        if(bytes<=UndoMeshBudget)break;if(history.size()>1)history.erase(history.begin());else future.erase(future.begin());
    }
}
void checkpoint() {
    if(transaction){transaction->dirty=true;return;}
    history.push_back(State{scene,workspace});future.clear();trimHistory();
}
void checkPosition(double x,double y,double z) {
    for(double p:{x,y,z})if(!std::isfinite(p)||std::abs(p)>1000000)
        throw std::runtime_error("Positions must be finite and within +/- 1,000,000 mm");
}
Object& object(int id) { auto i=scene.find(id); if(i==scene.end()) throw std::runtime_error("Select an object first"); return i->second; }
Object& editable(int id){auto& o=object(id);if(o.locked)throw std::runtime_error("Object is locked; unlock it before editing");return o;}
std::string jsonQuoted(const std::string& value){std::ostringstream out;out<<'"';for(unsigned char c:value){if(c=='"'||c=='\\')out<<'\\'<<c;else if(c<32)out<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<int(c)<<std::dec;else out<<c;}out<<'"';return out.str();}
void positive(const std::vector<double>& p, size_t n) {
    if(p.size()!=n) throw std::runtime_error("Wrong number of dimensions");
    for(double d:p) if(!std::isfinite(d)||d<0.001||d>10000) throw std::runtime_error("Dimensions must be 0.001 to 10000 mm");
}
void valid(const TopoDS_Shape& s) {
    if(s.IsNull()||!BRepCheck_Analyzer(s).IsValid()) throw std::runtime_error("The CAD kernel could not make valid geometry. Try different dimensions.");
}
std::vector<gp_Pnt> solveRectangle(double width,double height) {
    // Solve horizontal/vertical and dimensional constraints with real FreeCAD PlaneGCS.
    double p[8]={0.03,0.04,width*0.9,0.08,width*1.1,height*0.9,0.05,height*1.1};
    double zero=0;
    GCS::System solver;
    GCS::VEC_pD unknowns;
    for(auto& x:p)unknowns.push_back(&x);
    solver.declareUnknowns(unknowns);
    solver.addConstraintEqual(&p[0],&zero,1);
    solver.addConstraintEqual(&p[1],&zero,2);
    solver.addConstraintEqual(&p[1],&p[3],3);
    solver.addConstraintEqual(&p[2],&p[4],4);
    solver.addConstraintEqual(&p[5],&p[7],5);
    solver.addConstraintEqual(&p[6],&p[0],6);
    solver.addConstraintDifference(&p[0],&p[2],&width,7);
    solver.addConstraintDifference(&p[1],&p[7],&height,8);
    solver.initSolution();
    auto status=solver.solve();
    if(status!=GCS::SolveStatus::Success) throw std::runtime_error("FreeCAD Sketcher solver did not converge");
    solver.applySolution();
    if(std::abs((p[2]-p[0])-width)>1e-6||std::abs((p[7]-p[1])-height)>1e-6)
        throw std::runtime_error("Sketch constraint residual exceeds tolerance");
    std::vector<gp_Pnt> out;
    for(int i=0;i<4;i++)out.emplace_back(p[i*2]-width/2,p[i*2+1]-height/2,0);
    return out;
}
TopoDS_Shape make(const std::string& kind,const std::vector<double>& p) {
    TopoDS_Shape s;
    if(kind=="Box") { positive(p,3);s=BRepPrimAPI_MakeBox(gp_Pnt(-p[0]/2,-p[1]/2,0),p[0],p[1],p[2]).Shape(); }
    else if(kind=="Cylinder") { positive(p,2);s=BRepPrimAPI_MakeCylinder(p[0],p[1]).Shape(); }
    else if(kind=="Sphere") { positive(p,1);s=BRepPrimAPI_MakeSphere(gp_Pnt(0,0,p[0]),p[0]).Shape(); }
    else if(kind=="Torus") { positive(p,2);if(p[0]<=p[1]) throw std::runtime_error("Major radius must exceed tube radius");s=BRepPrimAPI_MakeTorus(gp_Ax2(gp_Pnt(0,0,p[1]),gp_Dir(0,0,1)),p[0],p[1]).Shape(); }
    else if(kind=="Ring") {
        positive(p,3);double r=p[0]/2;
        auto outer=BRepPrimAPI_MakeCylinder(r+p[1],p[2]).Shape();
        auto inner=BRepPrimAPI_MakeCylinder(r,p[2]).Shape();
        BRepAlgoAPI_Cut cut(outer,inner);cut.Build();if(!cut.IsDone())throw std::runtime_error("Ring cut failed");s=cut.Shape();
    }
    else if(kind=="Sketch pad") {
        positive(p,3);auto points=solveRectangle(p[0],p[1]);
        BRepBuilderAPI_MakePolygon polygon;for(const auto& pt:points)polygon.Add(pt);polygon.Close();
        auto face=BRepBuilderAPI_MakeFace(polygon.Wire()).Face();
        s=BRepPrimAPI_MakePrism(face,gp_Vec(0,0,p[2])).Shape();
    }
    else s=advancedPrimitive(kind,p);
    if(!advancedMeshPrimitive(kind))valid(s);return s;
}
double volume(const TopoDS_Shape& s) { GProp_GProps v;BRepGProp::VolumeProperties(s,v);return std::abs(v.Mass()); }
void place(Object& o) {
    gp_Trsf t;t.SetTranslation(gp_Vec(o.x,o.y,o.z));o.shape=BRepBuilderAPI_Transform(o.shape,t,true).Shape();
}
int insert(Object o) {if(scene.size()>=250)throw std::runtime_error("Workspace exceeds 250 objects");o.id=nextId++;scene[o.id]=o;return o.id;}
size_t triangleCount(const TopoDS_Shape& shape,size_t limit=4000000) {
    size_t count=0;
    for(TopExp_Explorer it(shape,TopAbs_FACE);it.More();it.Next()) {
        TopLoc_Location loc;auto tri=BRep_Tool::Triangulation(TopoDS::Face(it.Current()),loc);
        if(!tri.IsNull())count+=tri->NbTriangles();
        if(count>limit)throw std::runtime_error("Mesh exceeds the mobile triangle limit; export the selected object or hide other objects");
    }
    return count;
}
bool checkStlFile(const std::string& path) {
    std::ifstream in(path,std::ios::binary|std::ios::ate);
    if(!in)throw std::runtime_error("Cannot open STL file");
    auto size=in.tellg();if(size<0||size>std::streamoff(MaxStlBytes))throw std::runtime_error("STL exceeds the mobile 256 MB file limit");
    if(size>=84) {
        in.seekg(80);unsigned char raw[4];in.read(reinterpret_cast<char*>(raw),4);
        uint32_t n=uint32_t(raw[0])|(uint32_t(raw[1])<<8)|(uint32_t(raw[2])<<16)|(uint32_t(raw[3])<<24);
        if(uint64_t(size)==84+uint64_t(n)*50) {
            if(n>MaxStlTriangles)throw std::runtime_error("STL exceeds 2,000,000 triangles");
            if(n==0)throw std::runtime_error("STL contains no triangles");
            in.seekg(84);unsigned char record[50];
            for(uint32_t i=0;i<n;++i){if(!in.read(reinterpret_cast<char*>(record),50))throw std::runtime_error("Truncated binary STL");for(int j=12;j<48;j+=4){uint32_t bits=uint32_t(record[j])|(uint32_t(record[j+1])<<8)|(uint32_t(record[j+2])<<16)|(uint32_t(record[j+3])<<24);float v;std::memcpy(&v,&bits,4);if(!std::isfinite(v)||std::abs(v)>1000000)throw std::runtime_error("Invalid or oversized STL coordinates");}}
            return true;
        }
    }
    in.clear();in.seekg(0);char line[4096];size_t n=0,vertices=0;bool header=false;
    while(in.getline(line,sizeof(line))){std::istringstream tokens(line);tokens.imbue(std::locale::classic());std::string word;tokens>>word;if(word.empty())continue;if(!header){if(word!="solid")throw std::runtime_error("Invalid binary STL size or ASCII STL header");header=true;}
        if(word=="endfacet"&&++n>MaxStlTriangles)throw std::runtime_error("STL exceeds 2,000,000 triangles");
        if(word=="vertex"){double x,y,z;if(!(tokens>>x>>y>>z))throw std::runtime_error("Invalid ASCII STL vertex");for(double v:{x,y,z})if(!std::isfinite(v)||std::abs(v)>1000000)throw std::runtime_error("Invalid or oversized STL coordinates");if(++vertices>MaxStlTriangles*3)throw std::runtime_error("STL exceeds 2,000,000 triangles");}}
    if(!in.eof()||n==0||vertices!=n*3)throw std::runtime_error("Truncated or invalid ASCII STL");
    return false;
}
TopoDS_Shape selection(int id) {
    if(id>0)return object(id).shape;
    TopoDS_Compound c;BRep_Builder b;b.MakeCompound(c);int n=0;
    for(auto& [key,o]:scene)if(o.visible){b.Add(c,o.shape);n++;}
    if(!n)throw std::runtime_error("No visible objects to export");return c;
}
void exportShape(const TopoDS_Shape& shape,const std::string& path,const std::string& format,double tolerance=.015) {
    if(format=="stl") {
        BRepMesh_IncrementalMesh mesh(shape,tolerance,false,0.50,false);
        if(triangleCount(shape,MaxStlTriangles)==0)throw std::runtime_error("No triangles to export");
        StlAPI_Writer writer;writer.ASCIIMode()=false;
        if(!writer.Write(shape,path.c_str()))throw std::runtime_error("STL export failed");
    } else if(format=="step") {
        STEPControl_Writer w;
        if(w.Transfer(shape,STEPControl_AsIs)!=IFSelect_RetDone||w.Write(path.c_str())!=IFSelect_RetDone)throw std::runtime_error("STEP export failed");
    } else if(format=="iges") {
        IGESControl_Writer w("MM",1);if(!w.AddShape(shape)||!w.Write(path.c_str()))throw std::runtime_error("IGES export failed");
    } else if(format=="obj") {writeObj(shape,path,tolerance);
    } else if(format=="svg"||format=="dxf") {exportDrawing(shape,path,format);
    } else if(format=="brep") {
        if(!BRepTools::Write(shape,path.c_str()))throw std::runtime_error("BREP export failed");
    } else throw std::runtime_error("Unknown export format");
}
TopoDS_Shape importShape(const std::string& path,const std::string& format,bool& meshOnly) {
    TopoDS_Shape s;meshOnly=false;
    if(format=="step") {
        STEPControl_Reader r;if(r.ReadFile(path.c_str())!=IFSelect_RetDone||r.TransferRoots()==0)throw std::runtime_error("Cannot read STEP file");s=r.OneShape();valid(s);
    } else if(format=="brep") {
        BRep_Builder b;
        bool ascii=false;
        try{ascii=BRepTools::Read(s,path.c_str(),b);}catch(const Standard_Failure&){s.Nullify();}
        if(!ascii) {
            s.Nullify();if(!BinTools::Read(s,path.c_str()))throw std::runtime_error("Cannot read ASCII or binary BREP file");
        }
        valid(s);
    } else if(format=="iges") {
        IGESControl_Reader r;if(r.ReadFile(path.c_str())!=IFSelect_RetDone||r.TransferRoots()==0)throw std::runtime_error("Cannot read IGES file");s=r.OneShape();valid(s);
    } else if(format=="obj") {s=readObj(path);meshOnly=true;
    } else if(format=="stl") {
        bool binary=checkStlFile(path);
        // Exact binary length/count validation is stronger than the OCCT content heuristic.
        // A legal all-zero header/normal and small positive coordinates may look like ASCII.
        auto tri=binary?RWStl::ReadBinary(OSD_Path(path.c_str())):RWStl::ReadAscii(OSD_Path(path.c_str()));if(tri.IsNull()||tri->NbTriangles()==0)throw std::runtime_error("Cannot read STL mesh");
        if(tri->NbTriangles()>MaxStlTriangles)throw std::runtime_error("STL exceeds 2,000,000 triangles");
        TopoDS_Face f;BRep_Builder b;b.MakeFace(f,tri);s=f;meshOnly=true;
    } else throw std::runtime_error("Use STEP, IGES, OBJ, STL or BREP files");
    if(s.IsNull())throw std::runtime_error("File contains no geometry");return s;
}
std::vector<float> triangles(int selected,size_t limit=50000) {
    std::vector<float> out;
    size_t total=0;std::map<int,size_t> counts;
    for(auto& [id,o]:scene)if(o.visible) {
        if(!o.meshOnly){BRepMesh_IncrementalMesh m(o.shape,0.025,false,0.13,false);}
        size_t n=triangleCount(o.shape);if(n){counts[id]=n;total+=n;}
    }
    out.reserve(std::min(total,limit)*30);
    for(auto& [id,o]:scene) {
        if(!o.visible||!counts.count(id))continue;
        size_t budget=total<=limit?counts[id]:1+(limit-counts.size())*counts[id]/total;
        if(!o.preview||o.preview->budget!=budget)o.preview=std::make_shared<MeshPreview>(makePreview(o.shape,budget));
        float red=std::min(1.f,o.color[0]+(id==selected?.14f:0)),green=std::min(1.f,o.color[1]+(id==selected?.14f:0)),blue=std::min(1.f,o.color[2]+(id==selected?.14f:0));
        for(auto j:o.preview->indices){const auto& v=o.preview->vertices[j];out.insert(out.end(),{v.x,v.y,v.z,v.nx,v.ny,v.nz,red,green,blue,1.f});}
    }
    return out;
}
std::string metadata() {
    std::ostringstream s;s.imbue(std::locale::classic());s<<std::setprecision(12)<<'[';bool first=true;
    for(auto& [id,o]:scene) {
        if(!first)s<<',';first=false;Bnd_Box b;if(o.meshOnly)BRepBndLib::Add(o.shape,b);else BRepBndLib::AddOptimal(o.shape,b,false,false);double x0=0,y0=0,z0=0,x1=0,y1=0,z1=0;if(!b.IsVoid())b.Get(x0,y0,z0,x1,y1,z1);
        s<<"{\"id\":"<<id<<",\"type\":\""<<o.type<<"\",\"visible\":"<<(o.visible?"true":"false")<<",\"mesh\":"<<(o.meshOnly?"true":"false")<<",\"solid\":"<<(!o.meshOnly&&TopExp_Explorer(o.shape,TopAbs_SOLID).More()?"true":"false")<<",\"volume\":"<<(o.meshOnly||!TopExp_Explorer(o.shape,TopAbs_SOLID).More()?0:volume(o.shape))<<",\"xyz\":["<<o.x<<','<<o.y<<','<<o.z<<"],\"bounds\":["<<x1-x0<<','<<y1-y0<<','<<z1-z0<<"],\"dims\":[";
        for(size_t i=0;i<o.dims.size();i++){if(i)s<<',';s<<o.dims[i];}s<<"],\"graphOwned\":"<<(o.graphOwned?"true":"false")<<",\"curve\":"<<(curveShape(o.shape)?"true":"false")<<",\"color\":["<<o.color[0]<<','<<o.color[1]<<','<<o.color[2]<<"],\"surfaceMaterial\":["<<o.roughness<<','<<o.metallic<<"],\"name\":"<<jsonQuoted(o.name)<<",\"layer\":"<<jsonQuoted(o.layer)<<",\"locked\":"<<(o.locked?"true":"false")<<",\"bbox\":["<<x0<<','<<y0<<','<<z0<<','<<x1<<','<<y1<<','<<z1<<"],\"sourceTriangles\":"<<(o.meshOnly?triangleCount(o.shape):0)<<",\"coarsePreview\":"<<(o.preview&&o.preview->coarse?"true":"false")<<"}";
    }
    s<<']';return s.str();
}
gp_Pnt center(const Object& o) {
    Bnd_Box b;if(o.meshOnly)BRepBndLib::Add(o.shape,b);else BRepBndLib::AddOptimal(o.shape,b,false,false);
    if(b.IsVoid())throw std::runtime_error("Object has no bounds");double a,c,d,x,y,z;b.Get(a,c,d,x,y,z);return gp_Pnt((a+x)/2,(c+y)/2,(d+z)/2);
}
void transform(Object& o,const gp_Trsf& t,bool copyGeometry=false) {
    o.shape=BRepBuilderAPI_Transform(o.shape,t,copyGeometry,copyGeometry).Shape();o.preview.reset();
    Bnd_Box b;if(o.meshOnly)BRepBndLib::Add(o.shape,b);else {valid(o.shape);BRepBndLib::AddOptimal(o.shape,b,false,false);}
    double x0,y0,z0,x1,y1,z1;if(b.IsVoid())throw std::runtime_error("Object has no bounds");b.Get(x0,y0,z0,x1,y1,z1);for(double v:{x0,y0,z0,x1,y1,z1})if(!std::isfinite(v)||std::abs(v)>1000000)throw std::runtime_error("Transformed geometry exceeds the mobile coordinate limit");
}
}
#define GUARD std::lock_guard<std::mutex> lock(gate);try
#define CATCH(ret) catch(const Standard_Failure& f){fail(e,f.GetMessageString());return ret;}catch(const std::exception& f){fail(e,f.what());return ret;}catch(...){fail(e,"Unexpected CAD error");return ret;}
#define JNI(name) Java_org_freecad_mobilelab_NativeCad_##name
extern "C" JNIEXPORT jint JNICALL JNI(create)(JNIEnv* e,jclass,jstring kind,jdoubleArray d) {
    GUARD {Object o;o.type=utf(e,kind);o.dims=doubles(e,d);o.shape=make(o.type,o.dims);o.meshOnly=advancedMeshPrimitive(o.type);checkpoint();return insert(o);}CATCH(0)
}
extern "C" JNIEXPORT void JNICALL JNI(edit)(JNIEnv* e,jclass,jint id,jdoubleArray d) {
    GUARD {auto p=doubles(e,d);auto fresh=editable(id);fresh.shape=make(fresh.type,p);fresh.meshOnly=advancedMeshPrimitive(fresh.type);fresh.dims=p;place(fresh);fresh.preview.reset();checkpoint();scene[id]=fresh;}CATCH()
}
extern "C" JNIEXPORT jint JNICALL JNI(operation)(JNIEnv* e,jclass,jstring kind,jint a,jint b,jdouble amount) {
    GUARD {
        auto type=utf(e,kind);auto first=object(a);if(first.meshOnly)throw std::runtime_error("STL meshes support viewing and export; solid operations need STEP or created solids");
        Object result;result.type=type;
        if(type=="Fillet") {
            if(amount<=0||!std::isfinite(amount))throw std::runtime_error("Fillet radius must be positive");
            BRepFilletAPI_MakeFillet f(first.shape);TopTools_IndexedMapOfShape edges;TopExp::MapShapes(first.shape,TopAbs_EDGE,edges);for(int i=1;i<=edges.Extent();++i)f.Add(amount,TopoDS::Edge(edges(i)));
            f.Build();if(!f.IsDone())throw std::runtime_error("Fillet could not be built. Try a smaller radius.");result.shape=f.Shape();
        } else {
            auto second=object(b);if(a==b||second.meshOnly)throw std::runtime_error("Choose two different solid objects");
            if(type=="Union"){BRepAlgoAPI_Fuse f(first.shape,second.shape);f.Build();if(!f.IsDone())throw std::runtime_error("Union failed");result.shape=f.Shape();}
            else if(type=="Cut"){BRepAlgoAPI_Cut f(first.shape,second.shape);f.Build();if(!f.IsDone())throw std::runtime_error("Cut failed");result.shape=f.Shape();}
            else if(type=="Intersect"){BRepAlgoAPI_Common f(first.shape,second.shape);f.Build();if(!f.IsDone())throw std::runtime_error("Intersection failed");result.shape=f.Shape();}
            else throw std::runtime_error("Unsupported operation");
        }
        valid(result.shape);if(volume(result.shape)<1e-9)throw std::runtime_error("Operation produced no solid volume. Check object overlap.");
        checkpoint();scene[a].visible=false;if(type!="Fillet")scene[b].visible=false;return insert(result);
    }CATCH(0)
}
extern "C" JNIEXPORT void JNICALL JNI(move)(JNIEnv* e,jclass,jint id,jdouble x,jdouble y,jdouble z) {
    GUARD {checkPosition(x,y,z);auto fresh=editable(id);gp_Trsf t;t.SetTranslation(gp_Vec(x-fresh.x,y-fresh.y,z-fresh.z));transform(fresh,t);fresh.x=x;fresh.y=y;fresh.z=z;checkpoint();scene[id]=fresh;}CATCH()
}
extern "C" JNIEXPORT jint JNICALL JNI(duplicate)(JNIEnv* e,jclass,jint id,jdouble dx,jdouble dy,jdouble dz) {
    GUARD {checkPosition(dx,dy,dz);auto fresh=object(id);fresh.graphOwned=false;fresh.x+=dx;fresh.y+=dy;fresh.z+=dz;checkPosition(fresh.x,fresh.y,fresh.z);gp_Trsf t;t.SetTranslation(gp_Vec(dx,dy,dz));transform(fresh,t);checkpoint();return insert(fresh);}CATCH(0)
}
extern "C" JNIEXPORT void JNICALL JNI(scale)(JNIEnv* e,jclass,jint id,jdouble factor) {
    GUARD {if(!std::isfinite(factor)||factor<.0001||factor>1000)throw std::runtime_error("Scale factor must be 0.0001 to 1000");auto fresh=editable(id);if(factor==1)return;auto p=center(fresh);gp_Trsf t;t.SetScale(p,factor);if(fresh.type=="Box"||fresh.type=="Ring"||fresh.type=="Cylinder"||fresh.type=="Sphere"||fresh.type=="Torus"||fresh.type=="Sketch pad"||fresh.type=="Circle"||fresh.type=="Ellipse"||fresh.type=="Rectangle"){for(auto& d:fresh.dims)d*=factor;if(!fresh.dims.empty())positive(fresh.dims,fresh.dims.size());}else{fresh.type=fresh.meshOnly?"STL mesh":curveShape(fresh.shape)?"BREP curve":"BREP solid";fresh.dims.clear();}transform(fresh,t,true);fresh.x=p.X()+(fresh.x-p.X())*factor;fresh.y=p.Y()+(fresh.y-p.Y())*factor;fresh.z=p.Z()+(fresh.z-p.Z())*factor;checkPosition(fresh.x,fresh.y,fresh.z);checkpoint();scene[id]=fresh;}CATCH()
}
extern "C" JNIEXPORT void JNICALL JNI(rotate)(JNIEnv* e,jclass,jint id,jdouble x,jdouble y,jdouble z) {
    GUARD {for(double a:{x,y,z})if(!std::isfinite(a)||std::abs(a)>1000000)throw std::runtime_error("Rotation angles must be finite and within +/- 1,000,000 degrees");auto fresh=editable(id);x=std::remainder(x,360.);y=std::remainder(y,360.);z=std::remainder(z,360.);if(x==0&&y==0&&z==0)return;auto p=center(fresh);gp_Trsf rx,ry,rz;rx.SetRotation(gp_Ax1(p,gp_Dir(1,0,0)),x*M_PI/180);ry.SetRotation(gp_Ax1(p,gp_Dir(0,1,0)),y*M_PI/180);rz.SetRotation(gp_Ax1(p,gp_Dir(0,0,1)),z*M_PI/180);transform(fresh,rz*ry*rx);if(!fresh.dims.empty()){fresh.type=fresh.meshOnly?"STL mesh":curveShape(fresh.shape)?"BREP curve":"BREP solid";fresh.dims.clear();}checkpoint();scene[id]=fresh;}CATCH()
}
extern "C" JNIEXPORT void JNICALL JNI(restorePosition)(JNIEnv* e,jclass,jint id,jdoubleArray p) {
    GUARD {auto xyz=doubles(e,p);if(xyz.size()!=3)throw std::runtime_error("Project position needs X, Y, Z");checkPosition(xyz[0],xyz[1],xyz[2]);auto& o=object(id);checkpoint();o.x=xyz[0];o.y=xyz[1];o.z=xyz[2];}CATCH()
}
extern "C" JNIEXPORT void JNICALL JNI(beginTransaction)(JNIEnv* e,jclass,jboolean record){GUARD {if(transaction)throw std::runtime_error("CAD operation already in progress");transaction=std::make_unique<Transaction>(Transaction{scene,history,future,workspace,nextId,bool(record),false});}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(commitTransaction)(JNIEnv* e,jclass){GUARD {if(!transaction||previewState)throw std::runtime_error("No CAD transaction or preview is still active");if(transaction->dirty){if(transaction->recordUndo)history.push_back(State{transaction->original,transaction->originalWorkspace});future.clear();}transaction.reset();trimHistory();}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(rollbackTransaction)(JNIEnv* e,jclass){GUARD {previewState.reset();if(transaction){scene=std::move(transaction->original);history=std::move(transaction->undo);future=std::move(transaction->redo);workspace=std::move(transaction->originalWorkspace);nextId=transaction->originalNextId;transaction.reset();}}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(visible)(JNIEnv* e,jclass,jint id,jboolean v){GUARD {auto& o=object(id);if(o.visible!=bool(v)){checkpoint();o.visible=v;}}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(remove)(JNIEnv* e,jclass,jint id){GUARD {editable(id);checkpoint();scene.erase(id);}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(clear)(JNIEnv* e,jclass){GUARD {checkpoint();scene.clear();workspace.clear();}CATCH()}
extern "C" JNIEXPORT jboolean JNICALL JNI(undo)(JNIEnv* e,jclass){GUARD {if(history.empty())return false;future.push_back(State{scene,workspace});scene=std::move(history.back().objects);workspace=std::move(history.back().workspace);history.pop_back();return true;}CATCH(false)}
extern "C" JNIEXPORT jstring JNICALL JNI(objects)(JNIEnv* e,jclass){GUARD {auto s=metadata();return e->NewStringUTF(s.c_str());}CATCH(nullptr)}
extern "C" JNIEXPORT jfloatArray JNICALL JNI(mesh)(JNIEnv* e,jclass,jint selected){GUARD {auto v=triangles(selected);auto a=e->NewFloatArray(v.size());if(a&&!v.empty())e->SetFloatArrayRegion(a,0,v.size(),v.data());return a;}CATCH(nullptr)}
extern "C" JNIEXPORT jfloatArray JNICALL JNI(meshAtDetail)(JNIEnv* e,jclass,jint selected,jint budget){GUARD {if(budget<1000||budget>MaxDisplayTriangles)throw std::runtime_error("Preview detail must be 1,000 to 200,000 triangles");auto v=triangles(selected,budget);auto a=e->NewFloatArray(v.size());if(a&&!v.empty())e->SetFloatArrayRegion(a,0,v.size(),v.data());return a;}CATCH(nullptr)}
extern "C" JNIEXPORT void JNICALL JNI(write)(JNIEnv* e,jclass,jstring p,jstring f,jint selected){GUARD {auto path=utf(e,p),format=utf(e,f);if(format=="step"||format=="brep"||format=="iges"){for(auto& [id,o]:scene)if(o.meshOnly&&((selected>0&&selected==id)||(selected<=0&&o.visible)))throw std::runtime_error("STL meshes can be exported as STL; STEP, IGES and BREP require CAD geometry");}exportShape(selection(selected),path,format);}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(writeWithTolerance)(JNIEnv* e,jclass,jstring p,jstring f,jint selected,jdouble tolerance){GUARD {
    if(!std::isfinite(tolerance)||tolerance<.005||tolerance>.5)throw std::runtime_error("Export tolerance must be 0.005 to 0.5 mm");auto path=utf(e,p),format=utf(e,f);if(selected>0)object(selected);
    TopoDS_Compound c;BRep_Builder b;b.MakeCompound(c);int count=0;for(auto& [id,o]:scene)if(selected>0?selected==id:o.visible){if(o.meshOnly&&(format=="step"||format=="brep"||format=="iges"))throw std::runtime_error("CAD export cannot include mesh-only objects; hide them first");TopoDS_Shape shape=o.shape;if(!o.meshOnly&&(format=="stl"||format=="obj")){shape=BRepBuilderAPI_Copy(o.shape,true,false).Shape();BRepTools::Clean(shape);}b.Add(c,shape);count++;}if(!count)throw std::runtime_error("No geometry to export");exportShape(c,path,format,tolerance);
}CATCH()}
extern "C" JNIEXPORT jint JNICALL JNI(read)(JNIEnv* e,jclass,jstring p,jstring f){GUARD {Object o;auto format=utf(e,f);o.type=format=="stl"||format=="obj"?"STL mesh":format=="step"?"STEP solid":format=="iges"?"IGES solid":"BREP solid";o.shape=importShape(utf(e,p),format,o.meshOnly);if(curveShape(o.shape))o.type="BREP curve";checkpoint();return insert(o);}CATCH(0)}
extern "C" JNIEXPORT jstring JNICALL JNI(selfTest)(JNIEnv* e,jclass,jstring dir){GUARD {
    std::ostringstream report;auto root=utf(e,dir);
    auto box=make("Box",{10,20,3});if(std::abs(volume(box)-600)>1e-6)throw std::runtime_error("Box volume test failed");report<<"PASS: box volume = 600 mm³\n";
    auto ring=make("Ring",{18,1.6,3});double expected=M_PI*(10.6*10.6-9*9)*3;if(std::abs(volume(ring)-expected)>1e-5)throw std::runtime_error("Ring dimensions test failed");report<<"PASS: 18 mm ring bore and solid cut\n";
    auto pad=make("Sketch pad",{13,7,2});if(std::abs(volume(pad)-182)>1e-5)throw std::runtime_error("Sketch solver test failed");report<<"PASS: FreeCAD solver, constrained 13 × 7 mm rectangle\n";
    BRepFilletAPI_MakeFillet fillet(box);TopTools_IndexedMapOfShape edges;TopExp::MapShapes(box,TopAbs_EDGE,edges);for(int i=1;i<=edges.Extent();++i)fillet.Add(0.2,TopoDS::Edge(edges(i)));fillet.Build();if(!fillet.IsDone())throw std::runtime_error("Fillet test failed");valid(fillet.Shape());report<<"PASS: real BREP edge fillet\n";
    if(!BinTools::Write(box,(root+"/kernel-test-binary.brep").c_str()))throw std::runtime_error("Binary BREP export failed");
    bool binaryMesh=false;auto binary=importShape(root+"/kernel-test-binary.brep","brep",binaryMesh);if(std::abs(volume(binary)-600)>1e-6)throw std::runtime_error("Binary BREP round-trip failed");report<<"PASS: binary BREP import fallback, volume retained\n";
    exportShape(ring,root+"/kernel-test.stl","stl");auto tri=RWStl::ReadFile((root+"/kernel-test.stl").c_str());if(tri.IsNull()||tri->NbTriangles()<100)throw std::runtime_error("STL round-trip failed");report<<"PASS: smooth binary STL round-trip ("<<tri->NbTriangles()<<" triangles)\n";
    exportShape(ring,root+"/kernel-test.step","step");bool meshOnly=false;auto round=importShape(root+"/kernel-test.step","step",meshOnly);if(std::abs(volume(round)-expected)>1e-3)throw std::runtime_error("STEP round-trip failed");report<<"PASS: STEP round-trip, volume retained\n";
    auto profile=advancedPrimitive("Rectangle",{10,6});auto extruded=advancedModel("Extrude solid",{profile},{0,0,2});valid(extruded);if(std::abs(volume(extruded)-120)>1e-5)throw std::runtime_error("Profile extrusion test failed");report<<"PASS: exact closed-profile extrusion = 120 mm³\n";
    auto section=advancedModel("Section",{box},{0,0,1,0,0,1,1});valid(section);if(!curveShape(section))throw std::runtime_error("Section test failed");report<<"PASS: exact plane section and XY flattening\n";
    auto subd=advancedPrimitive("Subdivision form",{16,12,20,3,1,20});if(triangleCount(subd)!=768)throw std::runtime_error("Subdivision test failed");report<<"PASS: Catmull-Clark closed cage = 768 triangles\n";
    return e->NewStringUTF(report.str().c_str());
}CATCH(nullptr)}

extern "C" JNIEXPORT jint JNICALL JNI(curve)(JNIEnv* e,jclass,jstring kind,jdoubleArray coords,jboolean closed,jint replace){GUARD {
    Object fresh;fresh.type=utf(e,kind);fresh.shape=pointCurve(fresh.type,doubles(e,coords,256),closed);valid(fresh.shape);
    if(replace>0){auto old=editable(replace);fresh.id=replace;fresh.color=old.color;fresh.roughness=old.roughness;fresh.metallic=old.metallic;fresh.visible=old.visible;fresh.name=old.name;fresh.layer=old.layer;fresh.locked=old.locked;fresh.graphOwned=old.graphOwned;fresh.x=old.x;fresh.y=old.y;fresh.z=old.z;checkpoint();scene[replace]=fresh;return replace;}
    checkpoint();return insert(fresh);
}CATCH(0)}
extern "C" JNIEXPORT jstring JNICALL JNI(curveData)(JNIEnv* e,jclass,jint id){GUARD {
    auto& o=object(id);if(!curveShape(o.shape))throw std::runtime_error("Select an open NURBS control-point curve");
    TopTools_IndexedMapOfShape edges;TopExp::MapShapes(o.shape,TopAbs_EDGE,edges);if(edges.Extent()!=1)throw std::runtime_error("Control-point editing needs one NURBS curve");
    TopLoc_Location loc;double a,b;auto geom=BRep_Tool::Curve(TopoDS::Edge(edges(1)),loc,a,b);auto c=Handle(Geom_BSplineCurve)::DownCast(geom);
    if(c.IsNull()||std::abs(a-c->FirstParameter())>1e-8||std::abs(b-c->LastParameter())>1e-8||c->IsPeriodic()||c->Degree()!=std::min(3,c->NbPoles()-1)||c->NbPoles()>64)throw std::runtime_error("Edit supports open cubic control-point NURBS. Other curves can be transformed or rebuilt.");
    for(int i=1;i<=c->NbKnots();i++)if(std::abs(c->Knot(i)-double(i-1)/(c->NbKnots()-1))>1e-8||c->Multiplicity(i)!=((i==1||i==c->NbKnots())?c->Degree()+1:1))throw std::runtime_error("This curve uses custom knots; keep it exact or create a new control-point curve");
    std::ostringstream out;out.imbue(std::locale::classic());out<<std::setprecision(12)<<'[';for(int i=1;i<=c->NbPoles();i++){if(i>1)out<<',';auto p=c->Pole(i).Transformed(loc.Transformation());out<<p.X()<<','<<p.Y()<<','<<p.Z()<<','<<c->Weight(i);}out<<']';return e->NewStringUTF(out.str().c_str());
}CATCH(nullptr)}
extern "C" JNIEXPORT jint JNICALL JNI(model)(JNIEnv* e,jclass,jstring kind,jintArray ids,jdoubleArray params){GUARD {
    if(!ids||e->GetArrayLength(ids)<1||e->GetArrayLength(ids)>8)throw std::runtime_error("Choose 1 to 8 input objects");
    std::vector<jint> keys(e->GetArrayLength(ids));e->GetIntArrayRegion(ids,0,keys.size(),keys.data());std::vector<TopoDS_Shape> shapes;std::set<int> seen;auto type=utf(e,kind);bool meshRepair=type=="Repair mesh";
    for(int id:keys){auto& o=object(id);if(!seen.insert(id).second)throw std::runtime_error("Use different input objects");if(o.meshOnly&&!meshRepair)throw std::runtime_error("Exact modelling tools need CAD curves or surfaces; imported meshes support transforms and mesh export");shapes.push_back(o.shape);}
    Object result;result.type=meshRepair?"STL mesh":type;result.meshOnly=meshRepair;result.shape=advancedModel(type,shapes,doubles(e,params));if(!meshRepair)valid(result.shape);if(!meshRepair&&!TopExp_Explorer(result.shape,TopAbs_EDGE).More())throw std::runtime_error("Tool produced no geometry");
    checkpoint();return insert(result);
}CATCH(0)}
extern "C" JNIEXPORT jint JNICALL JNI(array)(JNIEnv* e,jclass,jint id,jstring kind,jint count,jdoubleArray params){GUARD {
    auto source=object(id);auto type=utf(e,kind);auto p=doubles(e,params);if(count<2||count>100)throw std::runtime_error("Array count must be 2 to 100");if(p.size()!=4)throw std::runtime_error("Array needs X, Y, Z and total angle");
    if(source.meshOnly&&triangleCount(source.shape)*size_t(count)>MaxStlTriangles)throw std::runtime_error("Mesh array exceeds 2,000,000 triangles");
    TopoDS_Compound compound;BRep_Builder b;b.MakeCompound(compound);for(int i=0;i<count;i++){auto copy=source;gp_Trsf t;
        if(type=="Linear array"){checkPosition(p[0]*i,p[1]*i,p[2]*i);t.SetTranslation(gp_Vec(p[0]*i,p[1]*i,p[2]*i));}
        else if(type=="Polar array"){if(std::abs(p[3])<.01||std::abs(p[3])>360)throw std::runtime_error("Polar total angle must be 0.01 to 360 degrees in magnitude");checkPosition(p[0],p[1],p[2]);double step=std::abs(p[3])==360?p[3]/count:p[3]/(count-1);t.SetRotation(gp_Ax1(gp_Pnt(p[0],p[1],p[2]),gp_Dir(0,0,1)),step*i*M_PI/180);}
        else throw std::runtime_error("Unknown array type");transform(copy,t);b.Add(compound,copy.shape);
    }Object result;result.type=source.meshOnly?"STL mesh":type;result.meshOnly=source.meshOnly;result.color=source.color;result.roughness=source.roughness;result.metallic=source.metallic;result.shape=compound;checkpoint();return insert(result);
}CATCH(0)}
extern "C" JNIEXPORT jint JNICALL JNI(mirror)(JNIEnv* e,jclass,jint id,jdoubleArray params){GUARD {
    auto p=doubles(e,params);if(p.size()!=6)throw std::runtime_error("Mirror needs plane point and normal");checkPosition(p[0],p[1],p[2]);gp_Vec normal(p[3],p[4],p[5]);if(normal.Magnitude()<1e-9)throw std::runtime_error("Mirror plane normal cannot be zero");
    auto fresh=object(id);fresh.graphOwned=false;gp_Trsf t;t.SetMirror(gp_Ax2(gp_Pnt(p[0],p[1],p[2]),gp_Dir(normal)));transform(fresh,t,true);fresh.type=fresh.meshOnly?"STL mesh":curveShape(fresh.shape)?"BREP curve":"BREP solid";fresh.dims.clear();fresh.x=fresh.y=fresh.z=0;checkpoint();return insert(fresh);
}CATCH(0)}
extern "C" JNIEXPORT void JNICALL JNI(material)(JNIEnv* e,jclass,jint id,jdoubleArray params){GUARD {
    auto p=doubles(e,params);if(p.size()!=3)throw std::runtime_error("Colour needs red, green and blue");for(double v:p)if(v<0||v>1)throw std::runtime_error("Colour channels must be 0 to 1");auto fresh=object(id);fresh.color={float(p[0]),float(p[1]),float(p[2])};checkpoint();scene[id]=fresh;
}CATCH()}
extern "C" JNIEXPORT jstring JNICALL JNI(analyze)(JNIEnv* e,jclass,jint id,jdouble draft){GUARD {auto& o=object(id);auto s=inspectShape(o.shape,o.meshOnly,draft);return e->NewStringUTF(s.c_str());}CATCH(nullptr)}
extern "C" JNIEXPORT jdouble JNICALL JNI(distance)(JNIEnv* e,jclass,jint first,jint second){GUARD {auto& a=object(first);auto& b=object(second);if(a.meshOnly||b.meshOnly||first==second)throw std::runtime_error("Distance needs two different CAD objects");BRepExtrema_DistShapeShape measure(a.shape,b.shape);measure.Perform();if(!measure.IsDone())throw std::runtime_error("Distance calculation failed");return measure.Value();}CATCH(0)}
extern "C" JNIEXPORT jfloatArray JNICALL JNI(lines)(JNIEnv* e,jclass,jint selected){GUARD {
    std::vector<float> out;for(auto& [id,o]:scene)if(o.visible&&curveShape(o.shape)){auto edges=sampleEdges(o.shape);for(auto& line:edges)for(size_t i=1;i<line.size();i++){if(out.size()>=400000)throw std::runtime_error("Visible curves exceed the mobile display budget; hide some curves");for(auto p:{line[i-1],line[i]})out.insert(out.end(),{float(p.X()),float(p.Y()),float(p.Z()),0,0,1,std::min(1.f,o.color[0]+(id==selected?.14f:0)),std::min(1.f,o.color[1]+(id==selected?.14f:0)),std::min(1.f,o.color[2]+(id==selected?.14f:0)),1});}}
    auto a=e->NewFloatArray(out.size());if(a&&!out.empty())e->SetFloatArrayRegion(a,0,out.size(),out.data());return a;
}CATCH(nullptr)}

extern "C" JNIEXPORT void JNICALL JNI(markGraphOwned)(JNIEnv* e,jclass,jint id,jboolean owned){GUARD {auto& o=object(id);if(o.graphOwned!=bool(owned)){checkpoint();o.graphOwned=owned;}}CATCH()}
extern "C" JNIEXPORT jboolean JNICALL JNI(redo)(JNIEnv* e,jclass){GUARD {if(future.empty())return false;history.push_back(State{scene,workspace});scene=std::move(future.back().objects);workspace=std::move(future.back().workspace);future.pop_back();trimHistory();return true;}CATCH(false)}
extern "C" JNIEXPORT jstring JNICALL JNI(getWorkspace)(JNIEnv* e,jclass){GUARD {return e->NewStringUTF(workspace.c_str());}CATCH(nullptr)}
extern "C" JNIEXPORT void JNICALL JNI(setWorkspace)(JNIEnv* e,jclass,jstring text){GUARD {auto value=utf(e,text);if(value.size()>1024*1024)throw std::runtime_error("Workspace recipe metadata exceeds 1 MiB");if(value!=workspace){checkpoint();workspace=std::move(value);}}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(properties)(JNIEnv* e,jclass,jint id,jstring name,jstring layer,jboolean locked){GUARD {auto n=utf(e,name),l=utf(e,layer);if(n.size()>256||l.empty()||l.size()>128)throw std::runtime_error("Name must fit 256 bytes and layer 1 to 128 bytes");auto& o=object(id);if(o.name!=n||o.layer!=l||o.locked!=bool(locked)){checkpoint();o.name=n;o.layer=l;o.locked=locked;}}CATCH()}
int filteredPick(const std::vector<double>& p,const std::string& filter){
    if(p.size()!=7||p[6]<=0||p[6]>1000000)throw std::runtime_error("Invalid pick ray");gp_Pnt origin(p[0],p[1],p[2]);gp_Vec direction(p[3],p[4],p[5]);if(direction.SquareMagnitude()<1e-15)throw std::runtime_error("Invalid pick direction");direction.Normalize();double nearest=1e100;int hit=0;
    if(filter!="All"&&filter!="Solids"&&filter!="Curves"&&filter!="Surfaces"&&filter!="Meshes")throw std::runtime_error("Unknown object selection filter");
    for(auto& [id,o]:scene)if(o.visible&&!o.locked){bool curve=curveShape(o.shape),solid=TopExp_Explorer(o.shape,TopAbs_SOLID).More();if(filter=="Solids"&&(o.meshOnly||!solid)||filter=="Curves"&&!curve||filter=="Surfaces"&&(o.meshOnly||solid||curve)||filter=="Meshes"&&!o.meshOnly)continue;
        if(!o.meshOnly&&TopExp_Explorer(o.shape,TopAbs_FACE).More()){IntCurvesFace_ShapeIntersector scan;scan.Load(o.shape,1e-7);scan.Perform(gp_Lin(origin,gp_Dir(direction)),0,1e8);if(scan.IsDone())for(int i=1;i<=scan.NbPnt();i++)if(scan.WParameter(i)>=0&&scan.WParameter(i)<nearest){nearest=scan.WParameter(i);hit=id;}}
        else if(o.meshOnly&&o.preview){const auto& m=*o.preview;for(size_t i=0;i+2<m.indices.size();i+=3){const auto& a=m.vertices[m.indices[i]];const auto& b=m.vertices[m.indices[i+1]];const auto& c=m.vertices[m.indices[i+2]];gp_Pnt q(a.x,a.y,a.z);gp_Vec u(q,gp_Pnt(b.x,b.y,b.z)),v(q,gp_Pnt(c.x,c.y,c.z)),h=direction.Crossed(v);double det=u.Dot(h);if(std::abs(det)<1e-12)continue;gp_Vec d(q,origin);double x=d.Dot(h)/det;if(x<0||x>1)continue;gp_Vec cross=d.Crossed(u);double y=direction.Dot(cross)/det;if(y<0||x+y>1)continue;double t=v.Dot(cross)/det;if(t>=0&&t<nearest){nearest=t;hit=id;}}}
        else if(curveShape(o.shape)){for(const auto& line:sampleEdges(o.shape))for(size_t i=1;i<line.size();i++){gp_Vec v(line[i-1],line[i]),r(line[i-1],origin);double c=v.SquareMagnitude(),b=direction.Dot(v),den=c-b*b;if(c<1e-15)continue;double t=std::abs(den)>1e-15?(b*v.Dot(r)-c*direction.Dot(r))/den:0;double u=std::max(0.,std::min(1.,(v.Dot(r)+b*t)/c));gp_Pnt q=line[i-1].Translated(v*u);t=gp_Vec(origin,q).Dot(direction);if(t>=0&&t<nearest&&q.Distance(origin.Translated(direction*t))<=p[6]){nearest=t;hit=id;}}}
    }return hit;
}
extern "C" JNIEXPORT jint JNICALL JNI(pick)(JNIEnv* e,jclass,jdoubleArray ray){GUARD {return filteredPick(doubles(e,ray),"All");}CATCH(0)}
extern "C" JNIEXPORT jint JNICALL JNI(pickFiltered)(JNIEnv* e,jclass,jdoubleArray ray,jstring filter){GUARD {return filteredPick(doubles(e,ray),utf(e,filter));}CATCH(0)}
extern "C" JNIEXPORT jint JNICALL JNI(textSolid)(JNIEnv* e,jclass,jdoubleArray xy,jintArray counts,jdouble depth){GUARD {if(!counts||e->GetArrayLength(counts)>256)throw std::runtime_error("Invalid text contours");std::vector<int> n(e->GetArrayLength(counts));if(!n.empty())e->GetIntArrayRegion(counts,0,n.size(),n.data());if(e->ExceptionCheck())throw std::runtime_error("Cannot read text contours");Object result;result.type="Text solid";result.shape=textContours(doubles(e,xy,32768),n,depth);valid(result.shape);checkpoint();return insert(result);}CATCH(0)}
extern "C" JNIEXPORT jint JNICALL JNI(arrayCurve)(JNIEnv* e,jclass,jint source,jint rail,jint count,jboolean orient){GUARD {auto a=object(source),b=object(rail);if(source==rail||a.meshOnly||b.meshOnly||!curveShape(b.shape))throw std::runtime_error("Choose a CAD source and a different single curve rail");Object result;result.type="Curve array";result.color=a.color;result.roughness=a.roughness;result.metallic=a.metallic;result.layer=a.layer;result.shape=alongCurve(a.shape,b.shape,count,orient);valid(result.shape);checkpoint();return insert(result);}CATCH(0)}

extern "C" JNIEXPORT void JNICALL JNI(rebuild)(JNIEnv* e,jclass,jint target,jstring kind,jintArray ids,jdoubleArray params){GUARD {
 auto fresh=editable(target);if(!ids||e->GetArrayLength(ids)<1||e->GetArrayLength(ids)>8)throw std::runtime_error("Feature needs 1 to 8 inputs");std::vector<jint> keys(e->GetArrayLength(ids));e->GetIntArrayRegion(ids,0,keys.size(),keys.data());std::vector<TopoDS_Shape> shapes;std::set<int> seen;for(int id:keys){if(id==target||!seen.insert(id).second)throw std::runtime_error("Invalid feature dependency");auto& o=object(id);if(o.meshOnly)throw std::runtime_error("Feature rebuild requires exact CAD geometry");shapes.push_back(o.shape);}auto type=utf(e,kind);auto p=doubles(e,params);
 if(type=="Union"||type=="Cut"||type=="Intersect"){if(shapes.size()!=2||!p.empty())throw std::runtime_error("Boolean feature needs two inputs");if(type=="Union"){BRepAlgoAPI_Fuse f(shapes[0],shapes[1]);f.Build();if(!f.IsDone())throw std::runtime_error("Union recompute failed");fresh.shape=f.Shape();}else if(type=="Cut"){BRepAlgoAPI_Cut f(shapes[0],shapes[1]);f.Build();if(!f.IsDone())throw std::runtime_error("Cut recompute failed");fresh.shape=f.Shape();}else{BRepAlgoAPI_Common f(shapes[0],shapes[1]);f.Build();if(!f.IsDone())throw std::runtime_error("Intersect recompute failed");fresh.shape=f.Shape();}if(volume(fresh.shape)<1e-9)throw std::runtime_error("Boolean recompute produced no solid volume");}
 else if(type=="Fillet"){if(shapes.size()!=1||p.size()!=1||p[0]<.001||p[0]>1000)throw std::runtime_error("Invalid fillet feature");BRepFilletAPI_MakeFillet f(shapes[0]);TopTools_IndexedMapOfShape m;TopExp::MapShapes(shapes[0],TopAbs_EDGE,m);for(int i=1;i<=m.Extent();i++)f.Add(p[0],TopoDS::Edge(m(i)));f.Build();if(!f.IsDone())throw std::runtime_error("Fillet recompute failed");fresh.shape=f.Shape();}
 else fresh.shape=advancedModel(type,shapes,p);valid(fresh.shape);fresh.type=type;fresh.dims.clear();fresh.preview.reset();fresh.x=fresh.y=fresh.z=0;checkpoint();scene[target]=fresh;
}CATCH()}
extern "C" JNIEXPORT jstring JNICALL JNI(topology)(JNIEnv* e,jclass,jint id){GUARD {auto& o=object(id);if(o.meshOnly)throw std::runtime_error("Indexed topology tools require CAD geometry");auto text=topologyData(o.shape);return e->NewStringUTF(text.c_str());}CATCH(nullptr)}
extern "C" JNIEXPORT jstring JNICALL JNI(surfaceData)(JNIEnv* e,jclass,jint id){GUARD {auto text=surfacePoles(object(id).shape);return e->NewStringUTF(text.c_str());}CATCH(nullptr)}
extern "C" JNIEXPORT jstring JNICALL JNI(curvature)(JNIEnv* e,jclass,jint id){GUARD {auto text=curveCurvature(object(id).shape);return e->NewStringUTF(text.c_str());}CATCH(nullptr)}
extern "C" JNIEXPORT void JNICALL JNI(surfacePole)(JNIEnv* e,jclass,jint id,jdoubleArray params){GUARD {auto fresh=editable(id);fresh.shape=changeSurfacePole(fresh.shape,doubles(e,params));valid(fresh.shape);fresh.type="BREP solid";fresh.dims.clear();fresh.preview.reset();checkpoint();scene[id]=fresh;}CATCH()}
extern "C" JNIEXPORT jdoubleArray JNICALL JNI(samplePoint)(JNIEnv* e,jclass,jint id,jdoubleArray params){GUARD {
 auto& o=object(id);if(o.meshOnly)throw std::runtime_error("Parametric point sampling requires exact CAD geometry");auto p=doubles(e,params);gp_Pnt point;
 for(double v:p)if(v<0||v>1)throw std::runtime_error("Point parameter fractions must be in [0,1]");
 if(p.size()==1){TopTools_IndexedMapOfShape m;TopExp::MapShapes(o.shape,TopAbs_EDGE,m);if(m.Extent()!=1)throw std::runtime_error("Curve point requires one edge");BRepAdaptor_Curve c(TopoDS::Edge(m(1)));point=c.Value(c.FirstParameter()+(c.LastParameter()-c.FirstParameter())*p[0]);}
 else if(p.size()==2){TopTools_IndexedMapOfShape m;TopExp::MapShapes(o.shape,TopAbs_FACE,m);if(m.Extent()!=1)throw std::runtime_error("Surface point requires one face");auto face=TopoDS::Face(m(1));double a,b,c,d;BRepTools::UVBounds(face,a,b,c,d);TopLoc_Location loc;auto surface=BRep_Tool::Surface(face,loc);if(surface.IsNull())throw std::runtime_error("Face has no exact surface");point=surface->Value(a+(b-a)*p[0],c+(d-c)*p[1]).Transformed(loc.Transformation());}
 else throw std::runtime_error("Point evaluation needs one curve fraction or two surface fractions");double v[3]={point.X(),point.Y(),point.Z()};auto result=e->NewDoubleArray(3);if(result)e->SetDoubleArrayRegion(result,0,3,v);return result;
}CATCH(nullptr)}

extern "C" JNIEXPORT void JNICALL JNI(beginPreview)(JNIEnv* e,jclass){GUARD {if(!transaction||previewState)throw std::runtime_error("Preview needs one active CAD transaction");previewState=std::make_unique<PreviewState>(PreviewState{scene,workspace,nextId,transaction->dirty});}CATCH()}
extern "C" JNIEXPORT void JNICALL JNI(endPreview)(JNIEnv* e,jclass){GUARD {if(!transaction||!previewState)throw std::runtime_error("No preview transaction");scene=std::move(previewState->objects);workspace=std::move(previewState->workspace);nextId=previewState->next;transaction->dirty=previewState->dirty;previewState.reset();}CATCH()}
extern "C" JNIEXPORT jint JNICALL JNI(drawing)(JNIEnv* e,jclass,jdoubleArray params,jintArray kinds){GUARD {
 auto p=doubles(e,params,12000);if(!kinds||e->GetArrayLength(kinds)<1||e->GetArrayLength(kinds)>2000)throw std::runtime_error("Drawing needs 1 to 2,000 curve segments");std::vector<jint> types(e->GetArrayLength(kinds));e->GetIntArrayRegion(kinds,0,types.size(),types.data());TopoDS_Compound compound;BRep_Builder builder;builder.MakeCompound(compound);size_t offset=0;
 for(int kind:types){size_t count=kind==1?4:6;if(kind<0||kind>2||offset+count>p.size())throw std::runtime_error("Invalid drawing segments");gp_Pnt origin(p[offset],p[offset+1],p[offset+2]);checkPosition(origin.X(),origin.Y(),origin.Z());TopoDS_Edge edge;
  if(kind==0){gp_Pnt end(p[offset+3],p[offset+4],p[offset+5]);checkPosition(end.X(),end.Y(),end.Z());if(origin.Distance(end)<1e-6)throw std::runtime_error("Drawing has a zero-length line");edge=BRepBuilderAPI_MakeEdge(origin,end).Edge();}
  else {double radius=p[offset+3];if(radius<.001||radius>10000)throw std::runtime_error("Drawing radius must be 0.001 to 10,000 mm");gp_Circ circle(gp_Ax2(origin,gp_Dir(0,0,1)),radius);if(kind==1)edge=BRepBuilderAPI_MakeEdge(circle).Edge();else{double start=p[offset+4],end=p[offset+5];if(std::abs(start)>1000000||std::abs(end)>1000000)throw std::runtime_error("Invalid arc angles");double span=std::fmod(end-start,360);if(span<=0)span+=360;start=std::remainder(start,360)*M_PI/180;edge=BRepBuilderAPI_MakeEdge(circle,start,start+span*M_PI/180).Edge();}}
  builder.Add(compound,BRepBuilderAPI_MakeWire(edge).Wire());offset+=count;
 }if(offset!=p.size())throw std::runtime_error("Extra drawing coordinates");Object result;result.type="BREP curve";result.shape=compound;valid(result.shape);checkpoint();return insert(result);
}CATCH(0)}
extern "C" JNIEXPORT jstring JNICALL JNI(thickness)(JNIEnv* e,jclass,jint id,jdouble threshold){GUARD {auto& o=object(id);if(o.meshOnly)throw std::runtime_error("Sampled thickness requires exact CAD solids");auto text=sampledThickness(o.shape,threshold);return e->NewStringUTF(text.c_str());}CATCH(nullptr)}

extern "C" JNIEXPORT void JNICALL JNI(surfaceMaterial)(JNIEnv* e,jclass,jint id,jdoubleArray params){GUARD {auto p=doubles(e,params);if(p.size()!=2||p[0]<.04||p[0]>1||p[1]<0||p[1]>1)throw std::runtime_error("Roughness must be .04 to 1 and metallic 0 to 1");auto fresh=object(id);fresh.roughness=p[0];fresh.metallic=p[1];checkpoint();scene[id]=fresh;}CATCH()}
extern "C" JNIEXPORT jfloatArray JNICALL JNI(surfaceValues)(JNIEnv* e,jclass){GUARD {std::vector<float> out;for(auto& [id,o]:scene)if(o.visible&&triangleCount(o.shape)>0){if(!o.preview)throw std::runtime_error("Build the display mesh before reading materials");for(size_t i=0;i<o.preview->indices.size();i++){out.push_back(o.roughness);out.push_back(o.metallic);}}if(out.size()>1200000)throw std::runtime_error("Material display budget exceeded");auto a=e->NewFloatArray(out.size());if(a&&!out.empty())e->SetFloatArrayRegion(a,0,out.size(),out.data());return a;}CATCH(nullptr)}

extern "C" JNIEXPORT jintArray JNICALL JNI(pickElement)(JNIEnv* e,jclass,jdoubleArray ray,jint kind){GUARD {auto p=doubles(e,ray);if(p.size()!=7||p[6]<=0||p[6]>1000000||kind<1||kind>3)throw std::runtime_error("Invalid topology selection ray");gp_Pnt origin(p[0],p[1],p[2]);gp_Vec direction(p[3],p[4],p[5]);if(direction.SquareMagnitude()<1e-15)throw std::runtime_error("Invalid ray direction");direction.Normalize();double nearest=1e100;int hit[3]={0,kind,0};auto line=gp_Lin(origin,gp_Dir(direction));auto rayEdge=BRepBuilderAPI_MakeEdge(line,0,1e8).Edge();
 for(auto& [id,o]:scene)if(o.visible&&!o.locked&&!o.meshOnly){TopTools_IndexedMapOfShape m;TopExp::MapShapes(o.shape,kind==1?TopAbs_FACE:kind==2?TopAbs_EDGE:TopAbs_VERTEX,m);if(m.Extent()>2000)throw std::runtime_error("Topology selection supports up to 2,000 subelements per object");if(kind==1){IntCurvesFace_ShapeIntersector scan;scan.Load(o.shape,1e-7);scan.Perform(line,0,1e8);if(scan.IsDone())for(int i=1;i<=scan.NbPnt();i++)if(scan.WParameter(i)>=0&&scan.WParameter(i)<nearest){nearest=scan.WParameter(i);hit[0]=id;hit[2]=m.FindIndex(scan.Face(i));}}
 else for(int i=1;i<=m.Extent();i++){gp_Pnt q;if(kind==2){BRepExtrema_DistShapeShape distance(m(i),rayEdge);distance.Perform();if(!distance.IsDone()||distance.NbSolution()<1||distance.Value()>p[6])continue;q=distance.PointOnShape1(1);}else q=BRep_Tool::Pnt(TopoDS::Vertex(m(i)));double t=gp_Vec(origin,q).Dot(direction);if(t>=0&&t<nearest&&q.Distance(origin.Translated(direction*t))<=p[6]){nearest=t;hit[0]=id;hit[2]=i;}}
 }auto a=e->NewIntArray(3);if(a)e->SetIntArrayRegion(a,0,3,hit);return a;
}CATCH(nullptr)}
