# JD - Personal AI Desktop Assistant for Windows

JD is a personal AI desktop assistant built specifically for Windows. This repository contains the modular, extensible foundation designed to support upcoming tasks (local/cloud LLM intelligence, an explicit safety approval system, file access, and app automations).

---

## Task 1 Capabilities Implemented

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
  - Text conversation acts as continuous fallback and visual record.

- **Visual Microphone Indicator & Voice Input**:
  - Click the `🎤` button to activate microphone capture.
  - A prominent indicator bar appears with an animated glowing mint-green pulse reacting live to your voice volume.
  - Transcribes your spoken words into text and automatically prompts JD.

- **Controls**:
  - Minimize / Hide button (`—`) in header.
  - Complete application exit button (`✕`) in header and tray.

---

## Project Structure

```
JD/
├── assets/
│   └── jd_icon.png            # Official JD companion avatar
├── core/
│   ├── __init__.py
│   ├── config.py              # Palette, hotkey, window dimensions, audio config
│   ├── companion.py           # Dialogue manager and assistant state
│   ├── voice.py               # Windows SAPI5 TTS worker & live microphone listener
│   └── hotkey.py              # Global Windows hotkey listener (Ctrl+Alt+J)
├── ui/
│   ├── __init__.py
│   ├── styles.py              # Dark theme QSS styling with glowing mint accents
│   ├── mic_indicator.py       # Animated audio-reactive glowing microphone widget
│   ├── chat_widget.py         # Message history, text input, and send controls
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
* `Enter`: Send message in the chat input.
