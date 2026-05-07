---
name: dynamic-pricing
---

# Skill: Dynamic Pricing & MLOS

## Trigger

Use proactively when:
- Running the morning routine (always — this is one of the daily steps)
- The operator asks about pricing, rates, MLOS, last-minute prices, "drop the price"
- The operator says "run dynamic pricing", "check pricing", "pricing automation"

> **Template note:** Replace `{{PMS_PROPERTY_ID}}`, `{{PRICING_TOOL}}` and `{{PMS_AVAILABILITY_TOOL}}` with the wrappers your setup uses. See [README.md](../../../README.md#customising) for guidance.

## Purpose

Apply the dynamic pricing rules:

1. **MLOS = 1** for every hotel room within 29 days of arrival.
2. **Drop the rate to a per-room floor** for the 0–6 day window when ≥1 hotel reservation already overlaps that night (this fills partly-booked nights at last-minute rates).
3. **Never raise rates** — if a room is already at or below floor for a date, flag it (informational) but do not push.
4. **Never touch whole-property / villa rentals** — out of scope.

**Approval is mandatory before any push.** This skill never pushes silently.

## Workflow

The `dynamic-pricing` sub-agent owns the work. From this skill:

1. **Spawn the sub-agent** with the goal "propose dynamic pricing changes for the next 30 days, present a diff, and wait for approval before pushing." Pass through any context the user provided (e.g. "only check the next 7 days" → set `--start` and `--end`).
2. The sub-agent runs `{{PRICING_TOOL}} --format json`, reads this skill, and renders a diff table.
3. The sub-agent asks: approve / edit / skip.
4. On approve, the sub-agent re-runs with `--push` (and any `--exclude` pairs from edits), then refreshes the availability mirror.
5. The sub-agent returns a one-line summary: "Pushed N changes (jobRef=X)" or "Skipped — no changes / operator chose to skip."

## Direct invocation (if no sub-agent context available)

If for some reason the sub-agent isn't being used, run the same flow inline:

```bash
{{PRICING_TOOL}} --format json
```

Render the diff, ask for approval, then on approval:

```bash
{{PRICING_TOOL}} --push
{{PMS_AVAILABILITY_TOOL}} --start <today> --end <today+30>
```

## Floor-price logic

Each room type has two floor prices:

| Tier | Window | Use when |
|---|---|---|
| **A** | 0–3 days out | Last-minute fill, room already partly booked on that night |
| **B** | 4–6 days out | Same condition, slightly less urgent |

Pseudocode:

```
for each (date, room) in next 30 days:
    if room is whole-property:
        continue
    if days_out > 6:
        # Only set MLOS=1 within 29d, no rate drops outside 0–6d
        if days_out <= 29 and current_mlos != 1:
            propose mlos=1
        continue

    floor = TIER_A_FLOOR[room] if days_out <= 3 else TIER_B_FLOOR[room]
    overlapping = count of confirmed reservations covering this night, excluding this room
    if overlapping == 0:
        continue   # not a fill scenario

    if current_rate <= floor:
        flag(date, room, "already at/below floor")
        continue   # never raise

    propose rate = floor
```

## Output to morning briefing

Either:
- "Dynamic pricing — N changes proposed across {rooms}. Awaiting approval." (default — rates not pushed yet, included in the briefing)
- "Dynamic pricing — no changes today."
- "Dynamic pricing — pushed N changes (jobRef=X)." (only if approval already given during this session)

## Critical rules

- **Approval gate is non-negotiable.** Always dry-run first. Show diff. Ask. Then push.
- Use `{{PRICING_TOOL}}`, not raw rate-plan API calls. Centralise the logic in one tool.
- The tool already excludes whole-property rentals and respects the booking-overlap condition — don't re-implement the logic in the agent.
- If `{{PRICING_TOOL}} --format json` returns `changes: []`, report "no changes" and stop. Don't push an empty body.
- If the PMS push raises a 4xx, capture the response and stop — do NOT retry without diagnosing (likely a stale rate ID or auth issue).
- Floor prices live in one place — either `.env` or a constants block at the top of `{{PRICING_TOOL}}`. Keep them in sync.
