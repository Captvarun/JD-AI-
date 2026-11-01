# JD - Personal AI Desktop Assistant for Windows

JD is a personal AI desktop assistant built specifically for Windows. This repository contains the modular, extensible foundation designed to support upcoming tasks (local/cloud LLM intelligence, an explicit safety approval system, file access, and app automations).

---

## Capabilities Implemented

### Task 1: Companion Foundation & Voice
- **Floating Windows Companion**:
  - Frameless, translucent, always-on-top floating desktop widget.
  - Features the official **JD Identity** (dark robotic helmet with glowing mint-green eyes on a pale lilac background) from `assets/jd_icon.png`.
  - Smooth click-and-drag movement to reposition anywhere on your desktop.
  - System tray icon with quick actions (Show/Hide, Mute/Unmute, Clear, Quit).
- **Global Hotkey Summon / Dismiss**:
  - Press `Ctrl + Alt + J` from any application to instantly summon JD into focus or dismiss it back to the background.
- **Conversation & Text Interaction**:
  - Dark futuristic chat interface styled to match JD's helmet aesthetic with glowing mint-green accents (`#52FFB8`).
  - Scrollable message history with distinct bubbles and timestamps.
  - Interactive text input field with `Enter` key submission and `Send` button.
- **Offline Speech Synthesis (TTS)**:
  - Uses native Windows SAPI5 (`pyttsx3`) for zero-latency, offline spoken greetings and responses.
  - Threaded worker ensures zero UI freezing.
  - Mute/Unmute toggle button in the header and tray.
- **Visual Microphone Indicator & Voice Input**:
  - Click the `🎤` button to activate microphone capture.
  - Animated glowing mint-green pulse reacting live to your voice volume.
  - Transcribes speech into text and submits it to JD.

### Task 2: Explicit Approval System & Persistent Action Log
- **Action Queue & Approval Gate (`ApprovalGate`)**:
  - Central security checkpoint ensuring that **no tool or operation with external effects** can ever execute without explicit, unbundled approval.
  - Actions are presented **one at a time** in an interactive **Approval Card**.
- **What JD Wants to Do & What It Will Affect**:
  - The Approval Card clearly exposes:
    - **Intent**: Exact description of what JD plans to perform.
    - **Target**: Highlights the external target/subsystem affected.
    - **Parameters**: Structured parameters or arguments.
- **Strict Single-Action Controls (Mouse & Keyboard)**:
  - **`✓ Approve` (`Enter`)**: Explicitly permits execution of that specific action.
  - **`✕ Reject` (`Esc`)**: Blocks execution immediately. JD explains the effect on the task and discards dependent steps.
  - Silence, closing the window, or approving another action never counts as approval.
- **Pause & Cancel Controls**:
  - **`⏸ Pause` / `▶ Resume` (`P`)**: Suspends the queue so no further actions run until resumed.
  - **`⏹ Cancel Task` (`C`)**: Discards all remaining pending actions for the active task and aborts the task.
- **Persistent Action Log (`data/action_log.json`)**:
  - Immutable record storing Task Name, Intent, Target, Decision (`APPROVED`, `REJECTED`, `CANCELED`), Timestamp, and Outcome.
  - **Survives restarts**: Viewable directly in JD via the `📋 Log` tab in the header.
- **Safe Built-in Demonstration Tools**:
  - Safe diagnostic pulses, notification audio chimes, and state checkpoints.
  - Type or say `"demo"` or `"pipeline"` (or click `[🧪 Propose Demo Action]` / `[⚡ Propose 3-Step Pipeline]`) to test the complete flow.

---

## Project Structure

```
JD/
├── assets/
│   └── jd_icon.png            # Official JD companion avatar
├── data/
│   └── action_log.json        # Persistent action log store (survives app restarts)
├── core/
│   ├── __init__.py
│   ├── config.py              # Palette, hotkey, window dimensions, audio config
│   ├── companion.py           # Dialogue manager and assistant state
│   ├── voice.py               # Windows SAPI5 TTS worker & live microphone listener
│   ├── hotkey.py              # Global Windows hotkey listener (Ctrl+Alt+J)
│   ├── approval.py            # Central ApprovalGate, ActionQueue, and PersistentActionLog
│   └── demo_tools.py          # Safe built-in demonstration tools for Task 2
├── ui/
│   ├── __init__.py
│   ├── styles.py              # Dark theme QSS styling with glowing mint accents
│   ├── mic_indicator.py       # Animated audio-reactive glowing microphone widget
│   ├── chat_widget.py         # Message history, text input, and send controls
│   ├── approval_widget.py     # Approval Card with Approve, Reject, Pause, and Cancel
│   ├── log_widget.py          # Persistent Action Log viewer with status badges
│   └── companion_window.py    # Main frameless floating companion window
├── main.py                    # Application bootstrap & event loop
├── run_jd.bat                 # One-click desktop launcher (runs without console)
├── requirements.txt           # Project dependencies
└── README.md
```

---

## How to Launch JD

### Option 1: Double-Click Launcher
Double-click `run_jd.bat` in the project root directory.

### Option 2: PowerShell / Command Prompt
```powershell
cd "C:\Users\M S VARUN\OneDrive\Desktop\JD"
.\.venv\Scripts\python main.py
```

### Keyboard Shortcuts
* `Ctrl + Alt + J`: Summon or hide JD from anywhere in Windows.
* `Enter` / `Return`: Approve proposed action (or send message in chat input).
* `Escape`: Reject proposed action.
* `P`: Pause / Resume action queue.
* `C`: Cancel active task.
