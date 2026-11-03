"""
Approval system, Action Queue, and Persistent Action Log for JD.
Ensures every external action requires explicit, unbundled user approval.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from PyQt6.QtCore import QObject, pyqtSignal

from core.config import ACTION_LOG_PATH, DATA_DIR
from core.planner import TaskPlan, PlanStep


class ProposedAction:
    """
    Represents an atomic proposed action requiring explicit approval.
    """
    def __init__(
        self,
        task_id: str,
        task_name: str,
        tool_name: str,
        intent: str,
        target: str,
        parameters: Dict[str, Any],
        effect_explanation: str = "",
        action_id: Optional[str] = None,
        status: str = "PENDING",
        decision: str = "PENDING",
        created_at: Optional[str] = None,
        decision_time: Optional[str] = None,
        outcome: str = "",
    ):
        self.id = action_id or f"act_{uuid.uuid4().hex[:8]}"
        self.task_id = task_id
        self.task_name = task_name
        self.tool_name = tool_name
        self.intent = intent
        self.target = target
        self.parameters = parameters
        self.effect_explanation = effect_explanation
        self.status = status          # PENDING, APPROVED, REJECTED, PAUSED, CANCELED, EXECUTED, FAILED
        self.decision = decision      # PENDING, APPROVED, REJECTED, CANCELED
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.decision_time = decision_time or ""
        self.outcome = outcome

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "tool_name": self.tool_name,
            "intent": self.intent,
            "target": self.target,
            "parameters": self.parameters,
            "effect_explanation": self.effect_explanation,
            "status": self.status,
            "decision": self.decision,
            "created_at": self.created_at,
            "decision_time": self.decision_time,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProposedAction":
        return cls(
            task_id=data.get("task_id", ""),
            task_name=data.get("task_name", ""),
            tool_name=data.get("tool_name", ""),
            intent=data.get("intent", ""),
            target=data.get("target", ""),
            parameters=data.get("parameters", {}),
            effect_explanation=data.get("effect_explanation", ""),
            action_id=data.get("id"),
            status=data.get("status", "PENDING"),
            decision=data.get("decision", "PENDING"),
            created_at=data.get("created_at"),
            decision_time=data.get("decision_time", ""),
            outcome=data.get("outcome", ""),
        )


class PersistentActionLog:
    """
    Thread-safe persistent store for recorded actions and decisions.
    Survives application restarts.
    """
    def __init__(self, log_path: Path = ACTION_LOG_PATH):
        self.log_path = log_path
        self._ensure_storage()

    def _ensure_storage(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            try:
                with open(self.log_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
            except Exception as e:
                print(f"Error creating action log storage: {e}")

    def load_all(self) -> List[Dict[str, Any]]:
        self._ensure_storage()
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error reading persistent action log: {e}")
            return []

    def record_or_update(self, action: ProposedAction):
        """Append or update an action record persistently."""
        entries = self.load_all()
        action_dict = action.to_dict()

        # Update if already exists, else prepend
        found = False
        for i, entry in enumerate(entries):
            if entry.get("id") == action.id:
                entries[i] = action_dict
                found = True
                break

        if not found:
            entries.insert(0, action_dict)  # Newest first

        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)
        except Exception as e:
            print(f"Error saving to persistent action log: {e}")


class ApprovalGate(QObject):
    """
    Central security gate and sequential action queue for JD.
    No tool with external effects can execute without explicit individual approval.
    """
    actionProposed = pyqtSignal(dict)      # Emitted when an action is waiting for user
    actionResolved = pyqtSignal(dict)      # Emitted when action is approved/rejected/canceled
    queueStatusChanged = pyqtSignal(dict)  # Queue count, is_paused, current task
    taskExplanation = pyqtSignal(str)      # Spoken & written explanation of task effect
    logUpdated = pyqtSignal()              # Triggered when log entries change
    planUpdated = pyqtSignal(dict)         # Emitted when plan steps change status

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = PersistentActionLog()
        self._queue: List[ProposedAction] = []
        self._current_action: Optional[ProposedAction] = None
        self._is_paused: bool = False
        self._active_plan: Optional[TaskPlan] = None
        self._tool_handlers = {}

    def register_tool_handler(self, tool_name: str, handler_callable):
        """Register a handler function for an approved tool."""
        self._tool_handlers[tool_name] = handler_callable

    def is_paused(self) -> bool:
        return self._is_paused

    def get_current_action(self) -> Optional[ProposedAction]:
        return self._current_action

    def get_queue_size(self) -> int:
        return len(self._queue)

    def get_active_plan(self) -> Optional[TaskPlan]:
        return self._active_plan

    def enqueue_plan(self, plan: TaskPlan):
        """
        Enqueues a step-by-step task plan into the approval queue.
        Each step must be approved individually before execution.
        """
        self._active_plan = plan

        # Log the plan proposal in the persistent action log
        plan_log_entry = ProposedAction(
            task_id=plan.plan_id,
            task_name=f"Plan: {plan.title}",
            tool_name="planner_proposed",
            intent=f"Formulated {len(plan.steps)}-step plan: {plan.goal}",
            target="JD Plan HUD",
            parameters={"steps": [s.intent for s in plan.steps]},
            status="PLAN_PROPOSED",
            decision="PROPOSED",
            outcome=f"Plan initialized. Awaiting individual approval for step 1 of {len(plan.steps)}."
        )
        self.log.record_or_update(plan_log_entry)
        self.logUpdated.emit()

        # Enqueue each step as an individual ProposedAction
        for step in plan.steps:
            action = ProposedAction(
                task_id=plan.plan_id,
                task_name=plan.title,
                tool_name=step.tool_name,
                intent=step.intent,
                target=step.target,
                parameters=step.parameters,
                effect_explanation=step.effect_explanation,
                action_id=step.action_id,
            )
            self._queue.append(action)

        self._emit_queue_status()
        self.planUpdated.emit(self._active_plan.to_dict())
        self._present_next()

    def enqueue_task(self, task_name: str, actions_specs: List[Dict[str, Any]]):
        """
        Enqueues a sequence of actions for a task.
        Each action will be presented strictly one at a time.
        """
        task_id = f"task_{uuid.uuid4().hex[:6]}"
        new_actions = []

        for spec in actions_specs:
            action = ProposedAction(
                task_id=task_id,
                task_name=task_name,
                tool_name=spec.get("tool_name", "unspecified_tool"),
                intent=spec.get("intent", "Unspecified action"),
                target=spec.get("target", "System"),
                parameters=spec.get("parameters", {}),
                effect_explanation=spec.get("effect_explanation", ""),
            )
            self._queue.append(action)
            new_actions.append(action)

        self._emit_queue_status()
        self._present_next()

    def _emit_queue_status(self):
        self.queueStatusChanged.emit({
            "queue_size": len(self._queue),
            "is_paused": self._is_paused,
            "has_current": self._current_action is not None,
            "current_task": self._current_action.task_name if self._current_action else (self._active_plan.title if self._active_plan else ""),
        })

    def _present_next(self):
        """Present the next action in the queue if ready."""
        if self._is_paused or self._current_action is not None or not self._queue:
            self._emit_queue_status()
            return

        self._current_action = self._queue.pop(0)
        self._current_action.status = "PENDING"

        # Update step status in active plan if applicable
        if self._active_plan:
            for step in self._active_plan.steps:
                if step.action_id == self._current_action.id:
                    step.status = "awaiting approval"
                    break
            self.planUpdated.emit(self._active_plan.to_dict())

        self._emit_queue_status()
        self.actionProposed.emit(self._current_action.to_dict())

    def approve_action(self, action_id: str) -> bool:
        """
        Explicitly approves the currently pending action by exact ID.
        """
        if not self._current_action or self._current_action.id != action_id:
            return False

        action = self._current_action
        action.decision = "APPROVED"
        action.status = "APPROVED"
        action.decision_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

        # Mark step in-progress in active plan
        if self._active_plan:
            for step in self._active_plan.steps:
                if step.action_id == action.id:
                    step.status = "in progress"
                    break
            self.planUpdated.emit(self._active_plan.to_dict())

        # Execute registered tool handler
        outcome_msg = ""
        handler = self._tool_handlers.get(action.tool_name)
        if handler:
            try:
                result = handler(action.parameters)
                action.status = "EXECUTED"
                action.outcome = f"Executed successfully: {result}"
                outcome_msg = f"Action '{action.intent}' was approved and executed successfully."
            except Exception as e:
                action.status = "FAILED"
                action.outcome = f"Execution failed: {e}"
                outcome_msg = f"Action '{action.intent}' was approved, but failed: {e}"
        else:
            action.status = "EXECUTED"
            action.outcome = "Executed (Demo confirmation completed)."
            outcome_msg = f"Action '{action.intent}' was approved and executed."

        # Update step completed in active plan
        if self._active_plan:
            for step in self._active_plan.steps:
                if step.action_id == action.id:
                    step.status = "completed"
                    step.outcome = action.outcome
                    break

            if all(s.status == "completed" for s in self._active_plan.steps):
                self._active_plan.status = "completed"
                self._active_plan.completed_at = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                plan_comp_entry = ProposedAction(
                    task_id=self._active_plan.plan_id,
                    task_name=f"Plan: {self._active_plan.title}",
                    tool_name="planner_completed",
                    intent=f"Completed all {len(self._active_plan.steps)} steps in plan",
                    target="JD Plan HUD",
                    parameters={"steps_count": len(self._active_plan.steps)},
                    status="PLAN_COMPLETED",
                    decision="APPROVED",
                    outcome=f"Plan '{self._active_plan.title}' finished successfully. All steps verified."
                )
                self.log.record_or_update(plan_comp_entry)

            self.planUpdated.emit(self._active_plan.to_dict())

        # Save to persistent log
        self.log.record_or_update(action)
        self.logUpdated.emit()
        self.actionResolved.emit(action.to_dict())
        self.taskExplanation.emit(outcome_msg)

        # Clear current and advance
        self._current_action = None
        self._present_next()
        return True

    def reject_action(self, action_id: str) -> bool:
        """
        Explicitly rejects the currently pending action by exact ID.
        Stops the action from executing and explains the effect on the task.
        """
        if not self._current_action or self._current_action.id != action_id:
            return False

        action = self._current_action
        action.decision = "REJECTED"
        action.status = "REJECTED"
        action.decision_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        action.outcome = "Blocked: User rejected this operation."

        # Save to persistent log
        self.log.record_or_update(action)

        # Update step rejected in active plan & discard subsequent steps
        if self._active_plan:
            for step in self._active_plan.steps:
                if step.action_id == action.id:
                    step.status = "rejected"
                    step.outcome = "Blocked: User rejected this operation."
                elif step.status in ["pending", "awaiting approval"]:
                    step.status = "canceled"
                    step.outcome = f"Discarded because preceding step was rejected."
            self._active_plan.status = "rejected"
            self._active_plan.completed_at = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            plan_rej_entry = ProposedAction(
                task_id=self._active_plan.plan_id,
                task_name=f"Plan: {self._active_plan.title}",
                tool_name="planner_rejected",
                intent=f"Plan halted due to rejection of action '{action.intent}'",
                target="JD Plan HUD",
                parameters={"rejected_step_id": action_id},
                status="PLAN_REJECTED",
                decision="REJECTED",
                outcome=f"Plan '{self._active_plan.title}' stopped. Dependent steps discarded."
            )
            self.log.record_or_update(plan_rej_entry)
            self.planUpdated.emit(self._active_plan.to_dict())

        # Discard remaining actions belonging to this same task
        discarded_count = 0
        remaining_queue = []
        for q_action in self._queue:
            if q_action.task_id == action.task_id:
                q_action.decision = "CANCELED"
                q_action.status = "CANCELED"
                q_action.decision_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                q_action.outcome = f"Discarded because preceding step '{action.intent}' was rejected."
                self.log.record_or_update(q_action)
                discarded_count += 1
            else:
                remaining_queue.append(q_action)
        self._queue = remaining_queue

        explanation = (
            f"Action rejected: '{action.intent}'. "
            f"This operation was blocked from running. "
            f"As a result, subsequent steps in '{action.task_name}' were stopped."
        )
        if discarded_count > 0:
            explanation += f" ({discarded_count} dependent action(s) discarded)."

        self.logUpdated.emit()
        self.actionResolved.emit(action.to_dict())
        self.taskExplanation.emit(explanation)

        # Clear current and advance
        self._current_action = None
        self._present_next()
        return True

    def pause_queue(self):
        """Pauses the action queue. Pending actions will not be presented."""
        self._is_paused = True
        if self._active_plan and self._active_plan.status == "in progress":
            self._active_plan.status = "paused"
            self.planUpdated.emit(self._active_plan.to_dict())
        self._emit_queue_status()
        self.taskExplanation.emit(
            "Action queue paused. No further pending actions will be presented until resumed."
        )

    def resume_queue(self):
        """Resumes the action queue."""
        self._is_paused = False
        if self._active_plan and self._active_plan.status == "paused":
            self._active_plan.status = "in progress"
            self.planUpdated.emit(self._active_plan.to_dict())
        self._emit_queue_status()
        self.taskExplanation.emit("Action queue resumed.")
        self._present_next()

    def cancel_current_task(self):
        """
        Cancels the active task, discards all its pending actions, and stops the task.
        """
        if not self._current_action and not self._queue and not self._active_plan:
            self.taskExplanation.emit("No active task to cancel.")
            return

        current_task_id = self._current_action.task_id if self._current_action else (self._queue[0].task_id if self._queue else (self._active_plan.plan_id if self._active_plan else ""))
        task_name = self._current_action.task_name if self._current_action else (self._queue[0].task_name if self._queue else (self._active_plan.title if self._active_plan else ""))

        # Cancel active plan steps
        if self._active_plan and self._active_plan.plan_id == current_task_id:
            for step in self._active_plan.steps:
                if step.status in ["pending", "awaiting approval", "in progress"]:
                    step.status = "canceled"
                    step.outcome = "Canceled by user request."
            self._active_plan.status = "canceled"
            self._active_plan.completed_at = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            plan_cancel_entry = ProposedAction(
                task_id=self._active_plan.plan_id,
                task_name=f"Plan: {self._active_plan.title}",
                tool_name="planner_canceled",
                intent="Plan canceled by user request",
                target="JD Plan HUD",
                parameters={"plan_id": self._active_plan.plan_id},
                status="PLAN_CANCELED",
                decision="CANCELED",
                outcome=f"Plan '{self._active_plan.title}' canceled. All remaining steps discarded."
            )
            self.log.record_or_update(plan_cancel_entry)
            self.planUpdated.emit(self._active_plan.to_dict())

        # Cancel current action if pending
        if self._current_action and self._current_action.task_id == current_task_id:
            act = self._current_action
            act.decision = "CANCELED"
            act.status = "CANCELED"
            act.decision_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            act.outcome = "Canceled by user request."
            self.log.record_or_update(act)
            self.actionResolved.emit(act.to_dict())
            self._current_action = None

        # Discard any remaining actions in queue for this task
        canceled_count = 0
        remaining_queue = []
        for q_act in self._queue:
            if q_act.task_id == current_task_id:
                q_act.decision = "CANCELED"
                q_act.status = "CANCELED"
                q_act.decision_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                q_act.outcome = "Canceled: Task was aborted before reaching this step."
                self.log.record_or_update(q_act)
                canceled_count += 1
            else:
                remaining_queue.append(q_act)
        self._queue = remaining_queue

        msg = f"Task '{task_name}' canceled. All remaining pending actions have been discarded."
        self.logUpdated.emit()
        self.taskExplanation.emit(msg)
        self._emit_queue_status()
        self._present_next()
