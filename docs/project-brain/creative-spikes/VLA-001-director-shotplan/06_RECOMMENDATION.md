# VLA-001 · Recommendation

**NARROW PRODUCTION OPT-IN CONDITIONED ON ASPECT-RATIO HARDENING.**

This replaces the pre-finding recommendation recorded at the end of the original VLA-001 run. Human post-render review subsequently found that Test B screenshots had been non-uniformly scaled. The architecture recommendation remained valid, but opt-in eligibility was blocked until the renderer/compiler defect was fixed and the same Test B passed again.

The condition is now **CLEARED** by the post-review hardening evidence: the original reviewed ShotPlan hash is unchanged, the same 44.6-second Test B was re-rendered, all ten registered-asset layers passed `ASSET_ASPECT_RATIO_INVARIANT`, and before/after frames show uniform focus crop instead of horizontal/vertical stretch. See `POST_REVIEW_ASSET_DISTORTION.md`.

The adapter generalized beyond F2, preserved the known F2 logic, kept geometry in the compiler, kept policy out of the renderer, and allowed Storyboard Review to catch and repair a semantic classification before final rendering.

The opt-in should expose `DirectorIR → ShotPlan → representative frames → semantic edit/reject/approve → VisualCompiler` behind an explicit project/run flag. The existing production path must remain the default. The opt-in should initially support the tested evidence and character recipes and record every operator edit as a revision-bound review event.

Do not cut over the production default yet. VLA-001 covers two short projects, one silent unseen visual proof, deterministic region selection and a standalone review surface. It does not prove long-form rhythm, real-model Director reliability across broad topics, GUI persistence inside the formal Workbench, final voice timing, or stable daily production.

The next authorized step, if accepted, is production opt-in wiring only. It should not expand the visual language or start four-minute output.
