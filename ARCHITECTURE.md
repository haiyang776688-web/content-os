# Content OS vNext · Phase 1 architecture

## Boundary

The existing Content OS at the configured `LEGACY_ROOT` remains a read-only migration source and an independently runnable application. vNext keeps its own SQLite database, artifact files, UI and HTTP server. It does not import Legacy runtime modules or write into the Legacy tree.

```text
HTML Workbench → FastAPI → Role Runtime → Gateway → Provider Adapter
                         ↓              ↓
                 Artifact Graph      Jobs / Observability
                         ↓
                EDT (timeline truth)
                 ├─ Remotion adapter
                 └─ Jianying exporter (outbound only)
```

Roles name work; workers choose providers and models. A worker assignment is project data, so changing it creates a new assignment artifact and does not change workflow code. All provider credentials pass through `SecretStore`; the browser receives only readiness and capability metadata.

The SQLite database holds mutable project projections, jobs, media indexes and references. Every substantial output is an immutable JSON artifact under `data/projects/<id>/artifacts/`. `events.jsonl` is append-only. Dependency edges store exact artifact IDs and output hashes. A new upstream revision marks dependent artifacts stale without rewriting historical artifact files.

The Character, Style, Voice and Element packs are separate registries. Production contracts refer to pack IDs and asset IDs. No workflow, director or timeline contract has XIAO-Y-specific branching. Legacy migration copies verified bytes into vNext packs and writes an explicit SHA manifest.

EDT is the only editable timeline representation. Renderer and exporter adapters consume it and cannot write changes back. Remotion output and Jianying output are derived artifacts with preflight and a degradation report.

## Packages

- `vnext/contracts.py`: canonical Pydantic contracts and schema export.
- `vnext/storage/`: SQLite, immutable artifacts, events and dependency graph.
- `vnext/gateways/`: model, voice and tool contracts.
- `vnext/core/`: role runtime, H2 and jobs.
- `vnext/media/`: linked folders, hash identity, thumbnails and short video proxies.
- `vnext/core/editing.py`: EDT validation and revisioned edit commands.
- `vnext/renderers/remotion/`: EDT mapping and preview component.
- `vnext/exporters/jianying/`: outbound mapping and loss report.
- `vnext/migration/`: verified Legacy pack migration.
- `vnext/apps/workbench/`: local FastAPI server and HTML UI.

## First phase limits

The local mocks work without paid keys, and the Remotion adapter renders real stills and MP4 previews from EDT. The mock voice is a test tone, not spoken TTS. Online provider calls use a configurable OpenAI-compatible chat endpoint; provider-specific multimodal mapping and online semantic quality require separate acceptance. The Jianying adapter writes both a transfer bundle and a native draft. Native open, edit, save, reopen and export were verified on the local 11.5.0-beta5 installation; see JIANYING_NATIVE_POC_REPORT.json. Export is one-way, has no draft import, and other versions are unverified. Every newly exported draft still requires a local open/edit/export check. Advanced NLE, login, team access, automatic publishing and full ASR are outside Phase 1.

## Phase 2 incremental foundation

Phase 1 contracts remain readable; `ProjectConfig.phase2_enabled` defaults to false. Enabling Phase 2 adds its formal rule sets, configuration snapshot and strict bound-script path. Ordinary imports become references, so imported plain text cannot bypass fact binding.

```text
Sources → FactPack → Primary Script → Editor → Independent Audit → H2
             ↑                               FAIL → owner Change Request
             └──────── evidence resolution ← DISAGREEMENT (no vote)
H2 Script → Scene/Beat DirectorIR → Pattern/Media → EDT V2 → real Storyboard
                                                   ↓          ↓
                                               Visual EDT   human Gate
                                                            ↓
                            Voice → EDT → Mechanical QA → Remotion → Video QA
                                                              ↓
                                   Native Export ← EDT → reference ReviewPack → H3
                                                                            (no publish)
08 Evolution → append ledgers → CURRENT_RULES + RULE_CATALOG → next skill snapshot
```

`vnext/phase2/knowledge.py` resolves six skill layers and records the effective versions. Four formal rule-set artifacts and the complete active rule catalog become role-specific snapshot dependencies. Source revisions only invalidate consumers of the referenced source IDs. A policy revision invalidates prior production snapshots even if it is the first newly activated rule. Historical Script parent IDs are metadata, not circular current dependencies; only ScriptEditor and stage replay can reuse a traceable historical parent. Audit, H2 and production require the canonical current Script.

DirectorIR expresses semantic IDs and intentions, never pixels or a specific font. Its design table is a read-only projection whose edits create a new owned IR revision through CommandBus. EDT V2 is still the timeline truth; schema upgrade is explicit and preserves original ranges. VISUAL_EDT ignores audio-only changes so adding approved voice does not invalidate a storyboard. Character/style/render-profile changes invalidate visual output; interface language changes do not.

Fonts are an independent local registry. TypographyProfile maps eight roles; ProjectFontSnapshot pins exact source hashes and face bytes. TTC faces are extracted to content-addressed cache files. Browser FontFace and Remotion load those same bytes. Production checks source/cache integrity and glyph coverage; fallback is explicit. Native fonts are reported unsupported/approximated until a target-specific mapping is actually verified. Font bytes are neither sent to providers nor included in the source release.

StageCache is a rebuildable projection over STAGE artifacts and exact hashes. It supports bounded reuse and individual stage rerun, not a background DAG scheduler. ReviewPack references exact current artifact IDs/hashes instead of copying source truth. QA can veto and route findings but cannot alter owned content. Native export remains one-way.

The local workbench has trusted single-user role checks, not account authentication or multi-tenant security. Real provider quality, advanced patterns, full geometry QA and portable typography remain separate acceptance items in CAPABILITY_ROADMAP.json.

## Phase 2 Closure: shared preview and i18n

`CompositionResolver` maps canonical EDT, current media bytes, typography snapshot, approved script and visual dependencies to one content-addressed composition. Both `RemotionAdapter.prepare` and the read-only `/preview` endpoint call it. `ProgramMonitor.tsx` and the render entry point import the same `Composition.tsx` scene. Only asset URL prefixes differ at the browser boundary. PREVIEW_FRAME, cache files, playhead, safe overlays, zoom and selection are non-canonical projections; the Player owns the audio/frame clock.

Font updates invalidate existing dependencies. Preview can show the latest draft with a stale warning; explicit timeline `REFRESH_DEPENDENCIES` creates a command-owned new EDT while retaining clips and rejecting obsolete Script/DirectorIR. Visual regeneration is an explicit command preserving audio tracks, never a silent mutation during preview. Formal render still requires current preflight, storyboard and mechanical checks.

All UI text uses centralized locale dictionaries plus canonical presentation mappings. Locale is a browser preference and not an artifact dependency. Locale switching reads dictionaries and restores inputs/selection/page; backend enums, IDs, hashes, user content and brand names stay canonical. Machine-readable details are collapsed with localized summaries. Future UI additions must update both dictionaries and registry coverage tests.
