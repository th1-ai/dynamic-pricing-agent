#!/usr/bin/env python3
"""PreToolUse hook: second lock on pricing pushes.

Reads the hook JSON from stdin. A Bash command that contains `--push` is
blocked (exit 2) when AUTONOMY.md is at PAUSED, or when the run is
unattended and AUTONOMY.md does not say `Level: 3`. Everything else passes
(exit 0). AUTONOMY.md has exactly one line `Level: <value>`, value 0, 1, 2,
3 or PAUSED. A missing file, a missing line, more than one line or an
unknown value counts as PAUSED. A run counts as unattended when its permission mode is `dontAsk`
or the environment has AUTONOMY_RUN=scheduled.

The hook checks the level and the kill switch only. The per-line limits in
AUTONOMY.md are applied by the agent.
"""
import json
import os
import re
import sys


def block(reason):
    print("autonomy-guard: " + reason, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        block("could not read the hook input, so the command is refused.")
    if not isinstance(data, dict) or data.get("tool_name") != "Bash":
        sys.exit(0)
    command = str((data.get("tool_input") or {}).get("command") or "")
    if not re.search(r"--push\b", command):
        sys.exit(0)

    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    values = []
    why = ""
    try:
        with open(os.path.join(root, "AUTONOMY.md"), encoding="utf-8") as fh:
            for line in fh:
                match = re.match(r"^Level:\s*(.*)$", line.strip())
                if match:
                    values.append(match.group(1).strip())
    except (OSError, UnicodeDecodeError):
        why = "AUTONOMY.md is missing or unreadable"
    if not why and len(values) != 1:
        why = "AUTONOMY.md has %d `Level:` lines, it needs exactly one" % len(values)
    if not why and values[0] not in ("0", "1", "2", "3", "PAUSED"):
        why = "AUTONOMY.md has an unknown level value"
    if not why and values[0] == "PAUSED":
        why = "AUTONOMY.md says Level: PAUSED"
    if why:
        block(why + ". This counts as PAUSED: no push until the operator sets a level.")
    level = int(values[0])

    unattended = (
        data.get("permission_mode") == "dontAsk"
        or os.environ.get("AUTONOMY_RUN") == "scheduled"
    )
    if not unattended:
        sys.exit(0)
    if level < 3:
        block("AUTONOMY.md says Level %d. An unattended push needs Level 3." % level)
    sys.exit(0)


if __name__ == "__main__":
    main()
