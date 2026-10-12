# TCU-001 Consumers

## Consumer A — aligned subtitles

The subtitle consumer receives the existing 45 subtitle clips. It preserves each `clip_id`, text string, order, and chunk count.

For each existing chunk boundary it tries to resolve the corresponding approved Script character span. It uses the aligned timestamp only when phrase coverage, anchor confidence, monotonic duration, and a conservative maximum boundary-shift guard all pass. A failed boundary uses the current timing value. A failed phrase remains on current timing.

The consumer never reads a raw Whisper segment boundary and never asks ASR to re-segment the Script.

Fallback behavior is covered for:

- a missing alignment artifact;
- partial phrase coverage;
- low-confidence or unresolved anchors;
- excessive boundary movement;
- invalid or non-monotonic timing.

## Consumer B — existing Beat timing

The Beat consumer receives the existing Visual EDT clips and a separate list of two user-approved Script-to-Beat bindings:

- `TG-004` → existing Beat `B-08-02`;
- `TG-007` → existing Beat `B-09-02`.

The consumer resolves each approved Script anchor against `AlignedTimingMap`, then moves only the boundary between the two already existing Beats. Clips inside each of those Beats are projected proportionally into the revised range. It does not create or remove a Beat and does not change a pattern, template, asset, Visual Job, Shot type, geometry, or motion policy.

If the binding is not explicitly approved, the Beat is missing, confidence is below threshold, or the timestamp falls outside the legal neighboring Beat range, the existing timing remains unchanged.

## Geometry and rendering boundary

The consumer emits timing-adjusted renderer props for this isolated experiment. Geometry remains the frozen Visual EDT geometry. The Remotion component renders those props and contains no alignment policy.

The A/B semantic projection deliberately strips only timeline timing and TCU provenance metadata. Its canonical hash is identical for CURRENT and ALIGNED, which proves that the experiment changes WHEN while preserving WHAT.
