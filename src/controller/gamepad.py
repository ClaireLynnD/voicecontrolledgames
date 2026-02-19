"""Xbox 360 virtual gamepad wrapper using vgamepad."""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

try:
    import vgamepad as vg

    VGAMEPAD_AVAILABLE = True
except ImportError:
    VGAMEPAD_AVAILABLE = False
    vg = None

# String name -> vgamepad button constant
BUTTON_MAP: dict[str, Any] = {}
if VGAMEPAD_AVAILABLE:
    BUTTON_MAP = {
        "a": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        "b": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        "x": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        "y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        "lb": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        "rb": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        "back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        "ls": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
        "rs": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        "guide": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
        "dpad_up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        "dpad_down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        "dpad_left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        "dpad_right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    }

ANALOG_INPUTS = {
    "left_stick_x",
    "left_stick_y",
    "right_stick_x",
    "right_stick_y",
    "left_trigger",
    "right_trigger",
}


class VoiceGamepad:
    """Wraps a vgamepad VX360Gamepad with voice-command-friendly methods."""

    def __init__(self):
        if not VGAMEPAD_AVAILABLE:
            raise RuntimeError(
                "vgamepad is not installed or ViGEmBus driver is missing.\n"
                "Install with: pip install vgamepad\n"
                "ViGEmBus: https://vigembusdriver.com/"
            )
        self._pad = vg.VX360Gamepad()
        self._lock = threading.Lock()
        self._held_buttons: set[str] = set()
        self._tap_timers: list[threading.Timer] = []
        logger.info("Virtual Xbox 360 gamepad created")

    def tap(self, button_name: str, duration_ms: int = 200):
        """Press a button for a duration then release."""
        button = BUTTON_MAP.get(button_name)
        if button is None:
            logger.warning(f"Unknown button: {button_name}")
            return

        with self._lock:
            self._pad.press_button(button=button)
            self._pad.update()

        def _release():
            with self._lock:
                self._pad.release_button(button=button)
                self._pad.update()
                self._held_buttons.discard(button_name)

        timer = threading.Timer(duration_ms / 1000.0, _release)
        self._tap_timers.append(timer)
        timer.start()

    def hold(self, button_name: str, duration_ms: int = 0):
        """Press and hold a button.

        If *duration_ms* is > 0, the button is automatically released after
        that many milliseconds.  Otherwise it is held until explicitly released.
        """
        button = BUTTON_MAP.get(button_name)
        if button is None:
            logger.warning(f"Unknown button: {button_name}")
            return

        with self._lock:
            self._pad.press_button(button=button)
            self._pad.update()
            self._held_buttons.add(button_name)

        if duration_ms > 0:
            def _release():
                with self._lock:
                    self._pad.release_button(button=button)
                    self._pad.update()
                    self._held_buttons.discard(button_name)

            timer = threading.Timer(duration_ms / 1000.0, _release)
            self._tap_timers.append(timer)
            timer.start()

    def release(self, button_name: str):
        """Release a held button."""
        button = BUTTON_MAP.get(button_name)
        if button is None:
            logger.warning(f"Unknown button: {button_name}")
            return

        with self._lock:
            self._pad.release_button(button=button)
            self._pad.update()
            self._held_buttons.discard(button_name)

    def set_analog(self, input_name: str, value: float):
        """Set an analog input to a value.

        Joysticks: -1.0 to 1.0
        Triggers: 0.0 to 1.0
        """
        with self._lock:
            if input_name == "left_stick_x":
                self._pad.left_joystick_float(x_value_float=value, y_value_float=0.0)
            elif input_name == "left_stick_y":
                self._pad.left_joystick_float(x_value_float=0.0, y_value_float=value)
            elif input_name == "right_stick_x":
                self._pad.right_joystick_float(x_value_float=value, y_value_float=0.0)
            elif input_name == "right_stick_y":
                self._pad.right_joystick_float(x_value_float=0.0, y_value_float=value)
            elif input_name == "left_trigger":
                self._pad.left_trigger_float(value_float=max(0.0, min(1.0, value)))
            elif input_name == "right_trigger":
                self._pad.right_trigger_float(value_float=max(0.0, min(1.0, value)))
            else:
                logger.warning(f"Unknown analog input: {input_name}")
                return
            self._pad.update()

    def execute_mapping(self, mapping) -> None:
        """Execute a controller action from a Mapping object."""
        target = mapping.target_input
        action = mapping.action_type

        if action == "tap":
            self.tap(target, duration_ms=mapping.duration_ms)
        elif action == "hold":
            self.hold(target, duration_ms=mapping.duration_ms)
        elif action == "release":
            self.release(target)
        elif action == "analog":
            self.set_analog(target, mapping.analog_value)
        else:
            logger.warning(f"Unknown action type: {action}")

    def release_all(self):
        """Reset all inputs to neutral."""
        # Cancel pending tap timers
        for timer in self._tap_timers:
            timer.cancel()
        self._tap_timers.clear()

        with self._lock:
            self._pad.reset()
            self._pad.update()
            self._held_buttons.clear()

    def cleanup(self):
        """Release all and clean up."""
        self.release_all()
        logger.info("Gamepad cleaned up")
