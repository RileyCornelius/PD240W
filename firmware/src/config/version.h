#pragma once

// ============================================================================
// Firmware Version Information
// ============================================================================

namespace Version {
constexpr const char* FIRMWARE_VERSION = "v2.1.0";
constexpr const char* HARDWARE_VERSION = "1.1.0";
// Versions of the driver libraries copied into lib/. Update together with the
// "version" field in lib/<driver>/library.json when the copies are refreshed.
constexpr const char* INA_FIRMWARE_VERSION = "v1.0.1";
constexpr const char* TPS_FIRMWARE_VERSION = "v1.0.2";
constexpr const char* PRODUCT_NAME = "PD240W";
constexpr const char* PRODUCT_SUBTITLE = "Power Supply";
constexpr const char* AUTHOR = "Theo Heng";
constexpr const char* COMPANY = "Synapticon GmbH";
constexpr const char* GITHUB = "https://github.com/theohg/PD240W";
constexpr const char* GITHUB_SHORT = "theohg/PD240W";
constexpr const char* TARGET = "RP2040 (Pico)";

// Build info (can be overridden by build system)
#ifndef BUILD_DATE
#define BUILD_DATE __DATE__
#endif

#ifndef BUILD_TIME
#define BUILD_TIME __TIME__
#endif
} // namespace Version
