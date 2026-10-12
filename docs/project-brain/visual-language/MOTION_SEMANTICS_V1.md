# Motion Semantics v1

Motion Semantics state why the picture changes. Animation primitives state how the renderer expresses that purpose.

| Semantic | Meaning | Typical deterministic primitives |
| --- | --- | --- |
| `FOCUS` | direct attention to one existing subject | pan, crop, zoom, dim non-focus |
| `REVEAL` | introduce new information at a semantic boundary | mask reveal, fade, short slide |
| `FOLLOW` | track a subject or token through a process | position interpolation, camera follow |
| `COMPARE` | expose a meaningful difference | split, wipe, matched scale, before/after |
| `INTERRUPT` | break an expected path because meaning changes | reaction cut, color field, abrupt scale change |
| `RETURN` | return from an interruption to the causing evidence | reverse handoff, matched region, camera restore |
| `CONNECT` | show a relationship or dependency | anchor line, path, node collection |
| `SETTLE` | stop motion on a conclusion or action | deceleration, completed underline, stable hold |

`HOLD`, `FADE`, `SLIDE_UP`, `SLOW_ZOOM` and `SLOW_PAN` remain renderer-level primitives. They are not valid substitutes for a Motion Semantic in a Shot Plan.

Motion must remain seek-safe: a frame rendered in isolation must match the same frame in video playback. Every primitive is a deterministic function of the shot-local frame. Continuous ambient motion is optional; it cannot be counted as a visual response unless information or attention changes.
