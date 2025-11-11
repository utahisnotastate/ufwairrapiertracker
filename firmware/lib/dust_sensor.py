# /lib/dust_sensor.py
# Driver for the GP2Y1010AU0F Optical Dust Sensor

from machine import Pin, ADC
import time


class DustSensor:
    def __init__(self, led_pin, adc_pin):
        self.led = Pin(led_pin, Pin.OUT)
        self.adc = ADC(Pin(adc_pin))
        self.adc.atten(ADC.ATTN_11DB)  # Full 0-3.6V range
        self.led.value(1)  # LED is off by default (inverted logic)

    def read_voltage(self):
        # This sensor requires a specific pulse sequence

        # 1. Turn LED on (pull low)
        self.led.value(0)

        # 2. Wait 280 microseconds for LED to stabilize
        time.sleep_us(280)

        # 3. Read ADC
        adc_val = self.adc.read()

        # 4. Wait 40us
        time.sleep_us(40)

        # 5. Turn LED off (pull high)
        self.led.value(1)

        # 6. Wait 9680us to complete 10ms cycle
        time.sleep_us(9680)

        # Convert 12-bit ADC (0-4095) to voltage (0-3.3V)
        # Using 3.3V as reference
        voltage = (adc_val / 4095) * 3.3

        # The sensor datasheet says output is ~0.5V to ~3.5V
        # But we will log the raw voltage for the ML model
        return voltage

    def read_dust_density(self):
        # This provides a calibrated value, but we don't need it
        # for ML anomaly detection. We'll use raw voltage.
        v = self.read_voltage()

        # Calibration from datasheet (approximate)
        if v < 0.5:
            v_dust = 0.5
        else:
            v_dust = v

        # (V - V_clean_air) / sensitivity
        # (V - 0.5) / 0.005 (for mg/m^3)
        density = (v_dust - 0.5) / 0.005

        if density < 0:
            return 0.0
        return density
