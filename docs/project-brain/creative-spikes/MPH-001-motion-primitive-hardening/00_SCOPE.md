# MPH-001 — Motion Primitive Contract Hardening

**Status:** PASS

**Baseline:** `p0/v1-integration-baseline-1@0dfe8aa`

## Question

Does every motion primitive currently declared or emitted by the Visual Compiler have an observable, deterministic Renderer consumer on an explicitly supported layer kind?

## Included

- producer/consumer inventory for the complete v1 motion vocabulary;
- one authoritative capability contract shared by compiler validation and Remotion;
- pre-render rejection of unknown and unsupported primitive/layer combinations;
- a real `MATCHED_WIPE` implementation;
- a truthful, RELATION-only `DRAW_CONNECTION` implementation;
- start/middle/settled render evidence for every non-static primitive;
- Asset Aspect-Ratio, VLA A/B and FAI regression.

## Excluded

Motion choreography, anticipation, overshoot, physics, secondary response, lighting, SFX, Creative Composer, SeeCut QA, GUI redesign and full production opt-in remain outside MPH-001.

The production timing default remains `CURRENT`. `DECISIONS.md` is unchanged.
