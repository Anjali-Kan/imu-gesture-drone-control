# IMU Gesture Drone Control

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Platform](https://img.shields.io/badge/Platform-ESP32--S3-green)
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

Wearable IMU-based hand gesture interface for intuitive, real-time drone control using natural hand motions.

---

## Table of Contents

- Overview  
- Demo  
- System Architecture  
- Features  
- Tech Stack  
- Hardware Setup  
- Software Setup  
- Usage  
- Project Structure  
- Results  
- Roadmap  
- Team  
- License  

---

## Overview

This project implements a wearable human–computer interaction system that enables users to control a drone using hand gestures. An IMU sensor captures motion data, which is processed in real time to recognize gestures and map them to drone commands.

The system focuses on:
- Natural interaction design
- Real-time sensing and control
- Embedded systems and signal processing
- Human activity recognition

---

## Demo

Add a demo video or GIF here.

---

## System Architecture

```
[ IMU Sensor ]
      ↓
[ ESP32-S3 Microcontroller ]
      ↓
[ Wireless Transmission ]
      ↓
[ Gesture Recognition (Python) ]
      ↓
[ Command Mapping ]
      ↓
[ Drone Control ]
```

---

## Features

- Real-time IMU data streaming (accelerometer and gyroscope)
- Gesture recognition using machine learning or signal processing
- Continuous motion-based control using gesture intensity
- Low-latency communication pipeline
- Safety mechanisms (gesture confirmation and emergency stop)
- Live visualization of sensor data and predictions

---

## Tech Stack

**Hardware**
- ESP32-S3
- MPU6050 or BNO055 IMU
- Programmable drone

**Software**
- Python
- scikit-learn
- NumPy
- PySerial / Bluetooth
- Matplotlib or Streamlit

---

## Hardware Setup

1. Connect IMU to ESP32 via I²C  
2. Mount IMU on glove or wristband  

---

## Software Setup

```bash
git clone https://github.com/yourteam/imu-gesture-drone-control
cd imu-gesture-drone-control

pip install -r requirements.txt
```

---

## Usage

```bash
python src/main.py
```

---

## Project Structure

```
imu-gesture-drone-control/
├── firmware/
├── data/
├── notebooks/
├── src/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── inference/
│   └── control/
├── docs/
├── requirements.txt
└── README.md
```

---

## Results

- Real-time gesture recognition achieved  
- Multiple gestures mapped to drone commands  
- Stable control using motion intensity  

---

## Roadmap

- [x] IMU data acquisition  
- [x] Data visualization  
- [ ] Gesture dataset collection  
- [ ] Gesture classification model  
- [ ] Drone integration  
- [ ] Final system demo  

---

## Team

- Member 1 — Embedded Systems  
- Member 2 — Machine Learning  
- Member 3 — Integration  

---

## License

This project is for academic and educational use.
