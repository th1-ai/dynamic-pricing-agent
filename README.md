# Dynamic Pricing Agent

A Claude Code sub-agent + skill for hotel operators. It proposes rate and minimum-length-of-stay (MLOS) changes for the next 30 days, presents a diff for review, and only pushes to the PMS after explicit approval. Dry-run is the default; nothing changes silently.

It can also run on a schedule. [`AUTONOMY.md`](AUTONOMY.md) sets how much it does when nobody is there: report only (the default), save a proposal for one-step approval, or push routine lines within limits that you set. See [Run it on its own](#run-it-on-its-own).

Built on the **WAT framework** (Workflows, Agents, Tools): probabilistic AI handles reasoning, deterministic scripts handle execution. This repo is the workflow and the agent. **You bring the tool**: a script that talks to your PMS (see [The pricing tool you supply](#the-pricing-tool-you-supply)).

---

## What it does

- **Drops the rate to a per-room floor** within the 0–6 day window when the room is free and at least one other reservation covers that night (filling the rest of a partly-booked night)
- **Sets MLOS = 1** for every room within 29 days of arrival (no minimum-stay barriers in the last-minute window)
- **Flags rooms already at or below floor** as informational — never raises rates
- **Always dry-runs first** — produces a diff grouped by room type, with reason codes, before anything is pushed
- **Pushes only after explicit approval** — and only the lines you approved. It re-checks the diff right before the push and stops if anything changed
- **Verifies and refreshes** — reads the rates back if you supply a rates helper, then refreshes any downstream cache (e.g. an availability mirror) so other tools quote the new rates

It does not forecast demand, watch competitors or raise prices. It applies two fixed rules with your floors.

---

## What you need

- [Claude Code](https://code.claude.com/docs/en/overview) installed
- A PMS with rate-plan and MLOS write access through an API. The reference setup uses Cloudbeds (`patchRate`), but any PMS with rate-plan write access works.
- A pricing tool for that PMS, written to the contract below. It is not included.

---

## Quick start

1. **Clone the repo** (or copy the `.claude/` folder into your existing Claude Code project):

   ```bash
   git clone https://github.com/th1-ai/dynamic-pricing-agent.git
   cd dynamic-pricing-agent
   ```

2. **Copy the env template** and fill it in — including your per-room floor prices:

   ```bash
   cp .env.example .env
   ```

3. **Open Claude Code** from the project root:

   ```bash
   claude
   ```

4. **Let Claude set it up with you.** Paste this as your first message:

   > Read the README and set this agent up with me. Ask me for each placeholder in the Customising table, one at a time, then replace it everywhere under `.claude/`. Check that each tool path I give exists. Do not run any tool with `--push`.

   Or do it by hand: edit [`.claude/agents/dynamic-pricing.md`](.claude/agents/dynamic-pricing.md) and [`.claude/skills/dynamic-pricing/SKILL.md`](.claude/skills/dynamic-pricing/SKILL.md) and replace the placeholders described in [Customising](#customising).

5. **Invoke the agent**:

   > "Run dynamic pricing for the next 30 days."

   Claude Code delegates to the `dynamic-pricing` sub-agent because of the `description` line in its front matter. To force it, type `@agent-dynamic-pricing` in your message.

   You get a diff. Answer **approve**, **drop** specific lines, or **skip**. Only an approval leads to a push.

---

## Verify it works

1. Run `/agents` in Claude Code. `dynamic-pricing` is in the list.
2. Type `/` and look for `dynamic-pricing` in the skill list.
3. Run `grep -rnE '\{\{[A-Z_]+\}\}' .claude/` in a terminal. No output means every placeholder is replaced.
4. Run your pricing tool by hand with `--format json`. It prints JSON and changes nothing in the PMS.
5. Ask for a dry run and answer **skip**. Check in the PMS that no rate changed.
6. For the first real push, approve one line only and drop the others. Check that line in the PMS.

---

## File structure

```
dynamic-pricing-agent/
├── README.md
├── AUTONOMY.md                                      # Autonomy level, limits, guard rails (you edit it)
├── .env.example
├── .gitignore
├── LICENSE
├── runs/
│   ├── README.md                                    # Format of the run log, proposals and handoff files
│   └── .gitkeep                                     # LOG.md, proposals/ and handoff/ appear here (git-ignored)
└── .claude/
    ├── settings.example.json                        # Example permissions + hook for scheduled runs (not loaded as is)
    ├── hooks/
    │   └── autonomy-guard.py                        # Hook: blocks an unattended push below Level 3, and every push when PAUSED
    ├── agents/
    │   └── dynamic-pricing.md                       # Sub-agent definition (propose / push / scheduled steps)
    ├── skills/
    │   └── dynamic-pricing/
    │       └── SKILL.md                             # Skill (rules, approval flow, tool contract)
    └── agent-memory/
        └── dynamic-pricing/
            ├── MEMORY.md                            # Memory index, loaded at agent start
            └── example-feedback-pattern.md          # Example "memory note"
```

---

## Customising

The agent and skill files (and the tool rules in `.claude/settings.example.json`) use placeholders so they can be adapted to any PMS. Replace the following before first run:

| Placeholder | What to put | Example |
|---|---|---|
| `{{HOTEL_NAME}}` | Hotel display name (shown in the diff header) | `The Garden Inn` |
| `{{PMS_PROPERTY_ID}}` | PMS property ID | `123456789` |
| `{{PRICING_TOOL}}` | Script that produces the dry-run diff and pushes on `--push` | `tools/dynamic_pricing.py` |
| `{{PMS_RATES_TOOL}}` | Optional helper that reads current rates and MLOS back, to verify a push | `tools/pms_rates.py` |
| `{{PMS_AVAILABILITY_TOOL}}` | Script that refreshes any downstream availability cache after a push | `tools/sync_availability.py` |
| `<PremiumRoom>` / `<StandardRoom>` | Your own room-type names (in the example diff only) | `SUITE`, `STANDARD` |

If you have no rates helper or no availability cache, delete that step from the agent file instead of leaving the placeholder in. Delete its allow rule from `.claude/settings.example.json` too. Without a rates helper the agent reports a push as "not verified" and does not push on its own at Level 3.

Floor prices per room type live in `.env` (or in a constants block in your pricing tool — pick one source of truth). The agent does not edit floors; you do.

`.env` holds values for your tools. Claude Code does not load it, so the tool paths must also be filled in as placeholders in the two files above.

---

## Run it on its own

Until now you asked and the agent answered. This section lets it run on a schedule. Everything here is an example: the commands and flags were checked against the Claude Code docs ([non-interactive mode](https://code.claude.com/docs/en/headless), [permissions](https://code.claude.com/docs/en/permissions), [hooks](https://code.claude.com/docs/en/hooks)), but the full scheduled run was not executed against a real PMS. Test it on your own setup before you rely on it.

### 1. Set the level

[`AUTONOMY.md`](AUTONOMY.md) holds exactly one line `Level: <value>` (0, 1, 2, 3 or PAUSED; shipped as `Level: 1`) and the limits. The agent reads it at the start of every run.

| Level | A scheduled run does | Reaches the PMS |
|---|---|---|
| PAUSED | Nothing, except one log entry with the reason | Nothing, approved pushes are refused too |
| 0 | Nothing. You ask, it proposes, you approve. | Only what you approve |
| 1 (default) | Dry run, checks, one entry in `runs/LOG.md` | Nothing |
| 2 | Also saves `runs/proposals/YYYY-MM-DD.md`. You say "approve today's pricing proposal". | Only what you approve |
| 3 | Also pushes MLOS = 1 lines and rate drops to the floor, inside the limits in `AUTONOMY.md` | Routine lines, within limits; the rest waits for you |

Never on its own, at any level: raising a rate, going below a floor, whole-property rentals, a retry after a failed push, messages to guests or partners. `Level: PAUSED` in `AUTONOMY.md` stops scheduled runs and every push. A missing file, a missing level line or an unknown value counts as PAUSED.

### 2. Permissions for a scheduled run

[`.claude/settings.example.json`](.claude/settings.example.json) is an example of least-privilege settings. Claude Code does not load a file with that name, so cloning this repo changes nothing. Copy it and pass the copy to the scheduled run only:

```bash
cp .claude/settings.example.json .claude/settings.scheduled.json
```

Fill in the tool placeholders in the copy (the setup prompt in Quick start does this for every file under `.claude/`). What it does:

- **Allows** the dry run, the rates helper, `date`, and writes to `runs/` and the agent memory.
- **Denies** any command that contains `--push`, plus `rm`, `curl`, `wget`, `git push`, reading `.env` and editing `AUTONOMY.md`. Deny rules win over allow rules.
- **Adds a hook**, [`.claude/hooks/autonomy-guard.py`](.claude/hooks/autonomy-guard.py) (needs `python3`). It runs before each Bash command and blocks a `--push` when `AUTONOMY.md` says `Level: PAUSED` (or is missing or unclear), or when the run is unattended and the level is below 3. It was tested on its own with allow and block cases, not inside a live scheduled run.

The Claude Code docs say that Bash rules match the command text and are not a hard security boundary. Keep the PMS credentials of the pricing tool as narrow as your PMS allows.

### 3. The command

```bash
cd /path/to/dynamic-pricing-agent && \
claude -p "/dynamic-pricing scheduled run" \
  --settings .claude/settings.scheduled.json \
  --permission-mode dontAsk \
  --permission-prompts none \
  --max-turns 40
```

- `-p` runs once without a terminal and prints the report. `/dynamic-pricing` loads the skill, which hands the run to the sub-agent.
- `--permission-mode dontAsk` denies every tool call that the settings do not allow, instead of asking.
- `--permission-prompts none` tells Claude that nobody can answer a prompt. It needs Claude Code v2.1.259 or later; leave it out on older versions.
- `--max-turns 40` stops a run that loops.
- Add `--output-format json` if a script reads the result; the report is then in the `result` field.

Run it once by hand first and read the output.

### 4. A scheduler example (cron on macOS or Linux)

Daily at 07:30, before the morning briefing. Add it with `crontab -e`, on one line:

```
30 7 * * * cd /path/to/dynamic-pricing-agent && { if grep -qxE 'Level: [123]' AUTONOMY.md; then /full/path/to/claude -p "/dynamic-pricing scheduled run" --settings .claude/settings.scheduled.json --permission-mode dontAsk --permission-prompts none --max-turns 40; else echo "Skipped: AUTONOMY.md is not at Level 1, 2 or 3"; fi; } > runs/last-report.txt 2>&1
```

- The `grep` starts Claude Code only at Level 1, 2 or 3. At Level 0, at `PAUSED`, or with a missing or unclear file, the run is skipped, costs nothing, and the reason is in the report file.
- cron has a short `PATH`: use the output of `which claude` as the full path. Cron uses the clock of the machine; the machine must be on.
- The report lands in `runs/last-report.txt`. Its first section is "Needs you". A quiet run says "Nothing needs you".
- If the cron job is not logged in, the Claude Code docs describe `claude setup-token` and the `CLAUDE_CODE_OAUTH_TOKEN` variable for scripts ([authentication](https://code.claude.com/docs/en/authentication)).
- A second run in the early afternoon catches same-day changes. More than two runs a day adds cost and little else.

The docs also list [Desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks) (run on your machine) as an alternative to cron. Cloud scheduled tasks run on a fresh clone without your local tools and `.env`, so they do not fit this agent as it is.

Headless use of a personal Pro or Max plan is subject to Anthropic's usage policy, which assumes ordinary individual use; for heavy or business-critical schedules use an API key or a team plan.

### 5. Move up one level at a time

1. Run 7 days at the current level.
2. Read `runs/LOG.md`: no errors, and the proposals are the ones you would have approved.
3. Change the one `Level:` line in `AUTONOMY.md`.

Level 3 needs one more change, on purpose, because it lets a run change live prices. In `.claude/settings.scheduled.json`, remove the deny rule `Bash(*--push*)` and add two allow rules: `Bash(<your pricing tool> --push *)` and `Bash(<your availability tool> *)`. Level 3 also needs the rates helper, because the agent does not push on its own without a read-back. The first 5 runs at Level 3 are shadow runs: the log shows what would be pushed, and nothing is.

To step back: lower the value on the level line, or set it to `PAUSED`. After a failed or unverified push the agent holds on its own until you add a `HOLD CLEARED` line to the log (see [`runs/README.md`](runs/README.md)).

---

## The pricing tool you supply

The agent calls your tool and trusts its output. The tool holds the pricing logic and the PMS credentials. The agent expects this interface:

| Command | Effect |
|---|---|
| `<pricing tool> --format json` | Dry-run. Prints the JSON below. Changes nothing. |
| `--start YYYY-MM-DD --end YYYY-MM-DD` | Limits the window. Default: today to today + 30 days. |
| `<pricing tool> --push` | Sends the changes to the PMS. Prints a confirmation reference. |
| `--exclude DATE:ROOMTYPEID` | Leaves one line out of the push. Repeatable. |
| `<rates tool> --start ... --end ...` | Optional. Prints current rates and MLOS from the PMS. |
| `<availability tool> --start ... --end ...` | Refreshes your availability cache, if you have one. |

Dry-run output (shape):

```json
{
  "booked_dates_count": 12,
  "changes": [
    {"date": "2026-04-28", "room": "SUITE", "room_type_id": "111", "days_out": 1,
     "current_rate": 340, "target_rate": 290, "target_minlos": null, "flag": null, "reason": "TierA + booking"},
    {"date": "2026-04-27", "room": "STANDARD", "room_type_id": "222", "days_out": 0,
     "current_rate": 150, "target_rate": null, "target_minlos": null, "flag": "already at/below floor", "reason": null}
  ],
  "patch_body": {"rates": [{"note": "the PMS-specific payload for the push changes"}]}
}
```

The agent relies on `changes[]` (with `target_rate`, `target_minlos`, `flag`), `patch_body` and `booked_dates_count`. The other field names are a suggestion. If your tool uses different flags or fields, change them in the agent and skill files so the three stay in step.

The rule logic that the tool must implement is in the skill file as pseudocode.

---

## How memory works

The agent uses Claude Code's per-agent memory (`memory: project`) at `.claude/agent-memory/dynamic-pricing/`. Claude Code loads `MEMORY.md` from that folder when the agent starts; the agent opens the other notes when the index points to them. After a run, it can save:

- **Feedback** — pricing patterns to repeat (e.g. "<PremiumRoom> rarely sells last-minute below 290; floor is right")
- **Project notes** — context that affects pricing (e.g. "local festival 12–14 July — leave those dates alone")
- **References** — pointers to other systems (e.g. "freed-room re-pricing is triggered by the room-upgrade agent")

[`example-feedback-pattern.md`](.claude/agent-memory/dynamic-pricing/example-feedback-pattern.md) shows the recommended format. Delete it, and its line in [`MEMORY.md`](.claude/agent-memory/dynamic-pricing/MEMORY.md), once you have your own.

This folder is committed to git. Keep guest names and other personal data out of it.

---

## Troubleshooting

- **Claude answers a pricing question itself and the agent does not run.** Name it: "use the dynamic-pricing agent", or `@agent-dynamic-pricing`. If `/agents` does not list it, check that you started `claude` in the folder that contains `.claude/`.
- **"Placeholder missing" or "tool not found".** A placeholder in double curly braces is still in the agent or skill file, or the path is wrong relative to the project root.
- **The agent stops with "zero booked nights".** The tool probably failed to fetch reservations. Run the tool by hand and read its error.
- **The push changed, or the agent refuses to push after approval.** A booking or rate changed between the diff and the push. Review the new diff and approve again.
- **The agent forgets notes between runs.** Per-agent memory depends on Claude Code's auto memory. Check that it is not turned off in your settings.
- **Push fails with a 4xx.** The agent stops and does not retry. Check the API credentials and rate-plan IDs in your tool.
- **A scheduled run reports a denied command.** `dontAsk` denies what the settings do not allow. Compare the command in the report with the allow rules in `.claude/settings.scheduled.json`; the tool path must match the rule text exactly.
- **A scheduled run does nothing.** Check `AUTONOMY.md`: the one `Level:` line must hold 1, 2 or 3 (0, `PAUSED`, a missing line or another value stops the run), then `runs/last-report.txt` for a login or path error.
- **Level 3 never pushes.** Read the latest `runs/LOG.md` entry: it names the reason (shadow run, hold, outside the push window, no rates helper, already pushed today).

---

## Related agents

This agent works well alongside:

- [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) — runs dynamic pricing in dry-run mode as part of the daily briefing. After a scheduled run it can read the `Briefing` and `Needs you` fields of the latest `runs/LOG.md` entry instead
- [`room-upgrade-agent`](https://github.com/th1-ai/room-upgrade-agent) — reports a "Re-price handoff" (freed room and dates) after an upgrade; pass it to this agent as a scoped dry run. The next scheduled run covers those nights too
- [`agent-notification-agent`](https://github.com/th1-ai/agent-notification-agent) — drafts emails to partner agencies after you change rates, so they do not sell stale prices. After a push this agent writes the pushed lines to `runs/handoff/dynamic-pricing-agent.md` as its input
- [`villa-analytics-agent`](https://github.com/th1-ai/villa-analytics-agent) — reports occupancy, ADR and forward pace, which helps you set the floors
- [`booking-inquiry-agent`](https://github.com/th1-ai/booking-inquiry-agent) — quotes rates in draft replies; the cache refresh after a push keeps those quotes current

The full set: [21 AI Agents That Run a Real Hotel](https://th1.ai/agent-stack).

---

## License

MIT — see [LICENSE](LICENSE).
