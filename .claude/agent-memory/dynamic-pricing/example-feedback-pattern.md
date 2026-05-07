---
name: Re-price the freed room whenever a room becomes available within 0–6 days
description: When a room frees up in the last-minute window (cancellation, no-show, upgrade), it almost always meets the rate-drop condition because at least one other room is still booked. Don't leave it at rack rate.
type: feedback
---

> **Example pattern.** This file shows the *shape* of a useful agent-memory note. Replace it with your own learnings as the agent runs.

**When this fires:**

- A guest cancels a reservation that started in the next 0–6 days
- A guest is a no-show
- A guest accepts an upgrade (the original room is now free)
- A reservation is shortened so its first or last night is now empty

**Why it matters:**

Inside the 0–6 day window, leaving a freed room at rack rate is leaving money on the table. If at least one other room is still booked on the same night, the rate-drop condition is met and the floor price is the right last-minute price.

**How to apply:**

1. As soon as the freeing event is detected (or executed by another agent), call this skill on the freed room and the affected dates only — don't re-run the full 30-day proposal.
2. Surface the proposal as part of the same operator interaction that caused the freeing event ("you just executed an upgrade — here's the re-price proposal for the now-free room").
3. If the freed room's date no longer overlaps with any other booking, no re-price is needed — report "no rate change needed" and stop.

**Anti-pattern:**

Running the full 30-day dry-run after every cancellation. Wasteful and noisy. Scope to the affected dates and room.

**Cross-agent integration:**

The `room-upgrade-agent` calls this skill automatically as Step 7 of executing an accepted upgrade.
