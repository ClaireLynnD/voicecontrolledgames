"""Profile management for voice command configurations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.config.mappings import Mapping

logger = logging.getLogger(__name__)


@dataclass
class Profile:
    """A named collection of voice-to-controller mappings."""

    name: str
    mappings: list[Mapping] = field(default_factory=list)

    def add_mapping(self, mapping: Mapping):
        self.mappings.append(mapping)

    def remove_mapping(self, index: int):
        if 0 <= index < len(self.mappings):
            self.mappings.pop(index)

    def update_mapping(self, index: int, mapping: Mapping):
        if 0 <= index < len(self.mappings):
            self.mappings[index] = mapping

    def save(self, directory: str):
        """Save profile as JSON to directory/{name}.json."""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        filepath = path / f"{self.name}.json"
        data = {
            "name": self.name,
            "mappings": [m.to_dict() for m in self.mappings],
        }
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Profile saved: {filepath}")

    @classmethod
    def load(cls, filepath: str) -> Profile:
        """Load a profile from a JSON file."""
        path = Path(filepath)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            name=data["name"],
            mappings=[Mapping.from_dict(m) for m in data["mappings"]],
        )


class ProfileManager:
    """Manages loading, saving, and listing profiles."""

    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> list[str]:
        """Return names of all available profiles."""
        return [p.stem for p in self.profiles_dir.glob("*.json")]

    def load_profile(self, name: str) -> Profile:
        filepath = self.profiles_dir / f"{name}.json"
        return Profile.load(str(filepath))

    def save_profile(self, profile: Profile):
        profile.save(str(self.profiles_dir))

    def delete_profile(self, name: str):
        filepath = self.profiles_dir / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Profile deleted: {name}")

    def create_default_profile(self) -> Profile:
        """Create a starter profile with common mappings."""
        profile = Profile(
            name="default",
            mappings=[
                Mapping("jump", "a", "tap", 200),
                Mapping("attack", "x", "tap", 200),
                Mapping("block", "b", "hold"),
                Mapping("release block", "b", "release"),
                Mapping("menu", "start", "tap", 200),
                Mapping("up", "dpad_up", "tap", 200),
                Mapping("down", "dpad_down", "tap", 200),
                Mapping("left", "dpad_left", "tap", 200),
                Mapping("right", "dpad_right", "tap", 200),
                Mapping("hold up", "dpad_up", "hold"),
                Mapping("hold down", "dpad_down", "hold"),
                Mapping("hold left", "dpad_left", "hold"),
                Mapping("hold right", "dpad_right", "hold"),
                Mapping("release up", "dpad_up", "release"),
                Mapping("release down", "dpad_down", "release"),
                Mapping("release left", "dpad_left", "release"),
                Mapping("release right", "dpad_right", "release"),
                Mapping("long up", "dpad_up", "tap", 800),
                Mapping("long down", "dpad_down", "tap", 800),
                Mapping("long left", "dpad_left", "tap", 800),
                Mapping("long right", "dpad_right", "tap", 800),
                Mapping("walk left", "left_stick_x", "analog", analog_value=-0.5),
                Mapping("walk right", "left_stick_x", "analog", analog_value=0.5),
                Mapping("run left", "left_stick_x", "analog", analog_value=-1.0),
                Mapping("run right", "left_stick_x", "analog", analog_value=1.0),
                Mapping("stop", "left_stick_x", "analog", analog_value=0.0),
            ],
        )
        self.save_profile(profile)
        return profile
