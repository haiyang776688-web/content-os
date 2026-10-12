# Visual System Migration

**Strategy:** add an isolated semantic ShotPlan and compiler, prove one F2-equivalent path, then migrate consumers. Existing artifacts and the VGB-002 Gold Masters remain intact.

## Current → target map

| Component | Decision | Current verified behavior | Target / reason |
| --- | --- | --- | --- |
| `DirectorIR` | **MODIFY** | production schema and GUI use Beat `pattern_id`, slots, action and motion; several descriptive fields have no render consumer | retain artifact ownership and graph; add a versioned ShotPlan output/adapter only after the slice proves consumption |
| `Beat` | **MODIFY** | script binding/order/timing are active; `visual_focus`, `visual_form`, `retention_function` are not production render inputs | preserve identity, script/fact bindings and human purpose; derive/validate `visual_job` and shots in a separate contract first |
| `Pattern` | **DEPRECATE** | eight patterns drive required slots and template selection | keep compatibility during migration; visual jobs + Shot Types become the semantic selection vocabulary |
| `Template` | **DEPRECATE** | twelve page-level layouts assign whole-frame composition | do not delete registry/assets; map legacy templates to Shot Types, then stop exposing page templates as the target Director choice |
| `VisualResolver` | **REPLACE** incrementally | combines semantic lookup, template allocation, action allocation, geometry, typography treatment and motion policy | new Visual Compiler consumes ShotPlan + registries + visual language and emits renderer-neutral EDT; formal cutover requires parity tests |
| `VisualProgression` | **MODIFY** | isolated human-authored screenshot operations proved context→crop→highlight progression; not a production artifact | reuse provenance/crop discipline and diagnostics inside compiler recipes; remove its fixed 2–4-state experimental constraint |
| Remotion Composition / Renderer | **KEEP** | renders EDT and can produce accepted F2 pixels; also contains some hidden text/motion styling policy | retain execution engine; move policy decisions into explicit EDT metadata/primitive recipes so Remotion performs `EDT → pixels` |
| Action allocator | **MODIFY** | selects a registered action from `character_intent` with repetition avoidance | accept `character_role`, map role to allowed intents, then allocate; preserve explicit human action override |
| QA | **MODIFY** | checks geometry, clipping, timing and repetition; model review is separate | add one-primary, evidence readability/provenance, text duplication, character justification and progression checks with warning/blocking ownership |

## Migration phases

### M0 — accepted direction and contracts

Record `DEC-011`, freeze the v1 visual vocabulary, classify Skill Matrix principles and pass static architecture review. No production path changes.

### M1 — isolated vertical slice

Compile the frozen VGB-002 script/evidence through `ShotPlan → Visual Compiler → EDT → Remotion`. Compare roles, evidence clarity, sequence, captions and anti-PPT behavior to F2. Keep the entry point isolated.

### M2 — compatibility adapter

Add a versioned Beat/DirectorIR-to-ShotPlan adapter behind an opt-in flag. The adapter must not silently translate missing evidence into text cards. Storyboard shows both semantic plan and rendered contact sheet.

### M3 — formal production opt-in

Write ShotPlan/compiled EDT as formal artifacts, preserve human overrides, add migration and rollback tests, and run a GUI-only controlled episode. Old Resolver remains selectable until parity and edit preservation pass.

### M4 — deprecation

Stop new Director outputs from selecting Pattern/Template pages. Retain readers/migrations for existing artifacts. Remove hidden renderer policy only after generated EDT carries equivalent explicit metadata.

## Compatibility and rollback rules

- Never rewrite existing DirectorIR, EDT or VGB artifacts in place.
- Every new contract has a schema version and deterministic validation.
- Legacy Pattern/Template IDs remain readable until all stored projects migrate.
- Human-selected actions, crops, text and timeline edits require an explicit preservation/rebase contract before formal regeneration.
- A failed visual reproduction stops migration at M1; it does not trigger patches in the production Resolver.

## Static Architecture Review

Review date: 2026-09-29. Scope: the target documents and proposed M1 boundary.

| Risk | Result | Evidence / control |
| --- | --- | --- |
| Duplicate concepts | **PASS** | Visual Job is narrative function; Shot Type is composition primitive; Evidence Treatment is proof presentation; Motion Semantic is reason for change. Detailed Skill classification has one canonical research file and one thin visual application profile. |
| Write-only fields | **PASS FOR TARGET CONTRACT** | every proposed Shot field has a named validator/compiler/QA consumer in `VISUAL_SYSTEM_VNEXT.md`; M1 tests must assert output changes or validation for every field |
| AI decides geometry | **PASS** | ShotPlan admits only registered IDs, normalized evidence regions and semantic/timing anchors; pixel geometry belongs to deterministic compiler recipes |
| Renderer hidden policy | **PASS FOR M1 DESIGN** | all protagonist, treatment, role, callout and motion decisions are encoded in EDT metadata/primitives; Remotion may only draw supplied primitives. Existing production renderer policy remains documented migration debt |
| Unnecessary abstraction | **PASS WITH LIMIT** | one new semantic contract and one compiler boundary are introduced; no new Agent, renderer, Platform Profile, Narration Unit or production artifact type is added in M1 |

The review approves M1. It does not approve production cutover.
