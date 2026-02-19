"""Profile management widget for selecting, creating, saving, and deleting profiles."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QWidget,
)


class ProfileSelector(QWidget):
    """Widget providing profile selection and management controls.

    Provides a combo box for selecting profiles and buttons for saving,
    creating, and deleting profiles. Emits signals when actions are requested.
    """

    profile_changed = pyqtSignal(str)
    profile_save_requested = pyqtSignal()
    profile_new_requested = pyqtSignal(str)
    profile_delete_requested = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create and arrange the UI elements."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._combo = QComboBox()
        self._combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self._combo.setMinimumWidth(160)
        layout.addWidget(self._combo)

        self._save_button = QPushButton("Save")
        self._save_button.setToolTip("Save the current profile")
        layout.addWidget(self._save_button)

        self._new_button = QPushButton("New")
        self._new_button.setToolTip("Create a new profile")
        layout.addWidget(self._new_button)

        self._delete_button = QPushButton("Delete")
        self._delete_button.setToolTip("Delete the selected profile")
        layout.addWidget(self._delete_button)

    def _connect_signals(self) -> None:
        """Wire up internal widget signals to external signals."""
        self._combo.currentTextChanged.connect(self._on_profile_changed)
        self._save_button.clicked.connect(self._on_save_clicked)
        self._new_button.clicked.connect(self._on_new_clicked)
        self._delete_button.clicked.connect(self._on_delete_clicked)

    def _on_profile_changed(self, text: str) -> None:
        """Handle combo box selection change."""
        if text:
            self.profile_changed.emit(text)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        self.profile_save_requested.emit()

    def _on_new_clicked(self) -> None:
        """Prompt the user for a new profile name and emit the signal."""
        name, ok = QInputDialog.getText(
            self, "New Profile", "Enter profile name:"
        )
        if ok and name.strip():
            self.profile_new_requested.emit(name.strip())

    def _on_delete_clicked(self) -> None:
        """Confirm and emit deletion of the currently selected profile."""
        profile_name = self.current_profile()
        if not profile_name:
            return

        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f'Are you sure you want to delete profile "{profile_name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_delete_requested.emit(profile_name)

    def refresh_profiles(self, profile_names: list[str]) -> None:
        """Update the combo box with the given list of profile names.

        Args:
            profile_names: Names to populate in the combo box.
        """
        current = self._combo.currentText()
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItems(profile_names)
        # Restore previous selection if still present
        idx = self._combo.findText(current)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        self._combo.blockSignals(False)
        # Emit for the restored (or new first) selection
        if self._combo.currentText():
            self.profile_changed.emit(self._combo.currentText())

    def current_profile(self) -> str:
        """Return the name of the currently selected profile."""
        return self._combo.currentText()
