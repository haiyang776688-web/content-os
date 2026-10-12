# CS-001 · Fresh controlled creative test

**Fresh project:** `PRJ-951fb6b86911` (`CS-001 · 四道关卡的真实工作台`) in an isolated test data directory. All production state changes were made through the Workbench GUI on port 8770. Read-only SQLite/JSONL inspection was used to verify produced artifacts, not to fabricate them. H2 and storyboard approval were performed by `CS-001 test operator` for this experiment; they are not the user's creative acceptance or publication authorization.

**Topic:** Why a video's “PASS” indicator is insufficient: the real Content OS Workbench's source confirmation, evidence-bound script, independent audit, storyboard and human final review. The only research source is the nonsensitive, versioned `fixtures/creative-spike-1-workbench-source.txt`, written from observable Workbench behavior. DeepSeek extracted 12 verbatim candidates; the test operator confirmed six as the latest Fact Pack. DeepSeek generated the final fact-bound script; GLM's independent audit returned `PASS`. An initial 12-fact script was too long for this short test. A shorter attempt was correctly rejected by the existing 380-character schema minimum. The accepted script is revision 3.

The three exact screenshots imported in the GUI are retained as `fixtures/creative-spike-1-evidence/research.png`, `script.png` and `audit.png` for reproducibility. They contain only the nonsensitive test Workbench state; no local voice reference audio or provider credentials are included.

| Measure | Observed value |
| --- | --- |
| Script characters, including line breaks | 505 |
| Script segments | 14 |
| Average segment text length | 35.14 characters |
| Director scenes / beats after GUI split | 6 / 15 |
| Average estimated beat duration before voice | 4.67 seconds |
| GUI-imported authentic Workbench screenshots | 3 |
| Media-bearing beats in provisional EDT | 4 |
| Text-only / no imported screenshot beats | 11 |
| Deliberate 1:N mapping | `SEG-04` → `BEAT-04` and `BEAT-5a133712b419`, 2.5 seconds each before audio retime |
| Provisional Director total duration | 70.0 seconds |
| Measured local voice / final timeline duration | 88.84 seconds / 88.84 seconds |

Pattern distribution: `SCREEN_DETAIL 4`, `CHARACTER_EXPLAIN_KEYWORD 3`, `A_B_COMPARE 3`, `THREE_POINT_SUMMARY 3`, `TIMELINE_PROCESS 1`, `CHARACTER_ACTION_SEQUENCE 1`.

Resolved existing-template distribution: `COMPARE_SPLIT 3`, `CHARACTER_CENTER 2`, `SCREEN_DETAIL_ZOOM 2`, `SCREEN_FULL_FRAME 2`, `THREE_POINT_SUMMARY 2`, `INFO_LEFT_CHARACTER_RIGHT 2`, `KEYWORD_FULL_FRAME 1`, `CHARACTER_LEFT_TEXT_RIGHT 1`.

XIAO-Y action distribution among ten character-bearing beats: `XACT-002 3`, `XACT-006 2`, `XACT-017 2`, `XACT-014 2`, `XACT-008 1`. Motion among fourteen character/media clips: `SLOW_ZOOM 7`, `STATIC 7`; no `SLOW_PAN` occurred because the media-bearing beats were classified as evidence. A media-free process beat is not counted as imported evidence merely because it has text.

The first real GLM Director output mapped 14 segments to 14 beats and initially chose two screenshots. Its media contract first failed on a pre-existing `MediaAsset.kind`/`type` mismatch; after the repair and safe filename labels, the second output chose three semantically named screenshots but still mapped 1:1. The GUI's small split operation created the deliberate same-segment pair. The source/screenshot/Fact/Script/Voice are held fixed for later visual comparison where possible.

The live local cloned VOICE is `ART-7ef0a1a38f894364` (88.84 seconds); the final `AUDIO_TIMING_MAP` is `ART-661d1f96d1054fe8`. The map's `provenance.method` is `MEASURED_SEGMENT_BOUNDARIES`, with 14 nonempty segment-level `phrase_ranges`. All 14 `word_ranges` lists and raw provider word timestamp lists are empty, so no word-level alignment is claimed. The final GUI-generated EDT is `ART-c537f9ba61ee4817`. `SEG-04` measures 17.44–24.68 seconds; its two beats now cover 17.44–21.06 and 21.06–24.68 seconds, respectively, both marked `source=AUDIO_TIMING_MAP`. Visual-only revisions did not regenerate the VOICE artifact.

The formal storyboard produced 30 start/end stills and a contact-sheet HTML. It exposed three shortcomings before MP4: screenshots occupy too little of the canvas, several beats remain mostly white, and XIAO-Y's open-arm pose recurs. The test-only storyboard gate records these reservations in its comment.

The final render is `ART-abfd8fd2604d4052`, `projects/PRJ-951fb6b86911/renders/RUN-dda8992671.mp4` under the isolated test data root. `ffprobe` reports H.264/AAC, 1920×1080, 30 fps, 88.896 seconds and 18,057,335 bytes. The measured voice and final EDT both remain 88.84 seconds; container duration includes the final video-frame rounding. Mechanical QA completed with `PASS` and zero issues. Real MiniMax `VIDEO_QA` completed with `FAIL`, nine reported issues, two marked `BLOCKER`, and two generated typography change requests. The MiniMax video input was a visual-only review derivative, so its time offsets must not be presented as exact master-MP4 timestamps. The observed subtitle fragment near the end of `SEG-04` in the master MP4 corroborates a truncation issue; other findings are recorded as model findings, not independently proven defects.

For the controlled motion-only check, the formal Remotion props were copied with the seven `motion.continuous` fields removed and rendered as `motion-off-baseline.mp4` in the isolated test data root. Script, Fact Pack, screenshots, voice, beat timings and templates stayed fixed. Its duration is also 88.896 seconds. This diagnostic isolates continuous motion only; it is not a reconstruction of pre-Spike Track B. A same-time frame pair is stored as `motion-ab-10s.png`. The subtle zoom is visible in the pair but does not make the small UI screenshot readable or change the white-card composition.
