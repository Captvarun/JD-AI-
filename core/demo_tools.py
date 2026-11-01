"""
Safe demonstration actions for Task 2.
Demonstrates the proposal, approval, rejection, pausing, and logging flow
without accessing files, web, shell, or third-party apps.
"""

import sys
import time
from typing import Dict, Any

try:
    import winsound
except ImportError:
    winsound = None


def handle_demo_diagnostic(params: Dict[str, Any]) -> str:
    """Simulate a safe internal diagnostic health check."""
    time.sleep(0.15)
    return "Diagnostic pulse successful: Internal state intact, speech latency nominal."


def handle_demo_audio_chime(params: Dict[str, Any]) -> str:
    """Trigger a standard Windows notification beep."""
    if winsound:
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return "Windows notification chime sounded."
        except Exception as e:
            return f"Audio chime simulated ({e})."
    return "Audio chime simulated."


def handle_demo_state_checkpoint(params: Dict[str, Any]) -> str:
    """Record an internal memory checkpoint."""
    checkpoint_name = params.get("checkpoint_id", "cp_default")
    return f"Session checkpoint '{checkpoint_name}' saved to memory."


DEMO_TOOL_REGISTRY = {
    "demo_diagnostic": handle_demo_diagnostic,
    "demo_chime": handle_demo_audio_chime,
    "demo_checkpoint": handle_demo_state_checkpoint,
}

# Pre-defined demonstration tasks
DEMO_SINGLE_TASK = {
    "task_name": "Assistant Diagnostic Self-Test",
    "actions": [
        {
            "tool_name": "demo_diagnostic",
            "intent": "Run internal diagnostic pulse to verify companion response latency",
            "target": "JD Internal Subsystem & Memory",
            "parameters": {"scope": "core_health", "safe_mode": True},
            "effect_explanation": "Will verify responsiveness of internal dialogue workers.",
        }
    ]
}

DEMO_MULTI_STEP_TASK = {
    "task_name": "Multi-Step Health & Notification Pipeline",
    "actions": [
        {
            "tool_name": "demo_diagnostic",
            "intent": "Step 1: Check internal memory health before issuing notification",
            "target": "JD Internal Health Monitor",
            "parameters": {"step": 1, "test": "memory_readiness"},
            "effect_explanation": "Verifies memory baseline. If rejected, subsequent chime will not trigger.",
        },
        {
            "tool_name": "demo_chime",
            "intent": "Step 2: Trigger Windows audio alert chime to verify speaker readiness",
            "target": "Windows Audio Notification Subsystem",
            "parameters": {"step": 2, "sound": "MB_ICONASTERISK"},
            "effect_explanation": "Will play an audible chime on your laptop speakers.",
        },
        {
            "tool_name": "demo_checkpoint",
            "intent": "Step 3: Save clean session restore point in assistant state",
            "target": "JD Session Store",
            "parameters": {"step": 3, "checkpoint_id": "post_chime_state"},
            "effect_explanation": "Updates assistant session snapshot.",
        }
    ]
}
