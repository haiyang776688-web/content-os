# VLA-001 · Test B — Unseen Content Generalization

## New project

Script ID: `VLA-001-UNSEEN-SCRIPT`.

Topic: why a storyboard must expose visual responsibility and support modification/rejection before final render. The 44.6-second Chinese script was not used in VGB-001, VGB-002 or VRE-001. Evidence consists of tracked Content OS storyboard and workbench screenshots with registered semantic regions.

The Director supplied nine ordinary beats. The adapter generated all nine shots; no ShotPlan shot was written by hand.

## Automatic distribution after review

- Visual Jobs: `TRANSITION 2`, `PROVE 2`, `EXPLAIN 1`, `DEMONSTRATE 2`, `WARN 1`, `SUMMARIZE 1`.
- Visual Modes: `BRAND_BALANCED 5`, `EVIDENCE_HEAVY 4`.
- Shot Types: `CHARACTER_INTRO 2`, `EVIDENCE_HIGHLIGHT 2`, `RELATION_EXPLAIN 1`, `EVIDENCE_FOCUS 2`, `CHARACTER_RESPONSIBILITY 1`, `SUMMARY 1`.
- Evidence Treatments: `HIGHLIGHT_REGION 2`, `RELATION 1`, `FOCUS_REGION 2`, `DETAIL_CROP 1`.
- Character Roles: `GUIDE 1`, `RESPONSIBILITY 1`, `TRANSITION 1`, `SUMMARY 1`.

Every `PROVE` and `DEMONSTRATE` shot has Evidence as its only PRIMARY. The `EXPLAIN` relation shot has Diagram as PRIMARY and evidence in the background. XIAO-Y is PRIMARY only for the opening transition, the explicit responsibility warning, the return transition and the final summary.

## Pre-render edit

The initial adapter result classified B-B04 as `DEMONSTRATE / EVIDENCE_FOCUS / FOLLOW`. Storyboard Review challenged that assumption: the narration asserts a review requirement and the registered inspector screenshot is being used as proof. Before MP4 rendering, the operator changed:

- Visual Job: `DEMONSTRATE` → `PROVE`;
- Shot Type: `EVIDENCE_FOCUS` → `EVIDENCE_HIGHLIGHT`;
- Evidence Treatment: `FOCUS_REGION` → `HIGHLIGHT_REGION`;
- Motion Semantic: `FOLLOW` → `FOCUS`.

The revised contact sheet was regenerated and approved against the new plan hash.

## Result

- 1920×1080, 30 fps, 1338 frames, 44.6 seconds.
- One PRIMARY per shot: PASS.
- Mode responsibility change: PASS.
- Registered evidence use: PASS.
- No consecutive repeated Shot Type: PASS.
- Page-template/PPT regression: PASS by full contact-sheet and sampled-render inspection.
- New voice generation: intentionally out of scope; the visual proof MP4 has no audio track.

Final SHA-256: `85249d36b95bf3a6ba4053b8f9e3bfcfd433b32d25b99dd3dd15be253c0e55d8`.
