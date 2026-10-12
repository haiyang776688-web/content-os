# Workflow constitution

1. **Role ≠ model.** Roles invoke worker profiles through a gateway. No workflow role calls a provider API directly.
2. **Character neutrality.** Director, media resolver, EDT and renderer read Character Pack data. None branch on `XIAO-Y_V1`.
3. **Artifact truth.** Research, Script, Audit, DirectorPlan, MediaSelection, Voice, Subtitle, EDT, Render and QA results are versioned artifacts. Hidden conversation state has no authority.
4. **Single writer.** Each artifact type has an owning role. Another role submits a Change Request; it cannot edit that role's output.
5. **Append-only history.** New revisions create new files and events. A projection may update; a historical artifact cannot.
6. **Independent review.** Audit sees original input, candidate artifact and criteria. It does not see the writer's private rationale or another reviewer opinion during first review.
7. **Gate outcomes.** PASS, FAIL and PASS_WITH_RISK are distinct. A residual risk requires explicit human acceptance. A FAIL blocks downstream work.
8. **Dependency validity.** Downstream artifacts bind exact upstream IDs and hashes. Changed inputs mark descendants STALE. STALE or ASSET_GAP blocks preflight.
9. **Human H2.** Director work requires an approved, locked Script revision. Editing the Script invalidates that approval for new work.
10. **Evolution authority.** Analytics can record observations. Only Evolution / 08 can formalize a rule.
11. **Language independence.** Interface, content and subtitle language are separate project fields. The language switch changes only the interface.
12. **Timeline authority.** EDT is the source of truth. Remotion and Jianying receive one-way exports. Jianying is never imported back.
13. **Privacy.** Local media is not uploaded without its asset and project cloud policy permitting the exact operation. `ASK_BEFORE_UPLOAD` requires explicit human action.
14. **Worker fallback.** The default is ASK. Writer, Director and Voice worker changes cannot happen silently.
15. **Secrets.** Credentials never enter project JSON, artifacts, logs, exports or browser responses.
16. **Creative policy first.** Creative policy outranks Analytics and all optimization suggestions. Six skill layers cannot override HARD constitution rules. Formal policy evolves only through08; all current active rule IDs enter the compiled catalog and next run snapshot.
17. **Fact integrity.** Source evidence, Fact IDs and bound Script segments are explicit. Humanize never silently changes fact bindings or quantities. Changed prose still needs independent audit; deterministic checks do not prove semantic equivalence.
18. **No majority voting.** Model conflicts become DISAGREEMENT and return to the evidence owner. Current owner-provided evidence and a recorded resolution are required to proceed.
19. **Storyboard before execution.** Real start/end stills for every Beat must be approved on the same current visual revision before Voice or video render. Rejection routes to Director. Audio-only additions do not change the approved visual revision.
20. **Mechanical first.** Code-checkable constraints precede model video review. QA outputs owner-routed findings and cannot rewrite content. Mock reviews and test tones are explicitly labeled and never represented as real model/voice acceptance.
21. **Font truth.** Typography roles resolve through a local pinned FontSnapshot. Missing hashes/glyphs block strict production; fallback requires an explicit policy. Preview drafts do not write formal artifacts until Apply. Native substitution/loss is reported, never silently labeled exact.
22. **Review versus publish.** H3 binds a current ReviewPack and explicitly accepts every residual risk. It never grants publication authority. H1/H4 and real platform integration are unfinished in vNext; no automatic publishing is permitted.
23. **History versus projections.** Immutable artifact JSON and JSONL history are not overwritten. CURRENT_RULES, PROJECT_STATE, stage/edit projections and caches may update. Undo/Redo creates a new owned revision, never rewrites the past.
