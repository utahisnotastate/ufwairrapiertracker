# main.py
# Air Rapier "Chronos" Attack Logger
# (c) 2025, Master Maker

import machine
import uos
import time
import mpu6050  # You will need to get this library
import bme280  # You will need to get this library
from machine import Pin, SoftI2C, SPI
from sdcard import SDCard

# --- Config ---
# I2C
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
BME280_A_ADDR = 0x76  # Target Sensor (Butt)
BME280_B_ADDR = 0x77  # Ambient Sensor (Chest)

# SPI (SD Card)
SPI_SCK_PIN = 18
SPI_MOSI_PIN = 23
SPI_MISO_PIN = 19
SPI_CS_PIN = 5
SD_MOUNT_POINT = '/sd'

# Logic
ATTACK_THRESHOLD_PA = 150  # Attack trigger (Pascals). 150 Pa is a sharp, sudden change. Tune this.
ATTACK_END_THRESHOLD_PA = 50  # When the differential is back within this range
LOG_FILE = f"{SD_MOUNT_POINT}/attack_log.csv"

# --- Globals ---
i2c = None
bme_a = None  # Target
bme_b = None  # Ambient
mpu = None  # Activity
sd = None  # SD Card

# State machine for attack detection
STATE_IDLE = 0
STATE_ATTACK = 1
attack_state = STATE_IDLE
attack_start_time = 0
attack_pressures = []
attack_activity = "Unknown"


# --- Initialization ---
def init_sensors():
    global i2c, bme_a, bme_b, mpu
    print("Initializing I2C and sensors...")
    try:
        i2c = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        devices = i2c.scan()
        print(f"I2C devices found: {[hex(d) for d in devices]}")

        # Init MPU6050 (Exercise 65)
        mpu = mpu6050.accel(i2c)
        print("MPU6050 (Activity) OK.")

        # Init BME280_A (Exercise 53)
        bme_a = bme280.BME280(i2c=i2c, address=BME280_A_ADDR)
        print("BME280 (Target) OK.")

        # Init BME280_B
        bme_b = bme280.BME280(i2c=i2c, address=BME280_B_ADDR)
        print("BME280 (Ambient) OK.")

        print("All sensors initialized.")
        return True
    except Exception as e:
        print(f"Sensor init failed: {e}")
        return False


def init_sdcard():
    global sd
    print("Initializing SD card (Exercise 77)...")[cite: 1330]
    try:
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
                f.write("timestamp,event_type,duration_ms,avg_delta_pa,activity\n")

        return True
    except Exception as e:
        print(f"SD card init failed: {e}")
        return False


# --- Helper Functions ---
def get_activity_status():
    try:
        accel_data = mpu.get_values()
        ax = accel_data["AcX"]
        ay = accel_data["AcY"]
        az = accel_data["AcZ"]

        # Simple activity detection based on magnitude
        # Values are raw, need calibration. For now, just use a rough threshold.
        # This is a very simple check. A real one would use a small buffer.
        mag_squared = (ax ** 2) + (ay ** 2) + (az ** 2)

        # ~16384 is 1G (still). Adjust these thresholds.
        if mag_squared < 18000 ** 2 and mag_squared > 15000 ** 2:
            return "Still"
        elif mag_squared > 20000 ** 2:
            return "Moving"
        else:
            return "Low Activity"

    except Exception as e:
        print(f"MPU read error: {e}")
        return "Unknown"


def get_timestamp():
    # Use internal RTC. Assumes it's been set, e.g., via ntptime.
    # For a real product, add an external RTC (DS1302/DS1307) [cite: 1046, 1050]
    t = time.localtime()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"


def log_event(event_type, duration, avg_delta_p, activity):
    print(f"LOGGING EVENT: {event_type}, Duration: {duration}ms, DeltaP: {avg_delta_p:.2f} Pa, Activity: {activity}")
    try:
        with open(LOG_FILE, 'a') as f:
            timestamp = get_timestamp()
            f.write(f"{timestamp},{event_type},{duration},{avg_delta_p:.2f},{activity}\n")
    except Exception as e:
        print(f"Failed to write to SD card: {e}")


# --- Main Loop ---
def run_tracker():
    global attack_state, attack_start_time, attack_pressures, attack_activity

    if not init_sensors() or not init_sdcard():
        print("Fatal error. Halting.")
        return

    print("--- Air Rapier Tracker ACTIVE ---")

    while True:
        try:
            # 1. Read sensor data
            # bme.pressure returns Pa
            pressure_a = bme_a.pressure
            pressure_b = bme_b.pressure
            delta_p = pressure_a - pressure_b
            current_activity = get_activity_status()

            # 2. Attack Detection Logic
            if attack_state == STATE_IDLE:
                if delta_p < -ATTACK_THRESHOLD_PA:
                    # ATTACK DETECTED
                    attack_state = STATE_ATTACK
                    attack_start_time = time.ticks_ms()
                    attack_activity = current_activity  # Log activity at start of attack
                    attack_pressures = [delta_p]
                    print(f"ATTACK DETECTED! DeltaP: {delta_p:.2f} Pa")

            elif attack_state == STATE_ATTACK:
                # We are currently in an attack
                attack_pressures.append(delta_p)

                if delta_p > -ATTACK_END_THRESHOLD_PA:
                    # ATTACK ENDED
                    attack_end_time = time.ticks_ms()
                    duration = time.ticks_diff(attack_end_time, attack_start_time)
                    avg_delta_p = sum(attack_pressures) / len(attack_pressures)

                    log_event("AirRapier_Attack", duration, avg_delta_p, attack_activity)

                    # Reset state
                    attack_state = STATE_IDLE
                    attack_pressures = []

            # Print status for debugging
            print(
                f"DeltaP: {delta_p:.2f} Pa | Activity: {current_activity} | State: {'IDLE' if attack_state == STATE_IDLE else 'ATTACK'}")

            time.sleep_ms(50)  # 20Hz sample rate

        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)


# Run the tracker
run_tracker()
