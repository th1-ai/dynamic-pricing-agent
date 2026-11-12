# runs/

The agent's working record. Everything here except this file and `.gitkeep` is ignored by git, because it holds your property's rates and tool error text.

| Path | Written when | Read by |
|---|---|---|
| `LOG.md` | Every scheduled run, and every push | The agent (to skip work already done), you, `morning-routine-agent` (the last entry is the latest run summary) |
| `proposals/YYYY-MM-DD.md` | Level 2 and up, when there is something to push | You, and the agent when you approve |
| `handoff/dynamic-pricing-agent.md` | After a push | `agent-notification-agent`, to draft partner emails |

## `LOG.md` format

The file ends with the marker line `<!-- end of log -->`. The agent adds each new entry directly above the marker with the Edit tool (it creates the file with only the marker if it is missing). Newest entry is last. Entries are never edited or deleted.

```
## 2026-04-27 07:30 scheduled
- Level: 2
- Checked: 2026-04-27 to 2026-05-26, 12 booked nights
- Pushed: none
- Proposed: 4 lines (runs/proposals/2026-04-27.md)
- Flagged: 2 at or below floor
- Errors: none
- Hold: no
- Needs you: Nothing needs you
- Briefing: Dynamic pricing: 4 changes proposed across SUITE, STANDARD. Awaiting approval.
```

Field notes:

- Heading: date, time (property time) and `scheduled` or `on request`.
- `Level`: the level read from `AUTONOMY.md`. For a run that stopped at Level 0 or PAUSED, the entry holds only the heading, this field and a `Reason` field. Add `(shadow 2/5)` during the shadow runs at Level 3.
- `Pushed`: `none`, or the count, the reference, `approved` or `autonomous`, the read-back result, and each line as `DATE:ROOMTYPEID`.
- `Hold`: `yes` after a failed or unverified push. You clear it by adding a line `HOLD CLEARED 2026-04-28` above the marker.
- `Briefing`: the one line that `morning-routine-agent` shows.

No guest names or other personal data in any file here.

## `proposals/YYYY-MM-DD.md`

The same diff the agent shows in a session, plus one `DATE:ROOMTYPEID` key per line. It is valid on its own day only. To approve, open Claude Code and say "approve today's pricing proposal" (add the lines to drop, if any). The agent re-runs the dry run and pushes only if the lines still match.

## `handoff/dynamic-pricing-agent.md`

Overwritten after each push: the push time, the reference, and each pushed line (date, room type, old value, new value). It is input for a draft; nothing is sent from here.
