"""
base_watcher.py – Template for all watchers.

All Watchers inherit from BaseWatcher and implement:
  - check_for_updates() -> list   : return list of new items to process
  - create_action_file(item) -> Path : create .md file in Needs_Action folder
"""
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder. Return the path created."""
        pass

    def run(self):
        """Main watcher loop – poll indefinitely at check_interval seconds."""
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        path = self.create_action_file(item)
                        self.logger.info(f'Action file created: {path}')
                    except Exception as e:
                        self.logger.error(f'Failed to create action file for item {item}: {e}')
            except Exception as e:
                self.logger.error(f'Error in check_for_updates: {e}')
            time.sleep(self.check_interval)
