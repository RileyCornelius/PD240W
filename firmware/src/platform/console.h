#pragma once

// Serial console bring-up (logs + CLI). Replaces the SDK's stdio_init_all(),
// which the Arduino-Pico core does not support. See arduino_compat.cpp.
namespace Console {
void init();
}
