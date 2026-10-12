# VRE-001 · Implementation

## Path

```text
evidence/input.json
→ build_f2_shot_plan()
→ ShotPlan validation
→ VisualCompiler
→ renderer-neutral EDTClip envelopes
→ explicit Remotion primitives
→ VRE-001-F2-Reproduction.mp4
```

`vnext/phase2/experimental/visual_language_v1.py` owns the v1 semantic contracts, compatibility policy, action-role mapping, deterministic layouts and EDT compilation. It is isolated under `experimental`; it does not create formal project artifacts or alter production state.

`src/vre001/Renderer.tsx` consumes concrete clips, geometry, colors, asset references and animation primitives. It contains no Shot Type, Visual Job or Visual Mode branching. It draws only supplied background, evidence, character, underline, relationship, node, callout, chrome, subtitle and audio layers.

`scripts/vre001.py` compiles, renders and compares the result with the F2 Gold Master. Generated previews and the MP4 remain outside Git. The cloned voice and pinned font remain ignored local inputs; unit tests replace media with synthetic registered files so a clean checkout can still test the compiler contracts without committing private voice data.

## Generated evidence

Output directory:

`${LOCAL_ROOT}/Documents/Codex/2026-09-22/referenced-chatgpt-conversation-this-is-an/outputs/vre-001`

It contains the semantic ShotPlan, renderer-neutral EDT, Remotion props, compiler diagnostics, render log, MP4, contact sheets and verification result.

## Boundary observed

The planner is a frozen F2 reproduction fixture. It proves that the target contract can express and render the accepted visual logic. It is not a general AI Director implementation and is not wired into the formal GUI path.
