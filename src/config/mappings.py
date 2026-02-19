"""Voice-to-controller mapping data structures."""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_INPUTS = [
    "a", "b", "x", "y",
    "lb", "rb",
    "start", "back",
    "ls", "rs",
    "guide",
    "dpad_up", "dpad_down", "dpad_left", "dpad_right",
    "left_stick_x", "left_stick_y",
    "right_stick_x", "right_stick_y",
    "left_trigger", "right_trigger",
]

VALID_ACTIONS = ["tap", "hold", "release", "analog"]


@dataclass
class Mapping:
    """A single voice command to controller input mapping."""

    voice_command: str
    target_input: str
    action_type: str = "tap"
    duration_ms: int = 200
    analog_value: float = 0.0

    def validate(self) -> list[str]:
        """Return a list of validation errors (empty if valid)."""
        errors = []
        if not self.voice_command.strip():
            errors.append("Voice command cannot be empty")
        if self.target_input not in VALID_INPUTS:
            errors.append(f"Invalid target input: {self.target_input}")
        if self.action_type not in VALID_ACTIONS:
            errors.append(f"Invalid action type: {self.action_type}")
        if self.action_type == "tap" and self.duration_ms <= 0:
            errors.append("Duration must be positive for tap actions")
        if self.action_type == "analog" and not (-1.0 <= self.analog_value <= 1.0):
            errors.append("Analog value must be between -1.0 and 1.0")
        return errors

    def to_dict(self) -> dict:
        return {
            "voice_command": self.voice_command,
            "target_input": self.target_input,
            "action_type": self.action_type,
            "duration_ms": self.duration_ms,
            "analog_value": self.analog_value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Mapping:
        return cls(
            voice_command=data["voice_command"],
            target_input=data["target_input"],
            action_type=data.get("action_type", "tap"),
            duration_ms=data.get("duration_ms", 200),
            analog_value=data.get("analog_value", 0.0),
        )
