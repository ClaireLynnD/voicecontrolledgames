"""Mapping table editor widget for voice-command-to-gamepad-input mappings."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config.mappings import VALID_ACTIONS, VALID_INPUTS, Mapping


# ---------------------------------------------------------------------------
# Delegates for combo-box columns
# ---------------------------------------------------------------------------

class _ComboBoxDelegate(QStyledItemDelegate):
    """Delegate that presents a QComboBox for editing a table cell."""

    def __init__(
        self, items: list[str], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._items = items

    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index,  # QModelIndex
    ) -> QComboBox:
        combo = QComboBox(parent)
        combo.addItems(self._items)
        return combo

    def setEditorData(self, editor: QComboBox, index) -> None:  # noqa: N802
        value = index.data(Qt.ItemDataRole.EditRole)
        idx = editor.findText(value or "")
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor: QComboBox, model, index) -> None:  # noqa: N802
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor: QComboBox, option, index) -> None:  # noqa: N802
        editor.setGeometry(option.rect)


# ---------------------------------------------------------------------------
# Column constants
# ---------------------------------------------------------------------------

_COL_VOICE_COMMAND = 0
_COL_TARGET_INPUT = 1
_COL_ACTION_TYPE = 2
_COL_DURATION = 3
_COL_ANALOG_VALUE = 4

_COLUMN_HEADERS = [
    "Voice Command",
    "Target Input",
    "Action Type",
    "Duration (ms)",
    "Analog Value",
]


class MappingEditor(QWidget):
    """Editable table of voice-command-to-gamepad-input mappings.

    Provides add/remove controls and emits ``mappings_changed`` whenever the
    user modifies any cell.
    """

    mappings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Table
        self._table = QTableWidget(0, len(_COLUMN_HEADERS))
        self._table.setHorizontalHeaderLabels(_COLUMN_HEADERS)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        header = self._table.horizontalHeader()
        if header is not None:
            header.setStretchLastSection(True)
            header.setSectionResizeMode(
                _COL_VOICE_COMMAND, QHeaderView.ResizeMode.Stretch
            )

        # Delegates for combo-box columns
        self._target_delegate = _ComboBoxDelegate(list(VALID_INPUTS), self._table)
        self._table.setItemDelegateForColumn(_COL_TARGET_INPUT, self._target_delegate)

        self._action_delegate = _ComboBoxDelegate(list(VALID_ACTIONS), self._table)
        self._table.setItemDelegateForColumn(_COL_ACTION_TYPE, self._action_delegate)

        layout.addWidget(self._table)

        # Buttons
        button_layout = QHBoxLayout()
        self._add_button = QPushButton("Add Mapping")
        self._remove_button = QPushButton("Remove Mapping")
        button_layout.addWidget(self._add_button)
        button_layout.addWidget(self._remove_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        self._add_button.clicked.connect(self._add_empty_row)
        self._remove_button.clicked.connect(self._remove_selected_row)
        self._table.cellChanged.connect(self._on_cell_changed)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_empty_row(self) -> None:
        """Append an empty row to the table."""
        row = self._table.rowCount()
        self._table.blockSignals(True)
        self._table.insertRow(row)
        self._init_row(row, "", "", "tap", "100", "0.0")
        self._table.blockSignals(False)
        self.mappings_changed.emit()

    def _remove_selected_row(self) -> None:
        """Remove the currently selected row, if any."""
        current_row = self._table.currentRow()
        if current_row >= 0:
            self._table.removeRow(current_row)
            self.mappings_changed.emit()

    def _init_row(
        self,
        row: int,
        voice_command: str,
        target_input: str,
        action_type: str,
        duration: str,
        analog_value: str,
    ) -> None:
        """Populate a single row with the provided values."""
        self._table.setItem(row, _COL_VOICE_COMMAND, QTableWidgetItem(voice_command))
        self._table.setItem(row, _COL_TARGET_INPUT, QTableWidgetItem(target_input))
        self._table.setItem(row, _COL_ACTION_TYPE, QTableWidgetItem(action_type))
        self._table.setItem(row, _COL_DURATION, QTableWidgetItem(duration))
        self._table.setItem(row, _COL_ANALOG_VALUE, QTableWidgetItem(analog_value))
        self._update_cell_enabled_state(row, action_type)

    def _update_cell_enabled_state(self, row: int, action_type: str) -> None:
        """Enable or disable Duration / Analog Value cells based on action type."""
        duration_item = self._table.item(row, _COL_DURATION)
        analog_item = self._table.item(row, _COL_ANALOG_VALUE)

        if duration_item is not None:
            if action_type in ("tap", "hold"):
                duration_item.setFlags(
                    duration_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled
                )
            else:
                duration_item.setFlags(
                    duration_item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                    & ~Qt.ItemFlag.ItemIsEnabled
                )

        if analog_item is not None:
            if action_type == "analog":
                analog_item.setFlags(
                    analog_item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled
                )
            else:
                analog_item.setFlags(
                    analog_item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                    & ~Qt.ItemFlag.ItemIsEnabled
                )

    def _on_cell_changed(self, row: int, column: int) -> None:
        """React to any cell edit, updating enabled state when action type changes."""
        if column == _COL_ACTION_TYPE:
            item = self._table.item(row, _COL_ACTION_TYPE)
            if item is not None:
                self._table.blockSignals(True)
                self._update_cell_enabled_state(row, item.text())
                self._table.blockSignals(False)
        self.mappings_changed.emit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_mappings(self, mappings: list[Mapping]) -> None:
        """Populate the table from a list of :class:`Mapping` objects.

        Args:
            mappings: Mappings to display.
        """
        self._table.blockSignals(True)
        self._table.setRowCount(0)

        for mapping in mappings:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._init_row(
                row,
                mapping.voice_command,
                mapping.target_input,
                mapping.action_type,
                str(mapping.duration_ms),
                str(mapping.analog_value),
            )

        self._table.blockSignals(False)

    def get_mappings(self) -> list[Mapping]:
        """Collect and return the current table contents as :class:`Mapping` objects."""
        mappings: list[Mapping] = []
        for row in range(self._table.rowCount()):
            voice_item = self._table.item(row, _COL_VOICE_COMMAND)
            target_item = self._table.item(row, _COL_TARGET_INPUT)
            action_item = self._table.item(row, _COL_ACTION_TYPE)
            duration_item = self._table.item(row, _COL_DURATION)
            analog_item = self._table.item(row, _COL_ANALOG_VALUE)

            voice_command = voice_item.text() if voice_item else ""
            target_input = target_item.text() if target_item else ""
            action_type = action_item.text() if action_item else "tap"
            duration_text = duration_item.text() if duration_item else "100"
            analog_text = analog_item.text() if analog_item else "0.0"

            try:
                duration_ms = int(duration_text)
            except ValueError:
                duration_ms = 100

            try:
                analog_value = float(analog_text)
            except ValueError:
                analog_value = 0.0

            mappings.append(
                Mapping(
                    voice_command=voice_command,
                    target_input=target_input,
                    action_type=action_type,
                    duration_ms=duration_ms,
                    analog_value=analog_value,
                )
            )
        return mappings
