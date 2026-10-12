# Minimal Next-Step Plan · max 5 items

Prioritized by information-gain / engineering-effort, not architectural completeness, per the task's instruction. All five are individually small; none require the PromptComposer/invocation-unification project or D-002's Narration Unit question to be resolved first.

---

## 1. Deterministic character-action allocator (replace first-match)

- **Change/Experiment:** Implement the hybrid allocator from `01_CLAUDE_REVIEW.md` Issue 4 — deterministic, seeded by `(project_id, beat_id)`, avoids the last `max_repeat` recently-used actions for the same semantic intent, falls back to full pool only when necessary.
- **Owner:** Director/Resolver code area (no Prompt change, no schema change).
- **Code area:** `vnext/phase2/hardening/visual.py`, `VisualResolver.plan` (the `if pack and template['allowed_character_presence']!=['NONE']:` block).
- **Expected benefit:** directly attacks the named Track B symptom “XIAO-Y pose 重复” with a single, isolated, fully deterministic function.
- **What it proves:** whether pose repetition was purely an allocation-algorithm artifact (fixable without touching Director/Prompt at all) or whether it persists even with diversity forced, which would redirect attention to the character-action *registry's* actual coverage for the semantic intents Track B used.
- **Failure condition:** re-running a similar topic still shows repeated poses despite a large-enough action pool with no `max_repeat` collisions — that would mean the registry itself lacks enough actions per intent, not that the allocator was the problem.

---

## 2. Continuous slow zoom (Ken Burns) on MEDIA/CHARACTER clips

- **Change/Experiment:** Add a time-driven `scale` interpolation (e.g. 1.0→1.04) across each MEDIA/CHARACTER clip's full on-screen duration, not just the existing 8-frame reveal window.
- **Owner:** Renderer code area.
- **Code area:** `vnext/renderers/remotion/project/src/Composition.tsx`, `ClipView`'s `base` style computation.
- **Expected benefit:** removes the confirmed “completely static once revealed” state for every non-text clip, the single most code-confirmed contributor to “slide/PPT feel” in this review.
- **What it proves:** whether “nothing moves” was the dominant driver of PPT-feel (if the next sample reads noticeably less static even with the *same* Director/Resolver output) or whether PPT-feel persists regardless, pointing back toward composition/density/pattern-choice issues instead.
- **Failure condition:** MiniMax/human review still flags the same PPT-like complaints after this change with no other variable changed — that isolates the problem away from motion and toward layout/pattern choice or content density.

---

## 3. Widen Director's reachable template set via a per-semantic allow-list (Resolver-side rotation, no schema change)

- **Change/Experiment:** Replace the static `SEMANTICS→TEMPLATES` 1:1 lookup with a `TEMPLATES_ALLOWED: dict[str, list[str]]` covering the currently-unreachable templates (`CHARACTER_CENTER`, `INFO_LEFT_CHARACTER_RIGHT`, `CHARACTER_LOGO`, `EXTREME_CLOSEUP`) for semantically-compatible patterns, and rotate deterministically among the allow-list the same way as item 1's allocator (can share the allocator primitive).
- **Owner:** Resolver code area (still zero LLM/schema change — Director continues to supply only `semantic_pattern`/`pattern_id`, never `template_id`).
- **Code area:** `vnext/phase2/hardening/visual.py`, the `TEMPLATES` dict and the `template_id=b.get('template_id') or TEMPLATES[semantic]` line in `VisualResolver.plan`.
- **Expected benefit:** uses 12 already-built, already-registered templates instead of ~7, at zero new asset/engineering cost, directly increasing per-beat visual variety.
- **What it proves:** whether template variety alone visibly reduces “slide-like” perception, independent of motion (item 2) and pose (item 1) — running all three together in the same test makes it hard to attribute improvement, so this should be measured both combined and (if resources allow) in at least one isolated run.
- **Failure condition:** some of the four newly-reachable templates render badly for real Track-B-style content (e.g. `EXTREME_CLOSEUP` assuming a tighter character crop than the asset supports) — that's a fast, visible failure in a single storyboard-still check, not a deep bug.

---

## 4. Add missing quality-taste instructions to Director's prompt (text-only, no schema change)

- **Change/Experiment:** Add the “no PPT feel / XIAO-Y consistency / no mechanical repeated action / no generic whiteboard replacement” instructions (drafted in full in D-003 Round 02 Review §5.4) to `director_contract.py`'s `instructions` string, which currently contains zero taste guidance.
- **Owner:** Prompt/Director contract code area.
- **Code area:** `vnext/providers/director_contract.py`.
- **Expected benefit:** currently the model generating `DIRECTOR_IR` receives literally none of the product's most emphasized creative constraints (`PRODUCT_TASTE.md`, `DECISIONS.md` DEC-010) — this is a near-zero-cost, high-relevance-to-user-intent fix that's been fully specified since the D-003 round and never implemented.
- **What it proves:** whether the LLM's own beat/pattern/slot choices (as opposed to the deterministic Resolver/Renderer layers items 1–3 touch) change when explicitly told what to avoid — a genuinely different lever from items 1–3, worth testing separately since it's the only one of the five that touches the LLM's actual output rather than deterministic post-processing.
- **Failure condition:** Director's beat/pattern choices are statistically unchanged before/after (same pattern distribution, same slot usage) — would suggest the model isn't meaningfully conditioning on this kind of prose instruction, and future quality gains need to come from tighter deterministic constraints (items 1–3) rather than more prompt text.

---

## 5. Inspect one real Track B `VOICE` artifact's `provenance.method` and re-run the next test with a deliberate 1:N beat/segment mapping

- **Change/Experiment:** (a) Read the actual `provenance.method` on Track B's `VOICE`/`AUDIO_TIMING_MAP` artifacts to close the D-002 “does Track B actually have word timestamps” unknown (near-zero cost, pure read). (b) For the *next* test topic, deliberately write a script where at least one segment maps to 2–3 beats (not 1:1 like Track B), so `AudioClock.retime`'s proportional-split code path is actually exercised for the first time, and record whether the resulting intra-segment beat cuts land in sensible places.
- **Owner:** D-002 evidence-gathering (no code change for part (a); a test-topic authoring choice for part (b), not an engineering change).
- **Code area:** none for (a) beyond a read; `vnext/phase2/hardening/audio.py` (`AudioClock.retime`) is what part (b) exercises, unmodified.
- **Expected benefit:** resolves the single largest remaining D-002 unknown this review identified — whether “current retime” is adequate for the 1:N case Track B never tested — with essentially no engineering spend, informing whether D-002's larger investment (Issue 6's option A’, B, or C) is urgent or can wait behind items 1–4.
- **What it proves:** if 1:N retime already lands cuts in reasonable places (subjectively reviewed), D-002's urgency drops and items 1–4 should be fully prioritized first; if cuts land badly (e.g. splitting mid-clause), that's concrete evidence D-002's option A’ (timestamp-weighted retime) deserves to jump ahead of item 3.
- **Failure condition:** N/A in the usual sense — this is a measurement step; its “failure” is simply an inconclusive read (e.g. no `PROVIDER_TIMESTAMPS` provenance on the actual local-clone voice used, meaning the richer word-level data was never available for Track B and a different voice provider/config is needed to test it at all).

---

## Deliberately excluded from this list (and why)

- **PromptComposer / invocation-path unification** (Synthesis §9 items 1–2): real, but architecture-completeness work, not the highest information-gain-per-effort item available right now; explicitly deprioritized per the task's own instruction to favor information gain over architectural completeness.
- **Schema double-embedding fix** (`runtime.py`/`gateway.py`): genuinely free and worth doing, but it is a token-cost/hygiene fix, not something that changes the *next test video's* creative quality — it doesn't compete for a slot in a 5-item creative-quality-focused plan, though it costs nothing to do alongside item 4 in the same sitting.
- **MiniMax fps/sampling changes** (Synthesis Issue 8's options A–D): explicitly deferred in `01_CLAUDE_REVIEW.md` — improving the *detector* before the *generator* changes (items 1–4) it would detect problems in is the wrong order.
- **3-minute Track C render test** (Issue 11): important, but it's a stability/risk question for *long-form* production, not a lever on the *next test video's creative quality*, which is what this 5-item list is scoped to per the task's own framing (“用最小工程量尽快让下一条测试视频的创作质量显著优于 Track B”).
- **Subtitle/QA truth-drift fix** (Issue 10): real and specified, but purely a hygiene/traceability fix with **zero visible pixel change** (the current pixels are already correct, only the EDT bookkeeping is dishonest about it) — it doesn't move creative quality at all, so it doesn't belong in a creative-quality-focused 5-item list despite being cheap.
