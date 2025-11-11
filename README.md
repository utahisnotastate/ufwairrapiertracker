# Inspired by the Air Rapier weapon in Chronicles of 23, this device is to show any victims that there is hope by building a tracker for the attacks so that you can show it to law enforcement. This code is being made open source to prevent this from occuring on any new timelines. There is hope a v2k detector of the Frey Effect
# This tool is being built to help the victims of 'touch less torture'. This gadget is to hopefully build data that can be passed onto law enforcement by Targetted Individuals to aid Law Enforcement to capture the criminals who do this using the military's budget. 

> Safety and clarity: This project does not endorse or assert any real-world claims about attacks or people. It’s an engineering exercise in signal detection and event logging using commodity sensors.

# ufwairrapiertracker V2.0

This is a wearable sensor fusion device designed to detect and log "Air Rapier" pneumatic vortex attacks.

This V2.0 model moves beyond simple thresholding and implements a multi-sensor array to capture a unique 3-part "attack signature":
1.  **Pneumatic Shock:** A sudden, localized barometric pressure drop.
2.  **Vibration Spike:** A high-frequency vibration/impact.
3.  **Acoustic Signature:** A distinct audio spike (whine or roar).

## Key Upgrades
* **Sensor Fusion:** Integrates a microphone (**MAX4466**) with the existing differential pressure sensors (**BME280 x2**) and accelerometer (**MPU6050**).
* **Machine Learning:** The included `analysis.py` script no longer uses a simple threshold. It employs an **Isolation Forest anomaly detection model** (a machine learning algorithm) to analyze the combined sensor data. This allows the system to identify complex attack patterns and filter out false positives.

## Hardware
* **MCU:** ESP32-S3-MINI (or similar)
* **Pressure:** 2x BME280 (one for target, one for ambient)
* **Activity/Vibration:** 1x MPU6050
* **Acoustic:** 1x MAX4466 Microphone Amplifier
* **Storage:** MicroSD Card Module
* **Power:** 3.7V LiPo Battery + TP4056 Charger

### Wiring
* **I2C (GPIO 21/22):** BME280_A (0x76), BME280_B (0x77), MPU6050 (0x68)
* **SPI (GPIO 18/19/23/5):** MicroSD Card Module
* **ADC (GPIO 35):** MAX4466 `OUT` pin

## Firmware (MicroPython)
The `main.py` script continuously samples all sensors and logs a data stream (`pressure_delta`, `vibration_mag`, `audio_level`) to the `log.csv` file on the SD card.

## Analysis (PC/Python)
The `analysis.py` script reads the `log.csv` file, trains an ML model on the "normal" data, and then predicts and reports all anomalous events that match the multi-sensor attack signature.
