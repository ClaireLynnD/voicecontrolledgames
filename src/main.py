"""Entry point for Voice Controlled Games."""

import glob
import logging
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.config.profile import ProfileManager
from src.gui.main_window import MainWindow
from src.speech.command_parser import CommandParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def find_vosk_model() -> str | None:
    """Look for a Vosk model directory in the project root."""
    matches = glob.glob("vosk-model*")
    dirs = [m for m in matches if __import__("os").path.isdir(m)]
    return dirs[0] if dirs else None


def main():
    app = QApplication(sys.argv)

    # Profile manager
    profile_mgr = ProfileManager("profiles")
    if not profile_mgr.list_profiles():
        profile_mgr.create_default_profile()

    # Virtual gamepad
    gamepad = None
    try:
        from src.controller.gamepad import VoiceGamepad
        gamepad = VoiceGamepad()
    except Exception as e:
        QMessageBox.warning(
            None,
            "Gamepad Error",
            f"Could not create virtual gamepad:\n\n{e}\n\n"
            "Install ViGEmBus from https://vigembusdriver.com/\n"
            "Then: pip install vgamepad\n\n"
            "The app will run without gamepad output.",
        )

    # Vosk model
    model_path = find_vosk_model()
    recognizer = None
    if model_path:
        try:
            from src.speech.recognizer import SpeechRecognizer
            recognizer = SpeechRecognizer(model_path)
        except Exception as e:
            QMessageBox.warning(
                None,
                "Speech Recognition Error",
                f"Could not initialize speech recognizer:\n\n{e}",
            )
    else:
        QMessageBox.information(
            None,
            "Vosk Model Not Found",
            "No Vosk model directory found (vosk-model*).\n\n"
            "Download a model from https://alphacephei.com/vosk/models\n"
            "and extract it to the project root.\n\n"
            "Recommended: vosk-model-small-en-us-0.15\n\n"
            "The app will run without speech recognition.",
        )

    # Command parser
    parser = CommandParser()

    # Main window
    window = MainWindow()

    # Load profiles into the UI
    window.set_profiles(profile_mgr.list_profiles())

    # Current profile state
    current_profile = None

    def load_profile(name: str):
        nonlocal current_profile
        try:
            current_profile = profile_mgr.load_profile(name)
            window.mapping_editor.load_mappings(current_profile.mappings)
            parser.update_mappings(current_profile.mappings)
            logger.info(f"Loaded profile: {name}")
        except Exception as e:
            logger.error(f"Failed to load profile '{name}': {e}")

    def save_profile():
        if current_profile is None:
            return
        current_profile.mappings = window.mapping_editor.get_mappings()
        profile_mgr.save_profile(current_profile)
        parser.update_mappings(current_profile.mappings)
        logger.info(f"Saved profile: {current_profile.name}")

    def new_profile(name: str):
        nonlocal current_profile
        from src.config.profile import Profile
        current_profile = Profile(name=name, mappings=[])
        profile_mgr.save_profile(current_profile)
        window.set_profiles(profile_mgr.list_profiles())
        window.profile_selector.set_profile(name)
        window.mapping_editor.load_mappings([])
        parser.update_mappings([])

    def delete_profile(name: str):
        nonlocal current_profile
        profile_mgr.delete_profile(name)
        profiles = profile_mgr.list_profiles()
        window.set_profiles(profiles)
        if profiles:
            load_profile(profiles[0])
        else:
            current_profile = None
            window.mapping_editor.load_mappings([])
            parser.update_mappings([])

    # Connect profile signals
    window.profile_selector.profile_changed.connect(load_profile)
    window.profile_selector.profile_save_requested.connect(save_profile)
    window.profile_selector.profile_new_requested.connect(new_profile)
    window.profile_selector.profile_delete_requested.connect(delete_profile)

    # Connect speech recognition
    def on_command_recognized(text: str):
        window.on_command_recognized(text)
        mapping = parser.parse(text)
        if mapping and gamepad:
            gamepad.execute_mapping(mapping)
            logger.info(f"Executed: {mapping.voice_command} -> {mapping.target_input} ({mapping.action_type})")

    if recognizer:
        recognizer.command_recognized.connect(on_command_recognized)
        recognizer.partial_result.connect(
            lambda t: window.statusBar().showMessage(f"Hearing: {t}")
        )
        recognizer.status_changed.connect(window.on_status_changed)
        recognizer.error_occurred.connect(
            lambda e: QMessageBox.warning(window, "Speech Error", str(e))
        )

    # Connect start/stop toggle
    def on_toggle_listening(checked: bool):
        if recognizer is None:
            window.toggle_action.setChecked(False)
            QMessageBox.warning(
                window,
                "No Speech Engine",
                "Speech recognizer is not available.\n"
                "Make sure a Vosk model is in the project root.",
            )
            return
        if checked:
            recognizer.start()
        else:
            recognizer.stop()

    window.toggle_action.toggled.connect(on_toggle_listening)

    # Load first profile
    profiles = profile_mgr.list_profiles()
    if profiles:
        window.profile_selector.set_profile(profiles[0])
        load_profile(profiles[0])

    window.show()
    exit_code = app.exec()

    # Cleanup
    if recognizer and recognizer.isRunning():
        recognizer.stop()
        recognizer.wait(3000)
    if gamepad:
        gamepad.cleanup()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
