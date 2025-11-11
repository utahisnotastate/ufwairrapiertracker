# Inspired by the Air Rapier weapon in Chronicles of 23, this device is to show any victims that there is hope by building a tracker for the attacks so that you can show it to law enforcement. This code is being made open source to prevent this from occuring on any new timelines. There is hope a v2k detector of the Frey Effect
# This tool is being built to help the victims of 'touch less torture'. This gadget is to hopefully build data that can be passed onto law enforcement by Targetted Individuals to aid Law Enforcement to capture the criminals who do this using the military's budget. 
# ufwairrapiertracker V4.0 (Forensic Edition)

This is a wearable, multi-sensor device designed to log and forensically verify "Air Rapier" pneumatic attacks for CSI-level credibility.

This V4.0 model captures a 4-part "attack signature" and makes the resulting data log **cryptographically tamper-evident**.

## Forensic Features

### 1. Multi-Sensor Fusion
The device logs a 4-part signature to prove the event:
* **Pneumatic Shock (BME280s):** Localized pressure drop.
* **Vibration (MPU6050):** High-frequency vibration.
* **Acoustic Signature (MAX4466):** Audio spike.
* **Physical Artifact (GP2Y1010AU0F):** **This is the key.** We log the airborne particulate density. A "vortex" attack would create a dust cloud, and this optical sensor provides the physical proof.

### 2. Geolocation Tagging
* **GPS (NEO-6M):** Every data point is geotagged with latitude, longitude, and altitude, providing an verifiable record of *where* the event occurred.

### 3. Forensic Log Integrity (Hash Chain)
* **Tamper-Evident:** The device uses the onboard `uhashlib` (SHA-256) module to create a **hash chain**.
* **How it Works:** Each log entry (e.g., `Log #100`) contains a cryptographic hash of the *entire previous entry* (`Log #99`). This "chains" the whole file together.
* **CSI-Level Credibility:** If a single byte of data is altered in the `log.csv` file, the hash chain will be broken. The included `analysis.py` script verifies this chain *before* analysis, proving the log is authentic and has not been tampered with.

## Hardware
* **MCU:** ESP32
* **Pressure:** 2x BME280
* **Vibration/Activity:** 1x MPU6050
* **Acoustic:** 1x MAX4466
* **GPS:** 1x NEO-6M
* **Particulate:** 1x GP2Y1010AU0F (Dust Sensor)
* **Storage:** MicroSD Card Module

## Firmware
The `main.py` script logs all 4 sensor streams + GPS data + the previous entry's hash to the SD card.

## Analysis
The `analysis.py` script:
1.  **Verifies** the entire log's hash chain for forensic integrity.
2.  **Trains** an ML anomaly detection model on the 4-sensor data.
3.  **Finds** and reports all "attack" events.
4.  **Plots** the verified attacks on a geographic map.
