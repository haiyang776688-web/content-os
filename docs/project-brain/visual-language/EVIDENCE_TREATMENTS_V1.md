# Evidence Treatments v1

Evidence Treatment answers how a registered evidence asset carries proof. It is distinct from Shot Type and animation.

| Treatment | Meaning | Deterministic compiler responsibility | QA expectation |
| --- | --- | --- | --- |
| `FULL_CONTEXT` | show the authentic surrounding UI/source | contain or cover inside safe area; preserve provenance | source identity and relevant region are locatable |
| `FOCUS_REGION` | move attention toward a registered normalized region | pan/zoom to the region without clipping it | focus matches semantic focus |
| `DETAIL_CROP` | make a registered region readable | crop from the original asset and preserve source hash/region | crop contains the claimed evidence |
| `HIGHLIGHT_REGION` | mark an exact subregion | draw a non-destructive overlay derived from normalized geometry | highlight does not obscure the source text |
| `DIM_NON_FOCUS` | reduce irrelevant context while retaining orientation | apply mask outside focus region | original context remains recognizable |
| `CALLOUT` | attach 1–4 words to a region | place callout away from source content and subtitle | label is short and does not make a new unsupported claim |
| `RELATION` | connect two registered objects or evidence nodes | produce stable anchors and relation line | relation is explanatory and accurately labelled |
| `BEFORE_AFTER` | compare two authenticated states | use consistent scale and a declared basis | both states and ordering are clear |

Every evidence-bearing shot records `evidence_asset_id`, treatment, normalized region when required, and semantic focus. Pixel crops belong to the compiler output, not the Director plan. Derived crops and overlays retain the original evidence asset ID, hash and normalized geometry.

Treatments may be combined only through a compiler-owned recipe. Examples: `FULL_CONTEXT → FOCUS_REGION → DETAIL_CROP`; `DETAIL_CROP + HIGHLIGHT_REGION`; `BEFORE_AFTER + CALLOUT`. The Director does not choose CSS or coordinates.

Evidence is not proof merely because it is visible. Semantic/Visual QA must still ask whether the shown region supports the narration and whether uncertainty or limitations remain visible.
