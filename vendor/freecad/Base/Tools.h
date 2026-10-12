// SPDX-License-Identifier: LGPL-2.1-or-later
#pragma once
#include <chrono>
namespace Base {
class TimeElapsed {
    std::chrono::steady_clock::time_point value = std::chrono::steady_clock::now();
public:
    static double diffTimeF(const TimeElapsed& a, const TimeElapsed& b) { return std::chrono::duration<double>(b.value-a.value).count(); }
};
}
