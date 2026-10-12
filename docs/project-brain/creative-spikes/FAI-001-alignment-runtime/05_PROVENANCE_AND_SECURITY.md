# Render Provenance and Security

## Render provenance

The EDT, resolved Remotion props and final `RENDER` artifact carry timing provenance. The manifest includes:

- `timing_mode` (`CURRENT` or `ALIGNED`);
- alignment artifact ID and output hash;
- engine and version;
- model name and SHA-256;
- coverage;
- `fallback_used` and fallback reason;
- the approved bindings actually applied.

The alignment map and binding artifacts are also dependencies of the opt-in resolved composition and EDT. This makes the final render traceable without moving alignment policy into Remotion.

When an alignment run fails or is unusable, `AudioClock` retains its deterministic AUDIO_TIMING_MAP result. The EDT remains buildable, Remotion still receives CURRENT timing, and the fallback reason remains visible in provenance.

The committed `FAI-001-FALLBACK-CURRENT.mp4` is a real H.264 render from props marked `timing_mode=CURRENT`, `fallback_used=true`, and `reason=ALIGNMENT_RUNTIME_NOT_AVAILABLE`. It completes at 1280×720, 30 fps, 1.5 seconds without an alignment artifact. Its props hash, video hash and media probe are recorded in `evidence/fallback-current-render-verification.json`.

## Permission and trust boundary

- only `ALIGNMENT` may create `ALIGNED_TIMING_MAP`;
- only `HUMAN` or `DIRECTOR` may create `BEAT_TIMING_BINDINGS`;
- only a `HUMAN` API action may opt a project into aligned timing;
- raw ASR output is disposable cache evidence, not a creative artifact;
- the production renderer cannot infer or introduce semantic boundaries.

## Repository hygiene

The repository ignores alignment model binaries and disposable alignment caches. The real verification runner exports only sanitized evidence: content hashes, engine/model identity, measurements and policy-free anchors. It does not export API keys, credentials, environment files, model files, executable files or absolute local dependency paths.
