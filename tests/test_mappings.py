"""Tests for Mapping dataclass and validation."""

from src.config.mappings import Mapping, VALID_INPUTS, VALID_ACTIONS


def test_create_mapping():
    m = Mapping("jump", "a", "tap", 200, 0.0)
    assert m.voice_command == "jump"
    assert m.target_input == "a"
    assert m.action_type == "tap"
    assert m.duration_ms == 200
    assert m.analog_value == 0.0


def test_mapping_defaults():
    m = Mapping("jump", "a")
    assert m.action_type == "tap"
    assert m.duration_ms == 200
    assert m.analog_value == 0.0


def test_to_dict_from_dict_roundtrip():
    original = Mapping("hold up", "dpad_up", "hold", 500, 0.0)
    data = original.to_dict()
    restored = Mapping.from_dict(data)
    assert restored.voice_command == original.voice_command
    assert restored.target_input == original.target_input
    assert restored.action_type == original.action_type
    assert restored.duration_ms == original.duration_ms
    assert restored.analog_value == original.analog_value


def test_validate_valid_mapping():
    m = Mapping("jump", "a", "tap", 200, 0.0)
    assert m.validate() == []


def test_validate_invalid_target():
    m = Mapping("jump", "invalid_button", "tap")
    errors = m.validate()
    assert any("target input" in e.lower() for e in errors)


def test_validate_invalid_action():
    m = Mapping("jump", "a", "invalid_action")
    errors = m.validate()
    assert any("action type" in e.lower() for e in errors)


def test_validate_empty_voice_command():
    m = Mapping("", "a", "tap")
    errors = m.validate()
    assert any("empty" in e.lower() for e in errors)


def test_validate_negative_duration():
    m = Mapping("jump", "a", "tap", -100)
    errors = m.validate()
    assert any("duration" in e.lower() for e in errors)


def test_validate_analog_out_of_range():
    m = Mapping("push", "left_stick_x", "analog", analog_value=2.0)
    errors = m.validate()
    assert any("analog" in e.lower() for e in errors)


def test_analog_mapping():
    m = Mapping("walk left", "left_stick_x", "analog", analog_value=-0.5)
    assert m.validate() == []
    d = m.to_dict()
    assert d["analog_value"] == -0.5
