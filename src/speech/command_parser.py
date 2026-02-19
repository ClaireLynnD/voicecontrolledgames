"""Matches recognized speech text to voice command mappings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.mappings import Mapping

logger = logging.getLogger(__name__)


class CommandParser:
    """Parses recognized text and finds matching voice command mappings."""

    def __init__(self, mappings: list[Mapping] | None = None):
        self._mappings: list[Mapping] = mappings or []
        self._sorted_commands: list[tuple[str, int]] = []
        self._rebuild_index()

    def _rebuild_index(self):
        """Sort commands longest-first for greedy matching."""
        self._sorted_commands = sorted(
            [(m.voice_command.lower(), i) for i, m in enumerate(self._mappings)],
            key=lambda x: len(x[0]),
            reverse=True,
        )

    def update_mappings(self, mappings: list[Mapping]):
        """Replace the current mappings list."""
        self._mappings = mappings
        self._rebuild_index()

    def parse(self, recognized_text: str) -> Mapping | None:
        """Find the best matching mapping for recognized text.

        Tries exact match first, then checks if any command phrase
        is contained in the recognized text (longest match wins).
        """
        text = recognized_text.strip().lower()
        if not text:
            return None

        # Exact match
        for command, idx in self._sorted_commands:
            if text == command:
                logger.info(f"Exact match: '{text}' -> {self._mappings[idx]}")
                return self._mappings[idx]

        # Substring match (longest command first)
        for command, idx in self._sorted_commands:
            if command in text:
                logger.info(f"Substring match: '{text}' contains '{command}' -> {self._mappings[idx]}")
                return self._mappings[idx]

        logger.debug(f"No match for: '{text}'")
        return None
