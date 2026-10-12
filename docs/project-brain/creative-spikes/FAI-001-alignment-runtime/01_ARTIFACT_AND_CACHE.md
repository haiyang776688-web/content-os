# AlignedTimingMap and Cache Identity

## Formal artifact

Production now has a strict, renderer-neutral `AlignedTimingMap` contract. Each artifact records:

- audio artifact ID and SHA-256;
- approved Script artifact ID and normalized-text SHA-256;
- engine name, engine version and executable SHA-256;
- model name and model SHA-256;
- language and creation time;
- coverage;
- phrase and character-level Script-span anchors;
- raw alignment evidence SHA-256;
- configuration SHA-256 and deterministic cache key;
- runtime, real-time factor and approximate memory evidence;
- provenance proving that raw ASR segments were not consumed as semantic boundaries.

The schema rejects creative-policy fields such as Beat count, Shot count, Visual Job, Shot type, geometry, animation policy and semantic-boundary decisions.

## Cache identity

The cache identity is derived from:

```text
audio_sha256
script_sha256
engine
engine_version
engine_binary_sha256
model_sha256
alignment_config_hash
```

A cache hit is accepted only after the stored artifact body, output hash and every identity field are validated. A changed audio file, Script, model, engine or configuration produces a different identity. A mismatched or corrupted prior artifact is marked `STALE` and is not consumed.

When a project is `ALIGNED_OPT_IN`, only usable `ALIGNED_TIMING_MAP` and `BEAT_TIMING_BINDINGS` artifacts enter the EDT stage dependency identity. A newly READY pair invalidates a previously cached CURRENT EDT. Missing, failed, blocked or stale alignment artifacts do not block CURRENT rendering.

## Semantic authorization

Alignment readiness alone is insufficient to retime a Beat. A separate `BeatTimingBindings` artifact must identify an already existing Beat boundary, the approved Script offset and the human or Director approval source. The runtime reports `READY` with `effective_state=CURRENT` until a usable binding exists.

The consumer applies an anchor only when:

1. project mode is `ALIGNED_OPT_IN`;
2. the alignment artifact is READY, identity-matching and above minimum coverage;
3. the binding is explicit and approved;
4. both adjacent character anchors meet confidence threshold;
5. the timestamp falls inside the legal neighboring Beat range.

Every failure leaves the original Beat timing unchanged.
