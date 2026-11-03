"""
Local Task Planning Subsystem for JD.
Deconstructs user requests submitted via voice or text into structured,
multi-step plans composed of safe actions, each requiring individual approval.
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class PlanStep:
    """
    An atomic step within a TaskPlan.
    """
    def __init__(
        self,
        step_number: int,
        tool_name: str,
        intent: str,
        target: str,
        parameters: Dict[str, Any],
        effect_explanation: str = "",
        action_id: Optional[str] = None,
        status: str = "pending",  # pending, awaiting approval, in progress, completed, rejected, canceled
        outcome: str = "",
    ):
        self.step_number = step_number
        self.action_id = action_id or f"step_{step_number}_{uuid.uuid4().hex[:6]}"
        self.tool_name = tool_name
        self.intent = intent
        self.target = target
        self.parameters = parameters
        self.effect_explanation = effect_explanation
        self.status = status
        self.outcome = outcome

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "action_id": self.action_id,
            "tool_name": self.tool_name,
            "intent": self.intent,
            "target": self.target,
            "parameters": self.parameters,
            "effect_explanation": self.effect_explanation,
            "status": self.status,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        return cls(
            step_number=data.get("step_number", 1),
            tool_name=data.get("tool_name", "unspecified"),
            intent=data.get("intent", ""),
            target=data.get("target", ""),
            parameters=data.get("parameters", {}),
            effect_explanation=data.get("effect_explanation", ""),
            action_id=data.get("action_id"),
            status=data.get("status", "pending"),
            outcome=data.get("outcome", ""),
        )


class TaskPlan:
    """
    Represents a full step-by-step proposed task plan.
    """
    def __init__(
        self,
        title: str,
        goal: str,
        steps: List[PlanStep],
        plan_id: Optional[str] = None,
        status: str = "in progress",  # in progress, paused, completed, rejected, canceled
        created_at: Optional[str] = None,
        completed_at: str = "",
    ):
        self.plan_id = plan_id or f"plan_{uuid.uuid4().hex[:8]}"
        self.title = title
        self.goal = goal
        self.steps = steps
        self.status = status
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.completed_at = completed_at

    def current_step(self) -> Optional[PlanStep]:
        for step in self.steps:
            if step.status in ["awaiting approval", "in progress"]:
                return step
        for step in self.steps:
            if step.status == "pending":
                return step
        return None

    def progress_percent(self) -> int:
        if not self.steps:
            return 0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return int((completed / len(self.steps)) * 100)

    def progress_text(self) -> str:
        if not self.steps:
            return "No steps"
        completed = sum(1 for s in self.steps if s.status == "completed")
        curr = self.current_step()
        if curr:
            return f"Step {curr.step_number} of {len(self.steps)} ({self.progress_percent()}%)"
        if self.status == "completed":
            return f"All {len(self.steps)} steps completed (100%)"
        if self.status in ["rejected", "canceled"]:
            return f"{self.status.capitalize()} at step {completed + 1} of {len(self.steps)}"
        return f"{completed}/{len(self.steps)} steps"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "progress_percent": self.progress_percent(),
            "progress_text": self.progress_text(),
        }


class TaskPlanner(QObject):
    """
    Local planning engine that generates structured, multi-step plans
    from voice or text input using safe demonstration tools.
    """
    planFormulated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def plan_from_text(self, prompt: str) -> TaskPlan:
        """
        Synthesize a structured multi-step plan from a user prompt.
        """
        lowered = prompt.lower().strip()

        # Check for specific intent combinations
        wants_audio = any(w in lowered for w in ["chime", "sound", "audio", "beep", "bell", "alert"])
        wants_checkpoint = any(w in lowered for w in ["checkpoint", "save", "restore", "snapshot", "state"])
        wants_diagnostic = any(w in lowered for w in ["diagnostic", "memory", "latency", "health", "check", "pulse", "audit"])

        steps = []
        step_idx = 1

        # If user asked for audio specifically
        if wants_audio and not wants_diagnostic and not wants_checkpoint:
            title = "Audio Alert & Speaker Verification"
            goal = "Verify laptop audio alert and system chime notification readiness"
            steps.append(PlanStep(
                step_number=step_idx,
                tool_name="demo_diagnostic",
                intent="Pre-check audio subsystem baseline latency",
                target="JD Audio Monitor",
                parameters={"scope": "audio_latency_precheck"},
                effect_explanation="Verifies audio thread readiness before sounding alert.",
            ))
            step_idx += 1
            steps.append(PlanStep(
                step_number=step_idx,
                tool_name="demo_chime",
                intent="Trigger Windows notification chime to verify speaker output",
                target="Windows Default Audio Device",
                parameters={"sound": "MB_ICONASTERISK"},
                effect_explanation="Plays an audible alert chime on laptop speakers.",
            ))

        # If user asked for checkpoint specifically
        elif wants_checkpoint and not wants_audio and not wants_diagnostic:
            title = "State Snapshot & Checkpoint Pipeline"
            goal = "Capture internal memory snapshot and store session restore point"
            steps.append(PlanStep(
                step_number=step_idx,
                tool_name="demo_diagnostic",
                intent="Scan memory variables prior to checkpoint snapshot",
                target="JD Memory Monitor",
                parameters={"scope": "pre_snapshot_scan"},
                effect_explanation="Ensures clean state before creating checkpoint.",
            ))
            step_idx += 1
            steps.append(PlanStep(
                step_number=step_idx,
                tool_name="demo_checkpoint",
                intent="Write assistant session checkpoint to memory store",
                target="JD Internal Session Store",
                parameters={"checkpoint_id": f"restore_point_{uuid.uuid4().hex[:4]}"},
                effect_explanation="Saves current assistant state.",
            ))

        # Comprehensive 3 or 4 step audit (default or combined)
        elif wants_audio and wants_checkpoint:
            title = "Full System Diagnostic & Audio Checkpoint Audit"
            goal = "Perform end-to-end audit: health pulse, notification chime, and state snapshot"
            steps.append(PlanStep(
                step_number=1,
                tool_name="demo_diagnostic",
                intent="Step 1: Check internal memory health and worker responsiveness",
                target="JD Core Health Subsystem",
                parameters={"step": 1, "test": "memory_readiness"},
                effect_explanation="Verifies memory baseline. If rejected, subsequent steps will not proceed.",
            ))
            steps.append(PlanStep(
                step_number=2,
                tool_name="demo_chime",
                intent="Step 2: Trigger Windows notification chime to test alert bridge",
                target="Windows Audio Notification Subsystem",
                parameters={"step": 2, "sound": "MB_ICONASTERISK"},
                effect_explanation="Will play an audible chime on laptop speakers.",
            ))
            steps.append(PlanStep(
                step_number=3,
                tool_name="demo_checkpoint",
                intent="Step 3: Save verified session restore point to memory",
                target="JD Session Store",
                parameters={"step": 3, "checkpoint_id": "post_audit_snapshot"},
                effect_explanation="Saves clean verified state snapshot.",
            ))

        else:
            # Standard 3-step assistant health inspection plan
            title = "Assistant Health & Latency Inspection"
            goal = f"Deconstructed task from: '{prompt}'"
            steps.append(PlanStep(
                step_number=1,
                tool_name="demo_diagnostic",
                intent="Step 1: Measure internal dialogue and speech latency",
                target="JD Core Dialogue Subsystem",
                parameters={"step": 1, "metric": "response_latency"},
                effect_explanation="Measures thread and speech queue latency.",
            ))
            steps.append(PlanStep(
                step_number=2,
                tool_name="demo_chime",
                intent="Step 2: Trigger Windows audio alert chime to confirm notification pipeline",
                target="Windows Audio Notification Subsystem",
                parameters={"step": 2, "sound": "MB_ICONASTERISK"},
                effect_explanation="Emits a standard notification chime.",
            ))
            steps.append(PlanStep(
                step_number=3,
                tool_name="demo_checkpoint",
                intent="Step 3: Snapshot verified configuration in assistant store",
                target="JD Session Store",
                parameters={"step": 3, "checkpoint_id": "health_audit_snapshot"},
                effect_explanation="Saves post-inspection session checkpoint.",
            ))

        plan = TaskPlan(title=title, goal=goal, steps=steps)
        self.planFormulated.emit(plan.to_dict())
        return plan

    def create_preset_plan(self, preset_type: str) -> TaskPlan:
        """Create standard preset test plans."""
        if preset_type == "audio_alert":
            return self.plan_from_text("test audio chime notification")
        elif preset_type == "checkpoint":
            return self.plan_from_text("save session state checkpoint")
        else:
            return self.plan_from_text("full health audit and latency check")
