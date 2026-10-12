# VPS-001 · Results

## FACT

- A and B use the same script, voice source range, evidence asset IDs and semantic beat times. Both render at 1920×1080/30 fps; A, B and B-motion-off have equal 19.178667-second MP4 duration and identical decoded-audio stream hashes.
- The experimental compiler generated nine visual states over four existing beats. Two screenshot crops are deterministic, pixel-preserving derivatives of the original Workbench images. No formal DirectorIR field or production project artifact changed.
- `VISUAL_STATE_HOLD` is 6.24 seconds in A by beat-level composition and 3.24 seconds in B by explicit state boundary. B's average state duration is 2.12 seconds. This metric does not assert that every state delivers equal cognitive value.
- B's subtitle repair preserves the concatenated text of the original `SEG-04` subtitle clips. Full-resolution B frames show “Fact ID” as one readable unit rather than the original isolated `t ID` fragment. All versions preserve the original voice audio.
- Focused tests pass; the existing full suite is **216 passed**, one known deprecation warning. All three renders completed.

## OBSERVATION

- **Evidence readability:** A shows the whole Workbench page at under half-frame width; UI controls and rule text cannot be read comfortably at ordinary 1080p viewing size. B enlarges the original import control and Fact-ID direction to readable size, with a yellow rectangle identifying the exact target. The short whole-page states establish context before the close views.
- **Information progression:** B changes from page context to a specific source-import control, then to a marked action; later it changes from script-page context to the Fact-ID line and a short conclusion. These are visible information changes inside existing beats, not new semantic beats. `BEAT-03` still progresses mainly through two short title changes over the same crop; it is the least convincing part of B.
- **Visual protagonist:** B has no XIAO-Y in these four beats. The screenshot is visually dominant in evidence states and the brief status label is dominant in `BEAT-03`. No frame examined has a character competing for screenshot attention.
- **PPT feel:** B is **BETTER**, not “MUCH BETTER.” The readable crop and pointed highlighter make the UI sequence resemble a guided screen demonstration more than A's isolated white slides. Hard state cuts and the repeated crop in `BEAT-03` still create some slide-like rhythm. This is a visual-model pass, not final-film acceptance.
- **Motion dependency:** B-motion-off retains the readable crops, explicit focus and nine-state progression. In the contact sheet and checked full-resolution frames it remains clearly better than A. The 1.8% zoom contributes little; the information-state sequence is doing the work.
- **Subtitle:** The original `SEG-04` cue split leaves a tiny `t ID` fragment. B's two complete cues remain fully within the frame in inspected full-resolution frames. No subtitle truncation was observed in the tested B interval.

## HYPOTHESIS / LIMITS

- The improvement is attributable to the bundled B treatment, not uniquely to a visual-state schema. This one 19.12-second sample does not establish that an AI Director can plan good states, that all source screens contain a useful crop, or that the full 88-second video is creatively ready.
- The research screenshot proves a local import control exists, but it does not depict a completed candidate-to-Fact confirmation. The `BEAT-03` labels express the approved narration, not an observed UI state transition. Likewise, the script screenshot shows a Fact-ID requirement; it is not a screenshot of Fact Pack internals. A next sample with actual before/after UI states would test a stronger evidence-led progression.
- A/B MP4s were reviewed with one-second whole-interval frame samples and selected 1080p frames. This is a visual review; it is not a claim of uninterrupted real-time audio-visual playback or user approval.

**Human visual-model verdict: PASS (`BETTER`).** The defined success criteria hold for the tested interval: evidence is readable, the protagonist is clear, at least two beats have multiple states, the longest designed hold falls below four seconds, XIAO-Y yields to evidence, and the confirmed subtitle truncation is repaired. This does not authorize integrating the experiment into formal DirectorIR or publishing the CS-001 film.
