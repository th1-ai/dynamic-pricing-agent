---
name: dynamic-pricing
description: Dynamic pricing and MLOS rules for hotel rooms. Proposes last-minute rate drops to a per-room floor and MLOS = 1 for the next 30 days as a dry-run diff, then pushes to the PMS only after the operator approves. Use during the morning routine, after a room frees up inside the next 6 days, or when the operator asks about pricing, rates, MLOS, last-minute prices or says "run dynamic pricing".
---

# Skill: Dynamic Pricing & MLOS

> **Template note:** replace `{{PRICING_TOOL}}`, `{{PMS_RATES_TOOL}}` and `{{PMS_AVAILABILITY_TOOL}}` before first use. See [README.md](../../../README.md#customising).

## The rules

1. **MLOS = 1** for every hotel room within 29 days of arrival, so a minimum stay does not block a short last-minute booking.
2. **Drop the rate to the per-room floor** in the 0–6 day window when the room is still free and at least one other reservation covers that night. The hotel is open and staffed for that night anyway, so a floor-price booking is extra revenue.
3. **Never raise a rate.** A room already at or below its floor is flagged for the operator and left alone.
4. **Never touch whole-property or villa rentals.**
5. **No push without approval.** The operator sees the dry-run diff first and approves it, in full or line by line.

## Who does what

- **Main conversation:** delegate to the `dynamic-pricing` sub-agent with the goal "propose dynamic pricing changes, return the diff, do not push". Pass on any scope the operator gave ("only the next 7 days" becomes `--start` / `--end`; a freed room becomes that room's affected nights). Show the operator the diff exactly as returned and ask: **approve all**, **drop lines** (date + room), or **skip today**.
- **On approval:** send the same sub-agent back to work (continue it, or delegate again) with "the operator approved the diff" and the dropped lines. On skip, do nothing and say "Skipped today, will re-evaluate tomorrow."
- **Sub-agent:** if you are the `dynamic-pricing` sub-agent, this skill is your rulebook. Follow the Propose and Push steps in your own instructions; do not delegate further.
- **No sub-agent available:** run the same flow inline: dry-run, diff, ask, and only then push, verify and refresh.

An approval covers one diff. A new dry-run with different lines needs a new approval.

## Tool contract

The operator supplies the tools. The flow assumes:

| Command | Effect |
|---|---|
| `{{PRICING_TOOL}} --format json` | Dry-run. Prints JSON with `changes[]`, `patch_body` and `booked_dates_count`. Changes nothing. |
| `... --start YYYY-MM-DD --end YYYY-MM-DD` | Limits the window (default: today + 30 days). |
| `{{PRICING_TOOL}} --push` | Sends `patch_body` to the PMS and prints a confirmation reference. |
| `... --exclude DATE:ROOMTYPEID` | Leaves one line out of the push. Repeatable. |
| `{{PMS_RATES_TOOL}} --start ... --end ...` | Optional. Reads current rates and MLOS back from the PMS, to verify a push. |
| `{{PMS_AVAILABILITY_TOOL}} --start ... --end ...` | Refreshes any downstream availability cache after a push. |

## Floor-price logic

Each room type has two floors. Tier A is the lower one, because the night is closer.

| Tier | Window | Use when |
|---|---|---|
| **A** | 0–3 days out | The room is free and another room is booked that night |
| **B** | 4–6 days out | Same condition, less urgent |

The tool implements this; the pseudocode is here so you can explain a line to the operator, not so you can recompute it.

```
for each (date, room) in the window:
    if room is whole-property:
        continue
    if room is not available that night:
        continue

    if days_out <= 29 and current_mlos != 1:
        propose mlos = 1

    if days_out > 6:
        continue                      # rate drops only in 0–6 days

    other_bookings = confirmed reservations in other rooms covering this night
    if other_bookings == 0:
        continue                      # not a fill scenario

    floor = TIER_A_FLOOR[room] if days_out <= 3 else TIER_B_FLOOR[room]
    if current_rate <= floor:
        flag(date, room, "already at or below floor")
        continue                      # never raise

    propose rate = floor
```

## Line for the morning briefing

Use exactly one:

- "Dynamic pricing: N changes proposed across <rooms>. Awaiting approval." (the default; nothing is pushed yet)
- "Dynamic pricing: no changes today."
- "Dynamic pricing: pushed N changes (ref X)." (only if the operator approved in this session)
- "Dynamic pricing: could not run (<reason>)." (tool error or failed sanity check; never report "no changes" for a failed run)

## Stop and ask the operator when

- the tool fails, returns invalid JSON, or shows zero booked nights on a 30-day run;
- a proposed rate is above the current rate;
- the PMS rejects the push (do not retry before the cause is known);
- the operator's instruction conflicts with a rule above ("raise the weekend rate", "drop below floor for this guest"). These are outside this skill: say so, and let the operator change the rate or the floor in the PMS or the tool.
