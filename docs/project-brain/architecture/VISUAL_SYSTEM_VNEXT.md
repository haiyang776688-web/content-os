# Visual System vNext

**Status:** TARGET CONTRACT / NOT THE CURRENT PRODUCTION PATH

**Accepted visual direction:** `DEC-011`

**Renderer:** Remotion remains the pixel executor under `DEC-001`.

## Boundary

The target system converts approved narrative meaning into a renderer-neutral timeline without asking a model for geometry.

```text
Bound Script + Facts + registered Evidence
                 ↓
          existing Director Beat
                 ↓
              ShotPlan
                 ↓
     deterministic Visual Compiler
        ↙           ↓            ↘
Asset Registry  Visual Language  Timing anchors
                 ↓
       renderer-neutral EDT
                 ↓
              Remotion
                 ↓
         storyboard / pixels / QA
```

The first implementation is an isolated vertical slice. It does not replace `DirectorIR`, `VisualResolver` or the formal Workbench flow.

## ShotPlan contract

```text
ShotPlan
  schema_version
  plan_id
  source_script_id
  visual_mode
  beats[]

ShotBeat
  beat_id
  script_segment_id
  visual_job
  shots[]

Shot
  shot_id
  shot_type
  start / end timing_anchor
  protagonist {primary, supporting[], background[]}
  evidence_asset_id?
  evidence_treatment?
  evidence_region?
  character_role?
  semantic_focus
  motion_semantic
  callout?
```

All enums are closed in v1. `visual_job` is consumed by compatibility validation and mode selection. `shot_type` selects a compiler recipe. `protagonist` drives layer hierarchy and QA. `evidence_treatment` produces evidence operations and provenance. `character_role` drives action allocation. `motion_semantic` selects a renderer-neutral animation intent. `timing_anchor` produces EDT ranges. No target field is write-only.

The Director may propose this semantic contract. It must not output geometry, crop pixels, font size, CSS, filesystem paths or unregistered asset/action IDs.

## Visual Job policy

| Job | Preferred primary | Mode preference | Allowed Shot Types | Evidence treatment | XIAO-Y role | Motion semantics | QA expectation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PROVE` | EVIDENCE | EVIDENCE_HEAVY | EVIDENCE_CONTEXT/FOCUS/DETAIL/HIGHLIGHT, RELATION_EXPLAIN | all except decorative CALLOUT alone | NONE/GUIDE | FOCUS, REVEAL, CONNECT, SETTLE | evidence asset and supporting region required |
| `DEMONSTRATE` | EVIDENCE | EVIDENCE_HEAVY | EVIDENCE_CONTEXT/FOCUS/DETAIL/COMPARE | FULL_CONTEXT, FOCUS_REGION, DETAIL_CROP, BEFORE_AFTER | NONE/GUIDE | FOLLOW, FOCUS, COMPARE, SETTLE | operation/state must exist in evidence |
| `EXPLAIN` | EVIDENCE or XIAOY | BRAND_BALANCED | CHARACTER_EXPLAIN, EVIDENCE_CONTEXT/FOCUS, RELATION_EXPLAIN | any relevant treatment | EXPLAINER/GUIDE/NONE | REVEAL, FOCUS, CONNECT | visual adds a cognitive change beyond subtitle |
| `COMPARE` | COMPARISON | context-dependent | EVIDENCE_COMPARE, RELATION_EXPLAIN | BEFORE_AFTER or paired context/detail | NONE/EXPLAINER | COMPARE, REVEAL, SETTLE | basis and both sides declared |
| `REACT` | XIAOY | BRAND_BALANCED | CHARACTER_REACTION, KEYWORD_PUNCTUATION | context retained when relevant | REACTION | INTERRUPT, RETURN | cause exists; next return anchor valid |
| `WARN` | XIAOY or EVIDENCE | BRAND_BALANCED | CHARACTER_REACTION/RESPONSIBILITY, EVIDENCE_HIGHLIGHT, KEYWORD_PUNCTUATION | HIGHLIGHT_REGION, DIM_NON_FOCUS, CALLOUT | WARNING/RESPONSIBILITY/NONE | INTERRUPT, FOCUS, RETURN | risk is source-bound or labelled opinion |
| `TRANSITION` | XIAOY or EVIDENCE | BRAND_BALANCED | CHARACTER_INTRO, EVIDENCE_CONTEXT, KEYWORD_PUNCTUATION | FULL_CONTEXT, FOCUS_REGION | GUIDE/TRANSITION/NONE | FOLLOW, CONNECT, RETURN | outgoing and incoming anchors declared |
| `SUMMARIZE` | XIAOY/TEXT/DIAGRAM | BRAND_BALANCED | SUMMARY, END_CARD | RELATION/CALLOUT only when grounded | SUMMARY/NONE | CONNECT, SETTLE | no new unsupported claim |

Mode preference is a resolver hint. `PROVE` can appear inside a Brand-balanced episode; one evidence-heavy episode can contain a short reaction. The system does not infer the global mode from measured screen time.

## Renderer-neutral EDT profile

The vertical slice uses the existing `EDTClip` envelope and reserves semantic metadata:

- `metadata.visual_language = XIAOY_EVIDENCE_EDITORIAL_V1`
- `metadata.shot_id`, `visual_job`, `shot_type`
- `metadata.protagonist_role`
- `metadata.evidence_treatment`, `evidence_source_sha256`, normalized source region
- `metadata.character_role`, resolved `action_id`
- `motion.semantic` plus a compiler-resolved primitive

EDT owns concrete timeline ranges, normalized positions, crop geometry, layer order and renderer-resolved primitives. Remotion consumes these values. Renderer components may implement primitive drawing but cannot choose a Shot Type, evidence treatment, protagonist or copy.

## Visual Compiler responsibilities

1. Validate the ShotPlan against the Visual Job policy.
2. Resolve registered evidence and character assets, preserving hashes and IDs.
3. Select a layout recipe from Shot Type and Visual Mode.
4. Convert normalized evidence regions into deterministic crop/highlight geometry.
5. Allocate an action from `character_role → semantic intent → registered actions`.
6. Convert Motion Semantic into an explicit primitive sequence.
7. Produce short typography layers without changing script or evidence text.
8. Emit diagnostics and QA metadata.

The compiler must fail on missing evidence, multiple primary protagonists, an incompatible role, unregistered assets, invalid normalized regions, narration-duplicating callouts or a relationship without named endpoints.

## Motion Primitive Capability Contract

**Verified in MPH-001.** The experimental Visual Compiler and Remotion renderer share one closed, machine-readable capability contract for `NONE`, `PUSH_IN`, `FADE_IN`, `FOLLOW_PATH`, `MATCHED_WIPE`, `POP_CUT`, `RETURN_TO_ANCHOR`, `DRAW_CONNECTION`, `SETTLE_HOLD`, `DRAW_UNDERLINE` and `LABEL_REVEAL`.

Every declared primitive has an observable deterministic consumer and explicit allowed layer kinds. `DRAW_CONNECTION` is a RELATION-only procedural path behavior. `DRAW_UNDERLINE` is UNDERLINE-only, and `LABEL_REVEAL` is CALLOUT-only. `MATCHED_WIPE` is a true EVIDENCE clip reveal rather than a fade alias. A CONNECT shot may retain its high-level semantic while supporting registered media uses an allowed media primitive.

Unknown names, declared capabilities without a Renderer consumer and unsupported primitive/layer pairs are BLOCKERs before render. Storyboard Review includes this QA beside the Asset Aspect-Ratio invariant, and the Renderer repeats the assertion rather than silently falling back to `NONE`.

The primitive layer may animate opacity, uniform container scale, translation, clipping/masking and procedural drawing. It cannot choose layout geometry or apply non-uniform transforms to registered media. Motion choreography and motion-design quality remain outside this verified capability contract.

## Motion Design Contract

**Verified as an experimental opt-in in MDC-001.** A renderer-neutral `MotionDesignPlan` sits between ShotPlan meaning and numeric Visual Compiler realization. Its first vocabulary is deliberately limited to EXPLAIN, FOCUS, IMPACT_WARN and CONNECT phrases composed from qualitative phases: anticipation, primary action or impact, secondary response, settle and hold.

The semantic plan declares PRIMARY / SECONDARY / BACKGROUND responsibility, relative order and SUBTLE / NORMAL / STRONG strength. It contains no frame counts, pixels, scales, easing curves, CSS or raw animation code. The deterministic Compiler owns numeric phase windows, offsets, primitive progress and uniform container-scale keyframes. Remotion consumes the compiled values without selecting a phrase or interpreting Shot Type, Visual Job or Director meaning.

Motion Design does not replace the MPH primitive vocabulary. Every emitted primitive/layer pair still passes the authoritative MPH capability contract. Storyboard mechanical review combines Asset Aspect-Ratio, Motion Primitive and Motion Design QA. The opt-in is disabled on the production path; production timing remains `CURRENT`.

## Asset Aspect-Ratio Invariant

**All registered visual assets preserve their intrinsic aspect ratio. Layout adaptation uses contain, uniform cover/crop, or uniform focus zoom/pan. Non-uniform scaling of source assets is forbidden.**

This invariant applies to image and screenshot evidence, video, XIAO-Y character PNGs, logos, icons, element assets and imported SVGs. Each resolved visual asset exposes `intrinsic_width`, `intrinsic_height` and `intrinsic_aspect_ratio`. Every compiled visual-asset clip exposes `aspect_ratio_policy = PRESERVE`, one of `CONTAIN / COVER_CROP / FOCUS_CROP`, and an explicit final media transform where `scale_x == scale_y` within 0.5%. Cropping may discard source pixels; it must never simulate crop by stretching the source.

The Visual Compiler owns the destination box, uniform scale and crop/pan offset. Director and ShotPlan remain geometry-free and cannot emit `x`, `y`, `width`, `height`, `scale_x` or `scale_y`. The renderer consumes the explicit transform and does not reinterpret Evidence Treatment or choose its own fit policy.

Video uses the same intrinsic-dimension and uniform-transform contract as still images. Registered raster, logo, icon and element assets use the same contract. Imported SVG assets resolve dimensions from `viewBox` or intrinsic width/height and render with their aspect ratio preserved. Procedural geometry such as lines, rectangles, underlines, arrows and diagram connections is explicitly marked `PROCEDURAL` and is exempt; only those primitives may use a non-uniform SVG viewport such as `preserveAspectRatio="none"`.

## Storyboard review projection

The target Storyboard Gate shows, per shot:

- ordered shot sequence and timing;
- primary/supporting/background protagonist;
- visual job and mode;
- evidence asset, treatment and source region;
- asset intrinsic ratio, fit mode, crop region and `PRESERVE` policy;
- XIAO-Y character role and resolved action;
- start/end stills plus a contact sheet;
- mechanical and semantic warnings.

This is a projection of ShotPlan + EDT, not an independent editable truth source.

## QA layers

### Mechanical QA

Checks schema, timing overlap/gaps, registered assets, source hashes, safe area, clipping, subtitle continuity, duplicate action/shot warnings, readable evidence geometry and one-primary constraint. It also checks final media transforms against intrinsic dimensions and emits the `ASSET_ASPECT_RATIO_DISTORTED` **BLOCKER** when policy, fit mode, source ratio or `scale_x / scale_y` violates the 0.5% tolerance. Storyboard approval is disabled while that blocker exists.

### Semantic / Visual QA

Checks whether evidence supports narration, whether the chosen treatment exposes the relevant region, whether XIAO-Y has a justified role, whether text duplicates narration and whether interruption/return/connection progression is logical.

### Human review

Answers “Would I keep watching?”, “Does this feel mechanical?” and “Does this still feel like PPT?”. No model majority vote replaces H3 or H4.

## v1 exclusions

Full DirectorIR migration, audio-first Narration Units, long-form production, Track C, HyperFrames, Platform Profiles, 9:16, publishing and Analytics are outside this contract.
