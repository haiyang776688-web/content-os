# Maintainer Handoff

## Current status

**PAUSED — SEEKING MAINTAINER.** No active-development or response-time promise is made.

The public snapshot descends from the last validated private engineering baseline:

```text
stage: MDC-001 — Motion Design Contract
private branch: p0/motion-design-contract-1
private commit: 8d7ff76b9bcc883ba0afe7dc6f3fc4d915e21122
historical result: 270 passed, 0 failed, 1 warning
```

The sanitized public snapshot was independently reinstalled and retested. Its result is recorded in the release report; do not substitute the historical result for a current run.

## What the system can do today

### Implemented in code

- FastAPI local Workbench and project/artifact store;
- model/voice gateway contracts, Mock execution and secret isolation;
- typed Source/Evidence/Fact/Claim/Script/Director/EDT/QA artifacts;
- provenance, dependency tracking, stale/invalidation and gate mechanics;
- visual/style/typography/asset registries;
- deterministic Visual Compiler and Remotion adapter;
- basic Timeline operations and preview/render equivalence;
- QA/governance foundations and one-way Jianying exporter code.

### Validated as controlled experiments

- Director → ShotPlan adapter and hash-bound Storyboard Review;
- XIAO-Y Evidence Editorial language and visual modes;
- aspect-ratio safe media handling;
- post-TTS timing/alignment and fallback on a bounded sample;
- Motion Primitive Contract;
- Motion Design Contract.

### Partially integrated

- latest vNext Director/ShotPlan/Motion path in the ordinary Workbench flow;
- Timeline GUI and user override/stale handling;
- ALIGNED timing runtime (opt-in; CURRENT remains default);
- Motion Design runtime (experimental/disabled by default);
- real Video QA/provider activation;
- current-project Jianying handoff verification.

### Not complete

- GUI-only E2E;
- long-job background execution/cancel/recovery;
- stable daily 3–5 minute production;
- H4 publishing authorization and platform publishing;
- production Analytics learning loop;
- multi-tenant deployment.

## First priority: GUI-001

Do not start by adding another model. The first recommended task is:

> A normal user completes one video only through the GUI.

Required path:

```text
Create Project
→ Research / Source registration
→ Script + H2
→ Voice
→ Director / ShotPlan
→ Storyboard Review
→ Visual / Motion compile
→ Render
→ H3 Final Review
→ Export
```

Acceptance forbids the user from using Terminal, curl, internal API shortcuts, JSON edits, database patches or direct Remotion CLI. Internal background workers may use those mechanisms.

A private, uncommitted GUI-001 worktree existed at project pause time, but it had 18 changed/untracked paths and did not complete fresh E2E acceptance. It was deliberately excluded. Treat it as an optional salvage source only after a new maintainer obtains authorized private access and audits it.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd vnext/renderers/remotion/project
npm ci
npx tsc --noEmit
npm run build:monitor
cd ../../../..

CONTENT_OS_TEST_NO_KEYCHAIN=1 python -m pytest vnext/tests tests -q
CONTENT_OS_DATA="$PWD/data" uvicorn vnext.apps.workbench.server:app --host 127.0.0.1 --port 8766
```

Then open `http://127.0.0.1:8766/`. Use Mock providers first. Real credentials and user media are optional local inputs and are never part of the repository.


## Code map

| Area | Location |
|---|---|
| Workbench/API | `vnext/apps/workbench/` |
| Runtime/governance/preflight | `vnext/core/` |
| Artifact/storage contracts | `vnext/contracts.py`, `contracts/`, `vnext/storage/` |
| Provider/voice adapters | `vnext/providers/`, `vnext/gateways/` |
| Phase 2 production/timeline/QA | `vnext/phase2/` |
| Visual/timing/motion experiments | `vnext/phase2/experimental/` |
| Remotion resolver/adapter | `vnext/renderers/remotion/` |
| Remotion composition | `vnext/renderers/remotion/project/src/` |
| Tests | `vnext/tests/`, `tests/` |
| Registries | `registries/` |
| Project truth/decisions | `docs/project-brain/` |
| Experiment reports | `docs/project-brain/creative-spikes/` |

## Constraints that should not be casually broken

1. Source/Evidence/Fact/Claim/Script must stay distinguishable and traceable.
2. Director does not own pixel geometry.
3. Semantic system decides WHAT; Alignment decides WHEN.
4. Visual Compiler owns deterministic numeric geometry/motion.
5. Renderer executes resolved artifacts and does not hide creative policy.
6. Real registered media cannot be non-uniformly stretched.
7. Declared motion capability must have a real consumer or fail fast.
8. EDT is the editable timeline truth; other timelines are producers/consumers.
9. QA can reject but does not silently rewrite upstream artifacts.
10. H3 final approval is distinct from H4 publish authorization.
11. A changed upstream artifact makes dependent approval stale.
12. Code implemented, GUI available and current artifact produced are separate claims.

Read [Architecture](OPEN_SOURCE_ARCHITECTURE.md), [Lessons](LESSONS_LEARNED.md) and `docs/project-brain/DECISIONS.md` before changing these boundaries.

## Test strategy

- Run the full Python suite with keychain disabled.
- Run TypeScript checking and `npm audit` in the Remotion project.
- For visual changes, add mechanical contract tests and an explicit human review note.
- For timing changes, record the exact audio/text fixture, timing source and consumer.
- For gate changes, test stale/hash mismatch and rejection, not only PASS.
- For GUI-001, write one browser-level acceptance that starts from a new project and does not call internal APIs directly.

The open snapshot contains synthetic images and Mock providers. Tests requiring real voice, third-party media, model weights or credentials must be optional and must never make the safe base suite fail.

## Known traps

- Old README/Project Brain phase labels are historical and can overstate current GUI integration.
- Parallel branches previously reintroduced aspect-ratio bugs; use a capability matrix before merging experiments.
- More precise timing is useless unless a downstream consumer reads it.
- Static contact sheets cannot approve dynamic motion.
- A Jianying exporter in code does not prove that a current sample was handed off.
- Adding motion effects often increases PPT feel when PRIMARY and phase structure are missing.
- Model self-critique is not independent QA.

## A practical first week

1. Reproduce the published tests and Workbench smoke in a clean clone.
2. Draw the current GUI/API path against the artifact dependency graph.
3. Implement one thin GUI-001 happy path with Mock providers.
4. Add user-visible pending/failure/stale/retry state for long steps.
5. Complete one browser-only run through Export.
6. Only then evaluate enabling ALIGNED timing or Motion Design by default.
7. Collect actual expressive gaps before proposing Creative Composer.

## Definition of v1

A v1 claim should require a normal user to complete a representative long-video workflow in the GUI, recover from a failed long step, inspect/modify key artifacts, approve Storyboard and H3, explicitly authorize H4 if publishing, and reproduce the output without hidden manual patches.
