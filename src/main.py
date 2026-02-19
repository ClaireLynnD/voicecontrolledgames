"""Entry point for Voice Controlled Games."""

import glob
import logging
import os
import sys
import zipfile

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from src.config.profile import ProfileManager
from src.config.settings import AppSettings
from src.gui.main_window import MainWindow
from src.speech.command_parser import CommandParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"
VOSK_MODEL_URL = f"https://alphacephei.com/vosk/models/{VOSK_MODEL_NAME}.zip"


def find_vosk_model() -> str | None:
    """Look for a Vosk model directory in the project root."""
    matches = glob.glob("vosk-model*")
    dirs = [m for m in matches if os.path.isdir(m)]
    return dirs[0] if dirs else None


class _ModelDownloader(QThread):
    """Background thread that downloads and extracts the Vosk model."""

    progress = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    finished_ok = pyqtSignal(str)    # extracted directory path
    failed = pyqtSignal(str)         # error message

    def run(self):
        import urllib.request

        zip_path = f"{VOSK_MODEL_NAME}.zip"
        try:
            req = urllib.request.Request(VOSK_MODEL_URL)
            with urllib.request.urlopen(req) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = resp.read(1024 * 64)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(".")

            os.remove(zip_path)
            self.finished_ok.emit(VOSK_MODEL_NAME)
        except Exception as e:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            self.failed.emit(str(e))


def download_vosk_model(parent=None) -> str | None:
    """Download the Vosk model with a progress dialog. Returns the model path or None."""
    dialog = QProgressDialog(
        f"Downloading {VOSK_MODEL_NAME}...", "Cancel", 0, 100, parent
    )
    dialog.setWindowTitle("Downloading Speech Model")
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.setMinimumDuration(0)
    dialog.setValue(0)

    result = [None]
    error = [None]

    downloader = _ModelDownloader()

    def on_progress(downloaded, total):
        if dialog.wasCanceled():
            downloader.terminate()
            return
        if total > 0:
            pct = int(downloaded * 100 / total)
            dialog.setValue(pct)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            dialog.setLabelText(
                f"Downloading {VOSK_MODEL_NAME}...\n"
                f"{mb_down:.1f} / {mb_total:.1f} MB"
            )

    def on_finished(path):
        result[0] = path
        dialog.setValue(100)
        dialog.close()

    def on_failed(msg):
        error[0] = msg
        dialog.close()

    downloader.progress.connect(on_progress)
    downloader.finished_ok.connect(on_finished)
    downloader.failed.connect(on_failed)

    downloader.start()
    dialog.exec()

    if dialog.wasCanceled():
        downloader.terminate()
        downloader.wait(3000)
        return None

    downloader.wait()

    if error[0]:
        QMessageBox.warning(
            parent,
            "Download Failed",
            f"Failed to download Vosk model:\n\n{error[0]}\n\n"
            "The app will run without speech recognition.",
        )
        return None

    return result[0]


def main():
    app = QApplication(sys.argv)

    # App settings
    settings = AppSettings("settings.json")

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
    if not model_path:
        model_path = download_vosk_model()
    if model_path:
        try:
            from src.speech.recognizer import SpeechRecognizer
            recognizer = SpeechRecognizer(
                model_path, device_index=settings.mic_device_index
            )
        except Exception as e:
            QMessageBox.warning(
                None,
                "Speech Recognition Error",
                f"Could not initialize speech recognizer:\n\n{e}",
            )

    # Command parser
    parser = CommandParser()

    # Main window
    window = MainWindow()

    # Load profiles into the UI
    window.set_profiles(profile_mgr.list_profiles())

    # Initialize mic selector with saved device
    window.mic_selector.set_device_index(settings.mic_device_index)

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

    def connect_recognizer_signals():
        """Connect all recognizer signals to their handlers."""
        if recognizer is None:
            return
        recognizer.command_recognized.connect(on_command_recognized)
        recognizer.partial_result.connect(
            lambda t: window.statusBar().showMessage(f"Hearing: {t}")
        )
        recognizer.status_changed.connect(window.on_status_changed)
        recognizer.error_occurred.connect(
            lambda e: QMessageBox.warning(window, "Speech Error", str(e))
        )
        recognizer.audio_level.connect(window.mic_selector.set_level)

    connect_recognizer_signals()

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

    # Connect mic device change
    def on_device_changed(device_index):
        settings.mic_device_index = device_index
        if recognizer is None:
            return
        was_running = recognizer.isRunning()
        if was_running:
            recognizer.stop()
            recognizer.wait(3000)
        recognizer.device_index = device_index
        if was_running:
            recognizer.start()

    window.mic_selector.device_changed.connect(on_device_changed)

    # Load first profile
    profiles = profile_mgr.list_profiles()
    if profiles:
        window.profile_selector.refresh_profiles(profiles)
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
