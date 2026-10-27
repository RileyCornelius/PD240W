/**
 * @file ina228_platform_i2c.h
 * @brief Platform-agnostic I2C helpers for INA228.
 *
 * @note Device addresses are always passed as 7-bit addresses.
 *       STM32 HAL shifts them internally; Arduino Wire and Pico SDK expect 7-bit.
 *
 * @copyright Copyright (c) 2026 Theo Heng
 * @license MIT License. See LICENSE file for details.
 */

#ifndef INA228_PLATFORM_I2C_H
#define INA228_PLATFORM_I2C_H

#include <stddef.h>
#include <stdint.h>

#include "ina228_platform_config.h"

#ifdef INA228_PLATFORM_ARDUINO
    #include <Wire.h>
#endif

#if defined(PLATFORM_ARDUINO)
    typedef TwoWire* bus_handle_t;
#elif defined(PLATFORM_STM32)
    typedef I2C_HandleTypeDef* bus_handle_t;
#elif defined(PLATFORM_RP2040)
    typedef i2c_inst_t* bus_handle_t;
#else
    typedef void* bus_handle_t;
#endif

bool ina228_i2c_probe(bus_handle_t bus, uint8_t device_address);
bool ina228_i2c_write_pointer(bus_handle_t bus, uint8_t device_address, uint8_t reg);
bool ina228_i2c_read_data(bus_handle_t bus, uint8_t device_address, uint8_t* buffer, size_t length);
bool ina228_i2c_write_register16(bus_handle_t bus, uint8_t device_address, uint8_t reg, uint16_t value);

#endif /* INA228_PLATFORM_I2C_H */
