# CS-001 · Results and limits

## FACT

- Track B's recorded final MP4 was 61.461333 seconds at 1080p/30 fps, with seven script segments and seven beats. Its documented manual inspection found sparse white frames and repeated XIAO-Y poses; its MiniMax review warned about crowding, missing concrete demonstrations and unbalanced white space. The Track B render itself was not available in this checkout for a same-screen frame comparison.
- CS-001 used a new isolated project, six confirmed source-bound facts, real DeepSeek script production, real GLM audit (`PASS`), three GUI-imported Workbench screenshots, 15 visual beats for 14 script segments, and 30 formal storyboard stills. The final script and the same-segment beat pair are identified in `02_CONTROLLED_TEST.md`.
- The contact sheet and real storyboard stills were opened and inspected at original resolution. Four beats contain registered screenshots; the other 11 do not. Five registered XIAO-Y actions and eight existing templates appear in the provisional resolved composition.
- Engineering verification after the GUI split: `PYTHONPATH=. .venv/bin/python -m pytest -q vnext/tests` → **213 passed**, one pre-existing Starlette/httpx deprecation warning. The fresh GUI project rendered an 88.896-second 1080p/30 fps H.264/AAC MP4. Mechanical QA returned `PASS` with zero issues. Real MiniMax visual QA returned `FAIL` with nine findings, including two typography blockers, and created two change requests.
- The final MP4's entire 88.896-second visual timeline was sampled at one-second intervals in three contact sheets and inspected, along with full-resolution storyboard stills and selected master-MP4 frames. The MP4 was not evaluated through uninterrupted real-time audio-visual playback. A same-props motion-off diagnostic render at identical duration isolated the seven continuous-motion clips; it did not recreate Track B.

## OBSERVATION

- The new global contact sheet makes a repeated open-arm pose and high white-space usage obvious across neighboring beats. Screenshot-bearing beats differ materially from pure text beats, but a screenshot occupies less than half the 1920px frame width in the inspected research beat; its UI labels are too small to serve as strong evidence at normal viewing size.
- The five distinct action IDs include several visually similar open-arm poses. This explains why the ID-level `ACTION_REPETITION` warning can correctly remain silent while a human still sees repetitive body language. A semantic-intent match and ID rotation are necessary but insufficient for perceived pose diversity.
- Three differently named screenshots were chosen by the second Director pass after the asset-label fix. The first pass selected two and misassigned at least one screenshot to its narration context. This supports passing a safe display label alongside the registered ID; it does not prove the Director always binds the right visual.
- Stronger prompt wording did not cause GLM to make a 1:N mapping on its own. A test operator used the new Workbench split action and assigned two distinct screenshots to `SEG-04`; the resultant IR has two 2.5-second beats with the same segment ID and unchanged segment-level estimated duration.
- The final 1:N pair retimed to 17.44–21.06 and 21.06–24.68 seconds from the same measured segment, with the VOICE artifact unchanged. `AUDIO_TIMING_MAP` has measured segment-level phrase ranges but no word ranges or raw provider word timestamps. This demonstrates segment-internal retiming, not word-level synchronization.
- One-second full-timeline review shows a mostly white sequence of small screenshot or XIAO-Y/text compositions. Several beats hold the same information state for roughly six to nine seconds. The screenshot content is generally too small to read at ordinary playback size; the contact-sheet-level variety is therefore more apparent than the in-frame evidence.
- Several different registered XIAO-Y action IDs depict nearly the same open-arm pose. Mechanical ID repetition QA correctly found no short-window ID recurrence, but it missed perceptual repetition. Template IDs rotate, yet several layouts still read as the same white-card language.
- The master MP4 shows a clipped subtitle fragment (`t ID)`) near the end of `SEG-04`; this supports MiniMax's typography concern. MiniMax's reported ~0.8–1.1-second offsets are relative to its visual-only review input, not verified master timestamps. Its other timeline/ID claims were not independently validated and should not be treated as code facts.
- In the same-time motion-on/off frame pair, the screenshot grows by only a few percent. This is restrained and avoids conspicuous Ken Burns motion, but it does not fix evidence legibility, perceived pose repetition or slide-like pacing.

## HYPOTHESIS

- Relative to the documented Track B problems, the real screenshots and broader template IDs probably make CS-001 slightly better in visual variety. The Track B MP4 is unavailable here and the topic, script length and beat count differ, so this is a qualified editorial judgment rather than a controlled whole-system A/B result. The PPT feeling remains unacceptable against `PRODUCT_TASTE.md`.
- A larger, legible evidence crop paired with a meaningful in-beat UI state change is more likely to help than additional 1–5% zoom. This remains a hypothesis for the next focused experiment.

## Before vs after

| Dimension | Track B (documented baseline) | CS-001 (current observed state) | Attribution limit |
| --- | --- | --- | --- |
| Evidence | No real media evidence documented in seven-beat creative finding | Three authentic GUI screenshots imported; four visual beats use them | Different topic and script |
| Beat mapping | 7 segments → 7 beats | 14 segments → 15 beats, including one deliberate 1:N pair | Split was a GUI test operation, not Director's initial output |
| Pose / template | Repeated XIAO-Y and sparse white frames observed | Five actions and eight templates, yet contact sheet still shows repeated open-arm pose and white space | Source render unavailable for quantified pose baseline |
| Motion | Fade/slide-style entrance then static | Seven character/media clips carry subtle continuous zoom; seven remain static | Same-props motion-off render shows a real but visually small difference |
| MP4 / QA | Track B render, Mechanical and MiniMax QA completed | 88.896-second MP4; Mechanical `PASS`/0; MiniMax `FAIL`/9, including 2 typography blockers | MiniMax's review-media timestamps are not master timestamps |

**Creative comparison verdict: `SLIGHTLY BETTER`, with low confidence against Track B because its render is not available for direct viewing.** The specific improvement is that registered screenshots appear and the template set is broader. The dominant slide/PPT feeling did not materially decline, XIAO-Y pose repetition is still obvious, screenshots do not yet become the visual protagonist, and subtle continuous motion has negligible effect on those failures. This is an informative failed creative acceptance, despite the engineering and render passes. The MiniMax `FAIL` independently prevents treating the current sample as an approved final video.
