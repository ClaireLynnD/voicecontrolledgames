"""Tests for CommandParser."""

from src.config.mappings import Mapping
from src.speech.command_parser import CommandParser


def _make_parser() -> CommandParser:
    mappings = [
        Mapping("jump", "a", "tap"),
        Mapping("attack", "x", "tap"),
        Mapping("hold up", "dpad_up", "hold"),
        Mapping("up", "dpad_up", "tap"),
        Mapping("walk left", "left_stick_x", "analog", analog_value=-0.5),
    ]
    return CommandParser(mappings)


def test_exact_match():
    parser = _make_parser()
    result = parser.parse("jump")
    assert result is not None
    assert result.voice_command == "jump"
    assert result.target_input == "a"


def test_case_insensitive():
    parser = _make_parser()
    result = parser.parse("JUMP")
    assert result is not None
    assert result.voice_command == "jump"


def test_no_match():
    parser = _make_parser()
    result = parser.parse("dance")
    assert result is None


def test_multi_word_command():
    parser = _make_parser()
    result = parser.parse("hold up")
    assert result is not None
    assert result.voice_command == "hold up"
    assert result.action_type == "hold"


def test_substring_match():
    parser = _make_parser()
    # "please jump now" contains "jump"
    result = parser.parse("please jump now")
    assert result is not None
    assert result.voice_command == "jump"


def test_longest_match_wins():
    parser = _make_parser()
    # "hold up" should match "hold up" not just "up"
    result = parser.parse("hold up")
    assert result is not None
    assert result.voice_command == "hold up"


def test_update_mappings():
    parser = _make_parser()
    new_mappings = [Mapping("fire", "b", "tap")]
    parser.update_mappings(new_mappings)

    assert parser.parse("jump") is None
    result = parser.parse("fire")
    assert result is not None
    assert result.target_input == "b"


def test_empty_text():
    parser = _make_parser()
    assert parser.parse("") is None
    assert parser.parse("   ") is None
