#pragma once

// doctest entry point shared by every suite. Each test folder is its own
// executable under `pio test`; its one .cpp includes this right after
//
//   #define DOCTEST_CONFIG_IMPLEMENT
//   #include <doctest.h>
//
// (doctest.h stays in the .cpp so PlatformIO's library finder sees it).
//
// "success" prints every passing assertion so PlatformIO's doctest runner can
// list the individual test cases; "no-exitcode" leaves pass/fail to that runner,
// which reads the [doctest] status lines. See
// https://docs.platformio.org/en/latest/advanced/unit-testing/frameworks/doctest.html

int main(int argc, char** argv) {
    doctest::Context context;
    context.setOption("success", true);
    context.setOption("no-exitcode", true);
    context.applyCommandLine(argc, argv);
    return context.run();
}
