"""
Multi-MCP Orchestrator – coordinates all MCP servers for the Gold Tier.

Routes Claude tool-call requests to the appropriate MCP server:
  - email       → SilverTier email_mcp_server   :8001
  - linkedin    → SilverTier linkedin_mcp_server :8002
  - odoo        → GoldTier  odoo_mcp_server      :8004
  - social      → GoldTier  social_media_mcp_server :8005

Also handles:
  - Health aggregation across all servers
  - Error recovery with retries and fallback logging
  - Audit trail of all routed actions
"""
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MCPOrchestrator] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MCP_REGISTRY: Dict[str, str] = {
    "email":     os.getenv("EMAIL_MCP_URL",    "http://localhost:8001"),
    "linkedin":  os.getenv("LINKEDIN_MCP_URL", "http://localhost:8002"),
    "whatsapp":  os.getenv("WHATSAPP_MCP_URL", "http://localhost:8003"),
    "odoo":      os.getenv("ODOO_MCP_URL",     "http://localhost:8004"),
    "social":    os.getenv("SOCIAL_MCP_URL",   "http://localhost:8005"),
}

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "./GoldTier/logs/orchestrator_audit.jsonl"))


def _audit(action: str, server: str, endpoint: str, payload: Any, result: Any, success: bool):
    record = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "server": server,
        "endpoint": endpoint,
        "payload": payload,
        "result": result,
        "success": success,
    }
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def call_mcp(
    server: str,
    endpoint: str,
    method: str = "POST",
    payload: Optional[dict] = None,
    retries: int = 3,
    backoff: float = 2.0,
) -> dict:
    """
    Route a call to a registered MCP server with retry logic.

    Args:
        server:   Key in MCP_REGISTRY (e.g. 'email', 'odoo').
        endpoint: Path on that server (e.g. '/send_email').
        method:   HTTP method ('GET' or 'POST').
        payload:  JSON body for POST requests.
        retries:  Number of retry attempts on failure.
        backoff:  Seconds between retries (doubles each attempt).

    Returns:
        Parsed JSON response dict.
    """
    if server not in MCP_REGISTRY:
        raise ValueError(f"Unknown MCP server: '{server}'. Available: {list(MCP_REGISTRY.keys())}")

    base_url = MCP_REGISTRY[server]
    url = f"{base_url}{endpoint}"
    last_exc = None

    for attempt in range(1, retries + 1):
        try:
            if method.upper() == "GET":
                resp = requests.get(url, timeout=30)
            else:
                resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            _audit(f"{method} {endpoint}", server, endpoint, payload, result, success=True)
            log.info("[%s] %s %s → %s", server, method, endpoint, result.get("status", "ok"))
            return result
        except Exception as exc:
            last_exc = exc
            log.warning("Attempt %d/%d failed for %s %s: %s", attempt, retries, server, endpoint, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)

    _audit(f"{method} {endpoint}", server, endpoint, payload, str(last_exc), success=False)
    log.error("All %d attempts failed for %s %s: %s", retries, server, endpoint, last_exc)
    raise RuntimeError(f"MCP call failed after {retries} attempts: {last_exc}")


def health_check_all() -> dict:
    """Check health of all registered MCP servers."""
    results = {}
    for name, base_url in MCP_REGISTRY.items():
        try:
            resp = requests.get(f"{base_url}/health", timeout=5)
            results[name] = {"status": "ok", "code": resp.status_code}
        except Exception as exc:
            results[name] = {"status": "error", "detail": str(exc)}
    return results


def send_email(to: str, subject: str, body: str, require_approval: bool = True) -> dict:
    return call_mcp("email", "/send_email", payload={
        "to": to, "subject": subject, "body": body, "require_approval": require_approval
    })


def post_linkedin(text: str, require_approval: bool = True) -> dict:
    return call_mcp("linkedin", "/post", payload={
        "text": text, "require_approval": require_approval
    })


def post_social(text: str, image_url: str | None = None) -> dict:
    return call_mcp("social", "/post/all", payload={
        "text": text, "image_url": image_url
    })


def create_odoo_invoice(partner_name: str, amount: float, description: str) -> dict:
    return call_mcp("odoo", "/invoice/create", payload={
        "partner_name": partner_name, "amount": amount, "description": description
    })


def get_odoo_profit_loss() -> dict:
    return call_mcp("odoo", "/report/profit_loss", method="GET")


if __name__ == "__main__":
    print("=== MCP Health Check ===")
    health = health_check_all()
    for server, status in health.items():
        icon = "✅" if status["status"] == "ok" else "❌"
        print(f"  {icon} {server}: {status}")
