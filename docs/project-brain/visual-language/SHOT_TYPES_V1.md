# Shot Types v1

Shot Types are semantic visual primitives. They replace “page template” as the target planning vocabulary, while the twelve existing template assets remain available through a compatibility map.

## Canonical set

| Shot type | Primary purpose | Typical protagonist | Compatible visual jobs |
| --- | --- | --- | --- |
| `CHARACTER_INTRO` | introduce the real object or question | XIAOY | EXPLAIN, TRANSITION |
| `CHARACTER_EXPLAIN` | explain a concept with supporting evidence or short text | XIAOY or EVIDENCE | EXPLAIN |
| `CHARACTER_REACTION` | interrupt an expectation and create a semantic beat | XIAOY | REACT, WARN |
| `CHARACTER_RESPONSIBILITY` | embody judgment, review or accountability | XIAOY | WARN, EXPLAIN |
| `EVIDENCE_CONTEXT` | establish the authentic source or UI context | EVIDENCE | PROVE, DEMONSTRATE, EXPLAIN |
| `EVIDENCE_FOCUS` | move attention to one meaningful region | EVIDENCE | PROVE, DEMONSTRATE |
| `EVIDENCE_DETAIL` | make a source detail readable | EVIDENCE | PROVE, DEMONSTRATE |
| `EVIDENCE_HIGHLIGHT` | mark the exact supporting or contradicting area | EVIDENCE | PROVE, WARN |
| `EVIDENCE_COMPARE` | show two evidence states or conditions | COMPARISON | COMPARE, DEMONSTRATE |
| `RELATION_EXPLAIN` | explain a relationship between named real objects | DIAGRAM or EVIDENCE | EXPLAIN, PROVE |
| `KEYWORD_PUNCTUATION` | deliver one short conceptual or emotional punctuation | TEXT, NUMBER or XIAOY | REACT, WARN, TRANSITION |
| `SUMMARY` | condense established information | XIAOY, TEXT or DIAGRAM | SUMMARIZE |
| `END_CARD` | close with a supported action or identity | XIAOY or TEXT | SUMMARIZE |

The first version is frozen at 13 types. New types require a demonstrated visual responsibility that cannot be expressed by these primitives.

## Legacy compatibility map

This is migration metadata, not permission to select a whole page layout in the target Director.

| Legacy template | Target Shot Type | Migration note |
| --- | --- | --- |
| `CHARACTER_CENTER` | `CHARACTER_INTRO` or `SUMMARY` | choose by visual job |
| `CHARACTER_LEFT_TEXT_RIGHT` | `CHARACTER_EXPLAIN` | text must be short; evidence takes priority when present |
| `INFO_LEFT_CHARACTER_RIGHT` | `CHARACTER_EXPLAIN` or `CHARACTER_RESPONSIBILITY` | responsibility requires real review context |
| `CHARACTER_LOGO` | `CHARACTER_EXPLAIN` | only when the asset is genuinely a logo or brand object |
| `CHARACTER_SCREEN` | `CHARACTER_REACTION` or `CHARACTER_RESPONSIBILITY` | screen remains contextual evidence |
| `EXTREME_CLOSEUP` | `CHARACTER_REACTION` | one reaction beat, not a reusable page |
| `KEYWORD_FULL_FRAME` | `KEYWORD_PUNCTUATION` | never repeat full narration |
| `SCREEN_FULL_FRAME` | `EVIDENCE_CONTEXT` | context first, then focus/detail as needed |
| `SCREEN_DETAIL_ZOOM` | `EVIDENCE_FOCUS` or `EVIDENCE_DETAIL` | choose treatment separately |
| `COMPARE_SPLIT` | `EVIDENCE_COMPARE` | both sides must have a declared comparison basis |
| `THREE_POINT_SUMMARY` | `SUMMARY` | no forced three-item count |
| `CTA_END_CARD` | `END_CARD` | CTA must be supported by the episode goal |

## Selection constraints

- `PROVE` and `DEMONSTRATE` require an evidence-bearing shot.
- `REACT` requires `CHARACTER_REACTION`; the next shot must `RETURN` to evidence when evidence caused the reaction.
- `RELATION_EXPLAIN` cannot imply a real operation unless the evidence contains that operation.
- Repeating a Shot Type is allowed when the semantic state changes; alternating types without information change is not progress.
