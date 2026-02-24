"""
ralph_wiggum_hook.py – Claude Code Stop Hook (Ralph Wiggum Loop)

This is a Claude Code Stop hook, NOT a standalone script.
It intercepts Claude's exit signal and decides whether to allow exit or re-inject the prompt.

How it works:
  1. Orchestrator creates a state file: /Vault/.ralph_state.json with the task prompt.
  2. Claude works on the task.
  3. Claude tries to exit → Claude Code calls this Stop hook.
  4. Hook checks:
       - Did Claude output <promise>TASK_COMPLETE</promise>? → allow exit (done).
       - Is the task file in /Done? → allow exit (done).
       - Max iterations reached? → allow exit (safety).
       - Otherwise → block exit, re-inject prompt (loop continues).

Installation (Claude Code settings):
  Add to ~/.config/claude-code/settings.json:
  {
    "hooks": {
      "Stop": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "python /path/to/BronzeTier/watchers/ralph_wiggum_hook.py"
            }
          ]
        }
      ]
    }
  }

State file format (/Vault/.ralph_state.json):
  {
    "prompt": "Process all files in /Needs_Action, move to /Done when complete",
    "completion_promise": "TASK_COMPLETE",
    "max_iterations": 10,
    "current_iteration": 0,
    "task_file": "/Vault/Needs_Action/task.md",   // optional: file-movement strategy
    "transcript_path": "/path/to/transcript"       // injected by Claude Code
  }

Exit codes (Claude Code Stop hook protocol):
  exit(0) → allow Claude to exit (task complete or max iterations)
  exit(1) → block exit, Claude Code re-injects prompt and continues
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [RalphWiggumHook] %(levelname)s %(message)s',
    handlers=[logging.FileHandler('ralph_wiggum.log', encoding='utf-8'), logging.StreamHandler()],
)
log = logging.getLogger('RalphWiggumHook')

VAULT_PATH  = Path(os.getenv('VAULT_PATH', './BronzeTier')).resolve()
STATE_FILE  = VAULT_PATH / '.ralph_state.json'
DONE_FOLDER = VAULT_PATH / 'Done'


def load_state() -> dict:
    """Load Ralph loop state from the vault state file."""
    if not STATE_FILE.exists():
        log.info('No state file found – allowing exit (no active Ralph loop).')
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception as e:
        log.error(f'Failed to read state file: {e}')
        return {}


def save_state(state: dict):
    """Persist updated state back to vault."""
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding='utf-8')


def clear_state():
    """Remove state file when task is complete."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        log.info('State file cleared – Ralph loop complete.')


def check_promise_in_transcript(transcript_path: str | None, promise: str) -> bool:
    """Check if Claude's output contains the completion promise tag."""
    if not transcript_path:
        return False
    try:
        transcript = Path(transcript_path).read_text(encoding='utf-8')
        return f'<promise>{promise}</promise>' in transcript
    except Exception:
        return False


def check_task_file_in_done(task_file: str | None) -> bool:
    """Check if the task file has been moved to /Done (file-movement strategy)."""
    if not task_file:
        return False
    task_path = Path(task_file)
    done_path = DONE_FOLDER / task_path.name
    return done_path.exists()


def main():
    """
    Main hook logic. Called by Claude Code on every Stop event.
    Reads stdin for hook context (Claude Code passes JSON via stdin).
    """
    # Claude Code passes hook context via stdin as JSON
    hook_input = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            hook_input = json.loads(raw)
    except Exception as e:
        log.warning(f'Could not parse hook input from stdin: {e}')

    transcript_path = hook_input.get('transcript_path') or hook_input.get('transcript')
    claude_output   = hook_input.get('output', '')

    state = load_state()
    if not state:
        # No active Ralph loop – allow exit normally
        log.info('No active Ralph loop. Allowing exit.')
        sys.exit(0)

    prompt            = state.get('prompt', '')
    completion_promise = state.get('completion_promise', 'TASK_COMPLETE')
    max_iterations    = int(state.get('max_iterations', 10))
    task_file         = state.get('task_file')
    current_iter      = int(state.get('current_iteration', 0)) + 1

    log.info(f'Ralph loop check: iteration {current_iter}/{max_iterations}')

    # ── Completion Check 1: Promise in transcript ────────────────────────────
    promise_found = (
        f'<promise>{completion_promise}</promise>' in claude_output
        or check_promise_in_transcript(transcript_path, completion_promise)
    )
    if promise_found:
        log.info(f'✅ Completion promise found: <promise>{completion_promise}</promise>. Allowing exit.')
        clear_state()
        sys.exit(0)

    # ── Completion Check 2: Task file moved to /Done ─────────────────────────
    if check_task_file_in_done(task_file):
        log.info(f'✅ Task file found in /Done: {task_file}. Allowing exit.')
        clear_state()
        sys.exit(0)

    # ── Safety: Max iterations reached ───────────────────────────────────────
    if current_iter >= max_iterations:
        log.warning(f'⚠️ Max iterations ({max_iterations}) reached. Forcing exit.')
        # Write a note to vault about incomplete task
        _write_incomplete_note(prompt, current_iter)
        clear_state()
        sys.exit(0)

    # ── Not done yet: update state and block exit ────────────────────────────
    state['current_iteration'] = current_iter
    state['last_checked'] = datetime.now().isoformat()
    save_state(state)

    log.info(f'🔄 Task not complete. Re-injecting prompt (iteration {current_iter}/{max_iterations}).')

    # Print the re-injection prompt to stdout — Claude Code reads this and
    # feeds it back to Claude as the next user message.
    print(f'\n[Ralph Wiggum Loop – Iteration {current_iter}/{max_iterations}]\n\n{prompt}\n\nContinue working. When complete, output: <promise>{completion_promise}</promise>')

    # Exit code 1 = block Claude from exiting, continue the loop
    sys.exit(1)


def _write_incomplete_note(prompt: str, iterations: int):
    """Write a note to Needs_Action when max iterations is hit without completion."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = VAULT_PATH / 'Needs_Action' / f'INCOMPLETE_TASK_{ts}.md'
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(
        f"""---
type: incomplete_task
created: {datetime.now().isoformat()}
iterations_used: {iterations}
status: needs_review
---

# ⚠️ Task Incomplete After {iterations} Iterations

## Original Prompt
{prompt}

## What Happened
The Ralph Wiggum loop ran {iterations} iterations without completing the task.

## Next Steps
- [ ] Review the task and break it into smaller steps
- [ ] Re-run with a more specific prompt
- [ ] Check if MCP servers are running
""",
        encoding='utf-8',
    )
    log.warning(f'Incomplete task note written: {filepath.name}')


# ── Standalone usage: start a Ralph loop ─────────────────────────────────────

def start_loop(
    prompt: str,
    completion_promise: str = 'TASK_COMPLETE',
    max_iterations: int = 10,
    task_file: str | None = None,
):
    """
    Create the state file to start a new Ralph Wiggum loop.

    Usage from CLI:
      python ralph_wiggum_hook.py --start \
        --prompt "Process all files in /Needs_Action" \
        --max-iterations 10

    Or from Python:
      from ralph_wiggum_hook import start_loop
      start_loop("Process all files in /Needs_Action")
    """
    state = {
        'prompt': prompt,
        'completion_promise': completion_promise,
        'max_iterations': max_iterations,
        'current_iteration': 0,
        'task_file': task_file,
        'started': datetime.now().isoformat(),
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_state(state)
    log.info(f'Ralph loop started. Prompt: {prompt[:80]}...')
    log.info(f'State file: {STATE_FILE}')
    print(f'\n[Ralph Wiggum Loop Started]\nPrompt: {prompt}\nMax iterations: {max_iterations}\n')
    print(f'Now run: claude "{prompt}"')
    print(f'Claude Code will automatically loop until <promise>{completion_promise}</promise> is output.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop – Claude Code Stop Hook')
    parser.add_argument('--start', action='store_true', help='Start a new Ralph loop (create state file)')
    parser.add_argument('--prompt', type=str, default='', help='Task prompt for the loop')
    parser.add_argument('--completion-promise', type=str, default='TASK_COMPLETE')
    parser.add_argument('--max-iterations', type=int, default=10)
    parser.add_argument('--task-file', type=str, default=None, help='Optional: task file to watch in /Done')
    args = parser.parse_args()

    if args.start:
        if not args.prompt:
            print('Error: --prompt is required with --start')
            sys.exit(1)
        start_loop(
            prompt=args.prompt,
            completion_promise=args.completion_promise,
            max_iterations=args.max_iterations,
            task_file=args.task_file,
        )
    else:
        # Called by Claude Code as a Stop hook
        main()
