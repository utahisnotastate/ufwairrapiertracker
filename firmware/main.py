# main.py
# ufwairrapiertracker V4.0 - Forensic Logger with Hash Chain

import machine
import uos
import time
import mpu6050
import bme280
import micropyGPS
import dust_sensor
import uhashlib  # For hash chain
import ubinascii  # For hash chain
from machine import Pin, SoftI2C, SPI, ADC, UART
from sdcard import SDCard

# --- Config ---
# I2C
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
BME280_A_ADDR = 0x76
BME280_B_ADDR = 0x77
MPU6050_ADDR = 0x68

# ADC (Mic)
MIC_ADC_PIN = 35

# DUST SENSOR
DUST_LED_PIN = 32
DUST_ADC_PIN = 33

# UART (GPS)
GPS_UART_NUM = 2
GPS_TX_PIN = 17
GPS_RX_PIN = 16

# SPI (SD Card)
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 23
SPI_MISO_PIN = 19
SPI_CS_PIN = 5
SD_MOUNT_POINT = '/sd'

LOG_FILE = f"{SD_MOUNT_POINT}/forensic_log_v4.csv"
LOG_INTERVAL_MS = 100  # Log 10 times per second

# --- Globals ---
i2c = None
bme_a, bme_b, mpu, mic_adc, sd = None, None, None, None, None
gps_uart = None
gps_parser = micropyGPS.MicropyGPS()
dust_sensor_dev = None


# --- Initialization ---
def init_all():
    global i2c, bme_a, bme_b, mpu, mic_adc, sd, gps_uart, dust_sensor_dev
    print("Initializing components V4.0...")

    try:
        i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        mpu = mpu6050.accel(i2c, MPU6050_ADDR)
        bme_a = bme280.BME280(i2c=i2c, address=BME280_A_ADDR)
        bme_b = bme280.BME280(i2c=i2c, address=BME280_B_ADDR)
        mic_adc = ADC(Pin(MIC_ADC_PIN));
        mic_adc.atten(ADC.ATTN_11DB)
        dust_sensor_dev = dust_sensor.DustSensor(DUST_LED_PIN, DUST_ADC_PIN)
        gps_uart = UART(GPS_UART_NUM, 9600, tx=GPS_TX_PIN, rx=GPS_RX_PIN, timeout=10)

        spi = SPI(1, 10000000, sck=Pin(SPI_SCK_PIN), mosi=Pin(SPI_MOSI_PIN), miso=Pin(SPI_MISO_PIN))
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
                f.write("timestamp,pressure_delta,vibration_mag,audio_level,dust_voltage,lat,lon,alt,prev_hash\n")

        print("--- Init complete. Starting logger. ---")
        return True

    except Exception as e:
        print(f"Fatal init error: {e}")
        return False


# --- Helper Functions ---
def get_vibration_magnitude():
    try:
        g = mpu.get_values()
        return (g["GyX"] ** 2 + g["GyY"] ** 2 + g["GyZ"] ** 2) ** 0.5
    except Exception:
        return 0.0


def update_gps():
    if gps_uart.any():
        try:
            line = gps_uart.readline()
            if line: gps_parser.update(line.decode('utf-8'))
        except Exception:
            pass


def get_hash(data_string):
    sha = uhashlib.sha256(data_string.encode('utf-8'))
    return ubinascii.hexlify(sha.digest()).decode('utf-8')


def get_last_line(filepath):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                return lines[-1].strip()  # Get the last line
            else:
                return None  # Only header exists
    except Exception as e:
        print(f"Error reading last line: {e}")
        return None


# --- Main Loop ---
def run_logger():
    if not init_all(): return

    last_log_time = 0

    # Get hash of the last line to start the chain
    last_line = get_last_line(LOG_FILE)
    if last_line:
        prev_hash = get_hash(last_line)
        print(f"Resuming hash chain from: {prev_hash}")
    else:
        prev_hash = "0" * 64  # Genesis hash
        print("Starting new log with genesis hash.")

    log_buffer = []

    while True:
        try:
            current_time = time.ticks_ms()
            update_gps()  # Continuously poll GPS

            if time.ticks_diff(current_time, last_log_time) >= LOG_INTERVAL_MS:
                last_log_time = current_time

                # --- 1. Get Sensor Snapshots ---
                timestamp = get_timestamp_ms()
                delta_p = bme_a.pressure - bme_b.pressure
                vib_mag = get_vibration_magnitude()
                audio_level = mic_adc.read()
                dust_v = dust_sensor_dev.read_voltage()  # This takes 10ms

                lat, lon, alt = 0.0, 0.0, 0.0
                if gps_parser.fix_stat > 0:
                    lat, lon, alt = gps_parser.latitude, gps_parser.longitude, gps_parser.altitude

                # --- 2. Create Log Line & Hash ---
                log_line = f"{timestamp},{delta_p:.2f},{vib_mag:.2f},{audio_level},{dust_v:.3f},{lat:.6f},{lon:.6f},{alt:.1f},{prev_hash}"

                # Update the hash for the *next* iteration
                prev_hash = get_hash(log_line)

                log_buffer.append(log_line + "\n")

                # --- 3. Write to SD Card ---
                if len(log_buffer) >= 20:  # Write every 2 seconds
                    with open(LOG_FILE, 'a') as f:
                        for line in log_buffer:
                            f.write(line)
                    log_buffer = []
                    print(
                        f"LOG: dP:{delta_p:.0f} Vb:{vib_mag:.0f} Au:{audio_level} Du:{dust_v:.2f} GPS:{gps_parser.fix_stat}")

        except Exception as e:
            print(f"Main loop error: {e}")
            if log_buffer:
                with open(LOG_FILE, 'a') as f:
                    for line in log_buffer:
                        f.write(line)
            time.sleep(1)


# Run the logger
run_logger()
