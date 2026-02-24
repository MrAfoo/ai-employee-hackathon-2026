"""
Weekly CEO Briefing Generator – Gold Tier.

Combines data from:
  - Odoo P&L report
  - Vault audit trail (Inbox/Needs_Action/Done counts)
  - MCP audit log (action success/failure rates)
  - Agent activity summary

Generates a CEO_Briefing_YYYY-WW.md in the vault and optionally emails it.

Run:  python briefing/ceo_briefing.py
      python briefing/ceo_briefing.py --email ceo@company.com
"""
import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CEOBriefing] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CEO_PROMPT = """\
You are an AI Chief of Staff preparing a concise weekly executive briefing for the CEO.

Today: {date}
Week: {week}

You have been given the following data:

## Accounting (Odoo P&L)
{pl_data}

## Agent Activity This Week
{agent_summary}

## Inbox / Action Items
{inbox_summary}

## Recent Errors / Issues
{error_summary}

Write a professional, structured CEO briefing in Markdown with these sections:
1. ## Executive Summary (3-5 bullet points, the most important things this week)
2. ## Financial Snapshot (key P&L numbers, trends)
3. ## Operations & Agent Performance (what the AI agents did, success rates)
4. ## Action Items for CEO (decisions needed, approvals required)
5. ## Opportunities & Risks
6. ## Next Week Outlook

Keep it tight — a CEO should be able to read it in under 5 minutes.
Use tables where helpful. Use ✅ ⚠️ ❌ emojis for quick status scanning.
"""


def _get_pl_data() -> str:
    """Fetch P&L from Odoo MCP server."""
    try:
        import requests
        odoo_url = os.getenv("ODOO_MCP_URL", "http://localhost:8004")
        resp = requests.get(f"{odoo_url}/report/profit_loss", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return (
            f"- Total Revenue: ${data.get('total_revenue', 0):,.2f}\n"
            f"- Total Expenses: ${data.get('total_expenses', 0):,.2f}\n"
            f"- Net Profit: ${data.get('net_profit', 0):,.2f}\n"
        )
    except Exception as exc:
        log.warning("Could not fetch Odoo P&L: %s", exc)
        return "_Odoo P&L unavailable – check Odoo MCP server._"


def _get_agent_summary() -> str:
    """Read the orchestrator audit log for weekly activity."""
    audit_path = Path(os.getenv("AUDIT_LOG_PATH", "./GoldTier/logs/audit.jsonl"))
    if not audit_path.exists():
        return "_No audit log found._"
    records = []
    try:
        with audit_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line.strip()))
                except Exception:
                    pass
    except Exception:
        return "_Could not read audit log._"

    total = len(records)
    success = sum(1 for r in records if r.get("status") == "success")
    failure = sum(1 for r in records if r.get("status") == "failure")
    success_rate = (success / total * 100) if total else 0

    action_counts: dict[str, int] = {}
    for r in records:
        a = r.get("action", "unknown")
        action_counts[a] = action_counts.get(a, 0) + 1

    top = sorted(action_counts.items(), key=lambda x: -x[1])[:5]
    top_str = "\n".join(f"  - {a}: {c} times" for a, c in top)
    return (
        f"- Total actions: {total}\n"
        f"- Success: {success} ({success_rate:.1f}%)\n"
        f"- Failures: {failure}\n"
        f"- Top actions:\n{top_str}"
    )


def _get_inbox_summary(vault_path: str) -> str:
    """Count notes in each vault folder."""
    vault = Path(vault_path)
    summary = []
    for folder in ["Inbox", "Needs_Action", "Done"]:
        fp = vault / folder
        count = len(list(fp.glob("*.md"))) if fp.exists() else 0
        summary.append(f"- {folder}: {count} notes")
    return "\n".join(summary)


def _get_error_summary() -> str:
    """Read recent errors from error log."""
    error_path = Path(os.getenv("ERROR_LOG_PATH", "./GoldTier/logs/errors.jsonl"))
    if not error_path.exists():
        return "_No errors logged this week. ✅_"
    errors = []
    try:
        with error_path.open("r", encoding="utf-8") as f:
            errors = [json.loads(line.strip()) for line in f if line.strip()]
    except Exception:
        return "_Could not read error log._"
    if not errors:
        return "_No errors logged this week. ✅_"
    recent = errors[-5:]
    lines = [f"- [{e.get('timestamp', '?')}] {e.get('action', '?')}: {e.get('error', '?')}" for e in recent]
    return f"Total errors: {len(errors)}\nRecent:\n" + "\n".join(lines)


def generate_briefing(vault_path: str, model: str | None = None) -> str:
    """Generate the CEO briefing document and write it to the vault."""
    model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    now = datetime.now()
    week_str = now.strftime("W%V-%Y")

    prompt = CEO_PROMPT.format(
        date=now.strftime("%Y-%m-%d %A"),
        week=week_str,
        pl_data=_get_pl_data(),
        agent_summary=_get_agent_summary(),
        inbox_summary=_get_inbox_summary(vault_path),
        error_summary=_get_error_summary(),
    )

    log.info("Generating CEO briefing with %s...", model)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    message = client.chat.completions.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    briefing_text = message.choices[0].message.content

    header = f"---\ngenerated: {now.isoformat()}\nweek: {week_str}\ntype: ceo_briefing\n---\n\n"
    full_doc = header + briefing_text

    # Write to vault
    vault = Path(vault_path)
    briefing_file = vault / f"CEO_Briefing_{week_str}.md"
    briefing_file.write_text(full_doc, encoding="utf-8")
    log.info("CEO briefing written: %s", briefing_file)
    return full_doc


def main():
    parser = argparse.ArgumentParser(description="Weekly CEO Briefing Generator")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./BronzeTier"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--email", default=None, help="Email address to send briefing to")
    args = parser.parse_args()

    briefing = generate_briefing(args.vault, args.model)

    if args.email:
        try:
            import requests
            email_url = os.getenv("EMAIL_MCP_URL", "http://localhost:8001")
            week_str = datetime.now().strftime("W%V-%Y")
            resp = requests.post(f"{email_url}/send_email", json={
                "to": args.email,
                "subject": f"Weekly CEO Briefing – {week_str}",
                "body": briefing,
                "require_approval": True,
            }, timeout=10)
            resp.raise_for_status()
            log.info("Briefing queued for email delivery: %s", resp.json())
        except Exception as exc:
            log.error("Failed to email briefing: %s", exc)

    print(briefing)


if __name__ == "__main__":
    main()
