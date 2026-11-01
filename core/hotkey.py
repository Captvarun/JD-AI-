"""
Global keyboard shortcut listener for JD.
Allows summoning and hiding JD from any active application on Windows.
"""

from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

from core.config import GLOBAL_HOTKEY


class GlobalHotkeyManager(QObject):
    """
    Manages system-wide keyboard shortcuts using pynput.
    Emits hotkeyTriggered on the Qt event loop.
    """
    hotkeyTriggered = pyqtSignal()

    def __init__(self, hotkey_str: str = GLOBAL_HOTKEY, parent=None):
        super().__init__(parent)
        self._hotkey_str = hotkey_str
        self._listener = None

    def start(self):
        """Start listening for the global hotkey."""
        try:
            self._listener = keyboard.GlobalHotKeys({
                self._hotkey_str: self._on_hotkey
            })
            self._listener.daemon = True
            self._listener.start()
        except Exception as e:
            print(f"Warning: Failed to register global hotkey {self._hotkey_str}: {e}")

    def stop(self):
        """Stop listening."""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _on_hotkey(self):
        self.hotkeyTriggered.emit()
