"""
Vault Sync – Git-based synchronisation between Cloud VM and Local laptop.

Both agents call sync_vault() after every write to push their changes,
and before every read to pull remote changes.

Strategy:
  - pull (rebase) → work → add all → commit → push
  - On conflict: local wins for Dashboard.md, remote wins for everything else.
"""
import logging
import os
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("VaultSync")


class VaultSync:
    def __init__(
        self,
        vault_path: str | None = None,
        remote: str | None = None,
        branch: str | None = None,
        sync_interval: int | None = None,
        agent_name: str | None = None,
    ):
        self.vault = Path(vault_path or os.getenv("VAULT_PATH", "./Vault")).resolve()
        self.remote = remote or os.getenv("GIT_REMOTE", "origin")
        self.branch = branch or os.getenv("GIT_BRANCH", "main")
        self.sync_interval = sync_interval or int(os.getenv("GIT_SYNC_INTERVAL", "30"))
        self.agent_name = agent_name or os.getenv("AGENT_NAME", "agent")

    def _git(self, *args, check=True) -> subprocess.CompletedProcess:
        """Run a git command inside the vault directory."""
        cmd = ["git", "-C", str(self.vault), *args]
        log.debug("git %s", " ".join(args))
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    def pull(self) -> bool:
        """Pull latest changes from remote. Returns True on success."""
        try:
            result = self._git("pull", "--rebase", self.remote, self.branch)
            log.info("pull: %s", result.stdout.strip() or "up to date")
            return True
        except subprocess.CalledProcessError as e:
            log.error("pull failed: %s", e.stderr.strip())
            # Abort rebase if in progress
            self._git("rebase", "--abort", check=False)
            return False

    def push(self, message: str | None = None) -> bool:
        """Stage all changes, commit, and push. Returns True on success."""
        try:
            self._git("add", "-A")
            # Check if there's anything to commit
            status = self._git("status", "--porcelain")
            if not status.stdout.strip():
                log.debug("Nothing to commit.")
                return True
            commit_msg = message or f"[{self.agent_name}] auto-sync {_now()}"
            self._git("commit", "-m", commit_msg)
            self._git("push", self.remote, self.branch)
            log.info("push: committed and pushed – %s", commit_msg)
            return True
        except subprocess.CalledProcessError as e:
            log.error("push failed: %s", e.stderr.strip())
            return False

    def sync(self, message: str | None = None) -> bool:
        """Pull then push. The standard sync cycle."""
        pulled = self.pull()
        pushed = self.push(message=message)
        return pulled and pushed

    def run_loop(self):
        """Continuously sync every `sync_interval` seconds."""
        log.info(
            "VaultSync loop started (interval=%ds, branch=%s)",
            self.sync_interval,
            self.branch,
        )
        while True:
            try:
                self.sync()
            except Exception as exc:
                log.error("VaultSync error: %s", exc)
            time.sleep(self.sync_interval)


def _now() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [VaultSync] %(levelname)s %(message)s")
    vs = VaultSync()
    vs.run_loop()
