"""
Audit Logger + Error Recovery – Gold Tier.

Provides:
  - Structured JSONL audit logging for all agent actions
  - Error recovery decorator with configurable retries + fallback
  - Weekly audit report generator
"""
import functools
import json
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "./GoldTier/logs/audit.jsonl"))
ERROR_LOG_PATH = Path(os.getenv("ERROR_LOG_PATH", "./GoldTier/logs/errors.jsonl"))


def _write_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


class AuditLogger:
    """Structured audit logger for all agent actions."""

    def __init__(self, log_path: Path | None = None, agent_name: str = "GoldTier"):
        self.log_path = log_path or AUDIT_LOG_PATH
        self.agent_name = agent_name

    def log(
        self,
        action: str,
        status: str,                  # 'success' | 'failure' | 'pending' | 'skipped'
        details: Any = None,
        error: str | None = None,
        duration_ms: float | None = None,
    ):
        record = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "action": action,
            "status": status,
            "details": details,
            "error": error,
            "duration_ms": duration_ms,
        }
        _write_jsonl(self.log_path, record)
        level = logging.ERROR if status == "failure" else logging.INFO
        log.log(level, "[%s] %s → %s", self.agent_name, action, status)

    def read_recent(self, hours: int = 168) -> list[dict]:
        """Read audit records from the last N hours (default 168 = 1 week)."""
        if not self.log_path.exists():
            return []
        cutoff = datetime.now() - timedelta(hours=hours)
        records = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    ts = datetime.fromisoformat(r["timestamp"])
                    if ts >= cutoff:
                        records.append(r)
                except Exception:
                    pass
        return records

    def weekly_summary(self) -> dict:
        """Generate a summary dict of the past week's activity."""
        records = self.read_recent(hours=168)
        total = len(records)
        by_status: dict[str, int] = {}
        by_action: dict[str, int] = {}
        errors = []
        for r in records:
            by_status[r.get("status", "unknown")] = by_status.get(r.get("status", "unknown"), 0) + 1
            by_action[r.get("action", "unknown")] = by_action.get(r.get("action", "unknown"), 0) + 1
            if r.get("status") == "failure":
                errors.append(r)
        return {
            "period": "last 7 days",
            "generated": datetime.now().isoformat(),
            "total_actions": total,
            "by_status": by_status,
            "top_actions": sorted(by_action.items(), key=lambda x: -x[1])[:10],
            "error_count": len(errors),
            "recent_errors": errors[-5:],
        }


def with_recovery(
    retries: int = 3,
    backoff: float = 2.0,
    fallback: Optional[Callable] = None,
    audit_logger: Optional[AuditLogger] = None,
):
    """
    Decorator: retry on failure with exponential backoff and optional fallback.

    Args:
        retries:       Number of retry attempts.
        backoff:       Base seconds between retries (doubles each attempt).
        fallback:      Optional callable(exception) → result on final failure.
        audit_logger:  If provided, logs success/failure to audit trail.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            action = func.__qualname__
            last_exc = None
            start = time.time()
            for attempt in range(1, retries + 1):
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start) * 1000
                    if audit_logger:
                        audit_logger.log(action, "success", duration_ms=duration)
                    return result
                except Exception as exc:
                    last_exc = exc
                    duration = (time.time() - start) * 1000
                    log.warning(
                        "[%s] attempt %d/%d failed: %s",
                        action, attempt, retries, exc
                    )
                    if attempt < retries:
                        sleep_time = backoff ** attempt
                        time.sleep(sleep_time)

            # All retries exhausted
            error_str = traceback.format_exc()
            if audit_logger:
                audit_logger.log(action, "failure", error=error_str)

            _write_jsonl(ERROR_LOG_PATH, {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "error": str(last_exc),
                "traceback": error_str,
            })

            if fallback:
                log.info("[%s] running fallback after %d failures", action, retries)
                return fallback(last_exc)

            raise last_exc

        return wrapper
    return decorator
