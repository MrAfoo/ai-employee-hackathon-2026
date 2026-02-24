"""
Ralph Wiggum Loop – Autonomous Multi-Step Task Completion.

Named after Ralph Wiggum's relentless optimism: the agent keeps trying
until the task is done or a maximum iteration limit is reached.

How it works:
  1. Claude receives a task description + available tools (MCP servers).
  2. Claude decides which tool to call and with what arguments.
  3. The orchestrator executes the tool call via the MCP registry.
  4. The result is fed back to Claude as context.
  5. Claude either calls another tool OR declares the task complete.
  6. Loop repeats until done or max_iterations reached.

Usage:
    python ralph_wiggum_loop.py --task "Draft and send a weekly summary email to the team"
"""
import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [RalphWiggum] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Tool definitions exposed to Claude ────────────────────────────────────────

TOOLS = [
    {
        "name": "send_email",
        "description": "Send an email via the Email MCP server.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "require_approval": {"type": "boolean", "default": True},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "post_linkedin",
        "description": "Publish a post on LinkedIn.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Post content (max 3000 chars)"},
                "require_approval": {"type": "boolean", "default": True},
            },
            "required": ["text"],
        },
    },
    {
        "name": "post_social_all",
        "description": "Broadcast a post to Twitter/X, Facebook, and Instagram simultaneously.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "image_url": {"type": "string", "description": "Optional image URL for Instagram/Facebook"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "get_odoo_report",
        "description": "Retrieve the current Profit & Loss summary from Odoo accounting.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_odoo_invoice",
        "description": "Create a draft invoice in Odoo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "partner_name": {"type": "string"},
                "amount": {"type": "number"},
                "description": {"type": "string"},
            },
            "required": ["partner_name", "amount", "description"],
        },
    },
    {
        "name": "write_vault_note",
        "description": "Write a Markdown note to the Obsidian vault.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "enum": ["Inbox", "Needs_Action", "Done"]},
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["folder", "title", "body"],
        },
    },
    {
        "name": "task_complete",
        "description": "Signal that the task is fully complete. Provide a summary of what was done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "What was accomplished"},
            },
            "required": ["summary"],
        },
    },
]


# ── Tool executor ──────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> Any:
    """Execute a tool call by routing to the appropriate MCP server or skill."""
    from orchestrator.multi_mcp_orchestrator import (
        send_email, post_linkedin, post_social, create_odoo_invoice, get_odoo_profit_loss
    )
    from pathlib import Path as _Path
    import sys
    sys.path.insert(0, str(_Path(__file__).parent.parent.parent))

    if tool_name == "send_email":
        return send_email(**tool_input)
    elif tool_name == "post_linkedin":
        return post_linkedin(**tool_input)
    elif tool_name == "post_social_all":
        return post_social(tool_input["text"], tool_input.get("image_url"))
    elif tool_name == "get_odoo_report":
        return get_odoo_profit_loss()
    elif tool_name == "create_odoo_invoice":
        return create_odoo_invoice(**tool_input)
    elif tool_name == "write_vault_note":
        vault_path = Path(os.getenv("VAULT_PATH", "./BronzeTier"))
        inbox = vault_path / tool_input["folder"]
        inbox.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in tool_input["title"])[:50]
        p = inbox / f"{ts}_{safe}.md"
        p.write_text(f"# {tool_input['title']}\n\n{tool_input['body']}\n", encoding="utf-8")
        return {"written": str(p)}
    elif tool_name == "task_complete":
        return {"done": True, "summary": tool_input["summary"]}
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


# ── Ralph Wiggum Loop ──────────────────────────────────────────────────────────

def ralph_wiggum_loop(
    task: str,
    model: str | None = None,
    max_iterations: int = 10,
    verbose: bool = True,
) -> dict:
    """
    Autonomous multi-step task completion loop.

    Args:
        task:           Natural language task description.
        model:          Claude model to use.
        max_iterations: Safety cap on loop iterations.
        verbose:        Print step-by-step reasoning.

    Returns:
        dict with keys: completed (bool), iterations (int), summary (str), history (list)
    """
    model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Convert Anthropic-style tool schemas to OpenAI/Groq format
    groq_tools = [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in TOOLS
    ]

    system_prompt = f"""You are an autonomous AI agent with access to multiple business tools.
Your job is to complete the following task by calling tools in sequence until it is done.

Current date/time: {datetime.now().strftime('%Y-%m-%d %H:%M %A')}

Rules:
- Call ONE tool at a time. Wait for the result before deciding the next step.
- When the task is fully complete, call `task_complete` with a summary.
- If a step fails, try an alternative approach or gracefully handle the error.
- Never give up without calling `task_complete` (even if you must report failure).

Task: {task}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please complete this task: {task}"},
    ]
    history = []
    iterations = 0

    log.info("Starting Ralph Wiggum Loop for task: %s", task)

    while iterations < max_iterations:
        iterations += 1
        log.info("=== Iteration %d/%d ===", iterations, max_iterations)

        response = client.chat.completions.create(
            model=model,
            max_tokens=2048,
            tools=groq_tools,
            tool_choice="auto",
            messages=messages,
        )

        choice = response.choices[0]
        msg = choice.message
        step = {"iteration": iterations, "finish_reason": choice.finish_reason, "actions": []}

        # Process response content
        tool_results = []
        task_done = False
        final_summary = ""

        if msg.content:
            if verbose:
                print(f"\n[Groq] {msg.content}")
            step["actions"].append({"type": "text", "content": msg.content})

        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_input = json.loads(tc.function.arguments)
                if verbose:
                    print(f"\n[Tool Call] {tool_name}({json.dumps(tool_input, indent=2)})")

                try:
                    result = execute_tool(tool_name, tool_input)
                    if verbose:
                        print(f"[Result] {json.dumps(result, default=str, indent=2)}")
                except Exception as exc:
                    result = {"error": str(exc)}
                    log.error("Tool %s failed: %s", tool_name, exc)

                step["actions"].append({"type": "tool_use", "tool": tool_name, "input": tool_input, "result": result})
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                })

                if tool_name == "task_complete":
                    task_done = True
                    final_summary = tool_input.get("summary", "")

        history.append(step)

        if task_done:
            log.info("Task completed in %d iterations: %s", iterations, final_summary)
            return {"completed": True, "iterations": iterations, "summary": final_summary, "history": history}

        if choice.finish_reason == "stop" and not tool_results:
            log.warning("Groq stopped without calling task_complete.")
            break

        # Add assistant response and tool results to messages
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
        messages.extend(tool_results)

    log.warning("Max iterations (%d) reached without task_complete.", max_iterations)
    return {"completed": False, "iterations": iterations, "summary": "Max iterations reached.", "history": history}


def main():
    parser = argparse.ArgumentParser(description="Ralph Wiggum Autonomous Loop")
    parser.add_argument("--task", required=True, help="Task description for the agent")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument("--model", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = ralph_wiggum_loop(
        task=args.task,
        model=args.model,
        max_iterations=args.max_iterations,
        verbose=not args.quiet,
    )

    print("\n" + "=" * 60)
    print(f"{'✅ COMPLETED' if result['completed'] else '⚠️  INCOMPLETE'}")
    print(f"Iterations: {result['iterations']}")
    print(f"Summary: {result['summary']}")


if __name__ == "__main__":
    main()
