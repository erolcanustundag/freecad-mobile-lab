#!/usr/bin/env python3
"""Compile the app's real shaders and exercise a VBO/VAO draw in a GLES 3 pbuffer.

Set GLES_LIBRARY_DIR to an EGL/GLESv2 pair (e.g. the Android emulator's
lib64/gles_swiftshader); set LD_LIBRARY_PATH to its companion lib64 directory.
This checks the actual GLSL and draw path, not Android Activity integration.
"""
import ctypes as c
import json
import os
from pathlib import Path
import re

I,U,P=c.c_int,c.c_uint,c.c_void_p

def bind(lib,name,result,args):
    f=getattr(lib,name);f.restype=result;f.argtypes=args;return f

root=Path(__file__).resolve().parents[1]
directory=Path(os.environ['GLES_LIBRARY_DIR'])
egl=c.CDLL(str(directory/'libEGL.so'),mode=c.RTLD_GLOBAL)
gl=c.CDLL(str(directory/'libGLESv2.so'))
d=bind(egl,'eglGetDisplay',P,[P])(None)
major=I();minor=I()
assert bind(egl,'eglInitialize',U,[P,c.POINTER(I),c.POINTER(I)])(d,c.byref(major),c.byref(minor)), 'Cannot initialize EGL'
attrs=(I*13)(0x3033,1,0x3040,0x40,0x3024,8,0x3023,8,0x3022,8,0x3025,16,0x3038)
config=P();count=I()
assert bind(egl,'eglChooseConfig',U,[P,c.POINTER(I),c.POINTER(P),I,c.POINTER(I)])(d,attrs,c.byref(config),1,c.byref(count)) and count.value
assert bind(egl,'eglBindAPI',U,[U])(0x30a0)
surface=bind(egl,'eglCreatePbufferSurface',P,[P,P,c.POINTER(I)])(d,config,(I*5)(0x3057,64,0x3056,64,0x3038))
context=bind(egl,'eglCreateContext',P,[P,P,P,c.POINTER(I)])(d,config,None,(I*3)(0x3098,3,0x3038))
assert surface and context
assert bind(egl,'eglMakeCurrent',U,[P,P,P,P])(d,surface,surface,context)
print('GLES renderer:',bind(gl,'glGetString',c.c_char_p,[U])(0x1f01).decode())
print('GLES version:',bind(gl,'glGetString',c.c_char_p,[U])(0x1f02).decode())

def compile_shader(kind,source,expect=True):
    shader=bind(gl,'glCreateShader',U,[U])(kind)
    raw=c.c_char_p(source.encode())
    bind(gl,'glShaderSource',None,[U,I,c.POINTER(c.c_char_p),c.POINTER(I)])(shader,1,c.byref(raw),None)
    bind(gl,'glCompileShader',None,[U])(shader)
    status=I();bind(gl,'glGetShaderiv',None,[U,U,c.POINTER(I)])(shader,0x8b81,c.byref(status))
    log=c.create_string_buffer(4096)
    bind(gl,'glGetShaderInfoLog',None,[U,I,c.POINTER(I),c.c_char_p])(shader,4096,None,log)
    assert bool(status.value)==expect, log.value.decode()
    if not expect:print('PASS: original reserved-uniform shader defect reproduced:',log.value.decode().strip())
    return shader

# This is the actual invalid name used by v0.1, rather than a mocked failure.
compile_shader(0x8b30,'#version 300 es\nprecision highp float;uniform bool flat;out vec4 result;void main(){result=vec4(1.0);}',False)
source=(root/'app/src/main/java/org/freecad/mobilelab/Shaders.java').read_text()
codes={name:json.loads(re.search(r'String '+name+r'\s*=\s*("(?:[^"\\]|\\.)*")',source).group(1)) for name in ['VERTEX','FRAGMENT']}
vs=compile_shader(0x8b31,codes['VERTEX']);fs=compile_shader(0x8b30,codes['FRAGMENT'])
program=bind(gl,'glCreateProgram',U,[])()
attach=bind(gl,'glAttachShader',None,[U,U]);attach(program,vs);attach(program,fs)
bind(gl,'glLinkProgram',None,[U])(program)
status=I();bind(gl,'glGetProgramiv',None,[U,U,c.POINTER(I)])(program,0x8b82,c.byref(status))
assert status.value,'App shaders could not link'
print('PASS: actual app vertex/fragment shader compilation and program link')
bind(gl,'glUseProgram',None,[U])(program)
location=bind(gl,'glGetUniformLocation',I,[U,c.c_char_p])
identity=(c.c_float*16)(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1)
uniform_matrix=bind(gl,'glUniformMatrix4fv',None,[I,I,c.c_ubyte,c.POINTER(c.c_float)])
for name in [b'mvp',b'mv']:uniform_matrix(location(program,name),1,0,identity)
uniform_bool=bind(gl,'glUniform1i',None,[I,I])
vertices=[]
for x,y in [(-.8,-.8),(.8,-.8),(0,.8)]:vertices.extend([x,y,0,0,0,1,.2,.8,.4,1])
data=(c.c_float*len(vertices))(*vertices)
vao=U();bind(gl,'glGenVertexArrays',None,[I,c.POINTER(U)])(1,c.byref(vao));bind(gl,'glBindVertexArray',None,[U])(vao)
vbo=U();bind(gl,'glGenBuffers',None,[I,c.POINTER(U)])(1,c.byref(vbo));bind(gl,'glBindBuffer',None,[U,U])(0x8892,vbo)
bind(gl,'glBufferData',None,[U,c.c_ssize_t,P,U])(0x8892,c.sizeof(data),data,0x88e4)
for index,size,offset in [(0,3,0),(1,3,12),(2,4,24)]:
    bind(gl,'glVertexAttribPointer',None,[U,I,U,c.c_ubyte,I,P])(index,size,0x1406,0,40,offset)
    bind(gl,'glEnableVertexAttribArray',None,[U])(index)
bind(gl,'glViewport',None,[I,I,I,I])(0,0,64,64)
clear=bind(gl,'glClear',None,[U]);bind(gl,'glClearColor',None,[c.c_float]*4)(0,0,0,1)
for unlit in [1,0]:
    clear(0x4000);uniform_bool(location(program,b'unlit'),unlit)
    bind(gl,'glDrawArrays',None,[U,I,I])(0x0004,0,3)
    pixel=(c.c_ubyte*4)();bind(gl,'glReadPixels',None,[I,I,I,I,U,U,P])(32,32,1,1,0x1908,0x1401,pixel)
    error=bind(gl,'glGetError',U,[])();assert error==0,hex(error)
    assert pixel[1]>pixel[0] and pixel[1]>pixel[2] and pixel[1]>40,list(pixel)
    print('PASS:', 'unlit shader' if unlit else 'lit shader','VBO/VAO triangle draw, center pixel',list(pixel))
# Exercise the new fragment paths and clip discard against actual pixels.
bind(gl,'glVertexAttrib2f',None,[U,c.c_float,c.c_float])(3,.25,.85)
for style in [1,2]:
    clear(0x4000);uniform_bool(location(program,b'unlit'),0);uniform_bool(location(program,b'style'),style)
    bind(gl,'glDrawArrays',None,[U,I,I])(0x0004,0,3)
    pixel=(c.c_ubyte*4)();bind(gl,'glReadPixels',None,[I,I,I,I,U,U,P])(32,32,1,1,0x1908,0x1401,pixel)
    assert bind(gl,'glGetError',U,[])()==0
    if style==1:assert pixel[1]>pixel[0] and pixel[1]>pixel[2],list(pixel)
    else:assert pixel[0]==pixel[1]==pixel[2] and pixel[0] in [15,16,239,240],list(pixel)
    print('PASS:', 'GGX material' if style==1 else 'zebra normals','real fragment draw',list(pixel))
clear(0x4000);uniform_bool(location(program,b'clipping'),1)
bind(gl,'glUniform1f',None,[I,c.c_float])(location(program,b'clipZ'),-1)
bind(gl,'glDrawArrays',None,[U,I,I])(0x0004,0,3)
pixel=(c.c_ubyte*4)();bind(gl,'glReadPixels',None,[I,I,I,I,U,U,P])(32,32,1,1,0x1908,0x1401,pixel)
assert list(pixel)==[0,0,0,255],list(pixel)
print('PASS: world Z clip plane discards fragments')
bind(egl,'eglMakeCurrent',U,[P,P,P,P])(d,None,None,None)
bind(egl,'eglDestroyContext',U,[P,P])(d,context);bind(egl,'eglDestroySurface',U,[P,P])(d,surface);bind(egl,'eglTerminate',U,[P])(d)
