"""Vosk speech recognition engine running in a background QThread."""

import json
import logging
import math
import struct

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


def compute_rms_level(pcm_data: bytes) -> float:
    """Compute RMS audio level from 16-bit PCM data, return 0.0-1.0."""
    n_samples = len(pcm_data) // 2
    if n_samples == 0:
        return 0.0
    samples = struct.unpack(f"<{n_samples}h", pcm_data)
    sum_sq = sum(s * s for s in samples)
    rms = math.sqrt(sum_sq / n_samples)
    return min(rms / 32767.0, 1.0)


def stereo_to_mono(pcm_data: bytes) -> bytes:
    """Downmix stereo 16-bit PCM to mono by averaging channels."""
    n_samples = len(pcm_data) // 2
    if n_samples < 2:
        return pcm_data
    samples = struct.unpack(f"<{n_samples}h", pcm_data)
    mono = []
    for i in range(0, n_samples, 2):
        mono.append((samples[i] + samples[i + 1]) // 2)
    return struct.pack(f"<{len(mono)}h", *mono)


def resample_linear(pcm_data: bytes, from_rate: int, to_rate: int) -> bytes:
    """Resample 16-bit mono PCM using linear interpolation."""
    if from_rate == to_rate:
        return pcm_data
    n_samples = len(pcm_data) // 2
    if n_samples == 0:
        return pcm_data
    samples = struct.unpack(f"<{n_samples}h", pcm_data)
    ratio = from_rate / to_rate
    out_len = int(n_samples / ratio)
    out = []
    for i in range(out_len):
        src_pos = i * ratio
        idx = int(src_pos)
        frac = src_pos - idx
        if idx + 1 < n_samples:
            val = samples[idx] * (1.0 - frac) + samples[idx + 1] * frac
        else:
            val = samples[idx]
        out.append(max(-32768, min(32767, int(val))))
    return struct.pack(f"<{len(out)}h", *out)


class SpeechRecognizer(QThread):
    """Continuously listens to the microphone and emits recognized text."""

    command_recognized = pyqtSignal(str)
    partial_result = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    audio_level = pyqtSignal(float)

    def __init__(self, model_path: str, sample_rate: int = 16000,
                 device_index: int | None = None, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.device_index = device_index
        self._running = False
        self._paused = False
        self._model = None
        self._recognizer = None

    def _init_model(self):
        """Initialize Vosk model and recognizer (caches model across restarts)."""
        import vosk

        vosk.SetLogLevel(-1)
        if self._model is None:
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

            # Determine device capabilities
            if self.device_index is not None:
                dev_info = audio.get_device_info_by_index(self.device_index)
            else:
                dev_info = audio.get_default_input_device_info()

            dev_channels = max(1, int(dev_info.get("maxInputChannels", 1)))
            dev_rate = int(dev_info.get("defaultSampleRate", self.sample_rate))

            # Try stereo at native rate first, fall back to mono at target rate
            stream = None
            capture_channels = dev_channels
            capture_rate = dev_rate

            for channels, rate in [
                (dev_channels, dev_rate),
                (1, dev_rate),
                (1, self.sample_rate),
            ]:
                try:
                    open_kwargs = dict(
                        format=pyaudio.paInt16,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=4096,
                    )
                    if self.device_index is not None:
                        open_kwargs["input_device_index"] = self.device_index
                    stream = audio.open(**open_kwargs)
                    capture_channels = channels
                    capture_rate = rate
                    dev_name = dev_info.get("name", "Unknown")
                    api_info = audio.get_host_api_info_by_index(
                        dev_info.get("hostApi", 0)
                    )
                    api_name = api_info.get("name", "Unknown")
                    logger.info(
                        f"Opened mic: [{self.device_index}] {dev_name} "
                        f"[{api_name}] channels={channels}, rate={rate}"
                    )
                    break
                except Exception:
                    continue

            if stream is None:
                self.error_occurred.emit("Failed to open microphone with any settings")
                return

            needs_downmix = capture_channels > 1
            needs_resample = capture_rate != self.sample_rate
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

                # Convert to mono 16kHz for Vosk
                if needs_downmix:
                    data = stereo_to_mono(data)
                if needs_resample:
                    data = resample_linear(data, capture_rate, self.sample_rate)

                self.audio_level.emit(compute_rms_level(data))

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
