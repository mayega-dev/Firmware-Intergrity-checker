# Real-Time Firmware Integrity Monitoring System for ESP32-S3

[![Target Platform](https://img.shields.io/badge/Target-ESP32--S3-blue.svg)](https://www.espressif.com/)
[![Framework](https://img.shields.io/badge/Framework-ESP--IDF%20v5.3.1-red.svg)](https://github.com/espressif/esp-idf)
[![GUI](https://img.shields.io/badge/Dashboard-PySide6%20%2F%20Qt-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Build Engine](https://img.shields.io/badge/Build-Docker%20%7C%20CMake%20%7C%20Ninja-0db7ed.svg)](https://www.docker.com/)

An edge-native, real-time firmware integrity verification and anti-rollback monitoring system designed for ESP32-S3 2.4GHz Wi-Fi smart surveillance nodes. This project provides hardware-accelerated SHA-256 partition verification, wear-aware Non-Volatile Storage (NVS) event logging, and a live PySide6 desktop administration dashboard to detect runtime memory breaches and unauthorized binary tampering.

---

## 📌 Project Overview

Embedded IoT edge nodes such as surveillance cameras running on ESP32-S3 microcontrollers are often targeted by runtime memory injection, unauthorized binary flashing, and firmware rollback attacks. Standard secure boot routines only validate code during initialization, leaving active execution memory unmonitored. 

This repository implements a lightweight 3-tier architecture:
1. **Edge Device Tier (ESP32-S3)**: Executes low-level C firmware utilizing ESP-IDF v5.3.1 and FreeRTOS. Performs pre-boot and continuous runtime SHA-256 partition hashing via `mbedTLS`, enforces an NVS-backed monotonic anti-rollback floor, and records security events to a wear-aware NVS ring-buffer.
2. **Transport Tier (Framed UART)**: Streams telemetry and critical alerts to a host system over a lightweight, tokenized serial framing protocol.
3. **Host Presentation Tier (PySide6 GUI)**: A cross-platform desktop application enabling operators to view live device health metrics, inspect interactive audit logs with CSV export capabilities, execute manual status polls, and run debug tamper simulations.

---

## ✨ Key Features

* **Continuous Runtime Hashing**: Hardware-accelerated SHA-256 checks across application partitions using `mbedTLS`.
* **Monotonic Anti-Rollback Floor**: Enforces minimum version floors via NVS to block vulnerable or legacy firmware binaries.
* **Wear-Aware NVS Ring-Buffer**: Maintains an on-device persistent event log optimized for flash wear management.
* **Framed UART Telemetry**: Serial communications protocol using explicit command tokens (`::STATUS::`, `::ALERT::`, `::POLL::`, `::TAMPER::`).
* **PySide6 Host Dashboard**: Live status visualization, event timeline graphing, raw UART console inspection, and interactive tamper testing.
* **Reproducible Docker Build Environment**: Containerized toolchain (`espressif/idf:v5.3.1`) integrating CMake, Ninja, and `esptool.py` for build reproducibility and SBOM generation.

---

## 🛠 Tech Stack & Tools

* **Embedded Firmware**: C (ESP-IDF v5.3.1, FreeRTOS, mbedTLS)
* **Target Hardware**: Espressif ESP32-S3 Microcontroller
* **Desktop Application**: Python 3.12+, PySide6 (Qt)
* **Build Engine**: Docker (`espressif/idf:v5.3.1`), CMake, Ninja, `esptool.py`
* **Storage & Telemetry**: ESP32 NVS Flash (Ring-Buffer) & SQLite/CSV (Host-side)



🚀 Quick Start Guide
# 1. Requirements
Workstation: Linux (Ubuntu 22.04 recommended), macOS, or Windows
Python 3.12+ installed
Docker Engine installed
ESP32-S3 Development Board connected via USB-C

# 2. Desktop Dashboard Setup
## Clone the repository
git clone [https://github.com/mayega-dev/Firmware-Intergrity-checker.git](https://github.com/mayega-dev/Firmware-Intergrity-checker.git)

cd Firmware-Intergrity-checker/dashboard
## Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate 

# On Windows: venv\Scripts\activate

## Install dependencies
pip install -r requirements.txt

## Launch the PySide6 Dashboard
python main.py

# 3. Build & Flash Firmware (Docker Pipeline)

cd ../docker
## Build the firmware image inside the standardized Docker container

docker-compose run --rm build-firmware

## Flash binary to ESP32-S3 (Replace /dev/ttyUSB0 with your device port)
esptool.py -p /dev/ttyUSB0 -b 921600 write_flash 0x10000 build/firmware-integrity-checker.bin




# 👥 Authors & Academic Context
This project was designed, implemented, and evaluated as part of a Bachelor’s degree requirement in Computer Security and Forensics at Uganda Technology and Management University (UTAMU).

Mayega Rodney - mayega.rodney@student.utamu.ac.ug

Ssempala Edward - ssempala.edward@student.utamu.ac.ug

Supervisor: Mr. Kivumbi Timothy (tkivumbi@utamu.ac.ug)
