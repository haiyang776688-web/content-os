# VRE-001 · Contract instance

The input is the same three-segment script, six captions, 19.12-second frozen voice and two authentic Workbench screenshots used by VGB-001/VGB-002. The manifest is [evidence/input.json](evidence/input.json).

## Semantic plan

| Shot | Time | Visual Job | Shot Type | PRIMARY | Evidence Treatment | Character Role | Motion Semantic |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| VRE-S01 | 0.00–1.05 | TRANSITION | CHARACTER_INTRO | XIAOY | FOCUS_REGION | GUIDE | REVEAL |
| VRE-S02 | 1.05–2.91 | DEMONSTRATE | EVIDENCE_FOCUS | EVIDENCE | FOCUS_REGION | NONE | FOCUS |
| VRE-S03 | 2.91–6.24 | PROVE | EVIDENCE_HIGHLIGHT | EVIDENCE | HIGHLIGHT_REGION | NONE | FOLLOW |
| VRE-S04 | 6.24–7.34 | REACT | CHARACTER_REACTION | XIAOY | DETAIL_CROP | REACTION | INTERRUPT |
| VRE-S05 | 7.34–9.87 | WARN | EVIDENCE_HIGHLIGHT | EVIDENCE | HIGHLIGHT_REGION | NONE | RETURN |
| VRE-S06 | 9.87–11.88 | WARN | CHARACTER_RESPONSIBILITY | XIAOY | DETAIL_CROP | RESPONSIBILITY | REVEAL |
| VRE-S07 | 11.88–12.75 | TRANSITION | CHARACTER_INTRO | EVIDENCE | DETAIL_CROP | TRANSITION | FOLLOW |
| VRE-S08 | 12.75–15.42 | EXPLAIN | RELATION_EXPLAIN | DIAGRAM | RELATION | NONE | CONNECT |
| VRE-S09 | 15.42–17.30 | PROVE | EVIDENCE_FOCUS | EVIDENCE | FOCUS_REGION | NONE | FOCUS |
| VRE-S10 | 17.30–19.12 | SUMMARIZE | EVIDENCE_HIGHLIGHT | EVIDENCE | HIGHLIGHT_REGION | SUMMARY | SETTLE |

The ShotPlan contains registered IDs, semantic labels and timing anchors. It contains no `x`, `y`, width, height, pixel crop, font size, CSS or absolute asset path. Named evidence regions are resolved from the registered input manifest.

Every field has a consumer:

- Visual Job validates compatible Shot Types.
- Visual Mode changes compiler layout recipes.
- Shot Type selects a deterministic recipe.
- Protagonist assigns PRIMARY/SUPPORTING/BACKGROUND layers and QA.
- Evidence Treatment produces evidence geometry/overlays and provenance metadata.
- Character Role selects a compatible registered action.
- Semantic focus is preserved in EDT and review data.
- Motion Semantic selects an explicit renderer-neutral primitive.
- Timing anchors produce EDT clip ranges and rhythm diagnostics.
