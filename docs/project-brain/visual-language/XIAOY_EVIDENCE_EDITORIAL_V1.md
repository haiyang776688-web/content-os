# XIAO-Y Evidence Editorial v1

**Status:** ACCEPTED VISUAL LANGUAGE PRINCIPLES

**Decision:** `DEC-011`

**Evidence:** VGB-002 F2 is the default Gold Master; F1 remains the Evidence-heavy reference.

**Scope:** visual planning, compilation, storyboard review and QA. This document does not claim the production Director already implements the system.

## Visual contract

Every shot must assign one visual responsibility to each layer:

| Layer | Responsibility | Must not become |
| --- | --- | --- |
| Evidence | prove, demonstrate, compare or provide real context | a small decorative screenshot |
| XIAO-Y | explain, react, warn, represent responsibility, guide a transition or settle a point | a permanent presenter sticker |
| Typography | a short callout, keyword, number or relationship label | a second full narration track |
| Motion | guide attention or express a change in information state | activity added only to hide a static page |

The system prefers a continuous evidence space. A character interruption must retain or return to the evidence that caused it. A relationship graphic must connect real objects or explicitly identify itself as an explanation. The renderer may choose animation primitives; it may not invent the narrative function.

## Visual modes

### `BRAND_BALANCED`

Default mode, derived from F2. It is suitable for general explanation, tutorials, rules, product logic and commentary where evidence is present but need not occupy every frame. Evidence commonly leads about 55–70% of the narrative interval and XIAO-Y has an explicit task. This range is a planning observation, not a validator threshold.

### `EVIDENCE_HEAVY`

Submode, derived from F1. Use when the UI, data, source, table, chart, before/after state or real operation is itself the story. Evidence commonly leads about 70–90%; XIAO-Y is `NONE` or `SUPPORTING`. F1 is retained and is not a rejected direction.

Mode selection follows `visual_job`, evidence availability and the cognitive change required. It must never be implemented as a percentage-only branch.

## One visual protagonist

Every shot declares exactly one `PRIMARY` protagonist. Other visible subjects are `SUPPORTING` or `BACKGROUND`.

Allowed protagonist kinds are `EVIDENCE`, `XIAOY`, `TEXT`, `NUMBER`, `COMPARISON` and `DIAGRAM`. A compiler must reject zero or multiple `PRIMARY` declarations. Evidence and XIAO-Y may share a frame; their roles must still be distinct.

## Target planning chain

```text
Beat
→ Visual Job
→ Visual Mode
→ Shot Plan
→ Protagonist
→ Evidence Treatment
→ Character Role
→ Motion Semantic
→ deterministic Visual Compiler
→ renderer-neutral EDT
→ Remotion pixels
```

The Director chooses meaning and registered asset references. It does not output `x`, `y`, width, height, crop pixels, font sizes or absolute paths.

## Acceptance boundaries

- A render that is valid, varied or animated can still fail because it feels like slides.
- A real screenshot is useful only when the relevant region is readable and supports the narration.
- Character identity and action consistency remain required even when Evidence is primary.
- A single 19.12-second reproduction proves a contract path, not stable long-form or daily production.
- Final watchability, mechanical feeling and PPT feeling remain human review questions.
