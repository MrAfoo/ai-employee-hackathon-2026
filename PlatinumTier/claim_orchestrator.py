"""
Claim Orchestrator – implements the claim-by-move pattern.

Agents atomically claim tasks by moving files:
  /Needs_Action/task.md  →  /In_Progress/<agent>/task.md

Only one agent can move the file — the other gets FileNotFoundError and skips.
This is the distributed locking mechanism for the Platinum Tier.
"""
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("ClaimOrchestrator")


class ClaimOrchestrator:
    """
    Watches /Needs_Action and claims tasks for this agent via atomic file move.
    Calls a handler function for each claimed task.
    On completion, moves task to /Done. On failure, moves to /Needs_Action (retry).
    """

    def __init__(
        self,
        vault_path: str | None = None,
        agent_name: str | None = None,
        poll_interval: int = 10,
    ):
        self.vault = Path(vault_path or os.getenv("VAULT_PATH", "./Vault")).resolve()
        self.agent_name = agent_name or os.getenv("AGENT_NAME", "local")
        self.poll_interval = poll_interval

        # Folder paths
        self.needs_action = self.vault / "Needs_Action"
        self.in_progress   = self.vault / "In_Progress" / self.agent_name
        self.done          = self.vault / "Done"
        self.updates       = self.vault / "Updates"

        # Ensure folders exist
        for folder in [self.needs_action, self.in_progress, self.done, self.updates]:
            folder.mkdir(parents=True, exist_ok=True)

        self._handlers: dict[str, Callable] = {}

    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler function for a given task type (frontmatter 'type' field)."""
        self._handlers[task_type] = handler
        log.info("Registered handler for task type: %s", task_type)

    def _claim(self, filepath: Path) -> Optional[Path]:
        """Atomically claim a file. Returns new path or None if already claimed."""
        dest = self.in_progress / filepath.name
        try:
            filepath.rename(dest)
            log.info("Claimed: %s → In_Progress/%s/%s", filepath.name, self.agent_name, filepath.name)
            return dest
        except (FileNotFoundError, PermissionError):
            # Another agent already claimed it
            return None

    def _complete(self, claimed_path: Path):
        """Move completed task to /Done and write an update note."""
        dest = self.done / claimed_path.name
        shutil.move(str(claimed_path), dest)
        self._write_update(claimed_path.name, "completed")
        log.info("Completed: %s → Done/", claimed_path.name)

    def _fail(self, claimed_path: Path, error: str):
        """On failure, move back to /Needs_Action for retry and log the error."""
        dest = self.needs_action / claimed_path.name
        shutil.move(str(claimed_path), dest)
        self._write_update(claimed_path.name, f"failed: {error}")
        log.error("Failed: %s – moved back to Needs_Action. Error: %s", claimed_path.name, error)

    def _write_update(self, task_name: str, status: str):
        """Write a status update note to /Updates."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        update_file = self.updates / f"{ts}_{self.agent_name}_{task_name}"
        update_file.write_text(
            f"---\nagent: {self.agent_name}\ntask: {task_name}\nstatus: {status}\ntimestamp: {datetime.now().isoformat()}\n---\n\n"
            f"**Agent:** `{self.agent_name}`  \n**Task:** `{task_name}`  \n**Status:** {status}  \n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )

    def _get_task_type(self, filepath: Path) -> str:
        """Read YAML frontmatter 'type' field from a markdown file."""
        try:
            content = filepath.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("type:"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return "unknown"

    def process_one(self) -> bool:
        """Try to claim and process one task. Returns True if a task was processed."""
        tasks = sorted(self.needs_action.glob("*.md"))
        for task_file in tasks:
            claimed = self._claim(task_file)
            if claimed is None:
                continue  # Already taken by another agent

            task_type = self._get_task_type(claimed)
            handler = self._handlers.get(task_type) or self._handlers.get("default")

            if handler is None:
                log.warning("No handler for task type '%s', skipping: %s", task_type, claimed.name)
                self._fail(claimed, f"no handler for type '{task_type}'")
                return True

            try:
                log.info("Processing [%s]: %s", task_type, claimed.name)
                handler(claimed)
                self._complete(claimed)
            except Exception as exc:
                self._fail(claimed, str(exc))
            return True

        return False  # Nothing to process

    def run(self):
        """Main loop — continuously poll /Needs_Action for tasks."""
        log.info(
            "ClaimOrchestrator started (agent=%s, poll=%ds)",
            self.agent_name,
            self.poll_interval,
        )
        while True:
            try:
                self.process_one()
            except Exception as exc:
                log.error("ClaimOrchestrator error: %s", exc)
            time.sleep(self.poll_interval)
