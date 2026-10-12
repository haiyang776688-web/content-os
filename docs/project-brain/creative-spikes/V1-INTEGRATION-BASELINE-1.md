# V1 Integration Baseline Closure

## Inputs

- FAI-001 baseline: `p0/alignment-runtime-integration-1@ef3b812d2479eeca826c0f225c525558c69f076f`
- Asset Aspect Ratio Hardening commits, applied in order:
  - `9c2d73b` — `fix: preserve visual asset aspect ratios`
  - `1e0a423` — `fix: retain semantic focus in aspect-safe crops`
- Common pre-integration base: `eea4b00e9b3809e16cd2c5b31123a5f4089cc00c`

The two asset commits cherry-picked without textual conflicts. The resulting renderer is the aspect-safe implementation: registered media uses an explicit uniform `media_transform`; the removed region-width/region-height `CropImage` sizing behavior is not present.

## Preserved capabilities

- `POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT`
- `AlignedTimingMap`
- `ALIGNED_OPT_IN`
- Existing Beat Timing Consumer
- alignment cache, invalidation, fallback, provenance, background JobEngine and model lifecycle
- production timing default remains `CURRENT`
- VLA Director → ShotPlan → Visual Compiler path
- registered-media aspect-ratio invariant with 0.5% tolerance
- `CONTAIN`, uniform `COVER_CROP`, and uniform `FOCUS_CROP`
- procedural geometry exemption
- `ASSET_ASPECT_RATIO_DISTORTED` BLOCKER before Storyboard approval

`DECISIONS.md` is unchanged.

## Validation

- FAI / TCU / VLA / VRE / aspect-ratio / job targeted tests: `38 passed`
- TypeScript no-emit check across the Remotion sources: `PASS`
- `git diff --check`: `PASS`
- Full repository suite: `252 passed`, `0 failed`, one dependency deprecation warning
- `ASSET_ASPECT_RATIO_DISTORTED` on valid integrated fixtures: `0 BLOCKER findings`
- Deliberately non-uniform fixture: correctly rejected as `ASSET_ASPECT_RATIO_DISTORTED`

The previously known `test_visual_binding_change_stales_edt_but_interface_language_does_not` failure does not reproduce on this integrated baseline; it passes with the complete suite.

## Result

**PHASE 0 PASS**

This branch is the only accepted base for MPH-001. It does not change production defaults or formal decisions.
