"""Microphone device selector and level meter widget."""

import logging

from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal

logger = logging.getLogger(__name__)


def enumerate_input_devices() -> list[dict]:
    """Return a list of dicts with 'index', 'name', 'host_api' for each input device.

    Devices are sorted with WASAPI first (lowest latency on Windows),
    then DirectSound, then others. Duplicate device names across host APIs
    are all included so the user can pick the variant that works with their
    hardware.
    """
    import pyaudio

    pa = pyaudio.PyAudio()

    # Build host API name lookup
    api_names = {}
    for i in range(pa.get_host_api_count()):
        api_info = pa.get_host_api_info_by_index(i)
        api_names[i] = api_info["name"]

    # Host API sort priority (lower = listed first)
    api_priority = {
        "Windows WASAPI": 0,
        "Windows DirectSound": 1,
        "MME": 2,
        "Windows WDM-KS": 3,
    }

    devices = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0:
            host_api = api_names.get(info["hostApi"], "Unknown")
            devices.append({
                "index": i,
                "name": info["name"],
                "host_api": host_api,
            })

    pa.terminate()

    # Sort by host API priority, then by name
    devices.sort(key=lambda d: (api_priority.get(d["host_api"], 99), d["name"]))

    return devices


class MicSelector(QWidget):
    """Toolbar widget: [Mic: label] [device dropdown] [level bar] [Refresh]

    Signals:
        device_changed(object): Emitted when the user picks a different device.
            The value is the PyAudio device index (int) or None for System Default.
    """

    device_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._devices: list[dict] = []
        self._setup_ui()
        self._connect_signals()
        self.refresh_devices()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Mic:"))

        self._combo = QComboBox()
        self._combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._combo.setMinimumWidth(200)
        layout.addWidget(self._combo)

        self._level_bar = QProgressBar()
        self._level_bar.setRange(0, 100)
        self._level_bar.setValue(0)
        self._level_bar.setTextVisible(False)
        self._level_bar.setFixedWidth(80)
        self._level_bar.setFixedHeight(16)
        layout.addWidget(self._level_bar)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setToolTip("Refresh microphone device list")
        layout.addWidget(self._refresh_btn)

    def _connect_signals(self):
        self._combo.currentIndexChanged.connect(self._on_combo_changed)
        self._refresh_btn.clicked.connect(self.refresh_devices)

    def refresh_devices(self):
        """Re-enumerate audio input devices and repopulate the dropdown."""
        current = self.selected_device_index()
        self._combo.blockSignals(True)
        self._combo.clear()

        self._combo.addItem("System Default", userData=None)
        self._devices = enumerate_input_devices()
        for dev in self._devices:
            label = f'{dev["name"]} [{dev["host_api"]}]'
            self._combo.addItem(label, userData=dev["index"])

        self._select_device_index(current)
        self._combo.blockSignals(False)

    def _select_device_index(self, device_index: int | None):
        """Select a combo entry by its PyAudio device index."""
        for i in range(self._combo.count()):
            if self._combo.itemData(i) == device_index:
                self._combo.setCurrentIndex(i)
                return
        self._combo.setCurrentIndex(0)

    def selected_device_index(self) -> int | None:
        """Return the PyAudio device index for the selected device, or None."""
        idx = self._combo.currentIndex()
        if idx < 0:
            return None
        return self._combo.itemData(idx)

    def set_device_index(self, device_index: int | None):
        """Programmatically select a device (e.g. from saved settings)."""
        self._combo.blockSignals(True)
        self._select_device_index(device_index)
        self._combo.blockSignals(False)

    def set_level(self, level: float):
        """Update the level meter. level is 0.0 to 1.0."""
        self._level_bar.setValue(int(level * 100))

    def _on_combo_changed(self, combo_idx: int):
        if combo_idx < 0:
            return
        device_index = self._combo.itemData(combo_idx)
        self.device_changed.emit(device_index)
