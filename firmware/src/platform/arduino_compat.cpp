// ============================================================================
// Arduino-Pico compatibility shim
// ============================================================================
// The Arduino-Pico core ships the Pico SDK headers and a prebuilt libpico, but
// without pico_stdio (and it blocks stdio_init_all() by macro). The application
// is written against the plain SDK, so this file routes the SDK console onto
// the core's UART driver and leaves the rest of the sources unchanged:
//
//   Console::init()            -> UART0 (Serial1) on GP16 TX / GP29 RX @ 115200,
//                                 the same console the old CMake build used
//   stdio_getchar_timeout_us() -> CLI input (getchar_timeout_us() wraps it)
//   _write()                   -> printf / LOG_* output (overrides the core's
//                                 weak stub, which discards output)
// ============================================================================

#include "platform/console.h"

#include <Arduino.h>
#include "config/board_config.h"

void Console::init() {
    Serial1.setTX(Board::PIN_UART_TX);
    Serial1.setRX(Board::PIN_UART_RX);
    Serial1.begin(Board::UART_BAUD);
}

int stdio_getchar_timeout_us(uint32_t timeout_us) {
    const uint32_t start = time_us_32();
    do {
        if (Serial1.available() > 0) {
            return Serial1.read();
        }
    } while (time_us_32() - start < timeout_us);
    return PICO_ERROR_TIMEOUT;
}

// Translates "\n" to "\r\n" like the SDK's stdio (PICO_STDIO_DEFAULT_CRLF_SUPPORT).
extern "C" ssize_t _write(int fd, const void* buf, size_t count) {
    (void)fd;
    const char* data = static_cast<const char*>(buf);
    for (size_t i = 0; i < count; ++i) {
        if (data[i] == '\n') {
            Serial1.write('\r');
        }
        Serial1.write(data[i]);
    }
    return static_cast<ssize_t>(count);
}
