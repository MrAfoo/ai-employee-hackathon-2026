"""
Vault Skill – Read/write Markdown notes in the Obsidian vault.
"""
import os
import re
from datetime import datetime
from pathlib import Path


class VaultSkill:
    """
    Provides read/write access to the Obsidian Markdown vault.

    Supported folders: Inbox, Needs_Action, Done
    """

    FOLDERS = ["Inbox", "Needs_Action", "Done"]

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path).expanduser().resolve()
        self._ensure_structure()

    def _ensure_structure(self):
        """Make sure Inbox / Needs_Action / Done exist."""
        for folder in self.FOLDERS:
            (self.vault / folder).mkdir(parents=True, exist_ok=True)

    def describe(self) -> str:
        return (
            "VaultSkill: read/write Markdown notes inside the Obsidian vault. "
            "Supports Inbox, Needs_Action, and Done folders."
        )

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def write_note(
        self,
        folder: str,
        title: str,
        body: str,
        tags: list[str] | None = None,
    ) -> Path:
        """
        Write a new Markdown note to *folder*.

        Args:
            folder: One of 'Inbox', 'Needs_Action', 'Done'.
            title:  Human-readable title (used as filename stem).
            body:   Markdown body text.
            tags:   Optional list of Obsidian tags.

        Returns:
            Path to the created file.
        """
        if folder not in self.FOLDERS:
            raise ValueError(f"folder must be one of {self.FOLDERS}")

        safe_title = re.sub(r"[^\w\- ]", "", title).strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_title}.md"
        filepath = self.vault / folder / filename

        tag_str = ""
        if tags:
            tag_str = "\ntags: [" + ", ".join(tags) + "]"

        note = f"""---
title: {title}
created: {datetime.now().isoformat()}{tag_str}
---

# {title}

{body}
"""
        filepath.write_text(note, encoding="utf-8")
        return filepath

    def move_note(self, note_path: Path | str, target_folder: str) -> Path:
        """
        Move a note from its current folder to *target_folder*.
        """
        note_path = Path(note_path)
        if target_folder not in self.FOLDERS:
            raise ValueError(f"target_folder must be one of {self.FOLDERS}")
        dest = self.vault / target_folder / note_path.name
        note_path.rename(dest)
        return dest

    def update_dashboard(self, agent_name: str, status: str, last_run: str | None = None):
        """
        Update the Dashboard.md agent status table row for *agent_name*.
        """
        dashboard = self.vault / "Dashboard.md"
        if not dashboard.exists():
            return
        content = dashboard.read_text(encoding="utf-8")
        last_run_str = last_run or datetime.now().strftime("%Y-%m-%d %H:%M")
        pattern = rf"(\| {re.escape(agent_name)} \|)[^|]+\|[^|]+\|"
        replacement = rf"\1 {status} | {last_run_str} |"
        new_content = re.sub(pattern, replacement, content)
        # Also update the timestamp header
        new_content = re.sub(
            r"> Last updated: .*",
            f"> Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            new_content,
        )
        dashboard.write_text(new_content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def list_notes(self, folder: str) -> list[dict]:
        """
        List all notes in *folder* with metadata.
        """
        if folder not in self.FOLDERS:
            raise ValueError(f"folder must be one of {self.FOLDERS}")
        folder_path = self.vault / folder
        notes = []
        for f in sorted(folder_path.glob("*.md")):
            notes.append(
                {
                    "path": str(f),
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
            )
        return notes

    def read_note(self, note_path: Path | str) -> str:
        """Return the full text of a note."""
        return Path(note_path).read_text(encoding="utf-8")

    def run(self, action: str, **kwargs):
        """
        Dispatch method for skill runners.

        Actions: write_note | move_note | list_notes | read_note | update_dashboard
        """
        method = getattr(self, action, None)
        if method is None:
            raise ValueError(f"Unknown VaultSkill action: {action}")
        return method(**kwargs)
