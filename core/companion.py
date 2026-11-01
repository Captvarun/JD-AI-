"""
Companion logic and dialogue engine for JD.
Provides greetings, conversation handling, and interface for the Approval System.
"""

from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from core.demo_tools import DEMO_SINGLE_TASK, DEMO_MULTI_STEP_TASK


class CompanionBrain(QObject):
    """
    Dialogue manager for JD.
    Processes user input, formats responses, and coordinates tasks with the ApprovalGate.
    """
    responseReady = pyqtSignal(str)
    requestTaskEnqueue = pyqtSignal(dict)  # Emits task spec to ApprovalGate
    requestPauseQueue = pyqtSignal()
    requestResumeQueue = pyqtSignal()
    requestCancelTask = pyqtSignal()
    requestSwitchView = pyqtSignal(str)    # 'chat' or 'log'

    INITIAL_GREETING = (
        "Greetings! I am JD, your personal AI desktop assistant. "
        "Task 2 is active: my explicit approval checkpoint and persistent action log are operational. "
        "You can type or say 'demo' to test an action proposal, or press Ctrl+Alt+J to summon or hide me."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []

    def get_greeting(self) -> str:
        return self.INITIAL_GREETING

    def record_message(self, sender: str, text: str):
        now = datetime.now().strftime("%I:%M %p")
        self.history.append({
            "sender": sender,
            "text": text,
            "time": now
        })

    def process_user_input(self, text: str):
        """
        Process user message and coordinate actions or conversation.
        """
        text = text.strip()
        if not text:
            return

        self.record_message("user", text)
        lowered = text.lower()

        # Handle Action Approval System triggers
        if any(w in lowered for w in ["run demo", "single demo", "test action", "test approval", "start demo", "propose action"]) or lowered == "demo":
            reply = "Proposing a demonstration action for your approval now. Please review the details on the approval card above."
            self.requestTaskEnqueue.emit(DEMO_SINGLE_TASK)

        elif any(w in lowered for w in ["multi demo", "multi-step", "pipeline", "test pipeline", "run pipeline"]):
            reply = "Initiating a 3-step demonstration pipeline. I will propose each action one by one for your individual approval."
            self.requestTaskEnqueue.emit(DEMO_MULTI_STEP_TASK)

        elif lowered in ["pause", "pause queue", "pause actions"]:
            reply = "Pausing the action queue as requested."
            self.requestPauseQueue.emit()

        elif lowered in ["resume", "resume queue", "unpause"]:
            reply = "Resuming the action queue."
            self.requestResumeQueue.emit()

        elif lowered in ["cancel", "cancel task", "abort", "stop task"]:
            reply = "Canceling active task and discarding all pending actions."
            self.requestCancelTask.emit()

        elif any(w in lowered for w in ["show logs", "view log", "action log", "history", "persistent log"]):
            reply = "Opening your persistent Action Log."
            self.requestSwitchView.emit("log")

        # Conversational greetings and queries
        elif any(w in lowered for w in ["hi", "hello", "hey", "greetings"]):
            reply = "Hello! JD online and ready. You can test our new Approval System by saying 'demo' or clicking the demo button."
        elif any(w in lowered for w in ["who are you", "what are you", "your name"]):
            reply = "I am JD, your personal Windows AI desktop companion. I have an explicit approval checkpoint so nothing runs without your permission."
        elif any(w in lowered for w in ["how are you", "status", "system status"]):
            reply = "All systems operational! Floating window, speech, hotkeys, approval gate, and persistent action log are active."
        elif any(w in lowered for w in ["hotkey", "shortcut", "hide", "summon"]):
            reply = "You can press Ctrl+Alt+J at any time from any app to summon or hide my companion window."
        elif any(w in lowered for w in ["approval", "how does approval work", "checkpoint"]):
            reply = (
                "Every external operation is held at the Approval Gate. I present the exact intent and target. "
                "You can click Approve or Reject, or press Enter / Escape. If rejected, the action never runs and is permanently logged."
            )
        elif any(w in lowered for w in ["what can you do", "help", "capabilities"]):
            reply = (
                "In Task 2, I provide a floating companion, offline voice, hotkeys, an explicit approval system, "
                "and a persistent action log. Say 'demo' to test a single action, or 'pipeline' to test multi-step actions."
            )
        elif any(w in lowered for w in ["search the web", "open file", "run code", "install", "control app"]):
            reply = (
                "External tool integrations (files, web, app automations) will be safely connected in future tasks, "
                "and every single one will route through this same approval checkpoint."
            )
        elif any(w in lowered for w in ["thank", "thanks"]):
            reply = "You're very welcome! Let me know if you want to test another action."
        elif any(w in lowered for w in ["bye", "goodbye", "quit", "exit"]):
            reply = "Goodbye for now! You can hide me with Ctrl+Alt+J or close me using the X button on the top right."
        else:
            reply = f"I received: \"{text}\". Say 'demo' to test the approval flow, or ask me about the action log."

        self.record_message("jd", reply)
        self.responseReady.emit(reply)
