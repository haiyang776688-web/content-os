# AlignedTimingMap v1

## Contract

`AlignedTimingMap` is an experimental, renderer-neutral timing artifact. It answers **WHEN** an approved Script span occurs in a hash-pinned audio artifact.

It contains:

- `script_artifact_hash`;
- `audio_artifact_hash`;
- phrase anchors;
- text-span anchors;
- `start_ms` / `end_ms`;
- confidence and coverage;
- provenance;
- alignment method;
- alignment artifact hash.

It deliberately excludes:

- Shot and Beat counts;
- semantic boundary decisions;
- layout geometry;
- animation policy;
- Visual Job or Shot type policy.

## Provenance

Sample A uses `POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT`. DTW token timing from the frozen ATS evidence is tolerant-matched back to the approved Script. The approved Script was not supplied as an ASR decoding prompt. Raw Whisper segments are never exposed as semantic boundaries.

Every artifact records the Script hash, audio hash, alignment evidence hash, ATS source commit, method, coverage, and whether raw ASR segment boundaries were consumed. `raw_asr_segment_boundaries_consumed` must remain `false`.

## Sample A artifact

The generated artifact is [aligned-timing-map.json](evidence/aligned-timing-map.json). Its measured properties are:

- Script coverage: `98.6911%`;
- phrase anchors: `9`;
- matched text-span anchors: `377`;
- raw ASR segment boundaries consumed: `false`.

Its `artifact_hash` is computed from canonical JSON before the hash field is attached. Consumers pin that hash in their metadata so a timing result can be traced back to the exact alignment input.

## Trust boundary

The map can locate a text span. It cannot decide that the span deserves a cut. Existing Beat movement requires a separate, explicit, approved semantic binding. Missing, ambiguous, weak, or out-of-range anchors fall back deterministically to current timing.
