"""
Main floating companion window for JD.
Provides a sleek, frameless desktop presence with the JD robot helmet avatar,
action approval system, persistent action log, voice interaction, and global hotkeys.
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
    QStackedWidget,
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
from ui.approval_widget import ApprovalWidget
from ui.plan_widget import PlanWidget
from ui.log_widget import ActionLogWidget
from core.voice import TTSWorker, VoiceListener
from core.companion import CompanionBrain
from core.hotkey import GlobalHotkeyManager
from core.approval import ApprovalGate
from core.planner import TaskPlanner, TaskPlan
from core.demo_tools import DEMO_TOOL_REGISTRY, DEMO_SINGLE_TASK, DEMO_MULTI_STEP_TASK


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
    Floating desktop companion window with Approval System and Action Log.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # Frameless, stays on top, tool window
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
        self.planner = TaskPlanner(self)
        self.approval_gate = ApprovalGate(self)
        for tool_name, handler in DEMO_TOOL_REGISTRY.items():
            self.approval_gate.register_tool_handler(tool_name, handler)

        self.tts = TTSWorker(self)
        self.listener = VoiceListener(self)
        self.hotkey_mgr = GlobalHotkeyManager(parent=self)

        self._init_ui()
        self._setup_connections()
        self._setup_tray()

        # Start subsystems
        self.tts.start()
        self.hotkey_mgr.start()

        # Position on bottom-right of screen
        self._position_on_screen()

        # Initial spoken & written greeting
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
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)

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

        # View Switcher Tabs: Chat & Log
        self.btn_tab_chat = QPushButton("💬 Chat", self.header)
        self.btn_tab_chat.setProperty("class", "ViewTabBtn")
        self.btn_tab_chat.setProperty("active", "true")
        self.btn_tab_chat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_chat.clicked.connect(lambda: self._switch_view("chat"))
        header_layout.addWidget(self.btn_tab_chat)

        self.btn_tab_log = QPushButton("📋 Log", self.header)
        self.btn_tab_log.setProperty("class", "ViewTabBtn")
        self.btn_tab_log.setProperty("active", "false")
        self.btn_tab_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tab_log.clicked.connect(lambda: self._switch_view("log"))
        header_layout.addWidget(self.btn_tab_log)

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

        # Stacked Widget to switch between Chat View and Action Log View
        self.stack = QStackedWidget(self.card)

        # ---------------- Page 0: Chat & Approval View ----------------
        self.page_chat = QWidget()
        page_chat_layout = QVBoxLayout(self.page_chat)
        page_chat_layout.setContentsMargins(10, 8, 10, 8)
        page_chat_layout.setSpacing(6)

        # Plan HUD (Visual step-by-step progress & statuses)
        self.plan_widget = PlanWidget(self.page_chat)
        page_chat_layout.addWidget(self.plan_widget)

        # Approval Card (Prominently at the top of the companion workspace)
        self.approval_widget = ApprovalWidget(self.page_chat)
        page_chat_layout.addWidget(self.approval_widget)

        # Chat conversation area
        self.chat_widget = ChatWidget(self.page_chat)
        page_chat_layout.addWidget(self.chat_widget, 1)

        # Microphone indicator (reacts live to audio level)
        self.mic_indicator = MicrophoneIndicator(self.page_chat)
        self.chat_widget.layout().insertWidget(1, self.mic_indicator)

        self.stack.addWidget(self.page_chat)

        # ---------------- Page 1: Persistent Action Log View ----------------
        self.log_widget = ActionLogWidget(self.approval_gate.log, self.stack)
        self.stack.addWidget(self.log_widget)

        card_layout.addWidget(self.stack, 1)
        root_layout.addWidget(self.card)

        self._update_log_tab_badge()

    def _setup_connections(self):
        # View Switching
        self.log_widget.backToChatRequested.connect(lambda: self._switch_view("chat"))
        self.brain.requestSwitchView.connect(self._switch_view)

        # Chat inputs -> Companion Brain
        self.chat_widget.messageSubmitted.connect(self._handle_user_message)
        self.chat_widget.voiceToggleRequested.connect(self._toggle_voice_input)
        self.mic_indicator.stopRequested.connect(self._stop_voice_input)

        # Brain -> Chat UI & TTS
        self.brain.responseReady.connect(self._handle_jd_response)
        self.brain.requestTaskEnqueue.connect(self._enqueue_task_from_brain)
        self.brain.requestPlanSynthesis.connect(self._handle_plan_request)
        self.brain.requestPauseQueue.connect(self.approval_gate.pause_queue)
        self.brain.requestResumeQueue.connect(self.approval_gate.resume_queue)
        self.brain.requestCancelTask.connect(self.approval_gate.cancel_current_task)

        # Plan HUD controls -> Planner & ApprovalGate
        self.plan_widget.planPresetRequested.connect(self._handle_plan_preset)
        self.approval_gate.planUpdated.connect(self.plan_widget.update_plan)

        # Approval Card controls -> ApprovalGate
        self.approval_widget.approveClicked.connect(self.approval_gate.approve_action)
        self.approval_widget.rejectClicked.connect(self.approval_gate.reject_action)
        self.approval_widget.pauseClicked.connect(self.approval_gate.pause_queue)
        self.approval_widget.resumeClicked.connect(self.approval_gate.resume_queue)
        self.approval_widget.cancelClicked.connect(self.approval_gate.cancel_current_task)
        self.approval_widget.quickDemoRequested.connect(self._trigger_demo_by_type)

        # ApprovalGate -> UI & TTS
        self.approval_gate.actionProposed.connect(self._on_action_proposed)
        self.approval_gate.actionResolved.connect(self._on_action_resolved)
        self.approval_gate.queueStatusChanged.connect(self._on_queue_status_changed)
        self.approval_gate.taskExplanation.connect(self._on_task_explanation)
        self.approval_gate.logUpdated.connect(self._on_log_updated)

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

        log_action = tray_menu.addAction("View Action Log")
        log_action.triggered.connect(lambda: (self._switch_view("log"), self.show()))

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

    def _switch_view(self, view_name: str):
        if view_name == "log":
            self.stack.setCurrentIndex(1)
            self.log_widget.refresh_log()
            self.btn_tab_chat.setProperty("active", "false")
            self.btn_tab_log.setProperty("active", "true")
        else:
            self.stack.setCurrentIndex(0)
            self.btn_tab_chat.setProperty("active", "true")
            self.btn_tab_log.setProperty("active", "false")

        # Repolish tab buttons
        self.btn_tab_chat.style().unpolish(self.btn_tab_chat)
        self.btn_tab_chat.style().polish(self.btn_tab_chat)
        self.btn_tab_log.style().unpolish(self.btn_tab_log)
        self.btn_tab_log.style().polish(self.btn_tab_log)

    def _update_log_tab_badge(self):
        count = len(self.approval_gate.log.load_all())
        self.btn_tab_log.setText(f"📋 Log ({count})" if count > 0 else "📋 Log")

    # ---------------- Approval & Task Handlers ----------------
    def _handle_plan_request(self, prompt: str):
        self._switch_view("chat")
        plan = self.planner.plan_from_text(prompt)
        self.chat_widget.add_message("system", f"📋 Plan Formulated: '{plan.title}' with {len(plan.steps)} steps.")
        self.approval_gate.enqueue_plan(plan)
        spoken_text = f"I have formulated a plan for {plan.title}. Step 1 is awaiting your explicit approval."
        self.tts.speak(spoken_text)

    def _handle_plan_preset(self, preset_type: str):
        self._switch_view("chat")
        plan = self.planner.create_preset_plan(preset_type)
        self.chat_widget.add_message("system", f"📋 Plan Formulated: '{plan.title}' with {len(plan.steps)} steps.")
        self.approval_gate.enqueue_plan(plan)
        spoken_text = f"I have formulated a plan for {plan.title}. Step 1 is awaiting your explicit approval."
        self.tts.speak(spoken_text)

    def _enqueue_task_from_brain(self, task_spec: dict):
        self._switch_view("chat")
        self.approval_gate.enqueue_task(task_spec["task_name"], task_spec["actions"])

    def _trigger_demo_by_type(self, demo_type: str):
        self._switch_view("chat")
        if demo_type == "multi":
            self._handle_plan_preset("audit")
        else:
            self.chat_widget.add_message("system", "Proposing single demonstration action...")
            self.approval_gate.enqueue_task(DEMO_SINGLE_TASK["task_name"], DEMO_SINGLE_TASK["actions"])

    def _on_action_proposed(self, action_dict: dict):
        # Switch to chat page so approval card is in front
        self._switch_view("chat")
        queue_size = self.approval_gate.get_queue_size()
        self.approval_widget.present_action(action_dict, queue_size)

        intent = action_dict.get("intent", "Action")
        target = action_dict.get("target", "System")
        active_plan = self.approval_gate.get_active_plan()
        if active_plan:
            curr_step = active_plan.current_step()
            step_num = curr_step.step_number if curr_step else 1
            spoken_prompt = f"Step {step_num} of {len(active_plan.steps)} proposed: {intent}. Affecting: {target}. Please approve or reject."
            self.chat_widget.add_message("system", f"⚠️ Step #{step_num} Proposed: {intent} (Target: {target})")
        else:
            spoken_prompt = f"Action proposed: {intent}. Affecting: {target}. Please approve or reject."
            self.chat_widget.add_message("system", f"⚠️ Action Proposed: {intent} (Target: {target})")
        self.tts.speak(spoken_prompt)

    def _on_action_resolved(self, action_dict: dict):
        if not self.approval_gate.get_current_action():
            self.approval_widget.clear_action()

    def _on_queue_status_changed(self, status: dict):
        self.approval_widget.set_paused(status.get("is_paused", False))
        if not status.get("has_current") and status.get("queue_size", 0) == 0:
            self.approval_widget.clear_action()

    def _on_task_explanation(self, explanation: str):
        self.chat_widget.add_message("jd", explanation)
        self.tts.speak(explanation)

    def _on_log_updated(self):
        self._update_log_tab_badge()
        self.log_widget.refresh_log()

    # ---------------- Speech & UI Handlers ----------------
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
