# Real Runtime Validation

## Runtime used

- Engine: `whisper.cpp 1.9.1`
- Model: `ggml-medium.bin`
- Model SHA-256: `6c14d5adee5f86394037b4e4e8b59f1673b6cee10e3cf0b11bbdbee79c156208`
- Model size: `1,533,763,059` bytes
- Language: Chinese
- DTW preset: medium
- Flash attention: disabled
- Approved Script used as decoding prompt: no

The executable and model were local machine dependencies. Neither is copied into Git. Evidence JSON contains hashes, versions and measurements without absolute local paths.

## Sample A regression

The real 84.76-second local cloned-voice master was run through the production `AlignmentRuntime`.

| Measurement | Result |
|---|---:|
| Script coverage | 98.6911% |
| Anchors | 386 |
| Alignment runtime | 17.031 s |
| Real-time factor | 0.2009 |
| Cache-miss wall time | 17.788 s |
| Valid cache-hit wall time | 0.016 s |
| Approximate child max RSS | 2,092.5 MiB |
| Estimated 4-minute runtime at measured RTF | 48.2 s |

The RSS value is the process-group cumulative `RUSAGE_CHILDREN_MAXRSS` observation on macOS. It is a practical upper observation for this run, not a portable per-process peak-memory guarantee.

With the two previously approved TCU bindings:

- TG-004 moves from 71,820 ms to 72,880 ms;
- TG-007 moves from 80,954 ms to 82,860 ms;
- Beat count remains `18 → 18`;
- Beat IDs and order remain identical;
- no semantic field is modified;
- raw ASR segments are not used as cuts.

This reproduces the frozen TCU-PASS consumer behavior using a freshly produced runtime artifact rather than the read-only ATS fixture.

The original-resolution TCU side-by-side frames were re-inspected after the real runtime run. Because the fresh runtime resolves the same 72,880 ms and 82,860 ms boundaries, the signed visual observations remain applicable: TG-004 does not enter the next Beat prematurely, the TG-006 forbidden-range cut is absent, TG-007 remains on the prior Beat until close to its approved anchor, and NC-004 is visually unchanged. The residual target errors are 100 ms and 288 ms, so no severe late Beat is present in the two approved regression targets. No new semantic cut is introduced.

## Multi-sample validation

Four distinct real cloned-voice utterances from the frozen Sample A production were aligned independently:

| Sample | Content category | Duration | Coverage | RTF |
|---|---|---:|---:|---:|
| SEG-01 | normal Mandarin; two-clause responsibility statement | 11.04 s | 98.0% | 0.2826 |
| SEG-04 | long clause; timing explanation | 10.28 s | 100.0% | 0.2730 |
| SEG-05 | contrast and reading-time warning | 10.08 s | 100.0% | 0.2889 |
| SEG-09 | late-video transition and conclusion | 8.88 s | 97.5% | 0.2918 |

All four produced monotonic per-segment timestamps inside the audio duration, no creative-policy fields and no raw-ASR semantic cuts.

## Honest limitation

These samples vary text structure, clause length, pacing location and meaning, but use the same local cloned speaker and source production. The available verified production corpus did not provide separate real examples containing English, digits, proper nouns, multiple speakers or substantially different speaking rates. FAI-001 does not claim those categories are validated.
