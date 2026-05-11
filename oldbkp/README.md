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

The current `src/control` implementation is sourced from the working
`djitellopy`-based controller pattern used in:
- `../Drone-Handcontrol/tello_controller.py`
- `../Drone-Demo-Final/utils/tello_controller.py`

Those were a better fit for this project than the raw UDP demo controllers in
`../Drone-Demo-230/drone-swarm/drone.py` and `../tello-demo/two/drone2.py`
because they already expose a reusable Python controller class around the Tello
SDK.

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
│   ├── control/
│   │   ├── tello_controller.py
│   │   └── gesture_bridge.py
│   └── main.py
├── docs/
├── requirements.txt
└── README.md
```

## Control Layer

- `src/control/tello_controller.py` contains the reusable `TelloController`
  wrapper for connect, takeoff, land, video, and RC control.
- `src/control/gesture_bridge.py` contains `TelloGestureBridge`, which maps
  keyboard input into drone actions (replace with IMU)
- The current flow - keyboard input runs in a
  background thread while the Tello camera stream is rendered on the main
  thread with OpenCV.

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

- Anjali Kanvinde — Embedded Systems & Hardware Integration  
- Vaikunth Elango —  Gesture Recognition & Data Processing
- Sribatscha Maharana —  System Integration & Application Development  

---

## License

This project is for academic and educational use.
