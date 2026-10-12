# VPS-001 · Controlled A/B test

## Frozen inputs

| Input | Shared by A and B |
| --- | --- |
| Project | CS-001 `PRJ-951fb6b86911` |
| Script | `ART-278087e926034f3b`, segments `SEG-02` to `SEG-04`; text unchanged |
| Voice | `ART-7ef0a1a38f894364`, source range 5.56–24.68 s, no resynthesis or playback-rate change |
| Audio clock | Measured segment-level `ART-661d1f96d1054fe8`; no word timestamps |
| Evidence | Existing research `MED-23b344b5d0c0` and script `MED-a380de2ef563` screenshots; no new evidence |
| Semantic beats | `BEAT-02`, `BEAT-03`, `BEAT-04`, `BEAT-5a133712b419`; boundaries unchanged |
| Video | 1920×1080, 30 fps, 574 frames for each version |

The only substantive independent variable is visual arrangement: A is the CS-001 layout, B is the nine-state manually designed visual progression. B also fixes the visually confirmed subtitle breakup without changing subtitle wording; that repair is recorded separately because it affects legibility. The dark canvas, crop scale, highlighter, text prominence and removal of XIAO-Y are visual treatments within B, so the test cannot attribute the improvement to a single one of them.

| Version | Local render | `ffprobe` duration | Decoded-audio SHA-256 equality |
| --- | --- | --- | --- |
| A, original composition slice | `outputs/vps-001-data/A.mp4` | 19.178667 s | Same across all three |
| B, progression | `outputs/vps-001-data/B.mp4` | 19.178667 s | Same across all three |
| B, motion off | `outputs/vps-001-data/B-motion-off.mp4` | 19.178667 s | Same across all three |

The 19.12-second source interval becomes 19.178667 seconds in the MP4 containers because of frame and AAC packet rounding; **all three output durations match**. The decoded audio stream hash is identical for A, B and B-motion-off. The private source audio file is not committed.

## Diagnostic

| Measure | A | B |
| --- | ---: | ---: |
| Existing semantic beats | 4 | 4 |
| Deliberate visual states | 4 beat-level compositions | 9 states: 3/2/2/2 |
| Maximum state hold | 6.24 s | 3.24 s |
| Average designed state duration | 4.78 s | 2.12 s |
| XIAO-Y in tested evidence sequence | Present in `BEAT-03` | Absent; UI or short status text is primary |
| Screenshot treatment | Small, mostly whole-page | Short whole-page context followed by readable crop and targeted highlight |
| `SEG-04` subtitle | Breaks “Fact ID” across a tiny final cue | Complete two-cue wording; no observed truncation |

The one-second contact views and rendered MP4s were used during the original review but are **PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**. The public snapshot retains the method and structured conclusions.

To reproduce locally, run `python -m vnext.phase2.experimental.visual_progression --props <CS-001 final props> --plan docs/project-brain/creative-spikes/VPS-001-visual-progression/ground_truth.json --public vnext/renderers/remotion/project/public --output <isolated output directory>` from the repository root. Render each emitted props file with the existing `ContentOSPreview` composition. The experiment requires the local CS-001 media cache and voice; committed screenshot fixtures alone are not a replacement for the private voice artifact.
