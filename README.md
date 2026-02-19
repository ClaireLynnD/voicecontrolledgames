# Voice Controlled Games

Control Steam games with your voice. This application creates a virtual Xbox 360 controller and maps spoken commands to button presses, D-pad directions, and analog stick movements using offline speech recognition.

## How It Works

1. **Vosk** listens to your microphone in real time (fully offline, no internet needed)
2. Recognized speech is matched against your configured voice commands
3. Matched commands trigger virtual Xbox 360 controller inputs via **vgamepad**
4. Steam sees the virtual controller as a real gamepad

## Prerequisites

- **Windows 10/11** (required for ViGEmBus virtual controller driver)
- **Python 3.9+**
- **A microphone**
- **ViGEmBus driver** — usually installed automatically with vgamepad. If not, download from [vigembusdriver.com](https://vigembusdriver.com/)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd voicecontrolledgames

# Install Python dependencies
pip install -r requirements.txt
```

### Download a Vosk Model

Download a speech recognition model from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) and extract it to the project root.

The **small English model** is recommended for low-latency gaming:
- [vosk-model-small-en-us-0.15](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip) (~40MB)

After extraction, your project root should contain a folder like `vosk-model-small-en-us-0.15/`.

## Usage

```bash
python -m src.main
```

The GUI will open with:
- **Toolbar** — Start/Stop listening toggle, profile selector, save/new/delete profile buttons
- **Mapping table** — Edit voice commands and their controller bindings
- **Command log** — Real-time display of recognized voice commands

Click **Start** to begin listening. Speak your configured commands and watch them trigger controller inputs.

## Voice Command Mapping

Each mapping connects a spoken word or phrase to a controller action:

| Field | Description |
|-------|-------------|
| **Voice Command** | Word or phrase to recognize (e.g., "jump", "hold up") |
| **Target Input** | Controller button or axis (e.g., `a`, `dpad_up`, `left_stick_x`) |
| **Action Type** | `tap`, `hold`, `release`, or `analog` |
| **Duration** | How long a tap holds the button (milliseconds) |
| **Analog Value** | Preset value for joystick/trigger (-1.0 to 1.0) |

### Action Types

- **tap** — Press the button for a set duration, then release. Use different durations for short vs long presses.
- **hold** — Press and keep held until a corresponding release command.
- **release** — Release a previously held button.
- **analog** — Set a joystick axis or trigger to a fixed value (e.g., half-tilt vs full-tilt).

### Default Profile Examples

The included default profile demonstrates all action types:

| Say | Action |
|-----|--------|
| "jump" | Tap A button (200ms) |
| "attack" | Tap X button (200ms) |
| "block" | Hold B button |
| "release block" | Release B button |
| "up" | Tap D-pad Up (200ms) |
| "long up" | Tap D-pad Up (800ms) |
| "hold up" | Hold D-pad Up |
| "release up" | Release D-pad Up |
| "walk left" | Left stick half-left (-0.5) |
| "run left" | Left stick full-left (-1.0) |
| "stop" | Left stick center (0.0) |

### Available Controller Inputs

**Buttons:** `a`, `b`, `x`, `y`, `lb`, `rb`, `start`, `back`, `ls`, `rs`, `guide`

**D-pad:** `dpad_up`, `dpad_down`, `dpad_left`, `dpad_right`

**Analog:** `left_stick_x`, `left_stick_y`, `right_stick_x`, `right_stick_y`, `left_trigger`, `right_trigger`

## Profiles

Profiles are saved as JSON files in the `profiles/` directory. Use the GUI to:

- **Switch profiles** — Select from the dropdown (e.g., one for platformers, one for RPGs)
- **Create new profiles** — Click "New" and name it
- **Save changes** — Click "Save" after editing mappings
- **Delete profiles** — Click "Delete" to remove the selected profile

## Running Tests

```bash
pytest tests/
```
