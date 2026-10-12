# Claude Synthesis Review · Scope & Baseline Verification

**Model:** Claude Sonnet 5 (Anthropic)
**Date:** 2026-09-29
**Target document:** `docs/project-brain/discussions/COUNCIL_SYNTHESIS_2026-09-29.md`
**Task type:** Engineering / Architecture Red Team Review — no Decision authority, no code changes.

## Baseline verification (equivalent of the requested git checks, via GitHub API — no local git access in this environment)

| Check | Expected | Observed | Result |
| --- | --- | --- | --- |
| `main` HEAD | near `270ffb8` | `get_commit(sha=main)` → `270ffb85c0145f4caa6c99d6dc67712224446375`, message `docs: make branch divergence snapshot explicit` | **PASS**, exact match |
| `p0/gui-only-e2e-interim` HEAD | `323f7a2376efcfcfd1643a3e9d15333e084c1739` | `get_commit(sha=p0/gui-only-e2e-interim)` → same SHA, message `test: record fresh live gui e2e track B` | **PASS**, exact match |
| merge base | `674957813b5efea3...` | Not independently recomputed (no merge-base API call available in this toolset); accepted from `HANDOFF_2026-09-29_P0_GUI_E2E.md` §8 and Synthesis header, both internally consistent with each other | **ACCEPTED, not independently recomputed** |
| `main` vs interim divergence | unknown until checked | `HANDOFF_2026-09-29_P0_GUI_E2E.md` §8 states ahead 10 / behind 16 as of its own write time. Not re-verified by an equivalent of `git diff --stat` (no such tool available); treated as self-reported by the repo's own docs, not independently recomputed | **ACCEPTED, not independently recomputed** |
| Business code changed between D-001 Final baseline and now | should be none unless explicitly stated | `list_commits` on `main` since `fc045b0` (D-001 Final) through `270ffb8` shows only `docs:`/`council:`-prefixed commits; no `vnext/` path changes. The interim branch is a **separate, diverged implementation branch** — its code is real and was read directly at HEAD, not assumed identical to `main` | **PASS**, no silent code drift on `main`; interim branch code read on its own ref |

**Important scoping note**: because `main` and `p0/gui-only-e2e-interim` are diverged (not merged), "the current code" is not a single tree. Every code file cited in `01_CLAUDE_REVIEW.md` was fetched at `refs/heads/main` (for files not known to differ) or explicitly re-fetched at the interim branch tip where the Synthesis's own claims concern P0-only behavior (Track B slice files, `HANDOFF` doc). Where a specific file's ref matters, the review states it. No file was assumed unchanged between the two refs without either (a) reading it on the actually-relevant ref, or (b) the file being outside the P0 diff surface (e.g. `vnext/phase2/production.py`, `vnext/phase2/hardening/visual.py`, `vnext/renderers/remotion/resolver.py`, `vnext/renderers/remotion/project/src/Composition.tsx`, `vnext/phase2/contracts.py`, `vnext/phase2/hardening/audio.py` were all read at `refs/heads/main`, which is standard practice for this repo — Council docs land on `main`, P0 implementation work lands on the interim branch, and prior rounds' evidence, e.g. D-003 Round 02, already established that engine/contract-level files are not part of the P0 GUI branch's own diff).

## Documents read this round

**Primary review target:**
- `docs/project-brain/discussions/COUNCIL_SYNTHESIS_2026-09-29.md` (full)

**Project Brain:**
- `CURRENT_STATE.md`, `IMPLEMENTATION_STATE.md`, `PRODUCT_TASTE.md`, `DECISIONS.md`, `OPEN_QUESTIONS.md`, `COUNCIL_PROTOCOL.md` — all read in full in prior Council rounds (D-001/D-003) at commits confirmed unchanged since (directory listing SHAs matched); **not re-fetched byte-for-byte this round**, treated as current per the no-code-drift check above. Where Track B facts postdate these files (all four still describe pre-P0 or partial P0 state), the newer `HANDOFF_2026-09-29_P0_GUI_E2E.md` and `SLICE-006-TRACK-B.md` are used as the authoritative, more recent source, consistent with the Synthesis's own evidence-priority rule.
- `HANDOFF_2026-09-29_P0_GUI_E2E.md` (full, newly read this round — this is the actual "branch divergence snapshot" the task's baseline commit refers to).

**Track B / p0-slices (read at interim branch tip `323f7a2`):**
- `SLICE-006-TRACK-B.md` (full)
- `SLICE-003-VOICE-TIMELINE.md` (full)
- `SLICE-004A-BACKGROUND-JOBS.md` (full)
- `SLICE-002-DIRECTOR-STORYBOARD.md`, `SLICE-004B-QA-H3-DELIVERY.md`, `SLICE-001-PROJECT-TO-H2.md`, `SLICE-005-TRACK-A.md`: **listed but not read this round** (directory listing confirmed their existence; content not fetched — see UNKNOWN markers in `01_CLAUDE_REVIEW.md` for anything that would have depended on them). This is a real gap, not an oversight to hide: Slice 2 in particular (Director/Storyboard) could contain additional detail on the first-still-job geometric preflight failure narrated in Track B; the review below relies on `SLICE-006-TRACK-B.md`'s own summary of that event plus the underlying code, not Slice 2's fuller narration.

**Prior Council rounds (read for continuity, not re-litigated):**
- D-001 (`00`–`05`, including my own `04_CLAUDE_FINAL.md`), D-002 (`00_TOPIC.md`, `01_GPT_PROPOSAL.md`), D-003 (`00`–`04`, including my own `02_CLAUDE_REVIEW.md`): all previously read in full in earlier rounds of this same conversation; content not re-fetched, summarized from memory of those rounds where cited.
- `WB-001-independent-gap-review/`, `WB-002-glm53-independent-review/`: **directory listings confirmed to exist; individual files (`00_SCOPE.md`, `01_GLM_BLIND_REVIEW.md`, `02_GLM_REVIEW_OF_WB001.md`, `03_MODEL_COMPARISON.md`, and WB-001's equivalents) were NOT read in full this round.** The Synthesis document's own §2 ("Reviewer 身份更正") already reproduces WB-002's self-correction verbatim, and the task prompt itself independently states the same correction — the two are consistent with each other, so the correction itself is treated as established without needing a third independent read. However, **any WB-001/WB-002 *finding* that the Synthesis cites as fact is only trusted here to the extent it was independently re-verified against actual code in this round** (see `01_CLAUDE_REVIEW.md` — most of the load-bearing claims in Synthesis §4 *were* independently re-derived from `vnext/phase2/production.py`, `vnext/phase2/hardening/visual.py`, `vnext/renderers/remotion/resolver.py`, and `Composition.tsx` directly, not taken on WB's or the Synthesis's word).

## Code read this round (all at `refs/heads/main` unless noted)

- `vnext/phase2/contracts.py` (full — `Beat`, `Scene`, `DirectorIR`, `QAItem`/`QAReport`, `EditCommand` schemas)
- `vnext/phase2/production.py` (full — `Production.ir`, `generate_edt`, `storyboard`, `storyboard_gate`, `CommandBus`, `mechanical()` QA, `Review`)
- `vnext/phase2/hardening/visual.py` (full — `VisualResolver.plan`, the character-action allocator, template/layout tables)
- `vnext/phase2/hardening/audio.py` (full — `AudioClock.create/from_voice/retime/subtitles`)
- `vnext/renderers/remotion/resolver.py` (full — `CompositionResolver`)
- `vnext/renderers/remotion/project/src/Composition.tsx` (full — actual motion primitives)
- `vnext/providers/director_contract.py`, `vnext/gateways/model/gateway.py` (read in the D-003 round of this same conversation; content reused, not re-fetched, since no code commits landed on `main` since then)

**Not read this round, flagged where it matters:** `vnext/core/governance.py`, `vnext/phase2/knowledge.py`, `vnext/phase2/intelligence.py` (read in an earlier session for MiniMax/VisualQA plumbing; not re-fetched this round — see UNKNOWN markers), `vnext/renderers/remotion/adapter.py`, `vnext/providers/workflow.py` (read in D-003 round), `vnext/core/runtime.py` (read in D-003 round), XIAO-Y character registry JSON, template/style registry JSON files, and the actual pytest test files. No test was executed; all test-count claims (205 passed, 23 passed) are taken from the branch's own recorded documents, not reproduced.

## What this scope does NOT cover

- No live server, no browser, no rendering was executed. Every timing/size number in this review is either quoted from `SLICE-006-TRACK-B.md`/`HANDOFF_2026-09-29_P0_GUI_E2E.md` (both self-reported by the same working session that produced Track B) or derived arithmetically from those numbers.
- No independent confirmation that the 205/23 test-pass counts are current; these are read, not re-run.
- WB-001's own document body was not read; only the Synthesis's digest of it and code that plausibly corroborates its claims were checked.
