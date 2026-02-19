"""Application-wide settings persistence (JSON file)."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULTS = {
    "mic_device_index": None,
}


class AppSettings:
    """Loads and saves a flat JSON dict of app-wide settings."""

    def __init__(self, path: str = "settings.json"):
        self._path = Path(path)
        self._data: dict = dict(_DEFAULTS)
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                self._data.update(raw)
            except Exception as e:
                logger.warning(f"Failed to load settings: {e}")

    def save(self):
        self._path.write_text(
            json.dumps(self._data, indent=2), encoding="utf-8"
        )

    @property
    def mic_device_index(self) -> int | None:
        return self._data.get("mic_device_index")

    @mic_device_index.setter
    def mic_device_index(self, value: int | None):
        self._data["mic_device_index"] = value
        self.save()
