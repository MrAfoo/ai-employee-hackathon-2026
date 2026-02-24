"""
Claude Reasoning Loop – reads vault Inbox notes and generates Plan.md.

How it works:
  1. Reads all notes from Inbox and Needs_Action folders.
  2. Sends them to Claude with a planning prompt.
  3. Claude produces a structured Plan.md with prioritised tasks.
  4. Plan.md is written to the SilverTier folder and also to the vault.

Run once:  python reasoning/reasoning_loop.py
Run loop:  python reasoning/reasoning_loop.py --loop
"""
import argparse
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ReasoningLoop] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PLAN_PROMPT = """\
You are an autonomous executive assistant AI. You have been given a set of notes from the agent's Inbox and Needs_Action folders.

Your job is to:
1. Analyse all notes and identify key themes, urgent items, opportunities, and follow-ups.
2. Produce a structured **Plan.md** document with the following sections:
   - ## 🔴 Urgent (do today)
   - ## 🟡 This Week
   - ## 🟢 Backlog
   - ## 💡 Opportunities
   - ## 📧 Emails to Send
   - ## 📱 Posts to Draft
   - ## 🔁 Next Loop Notes

Each item should be a checkbox `- [ ] Action item` with a brief rationale.

Today's date: {date}

Notes from Inbox and Needs_Action:
---
{notes}
---

Produce ONLY the Plan.md content (valid Markdown). Do not explain or add commentary outside the document.
"""


def _collect_notes(vault_path: Path) -> str:
    """Read all .md notes from Inbox and Needs_Action."""
    sections = []
    for folder in ["Inbox", "Needs_Action"]:
        folder_path = vault_path / folder
        if not folder_path.exists():
            continue
        notes = sorted(folder_path.glob("*.md"))
        for note in notes:
            try:
                text = note.read_text(encoding="utf-8")
                sections.append(f"### [{folder}] {note.name}\n\n{text}\n")
            except Exception as exc:
                log.warning("Could not read %s: %s", note, exc)
    return "\n---\n".join(sections) if sections else "No notes found in Inbox or Needs_Action."


def run_reasoning_loop(vault_path: str, plan_output: str, model: str, max_tokens: int) -> str:
    """
    Run one iteration of the reasoning loop.
    Returns the generated plan text.
    """
    vault = Path(vault_path).expanduser().resolve()
    notes = _collect_notes(vault)

    prompt = PLAN_PROMPT.format(
        date=datetime.now().strftime("%Y-%m-%d %A"),
        notes=notes,
    )

    log.info("Sending %d chars of notes to Groq (%s)...", len(notes), model)
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    message = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    plan_text = message.choices[0].message.content

    # Write Plan.md to output path
    plan_path = Path(plan_output).expanduser()
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    header = f"---\ngenerated: {datetime.now().isoformat()}\nmodel: {model}\n---\n\n"
    plan_path.write_text(header + plan_text, encoding="utf-8")
    log.info("Plan.md written to %s", plan_path)

    # Also write a copy into the vault
    vault_plan = vault / "Plan.md"
    vault_plan.write_text(header + plan_text, encoding="utf-8")
    log.info("Plan.md mirrored to vault: %s", vault_plan)

    return plan_text


def main():
    parser = argparse.ArgumentParser(description="Claude Reasoning Loop")
    parser.add_argument("--loop", action="store_true", help="Run continuously (uses WATCHER_POLL_INTERVAL)")
    parser.add_argument("--vault", default=os.getenv("VAULT_PATH", "./BronzeTier"), help="Vault path")
    parser.add_argument("--output", default=os.getenv("PLAN_OUTPUT_PATH", "./SilverTier/Plan.md"), help="Plan.md output path")
    parser.add_argument("--model", default=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), help="Groq model")
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("REASONING_MAX_TOKENS", "4096")))
    args = parser.parse_args()

    if args.loop:
        interval = int(os.getenv("WATCHER_POLL_INTERVAL", "3600"))
        log.info("Reasoning loop starting (interval=%ds)", interval)
        while True:
            try:
                run_reasoning_loop(args.vault, args.output, args.model, args.max_tokens)
            except Exception as exc:
                log.error("Reasoning loop error: %s", exc)
            time.sleep(interval)
    else:
        plan = run_reasoning_loop(args.vault, args.output, args.model, args.max_tokens)
        print("\n" + "=" * 60)
        print(plan)


if __name__ == "__main__":
    main()
