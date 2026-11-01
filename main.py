"""
JD - Personal AI Desktop Assistant for Windows
Main application entry point.
"""

import sys
import signal
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import APP_NAME, APP_SUBTITLE, ICON_PATH
from ui.companion_window import JDCompanionWindow


def main():
    # Enable high DPI scaling
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(f"{APP_NAME} - {APP_SUBTITLE}")
    app.setQuitOnLastWindowClosed(False)  # Allows running in tray/background

    # Set application icon
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    # Handle Ctrl+C gracefully from terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    # Create and show the companion window
    window = JDCompanionWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
