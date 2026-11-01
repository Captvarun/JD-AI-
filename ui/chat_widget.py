"""
Conversation area and text input widgets for JD.
"""

from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
)

from core.config import (
    COLOR_BUBBLE_USER,
    COLOR_BUBBLE_USER_TEXT,
    COLOR_BUBBLE_JD,
    COLOR_BUBBLE_JD_BORDER,
    COLOR_BUBBLE_JD_TEXT,
    COLOR_MINT,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
)


class MessageBubble(QFrame):
    """
    Styled message bubble representing a chat turn.
    """
    def __init__(self, sender: str, text: str, time_str: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        if not time_str:
            time_str = datetime.now().strftime("%I:%M %p")

        # Header with sender name and time
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        sender_label = QLabel("You" if sender == "user" else "JD", self)
        sender_label.setStyleSheet(
            f"font-size: 10px; font-weight: bold; color: {COLOR_TEXT_SECONDARY if sender == 'user' else COLOR_MINT};"
        )
        time_label = QLabel(time_str, self)
        time_label.setStyleSheet(f"font-size: 9px; color: {COLOR_TEXT_MUTED};")

        header_layout.addWidget(sender_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        layout.addLayout(header_layout)

        # Message text
        msg_label = QLabel(text, self)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        if sender == "user":
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {COLOR_BUBBLE_USER};
                    border: 1px solid #2B3346;
                    border-radius: 12px;
                }}
            """)
            msg_label.setStyleSheet(f"color: {COLOR_BUBBLE_USER_TEXT}; font-size: 12px; line-height: 1.4;")
        elif sender == "system":
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #171E28;
                    border: 1px dashed #3A455A;
                    border-radius: 10px;
                }
            """)
            msg_label.setStyleSheet("color: #A0ABC0; font-size: 11px; font-style: italic;")
        else:
            # JD message
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {COLOR_BUBBLE_JD};
                    border: 1px solid {COLOR_BUBBLE_JD_BORDER};
                    border-radius: 12px;
                }}
            """)
            msg_label.setStyleSheet(f"color: {COLOR_BUBBLE_JD_TEXT}; font-size: 12px; line-height: 1.4;")

        layout.addWidget(msg_label)


class ChatWidget(QWidget):
    """
    Main chat panel containing message history, text input, send button, and mic toggle.
    """
    messageSubmitted = pyqtSignal(str)
    voiceToggleRequested = pyqtSignal()
    ttsToggleRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Scroll area for chat messages
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("ChatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_container.setObjectName("ChatContentWidget")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 10, 12, 10)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()  # Keeps bubbles pushed to the bottom

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, 1)

        # Input Area Bar
        input_container = QWidget(self)
        input_container.setObjectName("InputAreaContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(6)

        # Microphone toggle button
        self.btn_mic = QPushButton("🎤", input_container)
        self.btn_mic.setObjectName("BtnMic")
        self.btn_mic.setToolTip("Click to speak with voice")
        self.btn_mic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mic.setFixedSize(36, 36)
        self.btn_mic.clicked.connect(self.voiceToggleRequested.emit)
        input_layout.addWidget(self.btn_mic)

        # Text input field
        self.input_field = QLineEdit(input_container)
        self.input_field.setObjectName("MessageInput")
        self.input_field.setPlaceholderText("Message JD... (Press Enter to send)")
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field, 1)

        # Send button
        self.btn_send = QPushButton("Send", input_container)
        self.btn_send.setObjectName("BtnSend")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setFixedHeight(36)
        self.btn_send.clicked.connect(self._on_send)
        input_layout.addWidget(self.btn_send)

        main_layout.addWidget(input_container)

    def add_message(self, sender: str, text: str):
        bubble = MessageBubble(sender, text, parent=self.chat_container)
        # Insert before the stretch
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, bubble)

        # Scroll to bottom smoothly
        QTimer.singleShot(50, self._scroll_to_bottom)

    def set_mic_active(self, active: bool):
        self.btn_mic.setProperty("active", "true" if active else "false")
        self.btn_mic.style().unpolish(self.btn_mic)
        self.btn_mic.style().polish(self.btn_mic)
        if active:
            self.btn_mic.setText("⏹")
            self.btn_mic.setToolTip("Listening... Click to stop")
        else:
            self.btn_mic.setText("🎤")
            self.btn_mic.setToolTip("Click to speak with voice")

    def _on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.add_message("user", text)
            self.messageSubmitted.emit(text)

    def _scroll_to_bottom(self):
        vsb = self.scroll_area.verticalScrollBar()
        vsb.setValue(vsb.maximum())
