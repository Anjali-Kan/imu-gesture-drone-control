"""Temporary control loop for driving Tello with keyboard input."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

try:
    import cv2
except ImportError:  # pragma: no cover - surfaced at runtime
    cv2 = None

try:
    from pynput import keyboard
    from pynput.keyboard import Key
except ImportError:  # pragma: no cover - surfaced at runtime
    keyboard = None
    Key = None

from .tello_controller import RCCommand, TelloController


@dataclass
class ControlState:
    """Current continuous RC state for the drone."""

    lr: int = 0
    fb: int = 0
    ud: int = 0
    yaw: int = 0
    flying: bool = False


class TelloGestureBridge:
    """
    Temporary keyboard-driven control loop.

    For now the keyboard is the source of control instructions.
    Later, the same loop can accept model predictions instead.
    """

    def __init__(
        self,
        controller: TelloController,
        speed: int = 40,
        yaw_speed: int = 60,
    ) -> None:
        self.controller = controller
        self.speed = speed
        self.yaw_speed = yaw_speed
        self.state = ControlState()
        self.stop_event = threading.Event()
        self.listener = None

    def run_keyboard_loop(self) -> None:
        if keyboard is None or Key is None:
            raise ImportError(
                "pynput is required for keyboard control. "
                "Install it with `pip install pynput`."
            )

        print("[CONTROL] Keyboard mode enabled.")
        print("[CONTROL] WASD move, arrows for up/down/yaw.")
        print("[CONTROL] T takeoff, N land, H hover, ESC quit.")
        print("[CONTROL] Press Q in the video window to close the stream.")
        print("[CONTROL] IMU/model hook is commented in this loop for later.")

        with keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        ) as listener:
            self.listener = listener
            listener.join()

    def start_keyboard_thread(self) -> threading.Thread:
        thread = threading.Thread(target=self.run_keyboard_loop, daemon=True)
        thread.start()
        return thread

    def stream_video_loop(self, window_name: str = "Tello Stream") -> None:
        """
        Show the Tello video stream on the main thread.

        This follows the working pattern from the older drone RC threading demo:
        keyboard input runs in a background thread while OpenCV stays on the
        main thread for reliable rendering.
        """
        if cv2 is None:
            raise ImportError(
                "opencv-python is required for video streaming. "
                "Install it with `pip install opencv-python`."
            )

        while not self.stop_event.is_set():
            frame = self.controller.get_frame()
            if frame is None:
                continue

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[CONTROL] Q pressed. Closing video stream.")
                self.stop_event.set()
                break

        cv2.destroyWindow(window_name)

    def apply_instruction(self, instruction: str, intensity: float = 1.0) -> bool:
        """
        Shared instruction handler for keyboard input now and model output later.
        """
        speed = self._scaled_speed(intensity)

        if instruction == "takeoff" and not self.state.flying:
            self.controller.takeoff()
            self.state.flying = True
            return True

        if instruction == "land" and self.state.flying:
            self.controller.land()
            self.state.flying = False
            self._reset_motion()
            return True

        if instruction == "hover":
            self._reset_motion()
            self._send_current_rc()
            return True

        if instruction == "move_forward":
            self.state.fb = speed
        elif instruction == "move_back":
            self.state.fb = -speed
        elif instruction == "move_left":
            self.state.lr = -speed
        elif instruction == "move_right":
            self.state.lr = speed
        elif instruction == "move_up":
            self.state.ud = speed
        elif instruction == "move_down":
            self.state.ud = -speed
        elif instruction == "yaw_left":
            self.state.yaw = -self.yaw_speed
        elif instruction == "yaw_right":
            self.state.yaw = self.yaw_speed
        else:
            return False

        self._send_current_rc()
        return True

    def release_instruction(self, instruction: str) -> bool:
        if instruction in {"move_forward", "move_back"}:
            self.state.fb = 0
        elif instruction in {"move_left", "move_right"}:
            self.state.lr = 0
        elif instruction in {"move_up", "move_down"}:
            self.state.ud = 0
        elif instruction in {"yaw_left", "yaw_right"}:
            self.state.yaw = 0
        else:
            return False

        self._send_current_rc()
        return True

    def _on_press(self, key) -> None:
        try:
            instruction = self._instruction_from_press(key)
            if instruction is None:
                return

            # to be placed - future IMU model hook:
            # prediction = imu_model.predict(windowed_sensor_data)
            # instruction = prediction.label
            self.apply_instruction(instruction)
        except Exception as exc:  # pragma: no cover - hardware/input dependent
            print(f"[CONTROL] Key press handling failed: {exc}")

    def _on_release(self, key):
        try:
            if key == Key.esc:
                print("[CONTROL] ESC pressed. Stopping controller loop.")
                if self.state.flying:
                    self.controller.land()
                    self.state.flying = False
                self.controller.stop_motion()
                self.stop_event.set()
                return False

            instruction = self._instruction_from_release(key)
            if instruction is None:
                return None

            self.release_instruction(instruction)
            return None
        except Exception as exc:  # pragma: no cover - hardware/input dependent
            print(f"[CONTROL] Key release handling failed: {exc}")
            return None

    def _instruction_from_press(self, key) -> Optional[str]:
        char = getattr(key, "char", None)
        if char:
            char = char.lower()
            if char == "w":
                return "move_forward"
            if char == "s":
                return "move_back"
            if char == "a":
                return "move_left"
            if char == "d":
                return "move_right"
            if char == "t":
                return "takeoff"
            if char == "n":
                return "land"
            if char == "h":
                return "hover"

        if key == Key.up:
            return "move_up"
        if key == Key.down:
            return "move_down"
        if key == Key.left:
            return "yaw_left"
        if key == Key.right:
            return "yaw_right"
        return None

    def _instruction_from_release(self, key) -> Optional[str]:
        char = getattr(key, "char", None)
        if char:
            char = char.lower()
            if char == "w":
                return "move_forward"
            if char == "s":
                return "move_back"
            if char == "a":
                return "move_left"
            if char == "d":
                return "move_right"

        if key == Key.up:
            return "move_up"
        if key == Key.down:
            return "move_down"
        if key == Key.left:
            return "yaw_left"
        if key == Key.right:
            return "yaw_right"
        return None

    def _send_current_rc(self) -> None:
        self.controller.send_rc(
            RCCommand(
                lr=self.state.lr,
                fb=self.state.fb,
                ud=self.state.ud,
                yaw=self.state.yaw,
            )
        )

    def _reset_motion(self) -> None:
        self.state.lr = 0
        self.state.fb = 0
        self.state.ud = 0
        self.state.yaw = 0

    def _scaled_speed(self, intensity: float) -> int:
        bounded = max(0.0, min(intensity, 1.0))
        return max(20, int(self.speed * bounded))
