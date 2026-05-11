# Gesture-Controlled Drone Navigation via Wearable IMU

---

## Slide 1 — Title

**Title:** Gesture-Controlled Drone Navigation via Wearable IMU
**Subtitle:** Real-time hand gesture recognition on embedded hardware for intuitive UAV control
**Course / Team / Date**

---

## Slide 2 — Motivation & Use Cases

**Why gesture control?**

Traditional drone controllers require dedicated hardware and a learning curve. A wearable IMU lets users fly a drone with natural hand movements — no joystick, no phone required.

**Valid use cases:**
- Search and rescue — operator keeps hands free, directs drone by pointing/tilting wrist
- Industrial inspection — technician wearing gloves can still issue commands
- Accessibility — users who cannot operate fine motor controllers
- Robotics research — cheap, low-latency gesture interface for any actuator
- Live demos / education — visually compelling, no special equipment needed

---

## Slide 3 — System Overview

**How it works (end-to-end):**

1. **ESP32-S3 + MPU-6050** worn on the wrist/hand
2. IMU sampled at **250 Hz** for a **2-second window** (500 samples)
3. Triggered by a serial command from the laptop
4. On-device C SVM classifies the gesture → sends `PREDICTED:<label>` back over serial
5. Python (`imu_control.py`) maps the label to a Tello RC command
6. **DJI Tello** executes the move for 0.8 seconds, then hovers

**Block diagram:**
```
[MPU-6050] --I2C--> [ESP32-S3] --USB Serial--> [Python] --WiFi--> [Tello]
               capture 500 samples        gesture → RC command
               run C SVM on-device
```

Two inference modes:
- **ARM mode** — C SVM runs on ESP32, no laptop model needed (what we use)
- **CSV mode** — ESP32 dumps raw CSV, Python sklearn model classifies

---

## Slide 4 — Hardware & Data Collection

**Hardware:**
- ESP32-S3 dev board
- MPU-6050 IMU (accelerometer + gyroscope) connected via I2C (SDA=GPIO0, SCL=GPIO1)
- 400 kHz I2C, gyro range ±500°/s, accel range ±2g

**Gestures (9 classes):**
forward, backward, left, right, up, down, clockwise, counterclockwise, none

**Dataset:**
- 30 samples per gesture (15 for "none") — **255 total windows**
- Collected using `capture_triggered.py`: press Enter → hold gesture for 2 seconds → saved as CSV

---

## Slide 5 — Feature Extraction

Each 2-second window (500 × 6 values) is compressed into a **60-feature vector**:

- 6 IMU channels: ax, ay, az, gx, gy, gz
- 10 statistics per channel:
  - mean, std, min, max, range
  - energy (mean of x²), peak_abs, rms
  - zero crossings (centered), mean absolute difference

Same feature code runs in Python (training) and C (on-device inference) — guaranteed consistency.

---

## Slide 6 — Classification Models

We evaluated four classifiers on the same 60-feature vectors using 5-fold cross-validation:

| Model | Description |
|---|---|
| **Linear SVM** | LinearSVC, C=1.0 — deployed on ESP32 in C |
| **k-Nearest Neighbors** | KNN, k=5, Euclidean distance on scaled features |
| **Random Forest** | 200 trees, no scaling needed |
| **MLP (Neural Net)** | 2 hidden layers (128→64), ReLU, Adam optimizer |

**Why Linear SVM for deployment:**
- Inference is a single matrix multiply + argmax — trivially implementable in C
- No dynamic memory, runs in ~1ms on ESP32
- Accuracy competitive with more complex models on this feature set

---

## Slide 7 — Results

*(Insert confusion matrix figure: `figures/confusion_matrices.png`)*
*(Insert accuracy comparison bar chart: `figures/accuracy_comparison.png`)*

**Key observations:**
- SVM achieves strong accuracy on most gestures
- forward/backward historically the hardest pair — both involve pitch axis, distinguished mainly by direction of acceleration peak
- "none" class (15 samples, rest position) has fewer samples but tends to be well-separated due to low overall motion energy
- Random Forest and MLP show similar accuracy; Linear SVM wins on deployment simplicity

**To generate figures:**
```bash
cd report/
python compare_models.py
```

---

## Slide 8 — Challenges

- **Forward/backward confusion** — initial model struggled; resolved by recollecting cleaner, more consistent data and removing a 5× downsampling step in the firmware that was causing feature mismatch between training and inference
- **Feature mismatch bug** — demo version downsampled 500→100 samples before inference but training used all 500; this silently degraded accuracy on two gestures
- **Serial timing** — DTR line on macOS resets the ESP32 on port open; required disabling DTR/RTS and adding a small delay before sending commands
- **Data consistency** — IMU orientation on wrist matters; model trained by one person may not generalize well to another without retraining
- **ARM command mismatch** — demo used `"ARM"` as the trigger string; new firmware uses empty string (just Enter); Python script had to be updated accordingly

---

## Slide 9 — Conclusion & Future Work

**What we built:**
A complete pipeline from wrist-worn IMU to live drone flight, with on-device gesture classification running entirely on an ESP32-S3 in C with no external dependencies.

**Future work:**
- Sliding window inference (continuous, no trigger needed)
- User-adaptive calibration to handle different wrist orientations
- Expand to more expressive gestures (wrist roll, finger pose via flex sensors)
- Replace SVM with a small quantized CNN for sequence-aware classification
- Wireless ESP32 → remove USB serial dependency entirely

---

## Running the code

**Flash firmware:**
```bash
cd data/gesture_recognition
. $IDF_PATH/export.sh
idf.py set-target esp32s3          # first time only
idf.py -p /dev/cu.usbserial-10 flash monitor
```

**Run drone control:**
```bash
cd <project root>
python src/imu_control.py --port /dev/cu.usbserial-10 --mode arm
# T = takeoff, N = land, ESC = quit
```

**Generate model comparison figures:**
```bash
cd report/
python compare_models.py
```
