# FAI-001 Result and Recommendation

## Final state

**FAI-PASS**

This pass is limited to the production integration of `POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT` for the **Existing Beat Timing Consumer**.

## Why it passes

- A formal, policy-free, hash-pinned `AlignedTimingMap` is implemented.
- Cache identity and invalidation cover audio, Script, engine, executable, model and configuration.
- Background run, status, progress, cancellation, retry, restart recovery and recompute use the existing job/stage/artifact system.
- Missing, corrupt, cancelled, failed, stale, insufficient and unapproved cases fall back deterministically to CURRENT.
- `CURRENT` remains the default.
- Alignment can retime only an existing Beat with a separate approved semantic binding.
- EDT and render manifests expose full timing provenance.
- A fresh 84.76-second real runtime regression reproduced the two TCU boundary improvements without changing 18 Beat identities or semantics.
- Four additional real utterances achieved 97.5–100% Script coverage with valid monotonic anchors.
- The required ten fault categories pass.
- No model binary, secret or absolute local dependency path is committed.

## Production recommendation

The implementation is suitable for a **constrained production opt-in** for the Existing Beat Timing Consumer. It is not recommended as a new default. Projects must remain `CURRENT` unless a human explicitly chooses `ALIGNED_OPT_IN`, a verified local model is available, and approved Beat bindings exist.

## Not established

- subtitle benefit;
- English, digits, proper nouns or multi-speaker robustness;
- broad voice/speaking-rate generalization;
- model download UX in the workbench;
- resumable partial ASR computation after a server restart;
- prosody repair;
- stable high-volume daily production economics.

No next phase is started and no formal decision is added to `DECISIONS.md` by this spike.
