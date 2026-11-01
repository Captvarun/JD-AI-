"""
Action Log Widget for JD.
Displays the persistent record of tasks, proposed actions, decisions, timestamps, and outcomes.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)

from core.config import (
    COLOR_MINT,
    COLOR_APPROVED,
    COLOR_REJECTED,
    COLOR_CANCELED,
    COLOR_PAUSED,
    COLOR_CARD_DARK,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
)
from core.approval import PersistentActionLog


class ActionLogItem(QFrame):
    """
    Renders a single persistent log record with color-coded status badges.
    """
    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionLogItem")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Top row: Decision Badge + Task Title + Timestamp
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        decision = record.get("decision", "PENDING").upper()
        badge_color = COLOR_APPROVED if decision == "APPROVED" else (
            COLOR_REJECTED if decision == "REJECTED" else COLOR_CANCELED
        )
        badge_bg = (
            "rgba(82, 255, 184, 0.15)" if decision == "APPROVED"
            else ("rgba(255, 94, 94, 0.15)" if decision == "REJECTED" else "rgba(142, 149, 165, 0.15)")
        )

        badge = QLabel(decision, self)
        badge.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_color};
            border: 1px solid {badge_color};
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 9px;
            font-weight: bold;
            font-family: Consolas, monospace;
        """)
        top_row.addWidget(badge)

        task_lbl = QLabel(record.get("task_name", "General Task"), self)
        task_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        top_row.addWidget(task_lbl, 1)

        time_str = record.get("decision_time") or record.get("created_at") or ""
        time_lbl = QLabel(time_str, self)
        time_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")
        top_row.addWidget(time_lbl)
        layout.addLayout(top_row)

        # Proposed Action Intent
        intent_lbl = QLabel(f"Action: {record.get('intent', 'Unspecified')}", self)
        intent_lbl.setWordWrap(True)
        intent_lbl.setStyleSheet("color: #E2E8F0; font-size: 11px;")
        layout.addWidget(intent_lbl)

        # Target Affected
        target_lbl = QLabel(f"Target: {record.get('target', 'None')}", self)
        target_lbl.setStyleSheet("color: #FFB84D; font-size: 10px; font-family: Consolas, monospace;")
        layout.addWidget(target_lbl)

        # Outcome
        outcome_text = record.get("outcome", "")
        if outcome_text:
            outcome_lbl = QLabel(f"Outcome: {outcome_text}", self)
            outcome_lbl.setWordWrap(True)
            outcome_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 10px; font-style: italic;")
            layout.addWidget(outcome_lbl)

        self.setStyleSheet(f"""
            #ActionLogItem {{
                background-color: {COLOR_CARD_DARK};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            #ActionLogItem:hover {{
                border-color: #3B465E;
            }}
        """)


class ActionLogWidget(QWidget):
    """
    Log viewer showing permanent history of all action proposals and outcomes.
    """
    backToChatRequested = pyqtSignal()

    def __init__(self, log_store: PersistentActionLog, parent=None):
        super().__init__(parent)
        self.log_store = log_store
        self._init_ui()
        self.refresh_log()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Top Bar with Title and Back button
        header_bar = QHBoxLayout()
        header_bar.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Persistent Action Log", self)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px; font-weight: bold;")
        title_box.addWidget(title)

        subtitle = QLabel("Survives restarts • Immutable record", self)
        subtitle.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")
        title_box.addWidget(subtitle)
        header_bar.addLayout(title_box, 1)

        self.btn_back = QPushButton("← Back to Chat", self)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: #1A212E;
                color: {COLOR_MINT};
                border: 1px solid {COLOR_MINT};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLOR_MINT};
                color: #000000;
            }}
        """)
        self.btn_back.clicked.connect(self.backToChatRequested.emit)
        header_bar.addWidget(self.btn_back)

        layout.addLayout(header_bar)

        # Scroll Area for Log Items
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()

        self.scroll_area.setWidget(self.items_container)
        layout.addWidget(self.scroll_area, 1)

    def refresh_log(self):
        """Reload entries from the persistent JSON store and re-render."""
        # Clear existing items (except stretch)
        while self.items_layout.count() > 1:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = self.log_store.load_all()
        if not entries:
            empty_lbl = QLabel("No actions recorded yet.\nPropose a demo action from Chat to see entries here.", self)
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; padding: 30px;")
            self.items_layout.insertWidget(0, empty_lbl)
            return

        for record in entries:
            widget = ActionLogItem(record, self.items_container)
            count = self.items_layout.count()
            self.items_layout.insertWidget(count - 1, widget)
