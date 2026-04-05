"""Reusable Tello drone controller for the IMU gesture project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import cv2
except ImportError:  # pragma: no cover - optional until video is needed
    cv2 = None

try:
    from djitellopy import Tello
except ImportError:  # pragma: no cover - surfaced at runtime
    Tello = None


@dataclass(frozen=True)
class RCCommand:
    """Continuous control values for the Tello RC interface."""

    lr: int = 0
    fb: int = 0
    ud: int = 0
    yaw: int = 0


class TelloController:
    """Thin, project-friendly wrapper around djitellopy's Tello client."""

    def __init__(self, enable_video: bool = False) -> None:
        self.enable_video = enable_video
        self.drone: Optional["Tello"] = None
        self.frame_reader = None
        self.connected = False

    def connect(self) -> int:
        """Connect to the drone and optionally start the video stream."""
        if Tello is None:
            raise ImportError(
                "djitellopy is required for TelloController. "
                "Install it with `pip install djitellopy opencv-python`."
            )

        if self.connected and self.drone is not None:
            return self.get_battery()

        self.drone = Tello()
        self.drone.connect()
        self.connected = True

        battery = self.drone.get_battery()
        print(f"[TELLO] Connected. Battery: {battery}%")

        if self.enable_video:
            self._start_video_stream()

        return battery

    def _require_connection(self) -> "Tello":
        if not self.connected or self.drone is None:
            raise RuntimeError("Drone is not connected. Call `connect()` first.")
        return self.drone

    def _start_video_stream(self) -> None:
        drone = self._require_connection()
        if cv2 is None:
            raise ImportError(
                "opencv-python is required when enable_video=True. "
                "Install it with `pip install opencv-python`."
            )

        print("[TELLO] Starting video stream...")
        drone.streamon()
        self.frame_reader = drone.get_frame_read()
        print("[TELLO] Video stream ready.")

    def get_battery(self) -> int:
        return self._require_connection().get_battery()

    def get_frame(self):
        """Return the latest camera frame when video streaming is enabled."""
        if not self.enable_video:
            raise RuntimeError("Video is disabled for this controller instance.")
        if self.frame_reader is None:
            raise RuntimeError("Video stream has not been started.")

        frame = self.frame_reader.frame
        if frame is None:
            return None

        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame

    def takeoff(self) -> None:
        self._require_connection().takeoff()

    def land(self) -> None:
        self._require_connection().land()

    def emergency(self) -> None:
        self._require_connection().emergency()

    def move_up(self, distance_cm: int) -> None:
        self._require_connection().move_up(distance_cm)

    def move_down(self, distance_cm: int) -> None:
        self._require_connection().move_down(distance_cm)

    def move_left(self, distance_cm: int) -> None:
        self._require_connection().move_left(distance_cm)

    def move_right(self, distance_cm: int) -> None:
        self._require_connection().move_right(distance_cm)

    def move_forward(self, distance_cm: int) -> None:
        self._require_connection().move_forward(distance_cm)

    def move_back(self, distance_cm: int) -> None:
        self._require_connection().move_back(distance_cm)

    def rotate_clockwise(self, degrees: int) -> None:
        self._require_connection().rotate_clockwise(degrees)

    def rotate_counter_clockwise(self, degrees: int) -> None:
        self._require_connection().rotate_counter_clockwise(degrees)

    def flip(self, direction: str) -> None:
        self._require_connection().flip(direction)

    def send_rc(self, command: RCCommand) -> None:
        self._require_connection().send_rc_control(
            command.lr,
            command.fb,
            command.ud,
            command.yaw,
        )

    def stop_motion(self) -> None:
        self.send_rc(RCCommand())

    def cleanup(self) -> None:
        """Shut down video and window state without forcing a land command."""
        if self.drone is None:
            return

        try:
            if getattr(self.drone, "stream_on", False):
                self.drone.streamoff()
        except Exception as exc:  # pragma: no cover - hardware dependent
            print(f"[TELLO] Failed to stop stream: {exc}")

        if cv2 is not None:
            try:
                cv2.destroyAllWindows()
            except Exception as exc:  # pragma: no cover - UI dependent
                print(f"[TELLO] Failed to close OpenCV windows: {exc}")
