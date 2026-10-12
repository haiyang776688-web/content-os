# MDC-001 — Motion Design Contract

**Status:** MDC-PASS

**Baseline:** `p0/motion-primitive-hardening-1@a180d8393ddff646601d9c97b8a3833af6d2984e`

## Question

Can a small renderer-neutral contract describe motion structure and primary/secondary rhythm without moving numeric animation parameters into Director or ShotPlan?

## Included

- four semantic Motion Phrases: EXPLAIN, FOCUS, IMPACT_WARN and CONNECT;
- PRIMARY / SECONDARY / BACKGROUND motion responsibility;
- semantic phases, relative order and qualitative strength;
- deterministic Compiler-owned numeric realization;
- Motion Preview plus static Storyboard Review;
- strict primitive-only / motion-designed A/B on four real Shot Types;
- motion, primitive, aspect-ratio, VLA and FAI regression.

## Excluded

Creative Composer, generated Remotion code, SeeCut QA or repair, Reference Library, Motion/SFX, music beat grids, TTS prosody, GUI redesign, physics and character rigs remain outside MDC-001.

Production timing default remains `CURRENT`. Motion Design is experimental and opt-in. `DECISIONS.md` is unchanged.
