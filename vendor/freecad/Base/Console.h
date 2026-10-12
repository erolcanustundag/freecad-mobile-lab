// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
#include <cstdio>
namespace Base {
struct AndroidConsole {
    template<class... A> void log(const char* text, const A&...) const { (void)text; }
    template<class... A> void warning(const char* text, const A&...) const { std::fprintf(stderr, "Sketcher warning: %s\n", text); }
};
inline AndroidConsole& Console() { static AndroidConsole instance; return instance; }
}
