"""Minimal entrypoint for keyboard control now and IMU control later."""

from __future__ import annotations

from control import TelloController, TelloGestureBridge


def main() -> None:
    controller = TelloController(enable_video=True)
    bridge = TelloGestureBridge(controller)

    keyboard_thread = None

    try:
        controller.connect()
        keyboard_thread = bridge.start_keyboard_thread()
        bridge.stream_video_loop()
    finally:
        bridge.stop_event.set()
        controller.stop_motion()
        if bridge.state.flying:
            try:
                controller.land()
            except Exception:
                pass
        if keyboard_thread is not None:
            keyboard_thread.join(timeout=1.0)
        controller.cleanup()


if __name__ == "__main__":
    main()
