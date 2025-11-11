# Save this file on your ESP32 as bme280.py

# MicroPython BME280 driver
#
# Copyright (c) 2016 - 2020, 2022 CATIE
#
# License: MIT
#
# Based on:
#   https://github.com/catie-aq/BME280_MicroPython
#   https://github.com/df-robot/DFRobot_BME280_MicroPython
#   https://github.com/HowToElectronics/MicroPython-BME280-Raspberry-Pi-Pico
#
import time
from machine import I2C
from micropython import const

# BME280 default address.
BME280_I2C_ADDR = const(0x76)

# Operating Modes
BME280_SLEEP_MODE = const(0x00)
BME280_FORCED_MODE = const(0x01)
BME280_NORMAL_MODE = const(0x03)

# Oversampling settings
BME280_OS_SKIP = const(0x00)
BME280_OS_1X = const(0x01)
BME280_OS_2X = const(0x02)
BME280_OS_4X = const(0x03)
BME280_OS_8X = const(0x04)
BME280_OS_16X = const(0x05)

# Filter settings
BME280_FILTER_OFF = const(0x00)
BME280_FILTER_2 = const(0x01)
BME280_FILTER_4 = const(0x02)
BME280_FILTER_8 = const(0x03)
BME280_FILTER_16 = const(0x04)

# Standby settings
BME280_STANDBY_0_5 = const(0x00)
BME280_STANDBY_62_5 = const(0x01)
BME280_STANDBY_125 = const(0x02)
BME280_STANDBY_250 = const(0x03)
BME280_STANDBY_500 = const(0x04)
BME280_STANDBY_1000 = const(0x05)
BME280_STANDBY_10 = const(0x06)
BME280_STANDBY_20 = const(0x07)

# BME280 Registers
BME280_REG_ID = const(0xD0)
BME280_REG_RESET = const(0xE0)
BME280_REG_CTRL_HUM = const(0xF2)
BME280_REG_STATUS = const(0xF3)
BME280_REG_CTRL_MEAS = const(0xF4)
BME280_REG_CONFIG = const(0xF5)
BME280_REG_PRESS_MSB = const(0xF7)
BME280_REG_PRESS_LSB = const(0xF8)
BME280_REG_PRESS_XLSB = const(0xF9)
BME280_REG_TEMP_MSB = const(0xFA)
BME280_REG_TEMP_LSB = const(0xFB)
BME280_REG_TEMP_XLSB = const(0xFC)
BME280_REG_HUM_MSB = const(0xFD)
BME280_REG_HUM_LSB = const(0xFE)

# BME280 calibration registers
BME280_REG_DIG_T1 = const(0x88)
BME280_REG_DIG_T2 = const(0x8A)
BME280_REG_DIG_T3 = const(0x8C)
BME280_REG_DIG_P1 = const(0x8E)
BME280_REG_DIG_P2 = const(0x90)
BME280_REG_DIG_P3 = const(0x92)
BME280_REG_DIG_P4 = const(0x94)
BME280_REG_DIG_P5 = const(0x96)
BME280_REG_DIG_P6 = const(0x98)
BME280_REG_DIG_P7 = const(0x9A)
BME280_REG_DIG_P8 = const(0x9C)
BME280_REG_DIG_P9 = const(0x9E)
BME280_REG_DIG_H1 = const(0xA1)
BME280_REG_DIG_H2 = const(0xE1)
BME280_REG_DIG_H3 = const(0xE3)
BME280_REG_DIG_H4 = const(0xE4)
BME280_REG_DIG_H5 = const(0xE5)
BME280_REG_DIG_H6 = const(0xE7)


class BME280:
    def __init__(self,
                 mode=BME280_OS_1X,
                 address=BME280_I2C_ADDR,
                 i2c=None,
                 **kwargs):

        self.address = address
        if i2c is None:
            raise ValueError('I2C object required.')
        self.i2c = i2c

        self.dig_T1 = self._read16(BME280_REG_DIG_T1, unsigned=True)
        self.dig_T2 = self._read16(BME280_REG_DIG_T2)
        self.dig_T3 = self._read16(BME280_REG_DIG_T3)

        self.dig_P1 = self._read16(BME280_REG_DIG_P1, unsigned=True)
        self.dig_P2 = self._read16(BME280_REG_DIG_P2)
        self.dig_P3 = self._read16(BME280_REG_DIG_P3)
        self.dig_P4 = self._read16(BME280_REG_DIG_P4)
        self.dig_P5 = self._read16(BME280_REG_DIG_P5)
        self.dig_P6 = self._read16(BME280_REG_DIG_P6)
        self.dig_P7 = self._read16(BME280_REG_DIG_P7)
        self.dig_P8 = self._read16(BME280_REG_DIG_P8)
        self.dig_P9 = self._read16(BME280_REG_DIG_P9)

        self.dig_H1 = self._read8(BME280_REG_DIG_H1, unsigned=True)
        self.dig_H2 = self._read16(BME280_REG_DIG_H2)
        self.dig_H3 = self._read8(BME280_REG_DIG_H3, unsigned=True)

        h4 = self._read8(BME280_REG_DIG_H4)
        h5 = self._read8(BME280_REG_DIG_H5)
        self.dig_H4 = (h4 << 4) | (h5 & 0x0F)

        h5_msb = self._read8(BME280_REG_DIG_H5 + 1)
        self.dig_H5 = (h5_msb << 4) | (h5 >> 4)

        self.dig_H6 = self._read8(BME280_REG_DIG_H6)

        self._write8(BME280_REG_CTRL_HUM, mode)

        self.t_fine = 0

        # Default settings
        self.oversample_temp = BME280_OS_1X
        self.oversample_pres = BME280_OS_1X
        self.filter = BME280_FILTER_OFF
        self.standby = BME280_STANDBY_0_5
        self.mode = BME280_NORMAL_MODE

        self._set_config()
        self._set_ctrl_meas()

    def _read8(self, register, unsigned=False):
        data = self.i2c.readfrom_mem(self.address, register, 1)[0]
        if not unsigned and data & 0x80:
            data -= 0x100
        return data

    def _read16(self, register, unsigned=False):
        data = self.i2c.readfrom_mem(self.address, register, 2)
        value = (data[1] << 8) | data[0]
        if not unsigned and value & 0x8000:
            value -= 0x10000
        return value

    def _write8(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytearray([value]))

    def _set_config(self):
        config = (self.standby << 5) | (self.filter << 2)
        self._write8(BME280_REG_CONFIG, config)

    def _set_ctrl_meas(self):
        ctrl_meas = (self.oversample_temp << 5) | (self.oversample_pres << 2) | self.mode
        self._write8(BME280_REG_CTRL_MEAS, ctrl_meas)

    def read_raw_data(self):
        # Read temperature, pressure, and humidity registers
        data = self.i2c.readfrom_mem(self.address, BME280_REG_PRESS_MSB, 8)

        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_hum = (data[6] << 8) | data[7]

        return raw_temp, raw_press, raw_hum

    def _compensate_temperature(self, raw_temp):
        var1 = (raw_temp / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = ((raw_temp / 131072.0 - self.dig_T1 / 8192.0) * (
                    raw_temp / 131072.0 - self.dig_T1 / 8192.0)) * self.dig_T3
        self.t_fine = var1 + var2
        temperature = self.t_fine / 5120.0
        return temperature

    def _compensate_pressure(self, raw_press):
        if self.t_fine == 0:
            self._compensate_temperature(self.read_raw_data()[0])  # Force temp reading if not done

        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1

        if var1 == 0:
            return 0  # Avoid division by zero

        p = 1048576.0 - raw_press
        p = (p - var2 / 4096.0) * 6250.0 / var1
        var1 = self.dig_P9 * p * p / 2147483648.0
        var2 = p * self.dig_P8 / 32768.0
        p = p + (var1 + var2 + self.dig_P7) / 16.0

        return p  # Pressure in Pa

    def _compensate_humidity(self, raw_hum):
        if self.t_fine == 0:
            self._compensate_temperature(self.read_raw_data()[0])  # Force temp reading if not done

        h = self.t_fine - 76800.0
        h = (raw_hum - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * h)) * \
            (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * h * \
                                      (1.0 + self.dig_H3 / 67108864.0 * h)))
        h = h * (1.0 - self.dig_H1 * h / 524288.0)

        if h > 100.0:
            h = 100.0
        elif h < 0.0:
            h = 0.0

        return h  # Humidity in %RH

    @property
    def temperature(self):
        """Returns temperature in degrees Celsius"""
        raw_temp, _, _ = self.read_raw_data()
        return self._compensate_temperature(raw_temp)

    @property
    def pressure(self):
        """Returns pressure in Pascals"""
        _, raw_press, _ = self.read_raw_data()
        return self._compensate_pressure(raw_press)

    @property
    def humidity(self):
        """Returns relative humidity in %"""
        _, _, raw_hum = self.read_raw_data()
        return self._compensate_humidity(raw_hum)

    @property
    def values(self):
        """Returns (temperature, pressure, humidity)"""
        raw_temp, raw_press, raw_hum = self.read_raw_data()

        temp = self._compensate_temperature(raw_temp)
        pres = self._compensate_pressure(raw_press)
        hum = self._compensate_humidity(raw_hum)

        return temp, pres, hum
