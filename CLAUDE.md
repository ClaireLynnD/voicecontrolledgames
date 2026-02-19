# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice-controlled virtual gamepad for Steam games. Uses speech recognition to map voice commands to Xbox 360 controller inputs via a virtual gamepad, with a PyQt6 GUI for configuration.

## Tech Stack

- **Speech Recognition:** Vosk (offline, low-latency streaming)
- **Virtual Controller:** vgamepad (Xbox 360 emulation via ViGEmBus)
- **GUI:** PyQt6
- **Audio:** PyAudio for microphone input
- **Config:** JSON profile files in `profiles/`

## Architecture

```
src/
├── main.py              # Entry point, launches GUI and speech engine
├── speech/
│   ├── recognizer.py    # Vosk speech recognition engine (background QThread)
│   └── command_parser.py # Matches recognized text to profile mappings
├── controller/
│   └── gamepad.py       # vgamepad Xbox 360 wrapper (tap/hold/release/analog)
├── config/
│   ├── profile.py       # Profile management (load/save/switch JSON profiles)
│   └── mappings.py      # Mapping data structures and validation
└── gui/
    ├── main_window.py   # Main PyQt6 window
    ├── mapping_editor.py # Voice-to-button mapping table editor
    └── profile_manager.py # Profile selector and management widget
```

### Threading Model

- **Main thread:** PyQt6 event loop + GUI
- **Speech thread:** Vosk continuously listens via PyAudio, emits recognized text via Qt signals
- **Gamepad actions:** Dispatched from main thread; timed holds use threading.Timer

### Key Concepts

- **Profile:** A JSON file in `profiles/` containing a list of voice-to-input mappings
- **Mapping:** Links a voice command (word/phrase) to a controller input + action type (tap/hold/release) + parameters (duration, analog value)
- **Action types:** `tap` (press + delay + release), `hold` (press until release command), `release` (explicit release), `analog` (set joystick/trigger to preset value)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.main

# Run tests
pytest tests/

# Run a single test
pytest tests/test_file.py::test_name
```

## ViGEmBus Requirement

The ViGEmBus driver must be installed on Windows for vgamepad to work. It is normally installed automatically with `pip install vgamepad`. If not, download from https://vigembusdriver.com/.

## Vosk Model

A Vosk model must be downloaded and placed in the project root (e.g., `vosk-model-small-en-us-0.15/`). The small English model is recommended for low-latency gaming use. Download from https://alphacephei.com/vosk/models.
