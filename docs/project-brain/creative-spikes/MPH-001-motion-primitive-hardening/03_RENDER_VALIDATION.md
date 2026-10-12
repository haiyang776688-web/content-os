# Render Validation

## Motion Primitive Gallery

- Output gallery: **PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**
- Contact sheet: **PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**
- Machine report: [motion-gallery-verification.json](evidence/motion-gallery-verification.json)
- Format: 1920×1080, 30fps, 15.0 seconds
- Gallery SHA-256: `3e5e48bfe929d0e2d7d79e7f6101f895da9b2298c41f23dad675682ea420efbf`

Each non-static primitive received 1.5 seconds. Frames were rendered at local animation start, middle and settled positions. Pixel comparison requires both start→middle and middle→settled to change. All 10 required primitives passed.

The contact sheet was also inspected visually. `MATCHED_WIPE` exposes a horizontal clip boundary; `DRAW_CONNECTION` draws only the two procedural relation paths; `DRAW_UNDERLINE` grows only procedural width; media primitives never stretch source pixels.

## VLA true-render regression

Evidence is recorded in [vla-regression-verification.json](evidence/vla-regression-verification.json). The reviewed Test A/B contact sheets are **PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**.

Test A rendered 574 frames / 19.178667 seconds with audio. Test B rendered 1,338 frames / 44.6 seconds. Render SHA values changed because CONNECT supporting Evidence now consumes `FADE_IN` while RELATION alone consumes `DRAW_CONNECTION`; ShotPlan semantics, Visual Job distributions, PRIMARY responsibility and geometry ownership did not change.

Visual inspection found no asset distortion and no new page-template or PPT regression.
