# VLA-001 · Static Architecture Review

| Check | Result | Evidence |
|---|---|---|
| Duplicate concepts | PASS WITH COMPATIBILITY NOTE | `ShotPlan.visual_mode` remains the VRE-001 plan-wide override; `ShotBeat.visual_mode` expresses VLA-001 responsibility changes. Both have separate compiler consumers. A later schema revision may rename the plan field to `default_visual_mode`, but this spike does not break VRE-001. |
| Write-only fields | PASS | Plan/beat identity, mode, job, type, protagonist, evidence binding/treatment, character role, semantic focus, motion and callout all reach validation, review, compiler output or provenance. Tests assert the plan/beat fields in compiled output. |
| Director decides geometry | PASS | Tests recursively reject geometry keys in generated ShotPlan. Coordinates appear only in registered asset regions and compiler recipes. Registered regions are asset metadata, not Director decisions. |
| Renderer hides visual policy | PASS | Renderer source contains no Visual Job, Visual Mode, Shot Type or Evidence Treatment branch. It draws explicit compiler layers and motion primitives. |
| Unnecessary abstraction | PASS WITH LIMIT | One adapter, one review contract and one existing compiler/renderer path are used. No new Agent, provider, template system or production service was introduced. The standalone HTML review surface is spike infrastructure and is not presented as formal Workbench integration. |

VLA-001 passes the M1 architecture boundary for a narrow production opt-in. This review does not approve a default-path migration.
