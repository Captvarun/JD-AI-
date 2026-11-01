"""
Companion logic and dialogue engine for JD.
Provides greetings, conversation handling, and a clean interface for future AI models.
"""

from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class CompanionBrain(QObject):
    """
    Dialogue manager for JD.
    Processes user input, formats responses, and maintains history.
    """
    responseReady = pyqtSignal(str)

    INITIAL_GREETING = (
        "Greetings! I am JD, your personal AI desktop assistant. "
        "I'm now active on your desktop. You can speak or type to me anytime, "
        "or press Ctrl+Alt+J to summon or hide me."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []  # List of dicts: {'sender': 'user'|'jd', 'text': str, 'time': str}

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
        Process user message and generate JD's spoken and written response.
        """
        text = text.strip()
        if not text:
            return

        self.record_message("user", text)
        lowered = text.lower()

        # Handle conversational greetings and queries
        if any(w in lowered for w in ["hi", "hello", "hey", "greetings"]):
            reply = "Hello! JD online and ready. What can I help you with?"
        elif any(w in lowered for w in ["who are you", "what are you", "your name"]):
            reply = "I am JD, your personal Windows AI desktop companion. I stay right here on your desktop, ready to assist whenever you need me."
        elif any(w in lowered for w in ["how are you", "status", "system status"]):
            reply = "All systems operational! My floating companion window, speech engine, microphone listener, and global hotkeys are working smoothly."
        elif any(w in lowered for w in ["hotkey", "shortcut", "hide", "summon"]):
            reply = "You can press Ctrl+Alt+J at any time from any app to summon or hide my companion window."
        elif any(w in lowered for w in ["what can you do", "help", "capabilities"]):
            reply = (
                "Right now in Task 1, I provide a floating desktop presence, global hotkey summoning, "
                "offline voice responses, live microphone speech recognition, and instant chat. "
                "In upcoming tasks, we will add web search, file access, and app automation with an explicit approval system."
            )
        elif any(w in lowered for w in ["search the web", "open file", "run code", "install", "control app"]):
            reply = (
                "Web search, file access, code execution, and application control are being built in our next tasks, "
                "complete with an explicit user approval system for safety."
            )
        elif any(w in lowered for w in ["thank", "thanks"]):
            reply = "You're very welcome! I'm always here if you need me."
        elif any(w in lowered for w in ["bye", "goodbye", "quit", "exit"]):
            reply = "Goodbye for now! You can hide me with Ctrl+Alt+J or close me using the X button on the top right."
        else:
            # Clear, grounded response acknowledging the message
            reply = f"I received: \"{text}\". My core companion systems are active and listening. What would you like to explore next?"

        self.record_message("jd", reply)
        self.responseReady.emit(reply)
