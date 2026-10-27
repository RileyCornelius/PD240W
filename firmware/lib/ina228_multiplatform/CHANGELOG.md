# Changelog

All notable changes to this library are documented in this file. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-07-06

### Added

- Arduino Library Manager metadata (`library.properties`).
- Native/host platform branch (`INA228_PLATFORM_NATIVE`/`_HOST`) for host/unit-test builds without MCU peripherals.

### Changed

- STM32 (HAL) and RP2040 (Pico SDK) I2C helpers now bound every transaction with a timeout instead of blocking forever, so a clock-stretching or locked-up slave returns `false` instead of hanging the caller.
- Reconciled `ci.yml`/`release.yml`/`platform_config.h` boilerplate with the sibling multiplatform libraries.

### Fixed

- `getTemperature()` sign-extended the raw DIETEMP register before scaling; reading it as unsigned made sub-zero temperatures wrap to roughly +500°C.

## [1.0.0] - 2026-05-13

### Added

- Initial release: multiplatform driver for the TI INA228 current, voltage, power, energy, and charge monitor over I2C (Arduino, ESP32, STM32, RP2040), built around a per-instance I2C bus handle, with CI and release workflows and example sketches.
