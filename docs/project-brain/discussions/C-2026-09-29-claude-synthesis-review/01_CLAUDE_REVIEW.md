# Claude Synthesis Review · Red Team on COUNCIL_SYNTHESIS_2026-09-29.md

**Model:** Claude Sonnet 5 (Anthropic)  
**Date:** 2026-09-29  
**Evidence priority used:** actual code (this round) > p0-slices / HANDOFF (this round) > Project Brain (prior rounds) > Council documents (prior rounds) > model inference. See `00_SCOPE.md` for exactly what was read and what wasn't.

Marking scheme: `FACT` (directly observed in code/docs this round) · `CURRENT_IMPLEMENTATION` (same, phrased as behavior) · `HYPOTHESIS` (a plausible but unproven causal claim) · `PROPOSAL` (a recommendation) · `UNKNOWN` (not checked).

---

## Overall verdict on the Synthesis document

**OPINION, stated up front:** This is the most disciplined of the Council documents produced so far — it correctly refuses several tempting single-cause stories, correctly separates Track B from the 84s historical sample, and correctly flags its own MiniMax/render-timeout extrapolations as unproven. On independently re-deriving its §4 claims from the actual resolver/renderer/production code, **every FACT-labeled claim in Synthesis §4 held up**, and I found the code evidence for several of them to be *stronger and more specific* than the Synthesis states (see §1 and §4 below — e.g. the first-match allocator, the motion vocabulary, and the write-only fields are all confirmed with exact code, not just corroborated). Where I disagree, it is mostly that the Synthesis's HYPOTHESIS-labeled root-cause model is still slightly too generous to Director/Resolver-layer explanations and under-weights two upstream layers (Beat *density* set by Director/Writer segmentation, and the *template registry being under-utilized rather than absent* — see Issue 1 and Issue 2 below). I also found one place where the Synthesis's own uncertainty ("UNKNOWN whether word timestamps exist") is resolvable from code I read this round, and one place where a **prior Claude Review of mine (D-003 Round 02) was factually wrong** and needs a public correction here, because the Synthesis's Prompt Governance framing partially depends on it.

---

## Issue 1 · Creative FAIL multi-factor model

**Verdict: MODIFY**

**Facts confirmed:**
- `FACT` (`vnext/phase2/hardening/visual.py`): the character-action allocator is exactly a first-match, `next()`-based deterministic lookup with **no state carried across beats** — `action=next((a for a in actions if a['id']==action_id),None) if action_id else next((a for a in actions if b.get('character_intent') in a.get('semantic_intents',[])),None)`. No rotation, no recency history, no diversity budget. This is stronger evidence than the Synthesis cites (it names the behavior but not the exact code shape); confirmed verbatim.
- `FACT` (`vnext/renderers/remotion/project/src/Composition.tsx`): the entire motion vocabulary is (a) opacity fade-in over 8 frames, (b) `HOLD` = binary visibility with no fade, (c) `SLIDE_UP` = an additional 20px→0px translateY over the same 8 frames, (d) an SVG underline/marker reveal via `clipPath`, (e) a small scale-in pulse for "treatment" text. There is **no** continuous pan/zoom, no camera drift, no crossfade between clips, no progressive zoom-into-evidence, and once a MEDIA/CHARACTER clip's reveal finishes, it is **completely static** for the rest of its on-screen duration. This is a direct, total confirmation of Synthesis §4.3 — not a partial one.
- `FACT` (`vnext/phase2/production.py`, `mechanical()`): `purpose`, `visual_focus`, `visual_form`, `retention_function`, `density`, `tempo` are validated as present on `Beat`/`Scene` (Pydantic schema) but **I traced every consumer of `DirectorIR` in this codebase this round** (`VisualResolver.plan`, `Production.generate_edt`, `mechanical()`) and none of them read these six fields. They pass through create/store but never reach the resolver, the renderer, or QA. Confirmed write-only, exactly as Synthesis §4.4 states.
- `FACT` (`vnext/phase2/production.py`, `mechanical()`): a repetition check *does already exist* — `if len({b['motion_intent'] for b in beats})==1: issue('MOTION_REPETITION','WARNING','DIRECTOR')` and an analogous all-same check for `pattern_id=='CHARACTER_EXPLAIN_KEYWORD'`. **This is a correction to the Synthesis, which implies (in §4.2, "没有 deterministic allocator / rotation / diversity budget" and by omission in §10's item 2 "partial action/pattern repetition QA") that no repetition QA exists at all.** It exists, but only for the degenerate all-identical case across the whole beat sequence — it fires only when literally every beat shares one motion_intent, which is a much weaker signal than "3 of 7 consecutive beats used the same action." Track B's own QA output (`MOTION_REPETITION` warning, per `SLICE-006-TRACK-B.md`) is a real instance of this all-same check actually firing, given only 3 allowed `motion_intent` values (`HOLD/FADE/SLIDE_UP`) across 7 beats makes coincidental collision likely.

**Inference accepted:** the multi-factor model itself (five layers multiplying) is a reasonable *description* of where problems currently sit, and I agree none of the single-factor retreats ("just Prompt", "just Renderer") are supported.

**Inference rejected:** the model as stated omits an upstream layer that is not "topic/evidence supply" and not "Director control" — it is **Writer/Script segmentation density**, i.e. how many segments a 300-word script gets split into, which mechanically caps how many Beats a 1:1-mapped Director can create (Track B: 317 characters → 7 segments → 7 beats). A script this short, split this finely, has very little room for a Beat to *not* feel like a slide change even with perfect Director/Resolver/Renderer machinery, because each Beat's `timing_intent` is bounded by a roughly 61s÷7≈8.8s average window with real variance underneath. This is not visible anywhere in the Synthesis's five-factor formula, and it is a layer *above* Director, not inside it.
- `HYPOTHESIS`: Track B's Creative FAIL may be partially a consequence of a **317-character/7-segment script being asked to fill a ~61s video** — i.e., low narration density relative to video length — rather than (or in addition to) Director/Resolver/Renderer limitations. I did not read the actual script text or `SLICE-001`/`SLICE-002` in enough depth to confirm this; it is a testable hypothesis, not a confirmed finding.

**Missing evidence:** the actual `SCRIPT` artifact's segment lengths and the actual per-Beat `timing_intent` values for Track B were not read this round (would require fetching the artifact payload from a live store, not available via GitHub).

**Corrected formulation:**
```
Creative FAIL
=
Writer/segmentation density (upstream, sets the Beat budget)
× 题材/证据供给
× Director 控制权 (confirmed narrow, but see Issue 2 — narrower than necessary, not narrow because no alternative exists)
× Resolver 映射 (confirmed first-match, zero diversity)
× Motion/Pattern vocabulary (confirmed near-empty, not "thin" — there is effectively one continuous-motion primitive: none)
× QA/Gate 可观察性 (confirmed stills-only; MOTION_REPETITION exists but is a weak all-same check, not partial-repetition)
```

**Recommended implementation / experiment:** before the next Track run, log the actual segment count and average segment length alongside the beat count, and treat "segments/beats vs. target duration" as a first-class confound to control for when judging whether the *next* sample's improvement came from Director/Resolver/Renderer changes or from simply writing a denser script.

**Priority:** P1 (informs interpretation of every other experiment; not itself a code change)

---

## Issue 2 · Director control boundary

**Verdict: MODIFY**

**Facts confirmed:**
- `FACT` (`vnext/phase2/production.py`, `PATTERN_MAP`/`PATTERNS`): Director already chooses from **8 registered semantic patterns** (`CHARACTER_EXPLAIN_KEYWORD`, `CHARACTER_REACTION_MEDIA`, `TIMELINE_PROCESS`, `A_B_COMPARE`, `SCREEN_DETAIL`, `THREE_POINT_SUMMARY`, `NUMBER_EMPHASIS`, `CHARACTER_ACTION_SEQUENCE`) via the required, schema-validated `pattern_id` field — this is functionally a template-*family* choice, already exposed to the LLM, already deterministic-schema-enforced (`UNKNOWN_PATTERN` raised otherwise).
- `FACT` (`vnext/phase2/hardening/visual.py`, `TEMPLATES`/`LAYOUTS`): there is a **separate, larger registry of 12 concrete layout templates** (`CHARACTER_CENTER`, `CHARACTER_LEFT_TEXT_RIGHT`, `INFO_LEFT_CHARACTER_RIGHT`, `CHARACTER_LOGO`, `CHARACTER_SCREEN`, `EXTREME_CLOSEUP`, `KEYWORD_FULL_FRAME`, `SCREEN_FULL_FRAME`, `SCREEN_DETAIL_ZOOM`, `COMPARE_SPLIT`, `THREE_POINT_SUMMARY`, `CTA_END_CARD`), but the **static** `SEMANTICS→TEMPLATES` map only ever auto-selects from about 7–8 of these 12 for a given `semantic_pattern` — the remaining templates (`CHARACTER_CENTER`, `INFO_LEFT_CHARACTER_RIGHT`, `CHARACTER_LOGO`, `EXTREME_CLOSEUP`) are only reachable if a human or the Director explicitly sets `template_id`.
- `FACT` (`vnext/phase2/production.py`, `CommandBus.execute`, `SET_BEAT`'s `permitted` set): `template_id`, `semantic_pattern`, `character_action_id`, and `element_ids` are **already in the permitted human-edit field set** for `SET_BEAT`. This means the *plumbing* for Director (or a constrained allocator) to set `template_id` already exists end-to-end (schema → CommandBus → resolver reads `b.get('template_id')` if present) — it is `director_contract.py` (confirmed in the D-003 round of this conversation) that locks `template_id`/`semantic_pattern` to `null` for LLM-authored `DIRECTOR_IR`, not a missing capability in the resolver or the edit path.

**Inference accepted:** the Synthesis's instinct to avoid "let the LLM output pixels/layout" is correct and should not be relaxed.

**Inference rejected:** the framing that Director's control is simply "narrow" understates that **most of the fix is not new engineering** — it is widening an *already-built, already-schema-constrained* enum (12 templates exist; only ~7 are reachable automatically) and/or building a small deterministic allocator that picks among the semantically-valid subset of the 12, rather than either (a) leaving it locked or (b) opening free-form layout as the Synthesis worries about.

**Corrected formulation:** Director control should expand to **semantic intent + a constrained `template_id` choice from a per-`semantic_pattern` allow-list** (not free choice of all 12, and never raw geometry), decided by one of:
- (A) Director/LLM picks `template_id` from an allow-list the schema validates (few-line change: replace the `TEMPLATES` static 1:1 map lookup with a `TEMPLATES_ALLOWED: dict[str, list[str]]` and validate `beat.template_id in TEMPLATES_ALLOWED[semantic]` in `Production.ir`'s existing per-beat validation loop);
- (B) a deterministic Resolver-side allocator does the same lookup but rotates among the allow-list per a `(recent_template_history, semantic)` rule, analogous to the fix Issue 4 needs for character actions anyway — and could reuse the same allocator primitive.

Option (B) is lower-risk (no LLM output space change, same guarantees as today) and can be built as one function shared with Issue 4's allocator. Option (A) gives Director real narrative control (e.g. deliberately choosing `EXTREME_CLOSEUP` for an emotional beat) but needs the Prompt-side quality guidance that D-003 already found missing (director_contract.py currently has zero taste/PPT-avoidance instructions — see my own D-003 Round 02 review, §Five/5.4, which is still accurate and unchanged since no code commits landed).

Which should still be a **deterministic Resolver decision**: which of the 12 templates' *layout coordinates* to use (the `LAYOUTS` dict itself) — this must never become an LLM output, and nothing in this review proposes changing that.

**Recommended implementation / experiment:** implement Option (B) first (Resolver-side allocator with template rotation among the per-semantic allow-list, zero schema/LLM change), measure whether Track B-class output improves; only escalate to Option (A) if (B) alone doesn't move the "PPT feel" needle, since (A) requires the Prompt work D-003 already scoped.

**Priority:** P0 (Option B) / P1 (Option A, contingent on B's result)

---

## Issue 3 · Semantic field → pixels

**Verdict: ACCEPT (with a sharper consumption-map)**

**Facts confirmed:** see Issue 1's write-only confirmation. I additionally traced `keyword`, `slots`, `media_need`, `character_intent`, `reveal_order`, `motion_intent`, `timing_intent` and found these **are** consumed (by `VisualResolver.plan`/`clips`, by `mechanical()`, or by `AudioClock.retime`). So the actual write-only set, confirmed by code, is exactly: `purpose`, `visual_focus`, `visual_form`, `retention_function`, `density` (on `Scene`), `tempo` (searched for in `Beat`/`Scene` schema — **not present as a field at all**, `UNKNOWN` whether Synthesis means a different field name or a planned-but-unadded one), and `phrase_id` on `Beat` (present, default `''`, and **I found zero references to `Beat.phrase_id` anywhere in `production.py`, `visual.py`, or `resolver.py`** — it appears to be entirely unused scaffolding, distinct from the *real* and *actually consumed* `phrase_ranges`/`word_ranges` living on `AudioTimingMap.entries`, which is a confusing naming collision worth fixing regardless of D-002's outcome).

**Consumption-point answer for the proposed new fields, since the Synthesis asks Claude to specify this:**

| Field | Best consumer | Why |
| --- | --- | --- |
| `visual_job` | Resolver (deterministic) | If this means "which of the 8 semantic patterns / 12 templates", it's exactly `pattern_id`/`template_id`, already present — don't add a new field, reuse/rename the existing ones rather than creating a third parallel concept. |
| `cognitive_change` | Mechanical QA (deterministic, cheap) | Could deterministically check "does this beat's primary text/number differ from the previous beat's" — a rough proxy computable without an LLM at all, directly attacking the "no new information" failure mode. |
| `viewer_should_notice` | Storyboard Gate reviewer UI (human-facing, not machine-consumed) | This reads as a *human review aid* — show it next to the still so a reviewer can judge "did the still actually make this noticeable", not as something Resolver/Renderer should act on. |
| `evidence_carrier` | Resolver, as a **hard requirement gate**, not a suggestion | If a Beat claims `semantic_pattern=EVIDENCE`/`SCREEN_DETAIL` but has no bound `media_asset_id`, this should raise the same class of error as the existing `PATTERN_SLOT_MISSING`/`ASSET_GAP` checks already in `Production.ir` — i.e. this is not a new field, it's tightening an existing validation path. |

**Corrected formulation:** don't add `visual_job`/`evidence_carrier` as new schema fields; they substantially duplicate `pattern_id` + existing slot-validation. Add `cognitive_change` only if a cheap deterministic proxy is specified up front (see above), otherwise defer. Delete or wire up `tempo`/`density`/`purpose`/`visual_focus`/`visual_form`/`retention_function`/`phrase_id` per the earlier D-003 review's rule: no field survives without a named consumer.

**Priority:** P1 (schema hygiene; not blocking the next test video)

---

## Issue 4 · XIAO-Y pose first-match

**Verdict: MODIFY**

**Facts confirmed:** see Issue 1. Exact mechanism re-confirmed.

**Corrected formulation — minimal implementable contract (Option C, hybrid, as the Synthesis's own candidate list correctly anticipates is likely right):**

```
allocate(intent, recent_action_ids: list[str], max_repeat: int, actions_for_intent: list[Action]) -> Action:
    candidates = actions_for_intent  # already filtered by semantic_intents, existing behavior
    if len(candidates) == 1: return candidates[0]  # no diversity possible, don't force it
    non_repeated = [a for a in candidates if a.id not in recent_action_ids[-max_repeat:]]
    pool = non_repeated or candidates  # fall back to full pool if everything was recently used
    seed = digest([project_id, beat_id])  # deterministic, not random — stable across re-renders of the same beat
    return pool[int(seed, 16) % len(pool)]
```

This keeps Director giving only `intent` (as today — no LLM output-space change), keeps the allocator fully deterministic and reproducible (same beat_id always resolves the same way unless the action registry or history changes), and needs only `recent_action_ids` threaded through `VisualResolver.plan`'s existing per-scene/per-beat loop (it already iterates beats in order and has access to prior beats in the same call).

**Recommended implementation / experiment:** implement exactly this function, re-run Track B's topic (or a fresh similar one) with it, and check whether XIAO-Y pose repetition (a named Creative FAIL symptom) visibly decreases without any Prompt or schema change.

**Priority:** P0 — this is one of the cheapest, most isolated changes in this entire review (single function, no schema change, no Prompt change, directly named as a Track B symptom).

---

## Issue 5 · Renderer / Remotion

**Verdict: ACCEPT**

**Facts confirmed:** fully re-derived from `Composition.tsx`, see Issue 1. The Synthesis's framing ("not a Remotion limitation, a Content OS Composition limitation") is correct — Remotion's `interpolate`/`Sequence`/frame-driven model can trivially express continuous pan/zoom, crossfades, etc.; nothing here is blocked by the framework, only by what `ClipView` currently computes.

**Minimum 3–5 motion primitives (as requested, prioritized by highest creative return for lowest implementation cost):**

1. **Continuous slow zoom on MEDIA/CHARACTER clips** ("Ken Burns"): interpolate `scale` from e.g. 1.0→1.04 across the clip's full on-screen duration instead of only across the 8-frame reveal window. This single change touches the static-after-reveal problem identified in Issue 1 for every MEDIA and CHARACTER clip with near-zero risk (pure CSS transform interpolation already used elsewhere in the file).
2. **Crossfade between consecutive clips on the same track** instead of hard cuts: requires knowing the *next* clip on the same track at render time (Composition already has the full `clips` array via props, so this is a lookup, not new data).
3. **Progressive evidence zoom for `SCREEN_DETAIL`/`EVIDENCE` patterns**: when `pattern_id` is `SCREEN_DETAIL`, interpolate a `crop`/`scale` combination from "full screenshot" to "zoomed on the relevant region" over the beat's duration — the `crop` prop already exists in `Clip` type and `styleFor()`, just not driven by time today.
4. **Camera hold with subtle drift** for `HOLD`-motion clips, replacing the current binary-visibility HOLD with a near-imperceptible slow pan (1–2% position drift), which costs nothing extra to implement once (1) exists (same interpolate primitive, smaller magnitude).

Item 5 (mask reveal / diagram state transition) is explicitly **not** recommended for the minimum set — it's higher-cost and lower-return than 1–4 for attacking "PPT feel" specifically, since 1–4 directly target "nothing moves once revealed", which is the concrete, code-confirmed root cause.

**Priority:** P0 for item 1 alone (highest ratio of creative impact to code risk of anything in this entire review); P1 for items 2–4.

---

## Issue 6 · D-002 “切在哪里 vs 切几刀”

**Verdict: MODIFY**

**Facts confirmed:**
- `FACT` (`vnext/phase2/hardening/audio.py`, `AudioClock.retime`): the "Current retime" mechanism is exactly as Synthesis describes — within a segment mapped to N beats, each beat's share of the real audio duration is `(e['end']-e['start']) * beats[c['beat_id']]['timing_intent'] / total`, i.e. **proportional to Director's own estimated `timing_intent` values, not to any independent signal about where the sentence's semantic weight actually falls.** Track B was 1:1 so this code path's *proportional-split* branch never had to divide anything (`total` = one beat's own `timing_intent`, ratio always 1) — this is worth stating explicitly because it means **Track B's 7:7 alignment exercised the *segment*-boundary correctness of retime, but exercised zero bits of the *intra-segment proportional split* logic**, which is exactly the part D-002's "1:N" scenario depends on.
- `FACT` (`vnext/phase2/hardening/audio.py`, `AudioClock.from_voice`/`create`): **`phrase_ranges` and `word_ranges` are real, populated, validated fields on `AudioTimingMap.entries`**, built from a voice provider's `phrase_timestamps`/`word_timestamps` when present (`PROVIDER_TIMESTAMPS` provenance method), with strict validation (`PHRASE_SCRIPT_MISMATCH`, `PHRASE_TIMING_OVERLAP`, hash-pinning). **This resolves the Synthesis's own stated UNKNOWN** ("`phrase_id`、`word_ranges` 等结构存在，但其是否在 Track B 真实 Voice 中可用仍需运行数据确认") at the *schema/plumbing* level: the capability is real and wired end-to-end for whichever provenance method the actual voice provider reports. Whether Track B's specific local cloned-voice run (`YU_LOCAL_V1`) used `PROVIDER_TIMESTAMPS` vs. `MEASURED_SEGMENT_BOUNDARIES` (a different, coarser provenance method also handled by this same file, keyed off segment-level measured audio files rather than word timestamps) is **still `UNKNOWN`** — I did not have access to the actual `VOICE` artifact payload's `provenance.method` value for Track B. This narrows the open question from "does the mechanism exist" (now resolved: yes) to "which provenance path did this one local voice run actually take" (still open, and answerable by inspecting one artifact, not by new engineering).
- `HYPOTHESIS` (Synthesis's own, and I have no code-level way to confirm or deny this round): whether "sentence-internal visual-focus timing mismatches pause/emphasis" actually occurred in Track B. Agreed this remains HYPOTHESIS.
- **A genuinely new finding this round, not in the Synthesis**: `FACT` (`vnext/phase2/hardening/audio.py`, `AudioClock.subtitles`): the subtitle-chunking code has a comment — `# Prefer supplied word ranges; otherwise visibly recorded proportional phrase split` — but **the actual implementation never reads `entry['word_ranges']` when splitting a long phrase into multiple subtitle lines/chunks; it always does character-count-proportional splitting within the phrase**, regardless of whether real word-level timestamps exist. This is a second, independent instance of the "comment promises a capability the code doesn't use" pattern the Synthesis flags for semantic fields in §4.4, found here in the *temporal* domain instead of the visual domain. It directly bears on Issue 6's "切在哪里" question: even where word-level ground truth exists, the *subtitle* split currently ignores it.

**Inference accepted:** the A/B/C framing ("current retime" / "phrase-anchor" / "full audio-first") is the right decomposition, and "7:7 = timing solved" is indeed an over-simplification, for the reason stated above (7:7 never touched the proportional-split code path at all).

**Inference rejected:** none outright, but I'd add: the Synthesis frames B ("phrase/word anchor") and C ("full audio-first") as differing mainly in *when* Director runs relative to Voice. There is an intermediate, cheaper option the Synthesis doesn't name: **keep the current Director-before-Voice order, but make `AudioClock.retime`'s proportional split use real word/phrase timestamps (once confirmed present) to weight the split instead of Director's blind `timing_intent` guess** — i.e., fix "where the audio cuts happen inside a multi-beat segment" without touching "when Director runs" or adding Narration Units. This is strictly smaller than B as scoped (B implies new anchor-based Beat-splitting logic; this is a one-function change to an existing retime path) and should be tried and measured before deciding whether B or C's larger investment is warranted.

**Corrected formulation:** `A current → A' current-with-real-timestamp-weighted-retime → B anchor-based Beat splitting → C full audio-first`, a four-point spectrum, not three, with A’ being nearly free (reuses existing validated data) and worth measuring before funding B or C.

**Recommended implementation / experiment:** (1) inspect one real Track B `VOICE` artifact's `provenance.method` to close the remaining UNKNOWN; (2) if `PROVIDER_TIMESTAMPS`/real word data is present for the local clone voice, implement A’ (weight `retime`'s proportional split by real sub-phrase timestamps instead of `timing_intent`) as a small, isolated change and test it on a 1:N-beat topic (Track B's 1:1 structure cannot exercise this at all — the next test topic should deliberately produce at least one 1:N segment/beat mapping).

**Priority:** P0 for the artifact inspection (near-zero cost, resolves a real unknown); P1 for implementing A’ contingent on that inspection's result.

---

## Issue 7 · Narration Units

**Verdict: REJECT (agree with Synthesis's own skepticism, and code confirms no gap requires it yet)**

**Facts confirmed:** `Beat.phrase_id` exists (unused, per Issue 3) and `AudioTimingMap.entries[].phrase_ranges`/`word_ranges` exist and are validated (per Issue 6). Between `ScriptSegment` + these two, the data needed to express “which word-range corresponds to which Beat, when a segment maps to multiple beats” is **already representable without a new Artifact type** — a `Beat` already carries `script_segment_id`; nothing stops adding (if A’/B from Issue 6 are pursued) a beat-level anchor into an existing entry's `phrase_ranges`/`word_ranges` rather than inventing a `NARRATION_UNIT` artifact type with its own ownership, SINGLE_WRITERS entry, and dependency graph.

**Corrected formulation:** no independent Narration Unit Artifact needed; agree fully with Synthesis's instruction not to default to needing it, and confirm from schema inspection that the existing fields are sufficient scaffolding for Issue 6's A’/B options.

**Priority:** DEFER (nothing to build; this is a “don't build it” verdict)

---

## Issue 8 · MiniMax Visual QA

**Verdict: NEEDS_EXPERIMENT**

**Facts confirmed:** `UNKNOWN` this round — I did not re-read `vnext/phase2/intelligence.py`'s `VisualQA` implementation in this session (read in an earlier session of this same conversation, not re-fetched here; the `fps=1` claim and system-prompt thinness were established there and are consistent with what the Synthesis states, but I am not re-verifying them fresh in this round, so I mark this **UNKNOWN-not-reverified** rather than FACT for this specific review). Track B's actual finding list (`SUBTITLE_OVERLAP_ARTIFACT`, `TEXT_TRUNCATION_RIGHT`, `TIMING_DENSITY_HIGH`, repeated text, missing platform demonstration, unbalanced whitespace) is consistent with the Synthesis's claimed 1fps-appropriate boundary (all of these are detectable from sparse frame sampling; none require sub-second motion perception).

**Inference accepted:** the static-useful/temporal-weak split is directionally right and matches what Track B's real findings could plausibly come from.

**Missing evidence:** no direct confirmation this round of the exact `fps` parameter or how many frames are actually sent per beat vs. per video.

**Corrected formulation:** unchanged from Synthesis, but downgraded from ACCEPT to NEEDS_EXPERIMENT purely on my own evidentiary honesty this round — I have prior-session knowledge supporting it, not this-round verification, and the task's own evidence-priority rule (code > everything) means I should not upgrade a not-freshly-checked claim to ACCEPT.

**Recommended implementation / experiment:** re-confirm `fps` and per-call frame budget directly from `intelligence.py` before funding any of options A–D; this is a five-minute read, not a project.

**Priority:** P0 for the confirmation read; DEFER on A–D until Issues 1–5 (which are cheaper and more clearly load-bearing for Creative FAIL) are tried first — spending on a better QA *detector* before spending on the *generator* changes that would fix what it detects is the wrong order of operations.

---

## Issue 9 · Storyboard Gate

**Verdict: MODIFY**

**Facts confirmed:** `FACT` (`vnext/phase2/production.py`, `Production.storyboard`): confirmed — exactly two static PNG stills per beat (`frames=[round((start+min(.2,(end-start)/4))*fps), round(max(start,end-.1)*fps)]`, i.e. a near-start and a near-end frame), rendered via `npx remotion still`, no motion/video preview generated for the Gate at all. This matches Synthesis §4.5 exactly.

**Corrected formulation:** given Issue 5's finding that motion is currently near-zero anyway (nothing moves once revealed except during the first 8 frames), a **short motion preview** (Synthesis's option A) would, *today*, look almost identical to the two-still version for most beats — there's barely any motion to preview. This makes "stills + short motion preview" a weak investment **until after** Issue 5's motion primitives are added; sequencing matters here. The lower-cost, higher-value-*right-now* fix is the Synthesis's second option in disguise: extend the *existing two-still* mechanism to include a **contact-sheet view across all beats side by side** (pure UI, reuses the exact PNGs already generated, zero new render cost) so a reviewer can visually scan for "beat 3 and beat 5 look identical" — which is a real, code-confirmed Creative FAIL symptom (XIAO-Y pose repetition, `MOTION_REPETITION` warning) that a contact sheet directly surfaces and per-beat stills do not.

**Recommended implementation / experiment:** ship the contact-sheet view first (no new render cost, reuses existing artifacts); revisit "stills + motion preview" after Issue 5's motion primitives exist, since only then will a motion preview show something a still doesn't.

**Priority:** P1 (contact sheet, cheap); DEFER (motion preview, sequenced after Issue 5)

---

## Issue 10 · Subtitle / Renderer Truth Drift

**Verdict: MODIFY, and I can now explain *why* it likely happened this way (new finding)**

**Facts confirmed:**
- `FACT` (`vnext/phase2/hardening/audio.py`, `AudioClock.subtitles`): the EDT-generating code explicitly sets `'color':'#ffffff','background':None` on every subtitle clip's metadata.
- `FACT` (`vnext/phase2/production.py`, `mechanical()`): the deterministic QA check is `if c.metadata.get('background'): issue('SUBTITLE_BACKGROUND',owner='SUBTITLE')` and `if c.metadata.get('color','#ffffff').lower() not in ('#ffffff','white'): issue('SUBTITLE_COLOR',...)` — both calls to `issue()` **omit the `severity` argument, whose default is `'BLOCKER'`**. That means: if the EDT's subtitle metadata ever declared a non-null `background`, mechanical QA would **hard-fail** the render (`FAIL`, not `PASS_WITH_RISK`), per `verdict='FAIL' if any(x.severity=='BLOCKER'...)`.
- **New `HYPOTHESIS` this round, directly explaining the drift the Synthesis only describes**: given the deterministic QA rule above already exists and already BLOCKERs on any declared subtitle background, the engineering path of least resistance for fixing “white subtitles on white canvas” under time pressure was very likely to add the dark backing **only in the renderer** (`Composition.tsx`), specifically *because* doing it honestly (setting `background` in the EDT metadata that `AudioClock.subtitles` emits) would have immediately tripped this pre-existing BLOCKER check and required a second, larger change to the QA rule itself. I do not have the actual commit message or PR discussion to confirm this was the reasoning, so this stays HYPOTHESIS, but it is a specific, testable one: **if this hypothesis is right, fixing the drift by updating the EDT metadata to be honest will require touching the `SUBTITLE_BACKGROUND` QA rule in the same change**, not just adding a config layer as the Synthesis's PROPOSAL suggests.

**Inference accepted:** this is option B (“legitimate Renderer Policy”) that needs a `Renderer-neutral Visual Style Config` / `Typography Profile` extension — I agree, but only if the QA rule change happens in the same breath, otherwise the fix just re-triggers the exact BLOCKER it was presumably built to avoid.

**Corrected formulation:** the minimal correct fix is: (1) add `subtitle_backing: {enabled: bool, opacity: float}` (or similar) to `TypographyProfile` (already exists as an artifact type, already has a `SUBTITLE` `FontRole`, natural home for this); (2) have `AudioClock.subtitles()` read it and set `background` truthfully instead of hardcoding `None`; (3) update the `SUBTITLE_BACKGROUND`/`SUBTITLE_COLOR` mechanical QA checks to validate *against the configured policy* rather than blanket-forbidding any background/non-white color; (4) have `Composition.tsx` read the same EDT metadata instead of unconditionally drawing its own backing. This is a coherent, small, four-file change, not a new subsystem.

**Recommended implementation / experiment:** implement the four-step fix above; verify by confirming `mechanical()` no longer needs a special-cased BLOCKER-avoidance and that `Composition.tsx`'s subtitle rendering is driven entirely by EDT metadata (i.e. delete the current unconditional dark-backing code path).

**Priority:** P1 (real EDT-truth violation, but not currently causing a visible defect — the pixels are already correct, just untracked)

---

## Issue 11 · Track C 3–5 minute risk

**Verdict: MODIFY**

**Facts confirmed:**
- `FACT` (`SLICE-006-TRACK-B.md`): first render 2m8s (128s) for 61.461s output; corrected re-render 2m4s (124s) for the same duration after a small EDT edit (one clip's x-position moved). **The near-identical render time (128s vs 124s) despite the EDT actually changing is itself informative**: it suggests render time in this range is not dominated by the specific edit's cost, consistent with the Synthesis's own caution about extrapolating from duration alone.
- `FACT` (`SLICE-004A-BACKGROUND-JOBS.md`): a **separate, synthetic 93.013-second** render is also on record, but that Slice document does not state its wall-clock render time (only that preflight/mechanical-check overhead was later moved out of the synchronous path) — I looked for it and it is genuinely not stated in the text I read. This means **I cannot confirm or deny the Synthesis's implicit 61s→124s→(linear extrapolation to 180s) scaling using this second data point**, contrary to what a naive reading might assume; the 93s sample is not usable as a second timing anchor from what's in this document.
- **Arithmetic check on the Synthesis's own extrapolation**: 124s / 61.461s ≈ 2.02× realtime. A naive linear extrapolation to 180s (3 min) gives ≈364s, which *would* exceed the 300s timeout — consistent with the Synthesis's caution that this deserves a real test, not a green light.

**Inference accepted:** "45MB is not a proven 3–5min blocker" — the KB/s arithmetic (Track B ≈70KB/s) is simple and correct; 3min≈13MB, 5min≈22MB, both under 45MB by a healthy margin, assuming bitrate doesn't change with duration (a reasonable assumption for a fixed-resolution H.264 encode of similar visual complexity).

**Inference rejected / sharpened:** the Synthesis's own §12 Q11 asks whether render time is driven by duration or by clip count/complexity — I can partially answer this from `VisualResolver.clips()`: **clip count scales with beat count, not duration directly**. A 7-beat, 61s video and a hypothetical 21-beat, 180s video (same beats-per-second density) would have roughly 3× the clip count (text slots, character clips, media clips, subtitle clips per beat), and Remotion's per-composition overhead (font loading via `delayRender`, asset resolution) is plausibly closer to linear-in-clip-count than linear-in-duration. This means **a meaningful 3-minute test must control for beat density**, not just stretch duration — a 3-minute video with the *same* ~8.8s/beat pacing as Track B would have ~20 beats (≈3× Track B's clip count), which is a fair proportional test; a 3-minute video with only 7–10 beats (sparser) would under-test render cost and over-estimate headroom.

**Corrected formulation:** the render-time driver hypothesis should be stated as “probably closer to O(beat/clip count) than O(duration) but unconfirmed”, and the required experiment must specify beat density, not just total duration, to be a meaningful test.

**Recommended implementation / experiment:** run the 3-minute test at Track B's pacing (≈20 beats, not fewer), record wall time, peak memory, storyboard time and QA input size as the Synthesis already proposes, **and additionally record clip count** so the next data point can actually distinguish the duration-driven vs. clip-count-driven hypotheses instead of leaving it as unresolved as it is now.

**Priority:** P1 (needed before Track C claims can be made either way, but not blocking the next Creative-quality iteration)

---

## Issue 12 · Prompt Governance

**Verdict: MODIFY**

**A correction to my own earlier work, made transparently because the Synthesis's framing partially rests on it:** in my D-003 Round 02 review (`docs/project-brain/discussions/D-003-role-prompt-quality-contract/02_CLAUDE_REVIEW.md`, §5.5/§8), I stated that `NUMBER_NOT_IN_APPROVED_SOURCE`-style number checking for Director "目前只是文本指令，没有对应的程序化校验" and proposed building a deterministic validator for it. **This was wrong.** Reading `vnext/phase2/production.py`'s `Production.ir` this round, I found it already exists: `if set(numbers(str(semantic_slots)+' '+beat.keyword))-set(numbers(segment['text']))): raise ValueError('DIRECTOR_NUMBER_MISMATCH')`, enforced deterministically at `DirectorIR` creation time, for every beat, unconditionally. **I did not have this file open during the D-003 review** (it was not in that round's required reading list) and inferred its absence from the *prompt text alone* mentioning the rule without verifying the code. This is exactly the kind of error the Council process exists to catch, and I'm flagging it in public rather than quietly fixing my old document, per the instruction not to edit D-003.

**Effect on the Synthesis's Prompt Governance ordering:** this strengthens, not weakens, Synthesis §9's point 5 ("deterministic 的事情不要继续塞 Prompt") — the codebase already has more deterministic coverage of Director's number-fabrication risk than either of my own D-003 review or (implicitly) the Synthesis credits it with, which further supports **not** spending early effort re-litigating rules that already have code enforcement, and instead prioritizing the parts of D-003 that have zero enforcement today: the PromptComposer/schema-dedupe work (still real — the double schema-embedding bug I found in `runtime.py`+`gateway.py` during D-003 Round 02 has not been touched by any commit since) and the actually-missing quality-taste instructions in `director_contract.py` (also still real, still zero PPT/XIAO-Y-consistency language, confirmed unchanged this round via the no-code-drift check in `00_SCOPE.md`).

**Verdict on the Synthesis's reordering (invocation → PromptComposer → schema dedupe → deterministic/LLM boundary → semantic consumption → Role Pack → Qualification):** **ACCEPT**, with one adjustment: given this round's Issue 3 finding (several "semantic consumption" fields resolve to “delete, don't wire up” rather than needing new consumer code), item 5 (“semantic consumption”) is cheaper than the Synthesis may be assuming — it's partly a deletion task, not a build task, and could be pulled earlier/merged with item 3 (schema dedupe) as a single “shrink the payload” pass.

**Recommended implementation / experiment:** before touching Creative FAIL (Issues 1–5), do only the **already-scoped, zero-design-risk** D-003 items in one small pass: (a) delete the double schema-embedding in `runtime.py`, (b) delete/stop-writing the confirmed-unused fields from Issue 3, (c) add the missing PPT/XIAO-Y-consistency instructions to `director_contract.py`'s `instructions` string (pure text addition, no schema change). None of these require new infrastructure (PromptComposer, invocation unification) and all three were already fully specified in the D-003 Round 02 review.

**Priority:** P0 for (a)/(b)/(c) above (cheap, already-specified, directly supports Issue 2's Director-quality work); P2 for the larger PromptComposer/invocation-unification project (real, but not blocking the next test video).

---

## §7 · Shared blind spots (GPT + Claude prior rounds + WorkBuddy + this Synthesis)

Only listing items with actual evidence behind them, per the task's own instruction not to pad this section:

1. **`FACT`-supported**: every round so far, including this one, has treated "Beat count == Segment count" (Track B's 7:7) as primarily a *timing* question (D-002's frame). Issue 1 above is the first time in this conversation's Council history that segment/beat **density relative to target duration** is named as a *separate*, upstream confound from both D-002 (timing accuracy) and Director/Resolver quality (visual execution). This is a real gap across all prior rounds, not just the Synthesis.
2. **`FACT`-supported**: no round, including this one until now, had actually opened `vnext/phase2/hardening/visual.py`'s `TEMPLATES`/`LAYOUTS` tables to notice that **12 templates already exist but only ~7 are reachable automatically**. Every prior round (D-003, and by inheritance the Synthesis) discussed “expanding Director's template control” as if new templates would need to be built. They don't — the registry is already there, unused. This is a real, evidence-backed shared blind spot, not a stretch.
3. **`HYPOTHESIS`, offered with appropriate hedging**: “去 PPT 感缺少明确可测试的 Product Quality Contract” (the task's own suggested blind spot) does appear real — nowhere in any document read across this entire conversation (D-001 through this Synthesis) is there a **numeric or checklist definition** of “not PPT-like” that a QA rule or a human reviewer could apply consistently. `MOTION_REPETITION`'s all-same check (Issue 1) is the closest thing that exists, and it's a weak proxy. I don't have a ready-made fix to propose here beyond noting Issue 2's contact-sheet reviewer aid (Issue 9) is a step toward *human-checkable* PPT-feel, not a formal contract.

Not claiming the other candidate blind spots the task lists (“should Director own beat density at all”, “is EDT carrying too much abstraction”, “should Resolver become a full Visual Compiler”, “does fixed XIAO-Y PNG cap variety for 3–5min video”) as confirmed — I don't have code evidence this round that clearly supports or refutes them beyond what's already in Issues 1–4 above, and manufacturing additional “blind spots” without evidence would violate the task's own instruction (“不要为了数量硬找”).
