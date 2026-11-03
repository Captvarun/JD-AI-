"""
Task Plan HUD Widget for JD.
Visualizes proposed multi-step plans with individual step statuses:
pending, awaiting approval, in progress, completed, rejected, and canceled.
"""

from typing import Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QFrame,
)

from core.config import (
    COLOR_MINT,
    COLOR_CARD_DARK,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_STATUS_PENDING,
    COLOR_STATUS_AWAITING,
    COLOR_STATUS_PROGRESS,
    COLOR_STATUS_COMPLETED,
    COLOR_STATUS_REJECTED,
    COLOR_STATUS_CANCELED,
)


def get_status_styling(status_str: str) -> tuple[str, str, str]:
    """Returns (label_text, text_color, background_color) for a step status."""
    st = status_str.lower().strip()
    if st == "awaiting approval":
        return ("AWAITING APPROVAL", COLOR_STATUS_AWAITING, "rgba(255, 170, 51, 0.22)")
    elif st == "in progress":
        return ("IN PROGRESS", COLOR_STATUS_PROGRESS, "rgba(82, 255, 184, 0.22)")
    elif st == "completed":
        return ("COMPLETED", COLOR_STATUS_COMPLETED, "rgba(56, 229, 160, 0.18)")
    elif st == "rejected":
        return ("REJECTED", COLOR_STATUS_REJECTED, "rgba(255, 94, 94, 0.22)")
    elif st == "canceled":
        return ("CANCELED", COLOR_STATUS_CANCELED, "rgba(142, 149, 165, 0.18)")
    else:  # pending
        return ("PENDING", COLOR_STATUS_PENDING, "rgba(77, 166, 255, 0.18)")


class PlanStepItem(QFrame):
    """
    Renders an individual step within the plan HUD.
    """
    def __init__(self, step_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setObjectName("PlanStepItem")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # Header: Step Number + Status Badge + Target
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        num_lbl = QLabel(f"#{step_data.get('step_number', 1)}", self)
        num_lbl.setStyleSheet(f"color: {COLOR_MINT}; font-size: 10px; font-weight: bold; font-family: Consolas, monospace;")
        top_row.addWidget(num_lbl)

        status_text, color, bg = get_status_styling(step_data.get("status", "pending"))
        badge = QLabel(status_text, self)
        badge.setStyleSheet(f"""
            background-color: {bg};
            color: {color};
            border: 1px solid {color};
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 8px;
            font-weight: bold;
            letter-spacing: 0.5px;
        """)
        top_row.addWidget(badge)

        target_lbl = QLabel(step_data.get("target", "System"), self)
        target_lbl.setStyleSheet("color: #FFB84D; font-size: 9px; font-family: Consolas, monospace;")
        top_row.addWidget(target_lbl, 1)

        layout.addLayout(top_row)

        # Intent Description
        intent_lbl = QLabel(step_data.get("intent", "No description"), self)
        intent_lbl.setWordWrap(True)
        intent_lbl.setStyleSheet("color: #E2E8F0; font-size: 11px;")
        layout.addWidget(intent_lbl)

        # Outcome (if resolved)
        outcome = step_data.get("outcome", "")
        if outcome:
            outcome_lbl = QLabel(f"Result: {outcome}", self)
            outcome_lbl.setWordWrap(True)
            outcome_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 9px; font-style: italic;")
            layout.addWidget(outcome_lbl)

        # Outline highlight if awaiting approval
        border_color = color if status_text == "AWAITING APPROVAL" else COLOR_BORDER
        self.setStyleSheet(f"""
            #PlanStepItem {{
                background-color: #11151F;
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
        """)


class PlanWidget(QFrame):
    """
    HUD Component that displays the active step-by-step plan,
    progress bar, and real-time step statuses.
    """
    planPresetRequested = pyqtSignal(str) # 'audit', 'audio', 'checkpoint'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlanWidget")
        self._current_plan_data: Optional[Dict[str, Any]] = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet(f"""
            #PlanWidget {{
                background-color: #141822;
                border: 1px solid #283347;
                border-radius: 12px;
                padding: 8px;
            }}
            .PlanTitle {{
                color: {COLOR_TEXT_PRIMARY};
                font-size: 12px;
                font-weight: bold;
            }}
            .PlanSubtitle {{
                color: {COLOR_TEXT_SECONDARY};
                font-size: 10px;
            }}
            QProgressBar {{
                background-color: #0E121A;
                border: 1px solid #232B3B;
                border-radius: 5px;
                height: 8px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_MINT};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Header Bar: Title, Plan Status, and Progress Text
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(6)

        self.lbl_title = QLabel("Proposed Task Plan", self)
        self.lbl_title.setProperty("class", "PlanTitle")
        header_row.addWidget(self.lbl_title, 1)

        self.lbl_plan_status = QLabel("IN PROGRESS", self)
        self.lbl_plan_status.setStyleSheet(f"""
            background-color: rgba(82, 255, 184, 0.15);
            color: {COLOR_MINT};
            border: 1px solid {COLOR_MINT};
            border-radius: 5px;
            padding: 1px 6px;
            font-size: 8px;
            font-weight: bold;
        """)
        header_row.addWidget(self.lbl_plan_status)

        self.lbl_progress = QLabel("0%", self)
        self.lbl_progress.setStyleSheet(f"color: {COLOR_MINT}; font-size: 10px; font-weight: bold; font-family: Consolas, monospace;")
        header_row.addWidget(self.lbl_progress)

        layout.addLayout(header_row)

        # 2. Goal / Subtitle
        self.lbl_goal = QLabel("", self)
        self.lbl_goal.setProperty("class", "PlanSubtitle")
        self.lbl_goal.setWordWrap(True)
        layout.addWidget(self.lbl_goal)

        # 3. Overall Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 4. Scrollable Steps List
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(130)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 0, 0, 0)
        self.steps_layout.setSpacing(4)
        self.steps_layout.addStretch()

        self.scroll_area.setWidget(self.steps_container)
        layout.addWidget(self.scroll_area)

        # 5. Standby Bar (shown when no plan is active)
        self.standby_widget = QWidget(self)
        standby_layout = QVBoxLayout(self.standby_widget)
        standby_layout.setContentsMargins(0, 2, 0, 2)
        standby_layout.setSpacing(6)

        standby_hdr = QLabel("📋 Task Planning HUD", self.standby_widget)
        standby_hdr.setStyleSheet(f"color: {COLOR_MINT}; font-size: 11px; font-weight: bold;")
        standby_layout.addWidget(standby_hdr)

        standby_desc = QLabel("Submit a multi-step task via voice or text, or test a preset plan below:", self.standby_widget)
        standby_desc.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 10px;")
        standby_layout.addWidget(standby_desc)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(6)

        btn_p1 = QPushButton("🔍 Health Audit (3 Steps)", self.standby_widget)
        btn_p1.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_p1.setStyleSheet(f"""
            QPushButton {{
                background-color: #172421;
                color: {COLOR_MINT};
                border: 1px solid {COLOR_MINT};
                border-radius: 6px;
                font-size: 9px;
                font-weight: bold;
                padding: 4px 6px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_MINT};
                color: #000000;
            }}
        """)
        btn_p1.clicked.connect(lambda: self.planPresetRequested.emit("audit"))
        preset_row.addWidget(btn_p1)

        btn_p2 = QPushButton("🔔 Audio Alert (2 Steps)", self.standby_widget)
        btn_p2.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_p2.setStyleSheet("""
            QPushButton {
                background-color: #1E2333;
                color: #8EB7FF;
                border: 1px solid #3B4D73;
                border-radius: 6px;
                font-size: 9px;
                font-weight: bold;
                padding: 4px 6px;
            }
            QPushButton:hover {
                background-color: #2F3E61;
                border-color: #8EB7FF;
            }
        """)
        btn_p2.clicked.connect(lambda: self.planPresetRequested.emit("audio"))
        preset_row.addWidget(btn_p2)

        standby_layout.addLayout(preset_row)
        layout.addWidget(self.standby_widget)

        self._show_active_plan(False)

    def _show_active_plan(self, is_active: bool):
        self.standby_widget.setVisible(not is_active)
        self.lbl_title.setVisible(is_active)
        self.lbl_plan_status.setVisible(is_active)
        self.lbl_progress.setVisible(is_active)
        self.lbl_goal.setVisible(is_active)
        self.progress_bar.setVisible(is_active)
        self.scroll_area.setVisible(is_active)

    def update_plan(self, plan_data: Dict[str, Any]):
        """Render the latest plan state with all step statuses."""
        self._current_plan_data = plan_data
        self._show_active_plan(True)

        self.lbl_title.setText(f"📋 Plan: {plan_data.get('title', 'Untitled Plan')}")
        self.lbl_goal.setText(plan_data.get("goal", ""))

        status = plan_data.get("status", "in progress").upper()
        self.lbl_plan_status.setText(status)
        if status == "COMPLETED":
            self.lbl_plan_status.setStyleSheet(f"background-color: rgba(56, 229, 160, 0.18); color: {COLOR_STATUS_COMPLETED}; border: 1px solid {COLOR_STATUS_COMPLETED}; border-radius: 5px; padding: 1px 6px; font-size: 8px; font-weight: bold;")
        elif status == "REJECTED":
            self.lbl_plan_status.setStyleSheet(f"background-color: rgba(255, 94, 94, 0.2); color: {COLOR_STATUS_REJECTED}; border: 1px solid {COLOR_STATUS_REJECTED}; border-radius: 5px; padding: 1px 6px; font-size: 8px; font-weight: bold;")
        elif status == "CANCELED":
            self.lbl_plan_status.setStyleSheet(f"background-color: rgba(142, 149, 165, 0.2); color: {COLOR_STATUS_CANCELED}; border: 1px solid {COLOR_STATUS_CANCELED}; border-radius: 5px; padding: 1px 6px; font-size: 8px; font-weight: bold;")
        elif status == "PAUSED":
            self.lbl_plan_status.setStyleSheet("background-color: rgba(255, 184, 77, 0.2); color: #FFB84D; border: 1px solid #FFB84D; border-radius: 5px; padding: 1px 6px; font-size: 8px; font-weight: bold;")
        else:
            self.lbl_plan_status.setStyleSheet(f"background-color: rgba(82, 255, 184, 0.15); color: {COLOR_MINT}; border: 1px solid {COLOR_MINT}; border-radius: 5px; padding: 1px 6px; font-size: 8px; font-weight: bold;")

        percent = plan_data.get("progress_percent", 0)
        self.progress_bar.setValue(percent)
        self.lbl_progress.setText(plan_data.get("progress_text", f"{percent}%"))

        # Re-render steps
        while self.steps_layout.count() > 1:
            item = self.steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        steps = plan_data.get("steps", [])
        for step in steps:
            step_widget = PlanStepItem(step, self.steps_container)
            self.steps_layout.insertWidget(self.steps_layout.count() - 1, step_widget)

    def clear_plan(self):
        self._current_plan_data = None
        self._show_active_plan(False)
