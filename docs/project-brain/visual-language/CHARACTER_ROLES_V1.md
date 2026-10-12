# XIAO-Y Character Roles v1

`character_role` explains why XIAO-Y is present. `action_id` is a later asset choice.

| Role | Narrative responsibility | Allowed prominence | Example semantic intents |
| --- | --- | --- | --- |
| `GUIDE` | introduce or point to a real object | PRIMARY briefly, then exit or support | POINT_LEFT, POINT_RIGHT, KEY_POINT |
| `EXPLAINER` | clarify a concept that evidence alone cannot express | PRIMARY or SUPPORTING | EXPLAIN, THINKING |
| `REACTION` | punctuate a revealed contradiction or surprise | PRIMARY for a short interruption | SURPRISE, CONFUSION |
| `WARNING` | signal risk or prevent a wrong inference | PRIMARY or SUPPORTING | SERIOUS, KEY_POINT |
| `RESPONSIBILITY` | represent human judgment, review or accountability | PRIMARY with evidence context | SERIOUS, APPROVE |
| `TRANSITION` | hand attention from one object/state to another | SUPPORTING | POINT_LEFT, POINT_RIGHT |
| `SUMMARY` | settle an established conclusion or action | PRIMARY or SUPPORTING | EXPLAIN, CTA, APPROVE |
| `NONE` | no character needed | absent | none |

## Allocation order

```text
character_role
→ semantic intent allowed for that role
→ registered action candidates
→ repetition-aware deterministic allocator
→ action_id
```

An explicit human action override remains intact. The allocator may vary a pose only inside a compatible role. It must not infer a role from a preselected pose.

## Presence rules

- `PROVE` and `DEMONSTRATE`: default `NONE` or supporting `GUIDE`.
- `REACT`: requires `REACTION` and a cause supplied by the prior/current evidence context.
- `WARN`: `WARNING` is allowed; evidence remains visible when the warning is factual.
- `TRANSITION`: character exits after transferring attention.
- `SUMMARIZE`: character may lead only after the information has already been established.
- A character that does not change attention, tone, accountability or continuity should be removed.
