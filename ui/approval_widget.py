"""
Approval Card Widget for JD.
Presents one proposed action at a time with intent, target, parameters,
Approve, Reject, Pause, and Cancel controls with both mouse and keyboard support.
"""

import json
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
)

from core.config import (
    COLOR_MINT,
    COLOR_MINT_HOVER,
    COLOR_REJECTED,
    COLOR_PAUSED,
    COLOR_CANCELED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_CARD_DARK,
    COLOR_BORDER,
)


class ApprovalWidget(QFrame):
    """
    Prominent approval card for reviewing and controlling proposed actions.
    Supports mouse clicks and keyboard shortcuts (Enter=Approve, Esc=Reject, P=Pause).
    """
    approveClicked = pyqtSignal(str)   # action_id
    rejectClicked = pyqtSignal(str)    # action_id
    pauseClicked = pyqtSignal()
    resumeClicked = pyqtSignal()
    cancelClicked = pyqtSignal()
    quickDemoRequested = pyqtSignal(str) # 'single' or 'multi'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ApprovalCard")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._current_action = None
        self._is_paused = False
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            #ApprovalCard {{
                background-color: #151A24;
                border: 1px solid #313D53;
                border-radius: 12px;
                padding: 10px;
            }}
            .SectionHeader {{
                color: {COLOR_MINT};
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.8px;
            }}
            .DetailLabel {{
                color: {COLOR_TEXT_PRIMARY};
                font-size: 12px;
            }}
            .TargetBox {{
                background-color: #0E121A;
                border: 1px solid #232B3B;
                border-radius: 6px;
                padding: 4px 8px;
                color: #FFB84D;
                font-size: 11px;
                font-family: Consolas, monospace;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # 1. Top Status Banner
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.lbl_badge = QLabel("⚠️ APPROVAL REQUIRED", self)
        self.lbl_badge.setStyleSheet(f"""
            background-color: rgba(255, 184, 77, 0.15);
            color: #FFB84D;
            border: 1px solid #FFB84D;
            border-radius: 6px;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 0.8px;
        """)
        top_row.addWidget(self.lbl_badge)

        self.lbl_task_name = QLabel("", self)
        self.lbl_task_name.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 10px; font-weight: bold;")
        top_row.addWidget(self.lbl_task_name, 1)

        self.lbl_queue_count = QLabel("", self)
        self.lbl_queue_count.setStyleSheet("color: #7A8499; font-size: 10px; font-family: Consolas, monospace;")
        top_row.addWidget(self.lbl_queue_count)

        layout.addLayout(top_row)

        # 2. What JD Wants to Do (Intent)
        intent_title = QLabel("WHAT JD WANTS TO DO:", self)
        intent_title.setProperty("class", "SectionHeader")
        layout.addWidget(intent_title)

        self.lbl_intent = QLabel("", self)
        self.lbl_intent.setWordWrap(True)
        self.lbl_intent.setProperty("class", "DetailLabel")
        self.lbl_intent.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.lbl_intent)

        # 3. What it will affect (Target)
        target_title = QLabel("WHAT IT WILL AFFECT:", self)
        target_title.setProperty("class", "SectionHeader")
        layout.addWidget(target_title)

        self.lbl_target = QLabel("", self)
        self.lbl_target.setProperty("class", "TargetBox")
        self.lbl_target.setWordWrap(True)
        layout.addWidget(self.lbl_target)

        # 4. Parameters details (collapsible/scrollable if long)
        self.lbl_params = QLabel("", self)
        self.lbl_params.setStyleSheet("color: #8C96AB; font-size: 10px; font-family: Consolas, monospace;")
        self.lbl_params.setWordWrap(True)
        layout.addWidget(self.lbl_params)

        # 5. Action Buttons (Approve, Reject, Pause, Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(6)

        # Approve Button (Enter)
        self.btn_approve = QPushButton("✓ Approve (Enter)", self)
        self.btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_approve.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_MINT};
                color: #0B130E;
                font-weight: bold;
                font-size: 11px;
                border: none;
                border-radius: 7px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_MINT_HOVER};
            }}
        """)
        self.btn_approve.clicked.connect(self._on_approve)
        btn_layout.addWidget(self.btn_approve, 1)

        # Reject Button (Esc)
        self.btn_reject = QPushButton("✕ Reject (Esc)", self)
        self.btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reject.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D1A1E;
                color: {COLOR_REJECTED};
                border: 1px solid {COLOR_REJECTED};
                font-weight: bold;
                font-size: 11px;
                border-radius: 7px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_REJECTED};
                color: #FFFFFF;
            }}
        """)
        self.btn_reject.clicked.connect(self._on_reject)
        btn_layout.addWidget(self.btn_reject, 1)

        # Pause / Resume Button
        self.btn_pause = QPushButton("⏸ Pause", self)
        self.btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pause.setStyleSheet(f"""
            QPushButton {{
                background-color: #1F2533;
                color: {COLOR_PAUSED};
                border: 1px solid #333D52;
                font-size: 10px;
                font-weight: bold;
                border-radius: 7px;
                padding: 6px 8px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_PAUSED};
            }}
        """)
        self.btn_pause.clicked.connect(self._on_toggle_pause)
        btn_layout.addWidget(self.btn_pause)

        # Cancel Task Button
        self.btn_cancel = QPushButton("⏹ Cancel", self)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #1B1E26;
                color: {COLOR_CANCELED};
                border: 1px solid #2B313F;
                font-size: 10px;
                font-weight: bold;
                border-radius: 7px;
                padding: 6px 8px;
            }}
            QPushButton:hover {{
                border-color: #FF5E5E;
                color: #FF5E5E;
            }}
        """)
        self.btn_cancel.clicked.connect(self.cancelClicked.emit)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        # 6. Standby container (shown when no action is pending)
        self.standby_widget = QWidget(self)
        standby_layout = QVBoxLayout(self.standby_widget)
        standby_layout.setContentsMargins(0, 4, 0, 4)
        standby_layout.setSpacing(6)

        standby_title = QLabel("🛡️ Explicit Approval Checkpoint Active", self.standby_widget)
        standby_title.setStyleSheet(f"color: {COLOR_MINT}; font-size: 11px; font-weight: bold;")
        standby_layout.addWidget(standby_title)

        standby_desc = QLabel("No external action runs without your permission. Test the approval flow:", self.standby_widget)
        standby_desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        standby_layout.addWidget(standby_desc)

        quick_btns = QHBoxLayout()
        quick_btns.setSpacing(6)

        btn_demo1 = QPushButton("🧪 Propose Demo Action", self.standby_widget)
        btn_demo1.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_demo1.setStyleSheet(f"""
            QPushButton {{
                background-color: #172421;
                color: {COLOR_MINT};
                border: 1px solid {COLOR_MINT};
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
                padding: 5px 8px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_MINT};
                color: #000000;
            }}
        """)
        btn_demo1.clicked.connect(lambda: self.quickDemoRequested.emit("single"))
        quick_btns.addWidget(btn_demo1)

        btn_demo2 = QPushButton("⚡ Propose 3-Step Pipeline", self.standby_widget)
        btn_demo2.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_demo2.setStyleSheet("""
            QPushButton {
                background-color: #1B212D;
                color: #8EB7FF;
                border: 1px solid #34486E;
                border-radius: 6px;
                font-size: 10px;
                font-weight: bold;
                padding: 5px 8px;
            }
            QPushButton:hover {
                background-color: #2B3A5A;
                border-color: #8EB7FF;
            }
        """)
        btn_demo2.clicked.connect(lambda: self.quickDemoRequested.emit("multi"))
        quick_btns.addWidget(btn_demo2)

        standby_layout.addLayout(quick_btns)
        layout.addWidget(self.standby_widget)

        # By default, start in standby mode
        self._show_standby(True)

    def _show_standby(self, in_standby: bool):
        self.standby_widget.setVisible(in_standby)
        self.lbl_badge.setVisible(not in_standby)
        self.lbl_task_name.setVisible(not in_standby)
        self.lbl_queue_count.setVisible(not in_standby)
        self.lbl_intent.setVisible(not in_standby)
        self.lbl_target.setVisible(not in_standby)
        self.lbl_params.setVisible(not in_standby)
        self.btn_approve.setVisible(not in_standby)
        self.btn_reject.setVisible(not in_standby)
        self.btn_pause.setVisible(not in_standby)
        self.btn_cancel.setVisible(not in_standby)

    def present_action(self, action_data: dict, queue_size: int = 0):
        self._current_action = action_data
        self._show_standby(False)

        task_name = action_data.get("task_name", "General Task")
        self.lbl_task_name.setText(task_name)
        self.lbl_intent.setText(action_data.get("intent", "No description"))
        self.lbl_target.setText(f"🎯 {action_data.get('target', 'System')}")

        params = action_data.get("parameters", {})
        if params:
            self.lbl_params.setText(f"Params: {json.dumps(params)}")
            self.lbl_params.show()
        else:
            self.lbl_params.hide()

        count_str = f"Remaining in queue: {queue_size}" if queue_size > 0 else "Final step in task"
        self.lbl_queue_count.setText(count_str)

        # Grab focus for immediate keyboard response
        self.setFocus()

    def clear_action(self):
        self._current_action = None
        self._show_standby(True)

    def set_paused(self, paused: bool):
        self._is_paused = paused
        if paused:
            self.btn_pause.setText("▶ Resume")
            self.btn_pause.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2D2718;
                    color: {COLOR_PAUSED};
                    border: 1px solid {COLOR_PAUSED};
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 7px;
                    padding: 6px 8px;
                }}
            """)
        else:
            self.btn_pause.setText("⏸ Pause")
            self.btn_pause.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1F2533;
                    color: {COLOR_PAUSED};
                    border: 1px solid #333D52;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 7px;
                    padding: 6px 8px;
                }}
            """)

    def _on_approve(self):
        if self._current_action:
            self.approveClicked.emit(self._current_action.get("id"))

    def _on_reject(self):
        if self._current_action:
            self.rejectClicked.emit(self._current_action.get("id"))

    def _on_toggle_pause(self):
        if self._is_paused:
            self.resumeClicked.emit()
        else:
            self.pauseClicked.emit()

    def keyPressEvent(self, event: QKeyEvent):
        """Keyboard support for approval controls."""
        if not self._current_action:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self._on_approve()
            event.accept()
        elif key == Qt.Key.Key_Escape:
            self._on_reject()
            event.accept()
        elif key == Qt.Key.Key_P:
            self._on_toggle_pause()
            event.accept()
        elif key == Qt.Key.Key_C:
            self.cancelClicked.emit()
            event.accept()
        else:
            super().keyPressEvent(event)
