"""
Human-in-the-Loop Approval Workflow

Provides CLI and programmatic approval gates before sensitive actions
(sending emails, posting to LinkedIn, etc.) are executed.

Usage:
    from reasoning.approval import ApprovalGate

    gate = ApprovalGate()
    if gate.request("Send email to CEO?", payload={"to": "ceo@co.com", ...}):
        # approved — proceed
    else:
        # rejected — abort
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class ApprovalGate:
    """
    Interactive CLI approval gate with optional audit logging.

    In automated environments (CI, headless), set AUTO_APPROVE=true in .env
    to bypass prompts (use with caution).
    """

    def __init__(
        self,
        auto_approve: bool = False,
        audit_log_path: str | None = None,
    ):
        self.auto_approve = auto_approve
        self.audit_log_path = Path(audit_log_path) if audit_log_path else None
        self._history: list[dict] = []

    def _log_decision(self, action: str, payload: Any, approved: bool, reason: str = ""):
        record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "payload": payload,
            "approved": approved,
            "reason": reason,
        }
        self._history.append(record)
        if self.audit_log_path:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.audit_log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        status = "✅ APPROVED" if approved else "❌ REJECTED"
        log.info("[ApprovalGate] %s – %s", status, action)

    def request(
        self,
        action: str,
        payload: Any = None,
        description: str = "",
    ) -> bool:
        """
        Request human approval for an action.

        Args:
            action:      Short name for the action (e.g. 'send_email').
            payload:     Data associated with the action (shown to reviewer).
            description: Human-readable description of what will happen.

        Returns:
            True if approved, False if rejected.
        """
        if self.auto_approve:
            self._log_decision(action, payload, approved=True, reason="AUTO_APPROVE=true")
            return True

        print("\n" + "=" * 60)
        print(f"⚠️  APPROVAL REQUIRED: {action}")
        print("=" * 60)
        if description:
            print(f"Description: {description}")
        if payload:
            print("\nPayload:")
            if isinstance(payload, dict):
                for k, v in payload.items():
                    print(f"  {k}: {v}")
            else:
                print(f"  {payload}")
        print()

        while True:
            choice = input("Approve? [y/n/d(etail)]: ").strip().lower()
            if choice in ("y", "yes"):
                reason = input("Optional note (press Enter to skip): ").strip()
                self._log_decision(action, payload, approved=True, reason=reason or "Approved by operator")
                print("✅ Approved.\n")
                return True
            elif choice in ("n", "no"):
                reason = input("Reason for rejection: ").strip()
                self._log_decision(action, payload, approved=False, reason=reason or "Rejected by operator")
                print("❌ Rejected.\n")
                return False
            elif choice == "d":
                print(json.dumps(payload, indent=2, default=str))
            else:
                print("Please enter y, n, or d.")

    def history(self) -> list[dict]:
        """Return full approval/rejection history for this session."""
        return list(self._history)

    def summary(self) -> dict:
        approved = sum(1 for r in self._history if r["approved"])
        rejected = len(self._history) - approved
        return {"total": len(self._history), "approved": approved, "rejected": rejected}
