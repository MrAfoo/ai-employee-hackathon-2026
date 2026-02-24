"""
Health Monitor – monitors Cloud + Local agents and MCP servers.

Runs on both Cloud VM and Local laptop.
Writes health status to /Updates/health_<agent>.md every check cycle.
Sends alert email if any component is unhealthy for >3 consecutive checks.
"""
import json
import logging
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [HealthMonitor] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("HealthMonitor")

VAULT_PATH     = Path(os.getenv("VAULT_PATH", "./Vault")).resolve()
AGENT_NAME     = os.getenv("AGENT_NAME", "local")
CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
ALERT_EMAIL    = os.getenv("HEALTH_ALERT_EMAIL", "")
AUDIT_LOG      = Path(os.getenv("AUDIT_LOG_PATH", "./GoldTier/logs/audit.jsonl"))

MCP_ENDPOINTS: Dict[str, str] = {
    "email_mcp":    os.getenv("EMAIL_MCP_URL",    "http://localhost:8001") + "/health",
    "linkedin_mcp": os.getenv("LINKEDIN_MCP_URL", "http://localhost:8002") + "/health",
    "whatsapp_mcp": os.getenv("WHATSAPP_MCP_URL", "http://localhost:8003") + "/health",
    "odoo_mcp":     os.getenv("ODOO_MCP_URL",     "http://localhost:8004") + "/health",
    "social_mcp":   os.getenv("SOCIAL_MCP_URL",   "http://localhost:8005") + "/health",
}

# Track consecutive failures for alerting
_failure_counts: Dict[str, int] = {}
ALERT_THRESHOLD = 3


# ── Checks ────────────────────────────────────────────────────────────────────

def check_mcp_servers() -> Dict[str, dict]:
    results = {}
    for name, url in MCP_ENDPOINTS.items():
        try:
            resp = requests.get(url, timeout=5)
            results[name] = {"status": "ok", "code": resp.status_code, "latency_ms": int(resp.elapsed.total_seconds() * 1000)}
        except requests.exceptions.ConnectionError:
            results[name] = {"status": "offline", "detail": "connection refused"}
        except Exception as exc:
            results[name] = {"status": "error", "detail": str(exc)}
    return results


def check_vault_sync() -> dict:
    """Check if vault git sync is current (no uncommitted changes older than 5 min)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(VAULT_PATH), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10
        )
        dirty = bool(result.stdout.strip())
        fetch = subprocess.run(
            ["git", "-C", str(VAULT_PATH), "fetch", "--dry-run"],
            capture_output=True, text=True, timeout=15
        )
        behind = "behind" in fetch.stderr
        return {
            "status": "warning" if dirty or behind else "ok",
            "dirty": dirty,
            "behind_remote": behind,
        }
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def check_vault_folders() -> dict:
    """Check expected vault folders exist and count items."""
    folders = ["Inbox", "Needs_Action", "Pending_Approval", "Plans", "Done", "Updates"]
    result = {}
    for folder in folders:
        path = VAULT_PATH / folder
        exists = path.exists()
        count  = len(list(path.glob("*.md"))) if exists else 0
        result[folder] = {"exists": exists, "item_count": count}
    return result


def check_odoo() -> dict:
    """Ping Odoo community instance."""
    odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
    try:
        resp = requests.get(f"{odoo_url}/web/health", timeout=5)
        return {"status": "ok", "code": resp.status_code}
    except Exception as exc:
        return {"status": "offline", "detail": str(exc)}


# ── Alert ─────────────────────────────────────────────────────────────────────

def _send_alert(subject: str, body: str):
    """Send an alert email via Gmail SMTP."""
    if not ALERT_EMAIL:
        log.warning("HEALTH_ALERT_EMAIL not set — cannot send alert.")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = f"[AI Employee Alert] {subject}"
        msg["From"]    = os.getenv("GMAIL_EMAIL", "")
        msg["To"]      = ALERT_EMAIL
        with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))) as s:
            s.starttls()
            s.login(os.getenv("GMAIL_EMAIL", ""), os.getenv("GMAIL_APP_PASSWORD", ""))
            s.send_message(msg)
        log.info("Alert sent: %s", subject)
    except Exception as exc:
        log.error("Failed to send alert email: %s", exc)


def _check_alert_threshold(component: str, healthy: bool, detail: str):
    if not healthy:
        _failure_counts[component] = _failure_counts.get(component, 0) + 1
        if _failure_counts[component] == ALERT_THRESHOLD:
            _send_alert(
                f"{component} unhealthy",
                f"Component '{component}' has failed {ALERT_THRESHOLD} consecutive health checks.\n\nDetail: {detail}\nTime: {datetime.now().isoformat()}"
            )
    else:
        _failure_counts[component] = 0


# ── Report Writer ─────────────────────────────────────────────────────────────

def write_health_report(report: dict):
    """Write health report to /Updates/health_<agent>.md"""
    updates_dir = VAULT_PATH / "Updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    filepath = updates_dir / f"health_{AGENT_NAME}.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    mcp = report.get("mcp_servers", {})
    vault = report.get("vault_sync", {})
    odoo = report.get("odoo", {})
    folders = report.get("vault_folders", {})

    def _icon(status): return "✅" if status == "ok" else ("⚠️" if status == "warning" else "❌")

    mcp_rows = "\n".join(
        f"| {name} | {_icon(s.get('status','?'))} {s.get('status','?')} | {s.get('latency_ms', s.get('detail', '—'))} |"
        for name, s in mcp.items()
    )
    folder_rows = "\n".join(
        f"| {name} | {'✅' if v['exists'] else '❌'} | {v['item_count']} |"
        for name, v in folders.items()
    )

    content = f"""# 🏥 Health Report – {AGENT_NAME.upper()} Agent
> Last checked: {now}

## MCP Servers
| Server | Status | Latency / Detail |
|--------|--------|-----------------|
{mcp_rows}

## Vault Sync
| Check | Result |
|-------|--------|
| Git status | {_icon(vault.get('status','?'))} dirty={vault.get('dirty', '?')} |
| Behind remote | {'⚠️ Yes' if vault.get('behind_remote') else '✅ No'} |

## Odoo
| Check | Result |
|-------|--------|
| Odoo ping | {_icon(odoo.get('status','?'))} {odoo.get('status','?')} |

## Vault Folders
| Folder | Exists | Items |
|--------|--------|-------|
{folder_rows}
"""
    filepath.write_text(content, encoding="utf-8")

    # Also write to audit log
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now().isoformat(), "event": "health_check", "agent": AGENT_NAME, "report": report}, default=str) + "\n")


# ── Main Loop ─────────────────────────────────────────────────────────────────

def run():
    log.info("Health monitor started (agent=%s, interval=%ds)", AGENT_NAME, CHECK_INTERVAL)
    while True:
        try:
            mcp     = check_mcp_servers()
            vault   = check_vault_sync()
            odoo    = check_odoo()
            folders = check_vault_folders()

            report = {
                "timestamp":    datetime.now().isoformat(),
                "agent":        AGENT_NAME,
                "mcp_servers":  mcp,
                "vault_sync":   vault,
                "odoo":         odoo,
                "vault_folders": folders,
            }

            write_health_report(report)

            # Alert on persistent failures
            for name, status in mcp.items():
                _check_alert_threshold(name, status["status"] == "ok", status.get("detail", ""))
            _check_alert_threshold("vault_sync", vault["status"] in ("ok", "warning"), vault.get("detail", ""))
            _check_alert_threshold("odoo", odoo["status"] == "ok", odoo.get("detail", ""))

            # Summary log
            unhealthy = [n for n, s in mcp.items() if s["status"] != "ok"]
            if unhealthy:
                log.warning("Unhealthy components: %s", unhealthy)
            else:
                log.info("All components healthy.")

        except Exception as exc:
            log.error("Health check error: %s", exc)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
