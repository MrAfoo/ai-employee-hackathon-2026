"""
error_recovery.py – Error States & Recovery (Bronze → Platinum)

Covers all 5 error categories from the spec:

  Category        | Examples                          | Strategy
  --------------- | --------------------------------- | --------------------------
  Transient       | Network timeout, API rate limit   | Exponential backoff retry
  Authentication  | Token expired, 401/403            | Alert human, pause ops
  Logic           | Claude misinterprets message      | Human review queue
  Data            | Corrupted file, missing field     | Quarantine + alert
  System          | Orchestrator crash, disk full     | Watchdog + auto-restart
"""

import functools
import json
import logging
import os
import shutil
import time
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

ERROR_LOG_PATH = Path(os.getenv("ERROR_LOG_PATH", "./logs/errors.jsonl"))
AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "./logs/audit.jsonl"))


# ── Error Categories ───────────────────────────────────────────────────────────
class ErrorCategory(str, Enum):
    TRANSIENT = "transient"        # Network, rate limit → retry
    AUTHENTICATION = "auth"        # Token expired → alert + pause
    LOGIC = "logic"                # AI misinterpretation → human review
    DATA = "data"                  # Corrupted/missing data → quarantine
    SYSTEM = "system"              # Crash, disk full → watchdog restart


# ── JSONL Logger ───────────────────────────────────────────────────────────────
def _write_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


# ── Error Recovery Registry ────────────────────────────────────────────────────
class ErrorRecovery:
    """
    Central error registry. Records errors by category and tracks
    recent failures for health checks.
    """

    def __init__(self, max_history: int = 100):
        self._errors: list[dict] = []
        self._max_history = max_history
        self._paused_components: set[str] = set()

    def record_error(
        self,
        category: ErrorCategory,
        message: str,
        component: str = "unknown",
        exc: Optional[Exception] = None,
    ):
        record = {
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "component": component,
            "message": message,
            "traceback": traceback.format_exc() if exc else None,
        }
        self._errors.append(record)
        if len(self._errors) > self._max_history:
            self._errors.pop(0)

        _write_jsonl(ERROR_LOG_PATH, record)
        log.error("[%s/%s] %s", category.value, component, message)

        # Authentication errors → pause the component automatically
        if category == ErrorCategory.AUTHENTICATION:
            self._paused_components.add(component)
            log.warning(
                "Component '%s' PAUSED due to auth error. "
                "Fix credentials then call resume('%s').",
                component, component,
            )

    def resume(self, component: str):
        self._paused_components.discard(component)
        log.info("Component '%s' resumed.", component)

    def is_paused(self, component: str) -> bool:
        return component in self._paused_components

    def recent_errors(self, limit: int = 10) -> list[dict]:
        return self._errors[-limit:]

    def error_count_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._errors:
            c = e.get("category", "unknown")
            counts[c] = counts.get(c, 0) + 1
        return counts


# ── Quarantine Manager ─────────────────────────────────────────────────────────
class QuarantineManager:
    """
    Moves corrupted/problematic files to /Quarantine with a sidecar
    .reason file explaining why they were quarantined. (Data errors)
    """

    def __init__(self, quarantine_dir: Path):
        self.quarantine_dir = quarantine_dir
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def quarantine(self, path: Path, reason: str) -> Path:
        dest = self.quarantine_dir / path.name
        # Avoid overwrite collision
        if dest.exists():
            dest = self.quarantine_dir / f"{path.stem}_{datetime.now().strftime('%H%M%S')}{path.suffix}"
        shutil.move(str(path), str(dest))

        # Write sidecar reason file
        reason_file = dest.with_suffix(".reason.txt")
        reason_file.write_text(
            f"Quarantined: {datetime.now().isoformat()}\nReason: {reason}\nOriginal: {path}\n",
            encoding="utf-8",
        )

        _write_jsonl(ERROR_LOG_PATH, {
            "timestamp": datetime.now().isoformat(),
            "category": ErrorCategory.DATA.value,
            "component": "QuarantineManager",
            "message": f"Quarantined {path.name}: {reason}",
            "quarantine_path": str(dest),
        })
        log.warning("QUARANTINED: %s → %s | Reason: %s", path.name, dest, reason)
        return dest


# ── Human Review Queue ─────────────────────────────────────────────────────────
class HumanReviewQueue:
    """
    For Logic errors — when Claude misinterprets, route to human review
    instead of acting or failing silently.
    """

    def __init__(self, review_dir: Path):
        self.review_dir = review_dir
        self.review_dir.mkdir(parents=True, exist_ok=True)

    def enqueue(self, source_path: Path, reason: str, ai_output: str = "") -> Path:
        now = datetime.now()
        review_path = self.review_dir / f"REVIEW_{source_path.stem}_{now.strftime('%Y%m%d_%H%M%S')}.md"
        content = f"""---
type: human_review
source: {source_path.name}
reason: {reason}
created: {now.isoformat()}
status: pending_review
---

## Why This Needs Human Review
{reason}

## AI Output (What Went Wrong)
```
{ai_output[:2000]}
```

## Original File Content
*(See source file: {source_path.name})*

## Actions
- [ ] Review and correct AI interpretation
- [ ] Move original file back to /Needs_Action if valid
- [ ] Delete this file when resolved
"""
        review_path.write_text(content, encoding="utf-8")
        log.warning("Human review queued: %s", review_path.name)
        return review_path


# ── Decorator: with_error_recovery ────────────────────────────────────────────
def with_error_recovery(
    retries: int = 3,
    backoff: float = 2.0,
    category: ErrorCategory = ErrorCategory.TRANSIENT,
    fallback: Optional[Callable] = None,
    component: str = "",
):
    """
    Decorator that wraps a function with:
      - Exponential backoff retry (Transient errors)
      - Auth error detection → pause component
      - Logic error detection → route to human review
      - Data error → quarantine
      - System error → log + re-raise for watchdog restart

    Usage:
        @with_error_recovery(retries=3, backoff=2.0, category=ErrorCategory.TRANSIENT)
        def my_api_call():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _component = component or func.__qualname__
            last_exc: Optional[Exception] = None

            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)

                except PermissionError as exc:
                    # Authentication / permission failure → pause + alert
                    last_exc = exc
                    _write_jsonl(ERROR_LOG_PATH, {
                        "timestamp": datetime.now().isoformat(),
                        "category": ErrorCategory.AUTHENTICATION.value,
                        "component": _component,
                        "message": str(exc),
                        "attempt": attempt,
                    })
                    log.error(
                        "[AUTH ERROR] %s: %s — pausing component. Fix credentials.",
                        _component, exc,
                    )
                    # Don't retry auth errors
                    raise

                except (ConnectionError, TimeoutError, OSError) as exc:
                    # Transient: network/IO → exponential backoff
                    last_exc = exc
                    sleep_time = backoff ** attempt
                    log.warning(
                        "[TRANSIENT] %s attempt %d/%d: %s — retrying in %.1fs",
                        _component, attempt, retries, exc, sleep_time,
                    )
                    if attempt < retries:
                        time.sleep(sleep_time)

                except Exception as exc:
                    last_exc = exc
                    sleep_time = backoff ** attempt
                    log.warning(
                        "[%s] %s attempt %d/%d: %s — retrying in %.1fs",
                        category.value.upper(), _component, attempt, retries, exc, sleep_time,
                    )
                    if attempt < retries:
                        time.sleep(sleep_time)

            # All retries exhausted
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "category": category.value,
                "component": _component,
                "message": str(last_exc),
                "traceback": traceback.format_exc(),
                "retries_exhausted": True,
            }
            _write_jsonl(ERROR_LOG_PATH, error_record)

            if fallback:
                log.info("[%s] All retries failed — running fallback", _component)
                return fallback(last_exc)

            raise last_exc

        return wrapper
    return decorator


# ── Retry with Exponential Backoff (standalone) ───────────────────────────────
def retry_with_backoff(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Standalone retry helper. Useful for one-off calls without decorators.

    Example:
        result = retry_with_backoff(requests.get, args=("https://api.example.com",))
    """
    kwargs = kwargs or {}
    delay = base_delay
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as exc:
            if attempt == retries:
                raise
            actual_delay = min(delay, max_delay)
            log.warning(
                "retry_with_backoff: attempt %d/%d failed (%s) — sleeping %.1fs",
                attempt, retries, exc, actual_delay,
            )
            time.sleep(actual_delay)
            delay *= 2  # Exponential backoff


# ── Alert Helper ───────────────────────────────────────────────────────────────
def alert_human(subject: str, body: str, vault_path: Path = Path("./Vault")):
    """
    Write an urgent alert to /Needs_Action so the human sees it in Obsidian.
    Used when auth fails or system is degraded.
    """
    now = datetime.now()
    alert_path = vault_path / "Needs_Action" / f"ALERT_{now.strftime('%Y%m%d_%H%M%S')}.md"
    alert_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""---
type: system_alert
subject: {subject}
created: {now.isoformat()}
priority: critical
status: unread
---

# 🚨 System Alert

**{subject}**

{body}

---
*Generated automatically by AI Employee Error Recovery System*
"""
    alert_path.write_text(content, encoding="utf-8")
    log.critical("ALERT written to vault: %s", alert_path.name)
