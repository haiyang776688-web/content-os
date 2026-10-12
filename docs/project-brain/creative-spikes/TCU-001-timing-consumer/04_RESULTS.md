# TCU-001 Results

## Existing Beat consumer

| Ground Truth | Human target | CURRENT | ALIGNED | CURRENT error | ALIGNED error |
|---|---:|---:|---:|---:|---:|
| TG-004 | 72,780 ms | 71,820 ms | 72,880 ms | 960 ms | 100 ms |
| TG-007 | 82,572 ms | 80,954 ms | 82,860 ms | 1,618 ms | 288 ms |

The median absolute error falls from **1,289 ms to 194 ms**. The two visible boundary shifts are 1,060 ms and 1,906 ms, roughly 31.8 and 57.2 frames at 30 fps, so this is observable timing movement rather than a sub-frame metric change.

Across the six `NO_BOUNDARY` cases, the aligned Beat consumer adds no new boundary. The current TG-006 false Beat hit at 80,954 ms is removed because the existing `B-09-01 → B-09-02` boundary moves to 82,860 ms.

Across the ten normal controls, no Beat control gains an additional boundary.

## Subtitle consumer

The aligned subtitle consumer adjusts timing in 34 of 45 existing chunks while preserving all text, IDs, order, and chunk count.

For the two approved positive targets, subtitle median error changes from **270.5 ms to 319.5 ms**. This does not establish a subtitle benefit. TG-004 remains on deterministic fallback; TG-007 lands at 288 ms. The subtitle result is therefore recorded as **no proven positive benefit on the two positive targets**.

Two normal-control windows, NC-008 and NC-009, contain a shifted existing subtitle boundary. Their hit count does not increase, and those controls are phrase-context normal regions rather than millisecond boundary labels. This is recorded as a timing change, not hidden; it is not classified as a new segmentation regression.

## Contract checks

- Script meaning unchanged: **PASS**
- DirectorIR unchanged: **PASS**
- effective ShotPlan semantic hash identical: **PASS**
- Visual EDT input hash identical: **PASS**
- Beat count `18 → 18`: **PASS**
- effective Shot count `18 → 18`: **PASS**
- subtitle chunks `45 → 45`: **PASS**
- raw ASR segments used as cuts: **NO**
- deterministic missing-alignment fallback: **PASS**
- deterministic partial-coverage fallback: **PASS**
- production default changed: **NO**
- `DECISIONS.md` changed: **NO**

## Visual evidence

The two full renders and synchronized comparison page are the primary viewing evidence. Static checks cover:

- TG-004 at 72.4 s: CURRENT has already entered `B-08-02`; ALIGNED remains in `B-08-01` until the approved boundary;
- TG-006 at 81.0 s: CURRENT cuts inside the forbidden range; ALIGNED does not;
- TG-007 at 82.0 s: CURRENT has entered `B-09-02` too early; ALIGNED remains in `B-09-01` until close to the approved boundary;
- NC-004 at 31.5 s: normal-control spot check.

Final render hashes, media metadata, decoded-audio equality, and static evidence hashes are recorded in `tcu001-verification.json` after rendering.

Original-resolution inspection of all four side-by-side frames passed. The Beat movement is plainly visible at TG-004 and TG-007, the current false cut in TG-006 disappears, and NC-004 retains the same state. The signed observations are in `evidence/visual-inspection.json`.
