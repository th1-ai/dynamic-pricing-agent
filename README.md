# Dynamic Pricing Agent

A Claude Code sub-agent + skill for hotel operators. It proposes rate and minimum-length-of-stay (MLOS) changes for the next 30 days, presents a diff for review, and only pushes to the PMS after explicit approval. Dry-run is the default; nothing changes silently.

Built on the **WAT framework** (Workflows, Agents, Tools): probabilistic AI handles reasoning, deterministic scripts handle execution.

---

## What it does

- **Drops the rate to a per-room floor** within the 0–6 day window when at least one reservation already overlaps that night (filling the rest of a partly-booked night)
- **Sets MLOS = 1** for every room within 29 days of arrival (no minimum-stay barriers in the last-minute window)
- **Flags rooms already at or below floor** as informational — never raises rates
- **Always dry-runs first** — produces a diff grouped by room type, with reason codes, before anything is pushed
- **Pushes only after explicit approval** — and only the lines you approved
- **Refreshes downstream caches** (e.g. an availability mirror) so other tools quote the new rates correctly

---

## What you need

- [Claude Code](https://claude.ai/code) installed
- A PMS with rate-plan and MLOS APIs — the agent calls a `pricing_tool`-style script that returns proposed changes as JSON, and pushes via `--push`. The reference setup uses Cloudbeds (`patchRate`), but any PMS with rate-plan write access works.

---

## Quick start

1. **Clone the repo** into a Claude Code project:

   ```bash
   git clone https://github.com/th1-ai/dynamic-pricing-agent.git
   cd dynamic-pricing-agent
   ```

2. **Copy the env template** and fill it in — including your per-room floor prices:

   ```bash
   cp .env.example .env
   ```

3. **Edit [`.claude/agents/dynamic-pricing.md`](.claude/agents/dynamic-pricing.md)** and [`.claude/skills/dynamic-pricing/SKILL.md`](.claude/skills/dynamic-pricing/SKILL.md) — replace the placeholders described in [Customising](#customising) with the wrappers your setup uses.

4. **Open in Claude Code** from the project root:

   ```bash
   claude
   ```

5. **Invoke the agent**:

   > "Run dynamic pricing for the next 30 days."

   Claude Code will pick up the `dynamic-pricing` sub-agent automatically because of the front-matter `description` line.

---

## File structure

```
dynamic-pricing-agent/
├── README.md
├── .env.example
├── .gitignore
├── LICENSE
└── .claude/
    ├── agents/
    │   └── dynamic-pricing.md                       # Sub-agent definition
    ├── skills/
    │   └── dynamic-pricing/
    │       └── SKILL.md                             # Skill (full process)
    └── agent-memory/
        └── dynamic-pricing/
            └── example-feedback-pattern.md          # Example "memory note"
```

---

## Customising

The agent and skill files use placeholders so they can be adapted to any PMS. Replace the following before first run:

| Placeholder | What to put | Example |
|---|---|---|
| `{{HOTEL_NAME}}` | Hotel display name | `The Garden Inn` |
| `{{PMS_PROPERTY_ID}}` | PMS property ID | `123456789` |
| `{{PRICING_TOOL}}` | Script that produces the dry-run diff and pushes on `--push` | `tools/dynamic_pricing.py` |
| `{{PMS_RATES_TOOL}}` | Optional helper that fetches current rate plans (used to verify pushes) | `tools/pms_rates.py` |
| `{{PMS_AVAILABILITY_TOOL}}` | Script that refreshes any downstream availability cache after a push | `tools/sync_availability.py` |
| `<PremiumRoom>` / `<StandardRoom>` | Your own room-type slugs | `SUITE`, `STANDARD` |

Floor prices per room type live in `.env` (or in a constants block in your pricing tool — pick one source of truth).

---

## How memory works

The agent uses Claude Code's per-agent memory at `.claude/agent-memory/dynamic-pricing/`. After each run, it can save:

- **Feedback** — pricing patterns to repeat (e.g. "<PremiumRoom> rarely sells last-minute below 290; floor is right")
- **Project notes** — context that affects pricing (e.g. "local festival 12–14 July — push floors up by 20% for those dates")
- **References** — pointers to other systems (e.g. "freed-room re-pricing is auto-triggered by the room-upgrade agent")

[`example-feedback-pattern.md`](.claude/agent-memory/dynamic-pricing/example-feedback-pattern.md) shows the recommended format. Delete it once you have your own.

---

## Related agents

This agent works well alongside:

- [`agent-notification-agent`](https://github.com/th1-ai/agent-notification-agent) — notifies external rental agents when rates change so they're not selling stale prices
- [`room-upgrade-agent`](https://github.com/th1-ai/room-upgrade-agent) — calls dynamic pricing on the freed room/dates whenever an upgrade is executed
- [`morning-routine-agent`](https://github.com/th1-ai/morning-routine-agent) — runs dynamic pricing as part of the daily briefing
- [`villa-analytics-agent`](https://github.com/th1-ai/villa-analytics-agent) — reports on whether last-minute discounts converted to bookings

---

## License

MIT — see [LICENSE](LICENSE).
