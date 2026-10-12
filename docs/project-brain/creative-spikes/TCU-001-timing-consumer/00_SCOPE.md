# TCU-001 — Timing Consumer Upgrade Spike

## Scope and isolation

TCU-001 asks one question: can Content OS consume more accurate aligned text timing to improve existing subtitle or Beat timing without changing creative semantics?

- Branch: `p0/timing-consumer-upgrade-1`
- Canonical baseline: `eea4b00e9b3809e16cd2c5b31123a5f4089cc00c`
- ATS-001 read-only evidence source: `p0/audio-timing-spike-1@e79aa07a1d06985237b177c9e65f980ad1aca3f3`
- Production default: **UNCHANGED**
- `DECISIONS.md`: **UNCHANGED**
- FAI-001: **NOT STARTED**

The experiment lives under `vnext/phase2/experimental/`. It does not modify `AudioClock`, the production renderer path, Director semantics, the Visual Compiler, or renderer policy.

## Three separate problems

### A. AUDIO PROSODY

This asks whether the final `voice.wav` itself contains an unnatural pause, an incorrect liaison, or an incorrect spoken phrase break.

TCU-001 does not repair audio prosody. If the frozen waveform contains a 300 ms pause, moving a visual or subtitle boundary cannot remove that pause and must not be reported as a prosody fix.

### B. TIMING TRUTH

This asks **when an already approved Script anchor occurs in the frozen audio**.

ATS-001 established that `POST-TTS ASR TIMING + TRANSCRIPT ALIGNMENT` can help locate specified anchors in Sample A. TCU-001 consumes the frozen DTW timing evidence only through a transcript-aligned, hash-pinned `AlignedTimingMap`.

### C. SEMANTIC POLICY

This asks whether a text location should become a subtitle, Beat, or Shot boundary.

Whisper and the `AlignedTimingMap` do not own this decision. Raw ASR segment boundaries are **FORBIDDEN AS SEMANTIC POLICY**. The experiment can move an existing approved boundary in time, but it cannot create or remove a Beat, re-segment the subtitle text, select a Shot type, or change a Visual Job.

## Frozen inputs

The A/B uses the same Sample A:

- frozen Script `ART-bef1d4cecaf94b5d`;
- frozen voice `ART-ce387c3fce5546ee`;
- existing DirectorIR `ART-b4d37b320dd5416e`;
- existing Visual EDT `ART-a592915c5e7f4634`;
- effective ShotPlan semantics frozen one-to-one from the 18 existing Director beats;
- 8 human Ground Truth cases: 6 `NO_BOUNDARY`, 2 `BOUNDARY`;
- 10 normal controls.

Sample A predates the formal DEC-011 ShotPlan artifact. For hash control, TCU-001 records `frozen-shotplan-semantics.json`, a one-to-one snapshot of the effective Director beat/shot semantics already consumed by the Visual EDT. It is not a newly generated DEC-011 plan and adds no policy.

## Explicit non-goals

TCU-001 does not repair TTS, change Script meaning, change Beat or Shot count, alter ShotPlan semantics, choose visual geometry, redesign motion, change production defaults, change `DECISIONS.md`, or start forced-alignment production integration.
