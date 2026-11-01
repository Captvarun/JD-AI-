"""
Microphone visual indicator widget.
Renders an animated glowing mint-green pulse indicator whenever voice input is active.
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from core.config import COLOR_MINT, COLOR_TEXT_SECONDARY, COLOR_CARD_DARK


class MicWaveWidget(QWidget):
    """
    Animated circular pulse widget rendered via QPainter.
    Pulses smoothly and expands dynamically when the user speaks.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self._is_active = False
        self._audio_level = 0.0  # 0.0 to 1.0
        self._pulse_phase = 0.0  # 0.0 to 1.0

        # Animation timer for smooth pulsing
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def set_active(self, active: bool):
        self._is_active = active
        if active:
            if not self._timer.isActive():
                self._timer.start(30)  # ~33 fps
        else:
            self._timer.stop()
            self._audio_level = 0.0
            self._pulse_phase = 0.0
        self.update()

    def set_audio_level(self, level: float):
        # Smooth the audio level transition
        self._audio_level = self._audio_level * 0.4 + level * 0.6
        self.update()

    def _on_tick(self):
        self._pulse_phase = (self._pulse_phase + 0.05) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() / 2.0
        center_y = self.height() / 2.0

        if self._is_active:
            # Draw outer expanding glow ring
            glow_radius = 8.0 + 7.0 * self._pulse_phase + (self._audio_level * 5.0)
            glow_alpha = int(180 * (1.0 - self._pulse_phase))
            glow_color = QColor(COLOR_MINT)
            glow_color.setAlpha(glow_alpha)

            painter.setPen(QPen(glow_color, 2.0))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(center_x - glow_radius, center_y - glow_radius, glow_radius * 2, glow_radius * 2))

            # Draw middle audio reactivity ring
            mid_radius = 6.0 + (self._audio_level * 6.0)
            mid_color = QColor(COLOR_MINT)
            mid_color.setAlpha(120)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(mid_color))
            painter.drawEllipse(QRectF(center_x - mid_radius, center_y - mid_radius, mid_radius * 2, mid_radius * 2))

            # Draw solid core center
            core_color = QColor(COLOR_MINT)
            painter.setBrush(QBrush(core_color))
            painter.drawEllipse(QRectF(center_x - 4.5, center_y - 4.5, 9, 9))
        else:
            # Subtle idle state
            idle_color = QColor(COLOR_TEXT_SECONDARY)
            idle_color.setAlpha(90)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(idle_color))
            painter.drawEllipse(QRectF(center_x - 4, center_y - 4, 8, 8))


class MicrophoneIndicator(QWidget):
    """
    Visible microphone status bar that appears during speech capture.
    Shows the pulsing wave, a status label, and a 'Done Speaking' button.
    """
    stopRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MicrophoneIndicator")
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(8)

        self.wave = MicWaveWidget(self)
        layout.addWidget(self.wave)

        self.status_label = QLabel("Microphone Standby", self)
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.status_label, 1)

        self.btn_done = QPushButton("Done Speaking", self)
        self.btn_done.setStyleSheet(f"""
            QPushButton {{
                background-color: #25332E;
                color: {COLOR_MINT};
                border: 1px solid {COLOR_MINT};
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_MINT};
                color: #000000;
            }}
        """)
        self.btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_done.clicked.connect(self.stopRequested.emit)
        self.btn_done.hide()
        layout.addWidget(self.btn_done)

        self.setStyleSheet(f"""
            #MicrophoneIndicator {{
                background-color: #121820;
                border: 1px solid #232D3F;
                border-radius: 8px;
            }}
        """)

    def set_listening(self, active: bool):
        self.wave.set_active(active)
        if active:
            self.status_label.setText("Listening... Speak into microphone")
            self.status_label.setStyleSheet(f"color: {COLOR_MINT}; font-size: 11px; font-weight: bold;")
            self.btn_done.show()
            self.setStyleSheet(f"""
                #MicrophoneIndicator {{
                    background-color: #11231E;
                    border: 1px solid {COLOR_MINT};
                    border-radius: 8px;
                }}
            """)
        else:
            self.status_label.setText("Microphone standby (Click 🎤 to speak)")
            self.status_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
            self.btn_done.hide()
            self.setStyleSheet(f"""
                #MicrophoneIndicator {{
                    background-color: #121820;
                    border: 1px solid #232D3F;
                    border-radius: 8px;
                }}
            """)

    def set_audio_level(self, level: float):
        self.wave.set_audio_level(level)
