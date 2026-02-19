"""Main application window for the voice-controlled gamepad project."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QToolBar,
    QWidget,
)

from src.gui.mapping_editor import MappingEditor
from src.gui.mic_selector import MicSelector
from src.gui.profile_manager import ProfileSelector


class MainWindow(QMainWindow):
    """Top-level window that ties together the profile selector, mapping
    editor, and a real-time command log.

    The window expects external code to:
    * Call :meth:`set_profiles` with available profile names.
    * Connect a speech recogniser's ``command_recognized(str)`` and
      ``status_changed(str)`` signals via :meth:`on_command_recognized`
      and :meth:`on_status_changed`.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._listening = False

        self.setWindowTitle("Voice Controlled Games")
        self.setMinimumSize(800, 600)

        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        """Create the main toolbar with listening toggle, profile selector,
        save, new, and delete actions."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Start / Stop listening toggle
        self._toggle_action = QAction("Start", self)
        self._toggle_action.setToolTip("Start or stop voice recognition")
        self._toggle_action.setCheckable(True)
        toolbar.addAction(self._toggle_action)

        toolbar.addSeparator()

        # Profile selector widget (combo + buttons)
        self._profile_selector = ProfileSelector()
        toolbar.addWidget(self._profile_selector)

        toolbar.addSeparator()

        # Microphone selector widget (combo + level bar + refresh)
        self._mic_selector = MicSelector()
        toolbar.addWidget(self._mic_selector)

        toolbar.addSeparator()

        # Status label shown on the right side of the toolbar
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self._status_label = QLabel("Idle")
        toolbar.addWidget(self._status_label)

    def _setup_central_widget(self) -> None:
        """Create a vertical splitter with the mapping editor on top and the
        command log on the bottom."""
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Mapping editor (top)
        self._mapping_editor = MappingEditor()
        splitter.addWidget(self._mapping_editor)

        # Command log (bottom)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Recognized commands will appear here...")
        splitter.addWidget(self._log)

        # Give the editor more space than the log by default
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _setup_status_bar(self) -> None:
        """Initialise the window status bar."""
        self.statusBar().showMessage("Ready")

    def _connect_signals(self) -> None:
        """Wire up internal signals."""
        self._toggle_action.toggled.connect(self._on_toggle_listening)

    # ------------------------------------------------------------------
    # Toolbar actions
    # ------------------------------------------------------------------

    def _on_toggle_listening(self, checked: bool) -> None:
        """Update UI state when the listening toggle is pressed."""
        self._listening = checked
        if checked:
            self._toggle_action.setText("Stop")
            self._toggle_action.setToolTip("Stop voice recognition")
            self.statusBar().showMessage("Listening...")
            self._status_label.setText("Listening")
        else:
            self._toggle_action.setText("Start")
            self._toggle_action.setToolTip("Start voice recognition")
            self.statusBar().showMessage("Stopped")
            self._status_label.setText("Idle")

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def profile_selector(self) -> ProfileSelector:
        """Access the :class:`ProfileSelector` widget."""
        return self._profile_selector

    @property
    def mic_selector(self) -> MicSelector:
        """Access the :class:`MicSelector` widget."""
        return self._mic_selector

    @property
    def mapping_editor(self) -> MappingEditor:
        """Access the :class:`MappingEditor` widget."""
        return self._mapping_editor

    @property
    def toggle_action(self) -> QAction:
        """Access the Start/Stop QAction."""
        return self._toggle_action

    @property
    def listening(self) -> bool:
        """Whether listening mode is currently active."""
        return self._listening

    # ------------------------------------------------------------------
    # Slots for external signals
    # ------------------------------------------------------------------

    def on_command_recognized(self, command: str) -> None:
        """Log a recognized voice command to the command log.

        This slot is intended to be connected to a speech recogniser's
        ``command_recognized(str)`` signal.

        Args:
            command: The recognized voice command text.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"[{timestamp}] {command}")
        # Scroll to bottom
        scrollbar = self._log.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())

    def on_status_changed(self, status: str) -> None:
        """Update the status label and status bar with a new status string.

        This slot is intended to be connected to a speech recogniser's
        ``status_changed(str)`` signal.

        Args:
            status: The new status text.
        """
        self._status_label.setText(status)
        self.statusBar().showMessage(status)

    # ------------------------------------------------------------------
    # Profile helpers
    # ------------------------------------------------------------------

    def set_profiles(self, profile_names: list[str]) -> None:
        """Populate the profile selector with available profile names.

        Args:
            profile_names: List of profile name strings.
        """
        self._profile_selector.refresh_profiles(profile_names)
