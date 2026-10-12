# Rhythm Rules v1

The governing rule is **Semantic Change → Visual Response**. There is no universal “cut every three seconds” rule.

## What counts as a response

- evidence context becomes focus/detail;
- a candidate reaches a decision boundary;
- a contradiction triggers `INTERRUPT`, then `RETURN`;
- responsibility moves from model output to human review;
- two real objects become related;
- a conclusion `SETTLE`s on the evidence that supports it.

Ambient zoom, arbitrary pose rotation and decorative fades do not count by themselves.

## Diagnostics

The compiler emits these measurements as observations:

- `seconds_since_last_visual_change`
- `shot_duration`
- `evidence_hold_duration`
- `reaction_duration`
- `visual_response_count`

They are `OBSERVATION` or `WARNING` in v1. They do not block a render solely because a number crosses a threshold. Long evidence holds can be correct when the user needs reading time; short cuts can still be wrong when no meaning changes.

## Continuity

Each shot records its incoming/outgoing semantic anchor. `INTERRUPT` caused by evidence should normally be followed by `RETURN`. `CONNECT` should start from an already introduced object. `SETTLE` should not introduce a new unsupported conclusion. These relations are more important than raw shot count.
