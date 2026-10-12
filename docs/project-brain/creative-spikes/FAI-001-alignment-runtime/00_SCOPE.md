# FAI-001 — Alignment Runtime Integration Spike

## Scope

FAI-001 integrates the timing method proven by ATS-001 and the existing Beat consumer proven by TCU-001 into a durable, opt-in runtime.

- Branch: `p0/alignment-runtime-integration-1`
- Frozen input baseline: `p0/timing-consumer-upgrade-1@8a42a83e34137864c1994ce75a389cd259c79e1b`
- Production consumer: **Existing Beat Timing Consumer only**
- Subtitle alignment: **OUT OF SCOPE**
- Production default: `CURRENT`
- Optional mode: `ALIGNED_OPT_IN`
- `DECISIONS.md`: **UNCHANGED**
- ATS-001 and TCU-001 code/evidence: **UNCHANGED**

`FAI` is retained only as the historical spike identifier. The implemented method is named exactly:

> **POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT**

It is not transcript-conditioned forced alignment. The approved Script is matched to local ASR/DTW observations after TTS; it is never passed to Whisper as a decoding prompt.

## Responsibility boundary

- Script / Director / approved Beat bindings own **WHAT** the content means and which boundary is allowed to move.
- `AlignedTimingMap` locates **WHEN** an approved Script span occurs in the hash-pinned final audio.
- Visual Compiler retains geometry, type size, crop and other presentation decisions.
- Renderer consumes the EDT and its timing provenance. It contains no alignment or semantic-boundary policy.

No raw ASR segment boundary may create a Beat, Shot, subtitle chunk, Visual Job, or semantic cut.

## Non-goals

FAI-001 does not change Script meaning, add or remove Beats, repair voice prosody, improve subtitles, choose visuals, change the renderer's visual policy, ship the 1.43 GiB model in Git, change the production default, modify formal project decisions, or begin another spike.
