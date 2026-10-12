# Local Project Inventory

Audit date: 2026-10-12

This inventory records the private development checkout as observed before creating the public snapshot. Paths and personal identifiers are intentionally omitted. It is evidence for snapshot selection, not a promise that every historical branch is publishable.

## Selected public source snapshot

| Item | Value |
|---|---|
| Latest validated engineering baseline | `p0/motion-design-contract-1` |
| Private baseline commit | `8d7ff76b9bcc883ba0afe7dc6f3fc4d915e21122` |
| First sanitized candidate | `open-source-prep` at `723a3cb89dacc79c5e39a23a45ec98bf95a26a24` |
| Final source | `open-source-prep` plus security, licensing, documentation and reproducibility corrections made by `open-source-final-audit` |
| History policy | Export tracked working tree only; create a new repository with fresh Git history |

`open-source-prep` is a direct descendant of the MDC baseline. It deliberately removes private Provider verification, the real local voice profile, model/font/media binaries and experimental renders. The final audit does not merge later unfinished product work.

## Worktrees found

| Branch / worktree | Commit | Working tree | Meaning |
|---|---:|---:|---|
| `p0/asset-aspect-ratio-hardening-1` | `1e0a423` | clean | Focus-preserving aspect-safe crop work; already represented in the later integration/MDC lineage. |
| `p0/alignment-runtime-integration-1` | `ef3b812` | clean | FAI opt-in runtime and fallback validation. |
| `p0/audio-timing-spike-1` | `e79aa07` | clean | ATS timing experiment. |
| `p0/gui-production-integration-1` | based on `8d7ff76` | **18 changed/untracked paths** | Unfinished GUI-001 implementation. Not validated, not committed and intentionally excluded from the public snapshot. |
| `p0/motion-design-contract-1` | `8d7ff76` | clean | Latest validated engineering baseline and source for open-source preparation. |
| `p0/motion-primitive-hardening-1` | `a180d83` | clean | MPH primitive producer/consumer contract. Ancestor of MDC. |
| `p0/timing-consumer-upgrade-1` | `8a42a83` | clean | TCU consumer validation. Incorporated through integration lineage. |
| `p0/v1-integration-baseline-1` | `0dfe8aa` | clean | Reconciles timing and visual hardening before MPH/MDC. |
| `open-source-final-audit` | based on `723a3cb` | expected audit edits | Final publication preparation only. |

The unfinished GUI work changes Workbench, API, runtime, production integration, storage, renderer and tests. It failed to complete a fresh GUI-only acceptance run before active development was stopped. Publishing it as production work would misrepresent the project and create an unaudited code path. It remains only in the private local worktree for possible future recovery.

## Local branches and experiment lineage

```text
private main / early Product Brain and Council work
  → creative fix and visual progression experiments
  → VGB-001 / VGB-002 visual language benchmarks
  → VRE-001 reverse engineering
  → VLA-001 Director → ShotPlan adapter
  → Asset Aspect Ratio Hardening
  → V1 Integration Baseline
  → MPH-001 Motion Primitive Hardening
  → MDC-001 Motion Design Contract (selected validated baseline)
  → open-source-prep
  → final sanitized publication audit
```

Timing work ran partly in parallel:

```text
ATS-001 timing spike
  → TCU-001 timing consumer validation
  → FAI-001 alignment runtime integration
  → V1 Integration Baseline
```

The branch graph also contains `p0/gui-only-e2e-interim`, visual benchmark branches and Council/documentation branches. All corresponding remote branches were synchronized at audit time except an old local visual-language branch behind its remote and the local `main` branch behind remote `main`. Neither stale local pointer was used as the publication source.

## Completed or validated capabilities found

The audit confirmed code/tests/docs for:

- artifact schemas, provenance, dependency invalidation and governance boundaries;
- local Workbench/FastAPI and mock-capable model/voice adapters;
- Source/Evidence/Fact/Claim/Script contracts;
- DirectorIR, ShotPlan and human storyboard review spike;
- renderer-neutral EDT and deterministic Remotion adapter;
- registered XIAO-Y/style/typography/visual-pattern assets;
- aspect-safe registered media handling;
- ATS/TCU/FAI timing and fallback experiments;
- Motion Primitive Contract and Motion Design Contract;
- mechanical QA and one-way Jianying exporter code;
- Project Brain, decisions, rejected ideas and experiment reports.

“Validated” here can mean experiment-level validation. It does not mean the capability is available in the normal GUI path.

## Incomplete capabilities found

- GUI-001 / GUI-only end-to-end production flow;
- latest vNext Director/ShotPlan/Motion paths fully integrated into the Production GUI;
- background long-job cancellation and recovery;
- complete user-facing Timeline override/invalidation behavior;
- H4 publishing authorization and real platform publishing;
- stable multi-video daily production validation;
- real multi-provider/video QA activation without private credentials/assets;
- confirmed current-project Jianying handoff artifact;
- production default adoption of ALIGNED timing or Motion Design.

## Important material not merged into the public snapshot

| Material | Reason |
|---|---|
| Uncommitted GUI-001 worktree | Incomplete, failed fresh E2E, no stable commit, would overstate readiness. |
| Real local cloned-voice registry and reference media | Personal biometric/private media. |
| Provider live-verification snapshot | May encode real account/provider execution details. |
| Experimental MP4/WAV and frame/contact-sheet evidence | Large, partly private, and redistribution status not uniformly established. |
| Cached third-party font copy | Font redistribution rights not established. |
| ASR/model weights and caches | Large external dependencies with separate licenses. |
| Historical Git commits/tags/remotes | Contain removed private data and must not enter public history. |

Where possible, the public snapshot keeps structural JSON, metrics, contracts and written conclusions. Three screenshot-based test inputs were replaced with purpose-built synthetic PNG fixtures; the local voice contract is represented by a metadata-only, unavailable example profile.

## Conflicts and omissions

1. Historical Project Brain documents describe several features as implemented while newer engineering documents classify their GUI use as partial. The public README uses separate `PRODUCTION IMPLEMENTED`, `EXPERIMENTALLY VALIDATED`, `PARTIALLY INTEGRATED`, `PLANNED` and `NOT STARTED` sections.
2. Historical reports recorded 270 passing tests at the MDC checkpoint. The public snapshot was tested independently and must cite its own result.
3. DeepSeek’s intended role is Red Team, while historical runtime defaults used it for Research/Script and used another provider for Audit. The public snapshot preserves this as a design/implementation divergence, not a resolved decision.
4. A Jianying exporter exists in code, but absence of a distributable current export artifact means the project cannot claim that the public sample completed Jianying handoff.
5. Historical screenshots and local paths were evidence of work, not portable documentation. Binary evidence was removed and local paths were replaced with neutral markers.

## Release decision

The sanitized snapshot is intentionally conservative. It favors reproducible contracts, tests, source code, original XIAO-Y assets and honest documentation over visual completeness of historical experiment reports. The original private repository remains the archival source for authorized maintainers who need private evidence; it is not part of the public release.
