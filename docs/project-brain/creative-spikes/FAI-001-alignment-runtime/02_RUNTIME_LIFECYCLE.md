# Runtime, Model and GUI Lifecycle

## Runtime states

The alignment state API exposes:

```text
NOT_REQUIRED
NOT_AVAILABLE
QUEUED
RUNNING
READY
FAILED
CANCELLED
STALE
FALLBACK
```

It also exposes requested mode, effective state, fallback use/reason, model status, artifact ID/hash, cache key, background-job progress and available GUI actions.

The existing local `JobEngine`, `StageCache`, artifact dependency graph and gates are reused. FAI-001 does not add a second checkpoint framework.

Available operations are:

- read alignment status;
- human-only switch between `CURRENT` and `ALIGNED_OPT_IN`;
- enqueue in the background;
- observe progress;
- cancel cooperatively;
- retry after failure or cancellation;
- recover an interrupted in-process job as FAILED after server restart;
- recompute after an identity change;
- submit approved Beat bindings.

The server restart behavior is deliberately honest: an in-process `whisper.cpp` process is not falsely marked resumable. The orphaned job becomes FAILED with `SERVER_RESTARTED`; its immutable inputs and cache identity allow a safe retry. If the completed artifact already exists, retry reuses it.

## Model lifecycle

The runtime supports:

- explicit executable discovery from `CONTENT_OS_WHISPER_CPP` or local `PATH`;
- explicit model discovery from `CONTENT_OS_ALIGNMENT_MODEL` or the managed data directory;
- SHA-256 and version verification;
- a user-triggered verified copy into `<content-os-data>/models/alignment/`;
- explicit `MISSING`, `CORRUPT`, `VERSION_MISMATCH`, `READY` states.

There are no silent downloads. The official `ggml-medium.bin` expected SHA-256 is pinned in configuration. Model binaries and disposable alignment caches are excluded from Git. A future GUI may attach download progress and license/source presentation to the exposed install action; that download UI is not implemented by this spike.

## Deterministic fallback

`CURRENT` remains the project default even when a valid model and alignment artifact are present. In `ALIGNED_OPT_IN`, missing model, missing voice, process failure, cancellation, stale inputs, insufficient coverage, missing bindings, low confidence and artifact-integrity failure all produce CURRENT timing. Render provenance records why fallback happened.
