"""
Watcher Skill – wraps Gmail and filesystem watchers as a unified skill.
"""
import threading
from pathlib import Path


class WatcherSkill:
    """
    Manages watcher threads for Gmail IMAP and filesystem events.
    Writes triggered notes directly into the vault via VaultSkill.
    """

    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self._threads: dict[str, threading.Thread] = {}

    def describe(self) -> str:
        return (
            "WatcherSkill: start/stop Gmail IMAP and filesystem watchers. "
            "Writes notes into vault Inbox when events are detected."
        )

    def start(self, watcher_type: str, **kwargs):
        """
        Start a watcher in a background thread.

        Args:
            watcher_type: 'gmail' or 'filesystem'
            **kwargs: passed to the underlying watcher run() function.
        """
        if watcher_type == "gmail":
            from ..watchers.gmail_watcher import GmailWatcher
            w = GmailWatcher(vault_path=self.vault_path, **kwargs)
        elif watcher_type == "filesystem":
            from ..watchers.filesystem_watcher import FilesystemWatcher
            w = FilesystemWatcher(vault_path=self.vault_path, **kwargs)
        else:
            raise ValueError(f"Unknown watcher type: {watcher_type}")

        t = threading.Thread(target=w.run, daemon=True, name=f"{watcher_type}-watcher")
        t.start()
        self._threads[watcher_type] = t
        return f"{watcher_type} watcher started (thread: {t.name})"

    def status(self) -> dict:
        """Return running status of all watcher threads."""
        return {
            name: "running" if t.is_alive() else "stopped"
            for name, t in self._threads.items()
        }

    def run(self, action: str, **kwargs):
        """Dispatch method for skill runners."""
        method = getattr(self, action, None)
        if method is None:
            raise ValueError(f"Unknown WatcherSkill action: {action}")
        return method(**kwargs)
