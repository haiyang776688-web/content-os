# TCU-001 Recommendation

## Decision

**TCU-PASS — based on the existing Beat timing consumer.**

The aligned timing artifact produces meaningful consumer value for two already approved, already existing Beat boundaries. Median error falls from 1,289 ms to 194 ms, no new Beat boundary appears in the six `NO_BOUNDARY` cases, no normal-control window gains a Beat boundary, and semantic/count/default invariants remain intact.

The subtitle consumer is not the basis for this pass. It preserves all content and segmentation and introduces no additional normal-control boundary count, but it does not improve the two positive-target median. That result should remain visible so later work does not overstate the scope of the evidence.

## What this proves

For Sample A, a renderer-neutral map of approved text anchors can improve **when an existing Beat occurs** without changing what the Beat means. It also demonstrates deterministic fallback for missing and partially covered alignment.

## What this does not prove

- It does not prove multi-sample generalization.
- It does not prove subtitle improvement.
- It does not repair the voice waveform or prosody.
- It does not justify raw ASR segmentation as creative policy.
- It does not establish a production lifecycle for alignment models or artifacts.
- It does not change the production default.

## Next-step boundary

The acceptance criteria permit recommending a later FAI-001 Forced Alignment Integration Spike to address model distribution, caching, background execution, cancellation, recovery, provenance, fallback, and artifact invalidation. **FAI-001 is not started by this work.** Any production opt-in remains a separate human decision after broader sampling.
