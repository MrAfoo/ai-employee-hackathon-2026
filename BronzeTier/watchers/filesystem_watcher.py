"""
filesystem_watcher.py – Drop Folder Watcher (BaseWatcher pattern).

Monitors a drop folder for new files. When a file appears:
  1. Copies it to /Needs_Action as FILE_<name>
  2. Creates a metadata .md file alongside it

Uses the `watchdog` library for cross-platform filesystem events.

Setup:
  Set WATCH_PATH in .env to the folder you want to monitor (your "drop folder").
"""
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

try:
    from base_watcher import BaseWatcher
except ImportError:
    from watchers.base_watcher import BaseWatcher

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [FSWatcher] %(levelname)s %(message)s',
)
log = logging.getLogger(__name__)


class DropFolderHandler(FileSystemEventHandler):
    """
    Handles new files dropped into the watch folder.
    Copies file to /Needs_Action and creates a metadata .md note.
    """

    def __init__(self, vault_path: str):
        super().__init__()
        self.needs_action = Path(vault_path) / 'Needs_Action'
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self._processed: set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        # Ignore hidden files and already-processed items
        if source.name.startswith('.') or str(source) in self._processed:
            return
        self._processed.add(str(source))
        try:
            dest = self.needs_action / f'FILE_{source.name}'
            shutil.copy2(source, dest)
            self.create_metadata(source, dest)
            log.info('File dropped and copied: %s → Needs_Action/', source.name)
        except Exception as e:
            log.error('Error handling dropped file %s: %s', source.name, e)

    def create_metadata(self, source: Path, dest: Path):
        """Create a .md metadata note alongside the copied file."""
        try:
            size = source.stat().st_size
        except OSError:
            size = 0

        meta_path = self.needs_action / f'{dest.stem}.md'
        meta_path.write_text(
            f"""---
type: file_drop
original_name: {source.name}
size: {size}
received: {datetime.now().isoformat()}
status: pending
priority: normal
---

# 📂 New File Drop: {source.name}

**File:** `{source.name}`
**Size:** {size:,} bytes
**Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Copied to:** `Needs_Action/FILE_{source.name}`

## Suggested Actions
- [ ] Review the file content
- [ ] Process or forward as needed
- [ ] Move this note to `/Done` when complete
""",
            encoding='utf-8',
        )


class FilesystemWatcher(BaseWatcher):
    """
    Watches a drop folder for new files using watchdog.
    Implements the BaseWatcher interface.
    """

    def __init__(self, vault_path: str, watch_path: str | None = None):
        super().__init__(vault_path, check_interval=1)
        self.watch_path = Path(
            watch_path or os.getenv('WATCH_PATH', str(Path(vault_path) / 'drop_folder'))
        ).resolve()
        self.watch_path.mkdir(parents=True, exist_ok=True)
        self._handler = DropFolderHandler(vault_path=vault_path)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.watch_path), recursive=False)

    def check_for_updates(self) -> list:
        """watchdog handles events via callbacks — nothing to poll here."""
        return []

    def create_action_file(self, item) -> Path:
        """Not used directly — DropFolderHandler handles file creation."""
        return self.needs_action

    def run(self):
        """Start the watchdog observer (overrides BaseWatcher.run)."""
        log.info('Starting filesystem drop-folder watcher on: %s', self.watch_path)
        self._observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._observer.stop()
            log.info('Filesystem watcher stopped.')
        self._observer.join()


if __name__ == '__main__':
    vault = os.getenv('VAULT_PATH', './BronzeTier')
    watch = os.getenv('WATCH_PATH', './drop_folder')
    watcher = FilesystemWatcher(vault_path=vault, watch_path=watch)
    watcher.run()

