# Slice 1 · Project → Source/Media → Fact → Script → Audit → H2

**Date:** 2026-09-28

**Branch:** `p0/gui-only-e2e-interim`

**Status:** PASS for the Slice 1 browser path; this is not P0 GUI-Only E2E acceptance or Track A/B.
**Council:** D-001 remains OPEN/PENDING; `DECISIONS.md` unchanged.

## Implemented in this slice

- New Project collects name, topic, content type and opens Source/Fact. Existing project records remain readable through default values.
- Research source import now has a file picker and drag target. Media import accepts a browser-selected file or drag/drop, copies it to a controlled project directory, registers a `media_asset_id`, and shows filename/type/status/source. Absolute folder linking remains advanced.
- The strict script page edits narration by segment, exposes Claim text/type and supported Fact/Evidence, and saves a formal new `SCRIPT` through `CommandBus` with `expected_revision`. A changed claim must match its edited segment exactly; a factual claim must select a supported Fact. Previous script text appears in a read-only comparison. Audit and H2 remain separate.
- A read-only workflow projection shows current stage/version/gate/status, unresolved risk count, next action, blocking reason, and history count using persisted Project/Artifact/Gate truth. It does not create another workflow state.

## Browser evidence (isolated data copy)

1. A new project `PRJ-26c9693f0aff` was created solely through the browser. A manually written, non-sensitive test document was imported with the file picker. The Source artifact is `ART-4348bd232b39440b`.
2. The browser selected per-call cloud consent. DeepSeek `deepseek-flash` extracted 11 source quotations (`RESEARCH` `ART-39ff2ac83a934171`). The browser confirmed them into 11 source-bound Facts (`FACT_PACK` `ART-15750cb580324dec`).
3. DeepSeek produced a 485-character formal strict script (`SCRIPT` v1 `ART-d084e00622b34b8e`). The deterministic coverage report was `PASS_WITH_RISK` because “第一步” looked like a ranking. The browser recorded a reasoned `NON_CLAIM` decision (`ART-62a7ed2bfbfb4e61`); this did not invent a Fact.
4. GLM `glm-4.7` performed independent audit on that script (`AUDIT` v1 `ART-3908d210233f40e0`, PASS). Browser H2 approval produced `H2_GATE` `ART-3f6b0ec0900e4784`, and the project became `SCRIPT_LOCKED` with the current script ID. No H4/publish action occurred.
5. In a separate isolated copy of the existing known regression project, the browser changed one sentence and its Claim, producing formal `SCRIPT` v5 `ART-6891fbd9531e4603`, current coverage PASS, a new independent audit, then H2. This specifically closes SPIKE-001's old `SCRIPT_REFERENCE` trap for strict existing scripts.
6. The media file picker copied a test Markdown file into a separate new project's controlled workspace and displayed its registered `MED-bef7c11b847b` identity. The source picker was also exercised from a fresh project.

All identifiers above are from temporary test data, not new production history. The production `phase2_preview_data` and known regression project were not changed by these browser tests. Cloud calls used only the test document, under the test project's per-call consent. No new sensitive media was sent.

## Automated verification

- `vnext/tests/test_p0_workflow.py` checks project metadata persistence, controlled media import, unsupported type rejection, strict script revision binding, and stale revision refusal.
- The full vNext suite after the final Slice 1 changes: **192 passed, 0 failed, 1 existing Starlette deprecation warning**.
- JavaScript syntax and both locale registries checked; the browser loaded the workflow status strip and correctly advanced the fresh project from Fact → Script → Audit/H2 → Director.

## Remaining outside Slice 1

The new project has **no Director IR, Storyboard, Voice, final EDT, Render, QA, H3, or deliverable**. Browser observations do not establish Track A's controlled provider-boundary fake or Track B's fresh 60–90 second live MP4. The existing default worker conflict remains: DeepSeek actually performed Research/Script, while independent Audit used GLM after selection. That does not settle Q-004 or revise the Red Team design.
