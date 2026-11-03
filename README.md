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

### Task 3: Working Task Planning Flow
- **Task Submission via Text or Voice**:
  - Submit any multi-step task by voice (clicking the mic) or by typing in the input box (e.g. *"Plan a health audit and audio test"* or *"Check memory and save checkpoint"*).
  - Quick-start preset buttons in the HUD: **`[🔍 Health Audit (3 Steps)]`** and **`[🔔 Audio Alert (2 Steps)]`**.
- **Step-by-Step Plan HUD (`PlanWidget`)**:
  - Visualizes the proposed plan in the floating companion window:
    - **Title & Goal**: Clear summary of the task objective.
    - **Overall Progress**: Dynamic progress bar and step counter (e.g., `Step 2 of 3 (66%)`).
    - **Real-time Step Status Badges**:
      - `PENDING`: Waiting in plan queue.
      - `AWAITING APPROVAL`: Currently presented at the Approval Gate.
      - `IN PROGRESS`: Actively executing.
      - `COMPLETED`: Successfully finished.
      - `REJECTED`: Blocked by user rejection.
      - `CANCELED`: Discarded or canceled due to preceding failure or user cancel.
- **Strict Individual Step Approval**:
  - **A plan-level approval never approves individual actions.**
  - Showing the proposed plan does not execute anything until each individual action is reviewed and approved in the Approval Card.
- **Persistent Plan Logging**:
  - Every plan formulation event, step status transition, individual user decision, and final plan outcome is recorded in `data/action_log.json` and retained across restarts.
- **Unified Pause & Cancel**:
  - Pausing freezes both the active plan HUD and the approval queue.
  - Canceling immediately stops the active task, marks all pending steps as `CANCELED`, and records the cancellation outcome.
- **Safe Local Tools**:
  - Employs local planning logic and safe built-in actions (`demo_diagnostic`, `demo_chime`, `demo_checkpoint`) without external network, shell, or third-party app exposure.

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
│   ├── planner.py             # Local task planner & plan step models
│   ├── approval.py            # Central ApprovalGate, ActionQueue, and PersistentActionLog
│   ├── voice.py               # Windows SAPI5 TTS worker & live microphone listener
│   ├── hotkey.py              # Global Windows hotkey listener (Ctrl+Alt+J)
│   └── demo_tools.py          # Safe built-in demonstration tools
├── ui/
│   ├── __init__.py
│   ├── styles.py              # Dark theme QSS styling with glowing mint accents
│   ├── mic_indicator.py       # Animated audio-reactive glowing microphone widget
│   ├── chat_widget.py         # Message history, text input, and send controls
│   ├── plan_widget.py         # Step-by-step Plan HUD with progress & status badges
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
* `P`: Pause / Resume action queue & active plan.
* `C`: Cancel active task & plan.
