# Sample A deterministic A/B

## Variants

### A — CURRENT_TIMING

The current production-derived props use measured phrase ranges and the existing proportional timing behavior.

### B — ALIGNED_TIMING_CONSUMER

The aligned props use the experimental consumers for existing subtitle chunks and the two explicitly approved existing Beat bindings.

Every non-timing input is identical. The same Script, waveform, DirectorIR, effective ShotPlan semantics, Visual EDT, media, typography, composition, fps, resolution, and renderer are used in both runs.

## Identity controls

The full hashes are recorded in [tcu001-ab-metrics.json](evidence/tcu001-ab-metrics.json). Key identities are:

| Input | SHA-256 / artifact output hash |
|---|---|
| Script text | `ca462d45d2e1329c9ec6766afe01db8e54ab2bc2c6294e8ab1bcd66ce4b2f173` |
| Audio | `2d0278e8a2bfcc2c483b2958d60ba9d6f902990bb7b2a2edf7879ddbec2cf813` |
| DirectorIR | `633455882206fc2ec728c4962dbb38c09e5e02198374ca541c11ad5b8151e515` |
| Frozen effective ShotPlan semantics | `a5136a23bca90222ceedbb173c52faa719d024d279102bf45569231e55050fc0` |
| Visual EDT | `aad11fc10e7b1ed2f3f1493ac645bd3bd4414475c5344130a4b4eee4429ca50d` |
| CURRENT timing artifact | `64d382a382acee0147e5cec14939c76dea65f8b1640ca5b7baca778eff7871a5` |
| ALIGNED timing artifact | `dec3b23281d7344593d34c17cfa391e39f5b2cac280bf28aa62d61dc205e8762` |

Both variants contain:

- 95 total clips;
- 18 existing Beats;
- 18 effective shots in the frozen semantic snapshot;
- 45 subtitle chunks.

The CURRENT and ALIGNED semantic projection hashes are both `42944f0a419e955e4da62d1c18325e168e30d015ffc45d12d8b8b36b9b3d5f33`.

## Viewing evidence

- CURRENT render: **PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**
- ALIGNED render: **PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**
- [Synchronized comparison page](evidence/comparison.html)

The comparison page provides direct jumps to TG-001 through TG-008 and NC-001 through NC-010. It synchronizes both players so the viewer can inspect the visual change around TG-004, TG-006, TG-007, and normal regions without relying on the JSON metrics.

Static side-by-side frames are also generated at the key review timestamps. Each image places CURRENT on the left and ALIGNED on the right.
