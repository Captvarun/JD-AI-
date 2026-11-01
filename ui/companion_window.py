"""
Main floating companion window for JD.
Provides a sleek, frameless desktop presence with the JD robot helmet avatar.
"""

from PyQt6.QtCore import Qt, QPoint, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QApplication,
)

from core.config import (
    APP_NAME,
    APP_SUBTITLE,
    GLOBAL_HOTKEY_DISPLAY,
    ICON_PATH,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_MINT,
    COLOR_CARD_DARK,
)
from ui.styles import MAIN_STYLESHEET
from ui.mic_indicator import MicrophoneIndicator
from ui.chat_widget import ChatWidget
from core.voice import TTSWorker, VoiceListener
from core.companion import CompanionBrain
from core.hotkey import GlobalHotkeyManager


def get_rounded_pixmap(pixmap: QPixmap, radius: int = 10) -> QPixmap:
    """Returns a smoothly rounded version of the pixmap."""
    if pixmap.isNull():
        return pixmap
    target = QPixmap(pixmap.size())
    target.fill(Qt.GlobalColor.transparent)

    painter = QPainter(target)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return target


class JDCompanionWindow(QWidget):
    """
    Floating desktop companion window.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Window flags: Frameless, stays on top, tool window to stay nimble
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # Window dragging state
        self._is_dragging = False
        self._drag_start_position = QPoint()

        # Core subsystems
        self.brain = CompanionBrain(self)
        self.tts = TTSWorker(self)
        self.listener = VoiceListener(self)
        self.hotkey_mgr = GlobalHotkeyManager(parent=self)

        self._init_ui()
        self._setup_connections()
        self._setup_tray()

        # Start subsystems
        self.tts.start()
        self.hotkey_mgr.start()

        # Position on bottom-right of the primary screen
        self._position_on_screen()

        # Trigger initial spoken and written greeting
        QTimer.singleShot(600, self._initial_greeting)

    def _init_ui(self):
        self.setStyleSheet(MAIN_STYLESHEET)

        # Outer root layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)

        # Main Card container with rounded borders
        self.card = QWidget(self)
        self.card.setObjectName("MainCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 1. Header Bar
        self.header = QWidget(self.card)
        self.header.setObjectName("HeaderWidget")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(10)

        # Avatar Icon (Using the exact uploaded JD helmet image)
        self.avatar_label = QLabel(self.header)
        self.avatar_label.setFixedSize(38, 38)
        if ICON_PATH.exists():
            orig_pixmap = QPixmap(str(ICON_PATH)).scaled(
                38, 38,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.avatar_label.setPixmap(get_rounded_pixmap(orig_pixmap, 10))
        header_layout.addWidget(self.avatar_label)

        # Title & Subtitle
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_row = QHBoxLayout()
        title_row.setSpacing(6)

        title_lbl = QLabel(APP_NAME, self.header)
        title_lbl.setObjectName("TitleLabel")
        title_row.addWidget(title_lbl)

        status_badge = QLabel("ONLINE", self.header)
        status_badge.setObjectName("BadgeOnline")
        title_row.addWidget(status_badge)
        title_row.addStretch()
        title_box.addLayout(title_row)

        subtitle_lbl = QLabel(APP_SUBTITLE, self.header)
        subtitle_lbl.setObjectName("SubtitleLabel")
        title_box.addWidget(subtitle_lbl)

        header_layout.addLayout(title_box, 1)

        # Shortcut pill hint
        shortcut_lbl = QLabel(GLOBAL_HOTKEY_DISPLAY, self.header)
        shortcut_lbl.setObjectName("ShortcutBadge")
        shortcut_lbl.setToolTip(f"Global hotkey to summon or hide {APP_NAME}")
        header_layout.addWidget(shortcut_lbl)

        # TTS Mute Toggle button
        self.btn_tts = QPushButton("🔊", self.header)
        self.btn_tts.setObjectName("BtnTTS")
        self.btn_tts.setToolTip("Toggle Speech Voice (Mute/Unmute)")
        self.btn_tts.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tts.setFixedSize(26, 26)
        self.btn_tts.clicked.connect(self._toggle_tts_mute)
        header_layout.addWidget(self.btn_tts)

        # Minimize / Hide button
        self.btn_hide = QPushButton("—", self.header)
        self.btn_hide.setObjectName("BtnHide")
        self.btn_hide.setProperty("class", "WindowCtrlBtn")
        self.btn_hide.setToolTip(f"Hide {APP_NAME} to background (Summon with {GLOBAL_HOTKEY_DISPLAY})")
        self.btn_hide.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hide.clicked.connect(self.hide)
        header_layout.addWidget(self.btn_hide)

        # Quit button
        self.btn_close = QPushButton("✕", self.header)
        self.btn_close.setObjectName("BtnClose")
        self.btn_close.setProperty("class", "WindowCtrlBtn")
        self.btn_close.setToolTip(f"Quit {APP_NAME} completely")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_application)
        header_layout.addWidget(self.btn_close)

        card_layout.addWidget(self.header)

        # 2. Chat Widget (Messages area + Text input + Mic button)
        self.chat_widget = ChatWidget(self.card)
        card_layout.addWidget(self.chat_widget, 1)

        # 3. Microphone Indicator Widget (Visible when listening)
        self.mic_indicator = MicrophoneIndicator(self.card)
        # Position mic indicator inside the card right above the input bar
        # We can add it directly to card_layout before input or inside chat widget
        self.chat_widget.layout().insertWidget(1, self.mic_indicator)

        root_layout.addWidget(self.card)

    def _setup_connections(self):
        # Chat inputs -> Companion Brain
        self.chat_widget.messageSubmitted.connect(self._handle_user_message)
        self.chat_widget.voiceToggleRequested.connect(self._toggle_voice_input)
        self.mic_indicator.stopRequested.connect(self._stop_voice_input)

        # Brain -> Chat UI & TTS
        self.brain.responseReady.connect(self._handle_jd_response)

        # Voice listener signals
        self.listener.listeningStarted.connect(self._on_listening_started)
        self.listener.listeningStopped.connect(self._on_listening_stopped)
        self.listener.audioLevel.connect(self.mic_indicator.set_audio_level)
        self.listener.speechRecognized.connect(self._handle_speech_recognized)
        self.listener.speechError.connect(self._handle_speech_error)

        # Global Hotkey -> Toggle visibility
        self.hotkey_mgr.hotkeyTriggered.connect(self.toggle_visibility)

    def _setup_tray(self):
        """Sets up a system tray icon for JD."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        if ICON_PATH.exists():
            self.tray_icon.setIcon(QIcon(str(ICON_PATH)))

        tray_menu = QMenu()
        show_action = tray_menu.addAction(f"Show / Hide JD ({GLOBAL_HOTKEY_DISPLAY})")
        show_action.triggered.connect(self.toggle_visibility)

        mute_action = tray_menu.addAction("Toggle Voice Mute")
        mute_action.triggered.connect(self._toggle_tts_mute)

        clear_action = tray_menu.addAction("Clear Conversation")
        clear_action.triggered.connect(self._clear_conversation)

        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit JD")
        quit_action.triggered.connect(self.close_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip(f"{APP_NAME} - {APP_SUBTITLE} ({GLOBAL_HOTKEY_DISPLAY})")
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()

    def _position_on_screen(self):
        """Positions JD smoothly at bottom-right corner of screen."""
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - WINDOW_WIDTH - 24
            y = geom.bottom() - WINDOW_HEIGHT - 32
            self.move(x, y)

    def _initial_greeting(self):
        greeting = self.brain.get_greeting()
        self.chat_widget.add_message("jd", greeting)
        self.tts.speak(greeting)

    @pyqtSlot()
    def toggle_visibility(self):
        """Summons or hides JD smoothly from any application."""
        if self.isVisible() and self.isActiveWindow():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self.chat_widget.input_field.setFocus()

    def _handle_user_message(self, text: str):
        # Stop speech playback if user interjects
        self.tts.stop_speaking()
        self.brain.process_user_input(text)

    def _handle_jd_response(self, text: str):
        self.chat_widget.add_message("jd", text)
        self.tts.speak(text)

    def _toggle_voice_input(self):
        if self.listener.is_listening():
            self._stop_voice_input()
        else:
            self.tts.stop_speaking()
            self.listener.start_listening()

    def _stop_voice_input(self):
        self.listener.stop_listening()

    def _on_listening_started(self):
        self.chat_widget.set_mic_active(True)
        self.mic_indicator.set_listening(True)

    def _on_listening_stopped(self):
        self.chat_widget.set_mic_active(False)
        self.mic_indicator.set_listening(False)

    def _handle_speech_recognized(self, text: str):
        self.chat_widget.add_message("user", text)
        self.brain.process_user_input(text)

    def _handle_speech_error(self, err_text: str):
        self.chat_widget.add_message("system", err_text)

    def _toggle_tts_mute(self):
        new_muted = not self.tts.is_muted()
        self.tts.set_muted(new_muted)
        if new_muted:
            self.btn_tts.setText("🔇")
            self.btn_tts.setToolTip("Voice speech muted (Click to unmute)")
        else:
            self.btn_tts.setText("🔊")
            self.btn_tts.setToolTip("Voice speech active (Click to mute)")

    def _clear_conversation(self):
        # Re-add greeting only
        pass

    def close_application(self):
        """Full clean application shutdown."""
        self.listener.stop_listening()
        self.tts.shutdown()
        self.hotkey_mgr.stop()
        QApplication.quit()

    # Window Dragging implementation
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        event.accept()
