"""
Voice and audio subsystems for JD.
Handles offline Windows SAPI5 speech synthesis (TTS) and microphone input capture.
"""

import math
import queue
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from core.config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    TTS_SPEECH_RATE,
    TTS_SPEECH_VOLUME,
)

try:
    import pythoncom
except ImportError:
    pythoncom = None


class TTSWorker(QThread):
    """
    Background worker thread for pyttsx3 Text-To-Speech.
    Prevents UI freezing and handles Windows SAPI5 COM threading.
    """
    speakingStarted = pyqtSignal(str)
    speakingFinished = pyqtSignal()
    errorOccurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue = queue.Queue()
        self._running = True
        self._muted = False
        self._engine = None

    def set_muted(self, muted: bool):
        self._muted = muted

    def is_muted(self) -> bool:
        return self._muted

    def speak(self, text: str):
        if not text:
            return
        self._queue.put(text)

    def stop_speaking(self):
        """Clear queue and stop current speech."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass

    def shutdown(self):
        self._running = False
        self.stop_speaking()
        self._queue.put(None)
        self.wait(2000)

    def run(self):
        if pythoncom:
            pythoncom.CoInitialize()

        try:
            import pyttsx3
            self._engine = pyttsx3.init("sapi5")
            self._engine.setProperty("rate", TTS_SPEECH_RATE)
            self._engine.setProperty("volume", TTS_SPEECH_VOLUME)

            # Try to pick a crisp voice if available
            voices = self._engine.getProperty("voices")
            if voices:
                # Default to first voice (e.g. David) or Zira
                self._engine.setProperty("voice", voices[0].id)
        except Exception as e:
            self.errorOccurred.emit(f"Speech synthesis init failed: {e}")
            self._engine = None

        while self._running:
            try:
                text = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if text is None or not self._running:
                break

            if self._muted or not self._engine:
                continue

            try:
                self.speakingStarted.emit(text)
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                self.errorOccurred.emit(f"Speech playback error: {e}")
            finally:
                self.speakingFinished.emit()

        if pythoncom:
            pythoncom.CoUninitialize()


class VoiceListener(QThread):
    """
    Captures live microphone audio using sounddevice.
    Emits real-time RMS audio levels to drive the visual pulse indicator.
    Transcribes captured speech using speech_recognition.
    """
    listeningStarted = pyqtSignal()
    listeningStopped = pyqtSignal()
    audioLevel = pyqtSignal(float)          # 0.0 to 1.0 (for pulsating mic indicator)
    speechRecognized = pyqtSignal(str)       # Transcribed user text
    speechError = pyqtSignal(str)           # Informative feedback

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_listening = False
        self._should_stop = False
        self._audio_chunks = []
        self._recognizer = sr.Recognizer()

    def start_listening(self):
        if not self.isRunning():
            self._should_stop = False
            self.start()

    def stop_listening(self):
        self._should_stop = True

    def is_listening(self) -> bool:
        return self._is_listening

    def run(self):
        self._is_listening = True
        self._audio_chunks = []
        self.listeningStarted.emit()

        def audio_callback(indata, frames, time_info, status):
            if not self._is_listening:
                return
            # Save audio chunk
            self._audio_chunks.append(indata.copy())
            # Calculate RMS amplitude for real-time visual indicator
            rms = np.sqrt(np.mean(indata**2))
            # Normalize to ~0.0 - 1.0 range with logarithmic feel
            level = min(1.0, max(0.0, float(rms * 12.0)))
            self.audioLevel.emit(level)

        try:
            with sd.InputStream(
                samplerate=AUDIO_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                dtype="int16",
                callback=audio_callback,
                blocksize=1024,
            ):
                silence_start = None
                max_duration = 10.0
                start_time = time.time()

                while not self._should_stop and (time.time() - start_time < max_duration):
                    self.msleep(50)

        except Exception as e:
            self._is_listening = False
            self.listeningStopped.emit()
            self.speechError.emit(f"Microphone access error: {e}")
            return

        self._is_listening = False
        self.audioLevel.emit(0.0)
        self.listeningStopped.emit()

        # Process recorded audio
        if not self._audio_chunks:
            self.speechError.emit("No audio was recorded.")
            return

        try:
            full_audio = np.concatenate(self._audio_chunks, axis=0)
            raw_bytes = full_audio.tobytes()

            audio_data = sr.AudioData(
                raw_bytes,
                sample_rate=AUDIO_SAMPLE_RATE,
                sample_width=2,  # 16-bit PCM = 2 bytes
            )

            # Transcribe via Google Speech Recognition API
            text = self._recognizer.recognize_google(audio_data)
            if text and text.strip():
                self.speechRecognized.emit(text.strip())
            else:
                self.speechError.emit("Could not detect clear words.")
        except sr.UnknownValueError:
            self.speechError.emit("JD couldn't clearly understand that. Please try again or type.")
        except sr.RequestError as e:
            self.speechError.emit(f"Speech service unavailable ({e}). You can type your message below.")
        except Exception as e:
            self.speechError.emit(f"Audio processing error: {e}")
