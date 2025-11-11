# main.py
# ufwairrapiertracker V2.0 - Sensor Fusion Logger

import machine
import uos
import time
import mpu6050  # From /lib
import bme280  # From /lib
from machine import Pin, SoftI2C, SPI, ADC
from sdcard import SDCard  # From /lib

# --- Config ---
# I2C (BME280s, MPU6050)
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
BME280_A_ADDR = 0x76  # Target Sensor (Butt)
BME280_B_ADDR = 0x77  # Ambient Sensor (Chest)
MPU6050_ADDR = 0x68

# ADC (Microphone)
MIC_ADC_PIN = 35

# SPI (SD Card)
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 23
SPI_MISO_PIN = 19
SPI_CS_PIN = 5
SD_MOUNT_POINT = '/sd'

LOG_FILE = f"{SD_MOUNT_POINT}/sensor_log.csv"
LOG_INTERVAL_MS = 50  # Log 20 times per second for high-res data

# --- Globals ---
i2c = None
bme_a = None  # Target
bme_b = None  # Ambient
mpu = None  # Activity/Vibration
mic_adc = None  # Acoustic
sd = None  # SD Card


# --- Initialization ---
def init_all():
    global i2c, bme_a, bme_b, mpu, mic_adc, sd
    print("Initializing components...")

    try:
        # I2C
        i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        devices = i2c.scan()
        print(f"I2C devices found: {[hex(d) for d in devices]}")

        mpu = mpu6050.accel(i2c, MPU6050_ADDR)
        print("MPU6050 (Vibration/Activity) OK.")

        bme_a = bme280.BME280(i2c=i2c, address=BME280_A_ADDR)
        print("BME280 (Target) OK.")

        bme_b = bme280.BME280(i2c=i2c, address=BME280_B_ADDR)
        print("BME280 (Ambient) OK.")

        # ADC
        mic_adc = ADC(Pin(MIC_ADC_PIN))
        mic_adc.atten(ADC.ATTN_11DB)  # Set full 0-3.6V range
        print("MAX4466 (Acoustic) OK.")

        # SPI / SD
        spi = SPI(1, sck=Pin(SPI_SCK_PIN), mosi=Pin(SPI_MOSI_PIN), miso=Pin(SPI_MISO_PIN))
        sd = SDCard(spi, Pin(SPI_CS_PIN))
        uos.mount(sd, SD_MOUNT_POINT)
        print(f"SD card mounted at {SD_MOUNT_POINT}")

        # Check for log file
        try:
            uos.stat(LOG_FILE)
            print("Log file found.")
        except OSError:
            print("Log file not found. Creating new one.")
            with open(LOG_FILE, 'w') as f:
                f.write("timestamp,pressure_delta,vibration_mag,audio_level\n")

        print("--- Init complete. Starting logger. ---")
        return True

    except Exception as e:
        print(f"Fatal init error: {e}")
        return False


# --- Helper Functions ---
def get_vibration_magnitude():
    # We will use Gyro data for high-frequency vibration
    try:
        gyro_data = mpu.get_values()
        gx = gyro_data["GyX"]
        gy = gyro_data["GyY"]
        gz = gyro_data["GyZ"]

        # Calculate magnitude of angular velocity
        mag = (gx ** 2 + gy ** 2 + gz ** 2) ** 0.5
        return mag
    except Exception:
        return 0.0


def get_timestamp_ms():
    # Use ticks_ms for high-res logging
    return time.ticks_ms()


# --- Main Loop ---
def run_logger():
    if not init_all():
        return

    last_log_time = 0
    log_buffer = []  # Buffer logs for faster SD card writes

    while True:
        try:
            current_time = time.ticks_ms()

            if time.ticks_diff(current_time, last_log_time) >= LOG_INTERVAL_MS:
                last_log_time = current_time

                # Get sensor snapshots
                timestamp = get_timestamp_ms()

                # 1. Pressure Delta
                pressure_a = bme_a.pressure
                pressure_b = bme_b.pressure
                delta_p = pressure_a - pressure_b  # In Pascals

                # 2. Vibration Magnitude
                vib_mag = get_vibration_magnitude()

                # 3. Audio Level
                # Read raw ADC value (0-4095). This is faster than voltage conversion.
                audio_level = mic_adc.read()

                # Format data
                log_line = f"{timestamp},{delta_p:.2f},{vib_mag:.2f},{audio_level}\n"
                log_buffer.append(log_line)

                # Write to SD card in chunks to prevent wear and speed up loop
                if len(log_buffer) >= 100:  # Write every 100 samples (5 seconds)
                    with open(LOG_FILE, 'a') as f:
                        for line in log_buffer:
                            f.write(line)
                    log_buffer = []  # Clear buffer
                    print(f"Wrote 100 samples to SD card. Last: {log_line.strip()}")

        except Exception as e:
            print(f"Main loop error: {e}")
            # Try to write remaining buffer before crashing
            if log_buffer:
                with open(LOG_FILE, 'a') as f:
                    for line in log_buffer:
                        f.write(line)
            time.sleep(1)


# Run the logger
run_logger()
