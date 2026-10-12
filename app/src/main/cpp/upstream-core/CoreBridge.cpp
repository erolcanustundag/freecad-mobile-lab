// SPDX-License-Identifier: LGPL-2.1-or-later
#include <Python.h>
#include <jni.h>
#include <QtCore/QString>
#include <cstdlib>
#include <mutex>
#include <stdexcept>
#include <string>

extern "C" PyObject* PyInit_FreeCAD();
namespace {
std::mutex serial;
PyObject* dispatcher = nullptr;
bool attempted = false;
std::string utf8(JNIEnv* env, jstring input) {
    if (!input) throw std::runtime_error("Missing argument");
    const jchar* chars = env->GetStringChars(input, nullptr);
    if (!chars) throw std::runtime_error("Cannot read Java string");
    const auto bytes = QString::fromUtf16(reinterpret_cast<const char16_t*>(chars),
        env->GetStringLength(input)).toUtf8();
    env->ReleaseStringChars(input, chars);
    return std::string(bytes.constData(), bytes.size());
}
std::string pythonError() {
    PyObject *type=nullptr, *value=nullptr, *trace=nullptr;
    PyErr_Fetch(&type,&value,&trace);
    PyErr_NormalizeException(&type,&value,&trace);
    PyObject* description=value ? PyObject_Str(value) : nullptr;
    const char* text=description ? PyUnicode_AsUTF8(description) : nullptr;
    std::string message=text ? text : "Embedded Python operation failed";
    Py_XDECREF(description);Py_XDECREF(type);Py_XDECREF(value);Py_XDECREF(trace);
    PyErr_Clear();return message;
}
void fail(JNIEnv* env, const std::string& message) {
    // ThrowNew expects modified UTF8. Create the message via UTF16 instead.
    const QString text=QString::fromUtf8(message.data(),message.size());
    jstring msg=env->NewString(reinterpret_cast<const jchar*>(text.utf16()),text.size());
    jclass cls=env->FindClass("java/lang/IllegalStateException");
    jmethodID ctor=env->GetMethodID(cls,"<init>","(Ljava/lang/String;)V");
    jobject exception=env->NewObject(cls,ctor,msg);
    env->Throw(static_cast<jthrowable>(exception));
    env->DeleteLocalRef(exception);env->DeleteLocalRef(msg);env->DeleteLocalRef(cls);
}
void status(PyStatus value) {
    if (PyStatus_Exception(value)) throw std::runtime_error(value.err_msg ? value.err_msg : "Python configuration failed");
}
}

extern "C" JNIEXPORT void JNICALL
Java_org_freecad_mobilelab_CoreNative_initialize(JNIEnv* env,jclass,jstring home,jstring scriptRoot,jstring documentRoot) {
    std::lock_guard<std::mutex> lock(serial);
    if(dispatcher) return;
    if(attempted){fail(env,"Core startup failed earlier. Close and reopen the document lab.");return;}
    attempted=true;
    try {
        const std::string root=utf8(env,home),scripts=utf8(env,scriptRoot),documents=utf8(env,documentRoot);
        setenv("FREECAD_USER_HOME",documents.c_str(),1);
        setenv("FREECAD_USER_DATA",documents.c_str(),1);
        setenv("FREECAD_USER_TEMP",(root+"/tmp").c_str(),1);
        if(PyImport_AppendInittab("FreeCAD",PyInit_FreeCAD)==-1) throw std::runtime_error("Cannot register FreeCAD Python module");
        PyConfig config;PyConfig_InitIsolatedConfig(&config);
        config.install_signal_handlers=0;config.write_bytecode=0;config.parse_argv=0;
        try {
            status(PyConfig_SetBytesString(&config,&config.home,root.c_str()));
            status(PyConfig_SetBytesString(&config,&config.program_name,"FreeCADMobileCore"));
            status(Py_InitializeFromConfig(&config));
        } catch(...) {PyConfig_Clear(&config);throw;}
        PyConfig_Clear(&config);
        PyObject* path=PySys_GetObject("path");
        PyObject* folder=PyUnicode_DecodeFSDefault(scripts.c_str());
        if(!folder || PyList_Insert(path,0,folder)!=0){Py_XDECREF(folder);throw std::runtime_error(pythonError());}
        Py_DECREF(folder);
        PyObject* module=PyImport_ImportModule("mobile_core");
        if(!module) throw std::runtime_error(pythonError());
        PyObject* configured=PyObject_CallMethod(module,"configure","s",documents.c_str());
        if(!configured){Py_DECREF(module);throw std::runtime_error(pythonError());}
        Py_DECREF(configured);
        dispatcher=PyObject_GetAttrString(module,"dispatch");Py_DECREF(module);
        if(!dispatcher)throw std::runtime_error(pythonError());
        PyEval_SaveThread(); // All subsequent calls acquire the GIL on their worker.
    } catch(const std::exception& e){fail(env,e.what());}
}

extern "C" JNIEXPORT jstring JNICALL
Java_org_freecad_mobilelab_CoreNative_request(JNIEnv* env,jclass,jstring input) {
    std::lock_guard<std::mutex> lock(serial);
    if(!dispatcher){fail(env,"Document core is not initialized");return nullptr;}
    PyGILState_STATE gil=PyGILState_Ensure();
    jstring output=nullptr;
    try {
        const auto text=utf8(env,input);
        if(text.size()>65536)throw std::runtime_error("Command exceeds 64 KiB");
        PyObject* arg=PyUnicode_DecodeUTF8(text.data(),text.size(),"strict");
        if(!arg)throw std::runtime_error(pythonError());
        PyObject* result=PyObject_CallFunctionObjArgs(dispatcher,arg,nullptr);Py_DECREF(arg);
        if(!result)throw std::runtime_error(pythonError());
        const char* bytes=PyUnicode_AsUTF8(result);
        if(!bytes){Py_DECREF(result);throw std::runtime_error(pythonError());}
        // The dispatcher always uses ensure_ascii=True.
        output=env->NewStringUTF(bytes);Py_DECREF(result);
    } catch(const std::exception& e){fail(env,e.what());}
    PyGILState_Release(gil);return output;
}
