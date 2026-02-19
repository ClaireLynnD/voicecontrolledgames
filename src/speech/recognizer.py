"""Vosk speech recognition engine running in a background QThread."""

import json
import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class SpeechRecognizer(QThread):
    """Continuously listens to the microphone and emits recognized text."""

    command_recognized = pyqtSignal(str)
    partial_result = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model_path: str, sample_rate: int = 16000, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.sample_rate = sample_rate
        self._running = False
        self._paused = False
        self._model = None
        self._recognizer = None

    def _init_model(self):
        """Initialize Vosk model and recognizer."""
        import vosk

        vosk.SetLogLevel(-1)
        self._model = vosk.Model(self.model_path)
        self._recognizer = vosk.KaldiRecognizer(self._model, self.sample_rate)

    def run(self):
        """Main thread loop: open mic and stream to Vosk."""
        import pyaudio

        try:
            self._init_model()
        except Exception as e:
            self.error_occurred.emit(f"Failed to load Vosk model: {e}")
            return

        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=4096,
            )
        except Exception as e:
            self.error_occurred.emit(f"Failed to open microphone: {e}")
            return

        self._running = True
        self.status_changed.emit("Listening")

        try:
            while self._running:
                if self._paused:
                    self.msleep(100)
                    continue

                data = stream.read(4096, exception_on_overflow=False)

                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        logger.info(f"Recognized: {text}")
                        self.command_recognized.emit(text)
                else:
                    partial = json.loads(self._recognizer.PartialResult())
                    partial_text = partial.get("partial", "").strip()
                    if partial_text:
                        self.partial_result.emit(partial_text)
        except Exception as e:
            self.error_occurred.emit(f"Recognition error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            self.status_changed.emit("Stopped")

    def stop(self):
        """Stop the recognition thread."""
        self._running = False
        self.status_changed.emit("Stopping...")

    def pause(self):
        """Pause recognition without stopping the thread."""
        self._paused = True
        self.status_changed.emit("Paused")

    def resume(self):
        """Resume recognition after pause."""
        self._paused = False
        self.status_changed.emit("Listening")
