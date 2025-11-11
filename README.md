# Inspired by the Air Rapier weapon in Chronicles of 23, this device is to show any victims that there is hope by building a tracker for the attacks so that you can show it to law enforcement. This code is being made open source to prevent this from occuring on any new timelines. There is hope a v2k detector of the Frey Effect
# This tool is being built to help the victims of 'touch less torture'. This gadget is to hopefully build data that can be passed onto law enforcement by Targetted Individuals to aid Law Enforcement to capture the criminals who do this using the military's budget. 
# Chronos Airflow Event Tracker

Small, cheap, open-source hardware + firmware to detect short, localized airflow/pressure events using two barometric sensors and an IMU. Logs to microSD for later analysis.

This repo is part of a portfolio series to promote an upcoming book about practical, low-cost open-source electronics. If you’re looking for a developer who can deliver affordable, accessible tools and documentation for makers, educators, and startups—this project is for you.

> Safety and clarity: This project does not endorse or assert any real-world claims about attacks or people. It’s an engineering exercise in signal detection and event logging using commodity sensors.


---

## ✨ Why this project
- Demonstrate end-to-end embedded workflow: hardware → firmware → data analysis
- Use inexpensive, widely available parts (ESP32, BME280/BMP280, MPU6050, microSD)
- Showcase robust documentation and reproducible results
- Serve as a portfolio example and companion to a book on open-source electronics

Mission: make open-source electronics tools cheaper, easier, and friendlier for everyone.


---

## 🔎 What it does
Chronos watches for a sudden, local pressure change by comparing two barometric sensors placed in different locations:
- Sensor A (target/local)
- Sensor B (ambient/reference)

It computes the differential pressure (A − B), watches for a sharp negative dip, tags the moment with an activity snapshot from the IMU, and logs an event to `attack_log.csv` on the microSD card.

- Sample rate: ~20 Hz (configurable)
- Storage: microSD (CSV)
- Extras: simple activity classifier from the MPU6050


---

## 🚀 Quick start
1) Hardware build
- See: [hardware/hardware.md](hardware/hardware.md) for enclosure and mounting guidance.
- Bill of Materials (BOM):
  - ESP32 (e.g., ESP32-S3-MINI or any small ESP32 board)
  - BME280 or BMP280 x2 (I2C)
  - MPU6050 (I2C)
  - microSD card module (SPI)
  - LiPo battery (3.7V 500–1000 mAh) + TP4056 charger (with protection)
  - Wires, strap, simple enclosure

2) Wiring (example pins; adjust to your board)
- I2C sensors (both BME280 + MPU6050)
  - SCL → GPIO 22
  - SDA → GPIO 21
  - Power → 3V3, GND → GND
- Fix duplicate BME280 address: set one to 0x76 and the other to 0x77 (via SDO pad wiring)
- microSD (SPI)
  - SCK → GPIO 18
  - MOSI → GPIO 23
  - MISO → GPIO 19
  - CS → GPIO 5

3) Firmware (MicroPython)
- Flash MicroPython to your ESP32.
- Copy these files to the board:
  - `firmware/main.py`
  - `firmware/bme280.py`
  - `firmware/mpu6050.py`
  - `firmware/sdcard.py`
- Reset the board; it will create `/sd/attack_log.csv` and begin logging.

4) Analytics (desktop)
- Copy `attack_log.csv` from the microSD to your computer.
- Install Python deps: `pip install pandas matplotlib`
- Run: `python analysis/analysis.py`
- Outputs: pie chart of activity, duration histogram, pressure vs. duration scatter plot


---

## 🧠 How it works
- Two barometric sensors (BME280/BMP280) are placed apart:
  - A: local/target
  - B: ambient/reference
- Differential pressure `ΔP = P_A − P_B` is monitored.
- If `ΔP` drops below a threshold for a short period, an event is detected.
- The IMU (MPU6050) provides an activity snapshot at the event onset.
- The event is appended to `/sd/attack_log.csv` as:
  ```csv
  timestamp,event_type,duration_ms,avg_delta_pa,activity
  2025-11-11 01:14:00,AirRapier_Attack,120,-180.5,Moving
  ```

Tuning knobs in `firmware/main.py`:
- `ATTACK_THRESHOLD_PA` (default: 150)
- `ATTACK_END_THRESHOLD_PA` (default: 50)
- Sample rate (sleep interval)


---

## 📂 Repository layout
- `hardware/hardware.md` — enclosure and mounting guidance
- `firmware/main.py` — MicroPython application (sensors + detection + logging)
- `firmware/bme280.py` — BME280 driver
- `firmware/mpu6050.py` — MPU6050 helper
- `firmware/sdcard.py` — microSD helper
- `analysis/analysis.py` — desktop analytics and plots


---

## 🔧 Build notes
- Ventilation matters. Ensure Sensor A (local) has a focused vent path, Sensor B (ambient) is well-vented to room air. See [hardware/hardware.md](hardware/hardware.md).
- Keep I2C cables short where possible; twisted pairs help.
- Use a proper LiPo with a protected charger; never power the ESP32 directly from a bare cell.
- Mount the microSD so you can remove the card without opening the whole case.


---

## 🧪 Calibration & tuning
- Verify both sensors read similar pressures at rest (ΔP ≈ 0). If not, check addresses and wiring.
- Adjust `ATTACK_THRESHOLD_PA` to fit your environment. Start at 150 Pa and iterate.
- Use the debug prints in `main.py` to watch `ΔP` and activity live at ~20 Hz.


---

## 🗺️ Roadmap
- On-device timestamp sync (NTP or external RTC)
- Better activity classification (windowed features vs. single-sample magnitude)
- Optional BLE/Wi‑Fi event notifications
- Battery gauge and safe shutdown


---

## 📣 Portfolio series + book
This repository is part of a portfolio line-up accompanying a book-in-progress about practical, low-cost open-source electronics. The goal is to show clean, documented, repeatable builds that others can learn from and reuse.

If you’re hiring or collaborating and want tools that are:
- inexpensive to build at home or in classrooms,
- easy to understand and modify,
- genuinely open and well-documented,

…then I’d love to work with you. Open an issue to start the conversation.


---

## 🤝 Contributing
Issues and pull requests are welcome. Please keep contributions focused on:
- clarity of documentation,
- hardware safety,
- reliability and testability of firmware,
- accessibility and cost-efficiency of parts and workflows.


---

## ⚠️ Safety
This project is about sensing and logging air pressure and motion. Do not use hardware in unsafe, invasive, or harmful ways. Follow battery safety best practices and local regulations.


---

## 🔒 License
No license has been selected yet. Until a license is added, all rights are reserved by the author. If you’d like to reuse this work, please open an issue to discuss terms.


---

_Last updated: 2025-11-11_
