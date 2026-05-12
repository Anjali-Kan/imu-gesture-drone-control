"""Real-time IMU gesture → Tello drone control.

Usage
-----
First train the model (once):
    python train.py

Then run (drone must be powered on and connected via Wi-Fi):
    python src/imu_control.py --port /dev/cu.usbserial-XXXX

CSV mode (default) — Python pkl inference:
    Sends 'CSV' to ESP32, reads raw IMU, classifies with trained model.

ARM mode — on-device C inference (no model needed):
    Sends Enter to ESP32, reads back 'PREDICTED:gesture'.
    Use this if you haven't trained the Python model yet.
    python src/imu_control.py --port /dev/cu.usbserial-XXXX --mode arm

Keyboard shortcuts (always active):
    T   → takeoff
    N   → land
    ESC → emergency stop + quit
    Q   → quit video window
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time

import numpy as np
import serial
from serial import SerialException

# Allow running as `python src/imu_control.py` from project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from control import TelloController, TelloGestureBridge
from gesture_recognition import extract_features

# ---------------------------------------------------------------------------
# Gesture → drone instruction mapping
# ---------------------------------------------------------------------------
GESTURE_MAP: dict[str, str] = {
    "forward":          "move_forward",
    "backward":         "move_back",
    "left":             "move_left",
    "right":            "move_right",
    "up":               "move_up",
    "down":             "move_down",
    "clockwise":        "yaw_right",
    "counterclockwise": "yaw_left",
    "none":             "hover",
    "unknown":          "hover",
}

# How long (seconds) the drone holds each gesture command before stopping
MOVE_DURATION = 0.8

# Expected number of IMU samples per capture window
NUM_SAMPLES = 500


# ---------------------------------------------------------------------------
# Serial helpers
# ---------------------------------------------------------------------------

def _is_log_line(line: str) -> bool:
    return line.startswith("I (") or line.startswith("E (") or line.startswith("W (")


def read_csv_capture(ser: serial.Serial, timeout: float = 8.0) -> np.ndarray | None:
    """Send 'CSV', collect 500 rows of IMU data. Returns N×6 array or None."""
    ser.reset_input_buffer()
    ser.write(b"CSV\n")
    ser.flush()

    rows: list[list[float]] = []
    header_seen = False
    deadline = time.time() + timeout

    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("ascii", errors="ignore").strip()
        if not line or _is_log_line(line):
            continue

        if not header_seen:
            if line == "time_us,ax,ay,az,gx,gy,gz":
                header_seen = True
            continue

        parts = line.split(",")
        if len(parts) == 7 and parts[0].isdigit():
            try:
                rows.append([float(p) for p in parts[1:]])  # drop timestamp
            except ValueError:
                pass

        if len(rows) >= NUM_SAMPLES:
            break

    if len(rows) < NUM_SAMPLES:
        print(f"[IMU] incomplete capture: got {len(rows)}/{NUM_SAMPLES} rows")
        return None

    return np.array(rows[:NUM_SAMPLES], dtype=np.float64)


def read_arm_prediction(ser: serial.Serial, timeout: float = 8.0,
                         stop_event: threading.Event | None = None) -> str:
    """Send Enter, show progress bar, wait for 'PREDICTED:<label>'."""
    ser.reset_input_buffer()
    ser.write(b"\n")
    ser.flush()

    CAPTURE_DUR = 2.0
    bar_done = threading.Event()

    def _progress() -> None:
        start = time.time()
        while not bar_done.is_set():
            elapsed = min(time.time() - start, CAPTURE_DUR)
            filled = int(elapsed / CAPTURE_DUR * 20)
            bar = "█" * filled + "░" * (20 - filled)
            print(f"\r  [{bar}] {elapsed:.1f}s — hold gesture!", end="", flush=True)
            time.sleep(0.05)
        print()  # newline after bar finishes

    progress_thread = threading.Thread(target=_progress, daemon=True)
    progress_thread.start()

    result = "none"
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            if stop_event and stop_event.is_set():
                break
            try:
                raw = ser.readline()
            except SerialException:
                break
            if not raw:
                continue
            line = raw.decode("ascii", errors="ignore").strip()
            if line.startswith("PREDICTED:"):
                result = line[len("PREDICTED:"):].strip().lower()
                break
    finally:
        bar_done.set()
        progress_thread.join()

    return result


# ---------------------------------------------------------------------------
# IMU gesture thread
# ---------------------------------------------------------------------------

class IMUGestureThread:
    def __init__(
        self,
        bridge: TelloGestureBridge,
        ser: serial.Serial,
        model,
        mode: str,
        stop_event: threading.Event,
        rest_seconds: int = 3,
    ) -> None:
        self.bridge = bridge
        self.ser = ser
        self.model = model
        self.mode = mode
        self.stop_event = stop_event
        self.rest_seconds = rest_seconds

    def start(self) -> threading.Thread:
        t = threading.Thread(target=self._run, daemon=True, name="imu-gesture")
        t.start()
        return t

    def _run(self) -> None:
        print("[IMU] Gesture thread started. Perform a gesture now.")
        while not self.stop_event.is_set():
            try:
                gesture = self._capture_gesture()
            except SerialException:
                break  # serial closed on shutdown — exit cleanly
            if gesture is None:
                continue

            print(f"[IMU] Detected: {gesture}")
            instruction = GESTURE_MAP.get(gesture, "hover")

            if not self.bridge.state.flying:
                print("[IMU] Not flying — use T to takeoff")
            else:
                self.bridge._reset_motion()
                if instruction != "hover":
                    self.bridge.apply_instruction(instruction)
                time.sleep(MOVE_DURATION)
                self.bridge._reset_motion()
                self.bridge._send_current_rc()

            self._rest_countdown()

    def _rest_countdown(self) -> None:
        for remaining in range(self.rest_seconds, 0, -1):
            if self.stop_event.is_set():
                return
            print(f"\r  rest... next capture in {remaining}s ", end="", flush=True)
            time.sleep(1)
        print("\r  ready — perform gesture now!       ", flush=True)

    def _capture_gesture(self) -> str | None:
        if self.mode == "arm":
            return read_arm_prediction(self.ser, stop_event=self.stop_event)

        data = read_csv_capture(self.ser)
        if data is None:
            return None

        features = extract_features(data).reshape(1, -1)
        try:
            prediction = self.model.predict(features)[0]
            return str(prediction).lower()
        except Exception as e:
            print(f"[IMU] prediction error: {e}")
            return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="IMU gesture → Tello drone control")
    p.add_argument("--port", required=True, help="Serial port for ESP32 (e.g. /dev/cu.usbserial-1120)")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--mode", choices=["csv", "arm"], default="csv",
                   help="csv: Python pkl inference; arm: on-device C SVM")
    p.add_argument("--no-video", action="store_true", help="Skip Tello video stream")
    p.add_argument("--speed", type=int, default=40, help="RC speed 0–100")
    p.add_argument("--rest", type=int, default=3, help="seconds to rest between captures")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Load model for CSV mode
    model = None
    if args.mode == "csv":
        model_path = os.path.join(_ROOT, "models", "svm_model.pkl")
        if not os.path.exists(model_path):
            print(f"[ERROR] Model not found at {model_path}")
            print("  Run `python train.py` first, or use --mode arm for on-device inference.")
            sys.exit(1)
        import joblib
        model = joblib.load(model_path)
        print(f"[INFO] Loaded model: {model_path}")

    # Open serial connection to ESP32
    print(f"[INFO] Opening serial {args.port} @ {args.baud}")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except SerialException as e:
        print(f"[ERROR] Cannot open serial port: {e}")
        sys.exit(1)
    time.sleep(0.5)  # let ESP32 stabilise after DTR toggle

    # Tello setup
    enable_video = not args.no_video
    controller = TelloController(enable_video=enable_video)
    bridge = TelloGestureBridge(controller, speed=args.speed)

    stop_event = bridge.stop_event

    try:
        controller.connect()

        # Keyboard thread for takeoff / land / ESC
        keyboard_thread = bridge.start_keyboard_thread()

        # IMU gesture thread
        imu = IMUGestureThread(bridge, ser, model, args.mode, stop_event, args.rest)
        imu_thread = imu.start()

        print("\n[INFO] Ready. Keyboard: T=takeoff, N=land, ESC=quit")
        print(f"[INFO] Mode: {args.mode.upper()} | Perform gestures with the IMU\n")

        if enable_video:
            bridge.stream_video_loop()
        else:
            # No video — just keep main thread alive
            while not stop_event.is_set():
                time.sleep(0.1)

    finally:
        stop_event.set()
        controller.stop_motion()
        if bridge.state.flying:
            try:
                controller.land()
            except Exception:
                pass
        ser.close()
        controller.cleanup()
        print("[INFO] Shutdown complete.")


if __name__ == "__main__":
    main()
