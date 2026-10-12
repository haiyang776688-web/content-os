# VLA-001 · Post-Review Asset Distortion

## Human post-render finding

After the original VLA-001 Test B was rendered and reported, human viewing found that multiple screenshots were scaled non-uniformly. UI text, controls and screenshot regions appeared too wide or too tall. This finding supersedes the original visual-inspection claim for asset geometry; the original files and hashes remain in the record and are not rewritten as if the defect never existed.

## Root cause

The real implementation defect was in `vnext/renderers/remotion/project/src/vre001/Renderer.tsx`. The old `CropImage` mapped a registered source region by setting image width to `100 / region.width` and image height to `100 / region.height` independently. When the registered region ratio differed from the destination box ratio, the browser applied different horizontal and vertical scale factors.

The defect was in renderer/media geometry. It was not a ShotPlan semantic error and did not invalidate the Director → ShotPlan architecture. It did mean the earlier narrow production opt-in recommendation had to become **NARROW PRODUCTION OPT-IN CONDITIONED ON ASPECT-RATIO HARDENING**.

## Resolution: ASSET_ASPECT_RATIO_INVARIANT

The hardening adds one invariant for every registered visual source:

> All registered visual assets preserve their intrinsic aspect ratio. Layout adaptation uses contain, uniform cover/crop, or uniform focus zoom/pan. Non-uniform scaling of source assets is forbidden.

The Asset Registry contract now records or resolves intrinsic width, intrinsic height and intrinsic aspect ratio. Visual Compiler chooses `CONTAIN`, `COVER_CROP` or `FOCUS_CROP`, computes one uniform scale plus crop/pan offsets, and emits the final media transform. Renderer consumes those explicit values. XIAO-Y character assets use `CONTAIN`. Video and imported SVG assets use the same preservation contract; procedural shapes are explicitly distinguished and exempt.

Mechanical QA checks the final transform with a 0.5% tolerance. A violation produces:

```text
code: ASSET_ASPECT_RATIO_DISTORTED
severity: BLOCKER
```

The Storyboard Review projection now displays Asset, Intrinsic ratio, Fit mode, Crop region and Aspect policy. Its approval function refuses a review unless the aspect-ratio check passes.

## Same-input Test B rerender

The hardening reran the original VLA-001 Test B with the same script, Evidence, timing, semantic edits and reviewed ShotPlan.

- Reviewed ShotPlan canonical SHA-256 before and after: `97ced1ac05224571ecd27449a2eb94463dc05fd57e98a6f96048c7a6ca4a327d`.
- Duration: `44.6` seconds.
- Frames: `1338`.
- Resolution / frame rate: `1920×1080 / 30 fps`.
- Registered visual layers checked: `10`.
- Mechanical result: `PASS`, zero findings.
- Initial invariant-only hardening MP4 SHA-256: `9dee1f276a0cf95db3446cffd726e7d97d23b536c5a1929ef0342a2a2cd73a05`. It removed non-uniform scaling, but the completion audit found that extreme wide/tall regions were being cropped too aggressively.
- Final focus-preserving MP4 SHA-256: `1687834bf6fb3cd0ef7255e3b4ec78572d0339e2c92cb9aaa022743e75e146ff`.
- Original defective MP4 SHA-256 retained for comparison: `85249d36b95bf3a6ba4053b8f9e3bfcfd433b32d25b99dd3dd15be253c0e55d8`.

Five representative before/after comparisons cover a full contact-sheet region, the narrow Director inspector, the preview stage, the mixed XIAO-Y/evidence composition and the wide history region. Human inspection confirms normal UI font and button proportions, circular details remain circular, XIAO-Y is not compressed or stretched, and focused evidence remains readable. The final focus policy keeps the destination covered while preserving as much of an extreme wide/tall semantic region as its ratio permits. The visual sequence does not regress to a page-template slideshow.

## Remaining risks

- Test B proves still-image Evidence and XIAO-Y PNG behavior at 1920×1080. The video contract is implemented and type-checked, but this spike does not claim a separate moving-video acceptance render.
- Imported SVG dimension and `viewBox` preservation are defined in the resolver/renderer contract; this Test B contains no imported SVG fixture.
- Focus-region readability still depends on the quality of registered semantic regions. A poorly registered region can be preserved correctly and still point at the wrong evidence.
- This is short-form experimental-path evidence. It does not establish long-form rhythm or authorize a production-default switch.

## Opt-in status

The aspect-ratio condition is **CLEARED** for the previously recommended narrow experimental opt-in. This does not switch the production default and does not broaden the VLA-001 evidence beyond its original short-form scope.
