# Producer / Consumer Audit

The machine-readable record is [motion-primitive-contract-audit.json](evidence/motion-primitive-contract-audit.json). It reports 11 declared primitives, 11 implemented consumers and zero declared-but-unrendered capabilities.

| Primitive | Producer / semantic source | Allowed layer kinds | Renderer behavior | Result |
| --- | --- | --- | --- | --- |
| `NONE` | implicit static layer | BACKGROUND, CHROME, FACT_NODE, SUBTITLE | stable base style | PASS |
| `PUSH_IN` | FOCUS | EVIDENCE, CHARACTER | uniform scale 0.92 → 1 | PASS |
| `FADE_IN` | REVEAL; supporting context for CONNECT | EVIDENCE, CHARACTER | opacity 0 → 1 | PASS |
| `FOLLOW_PATH` | FOLLOW | EVIDENCE, CHARACTER | x translation to compiled anchor | PASS |
| `MATCHED_WIPE` | COMPARE | EVIDENCE | left-to-right clip reveal plus small x arrival | PASS |
| `POP_CUT` | INTERRUPT | EVIDENCE, CHARACTER | uniform scale 0.82 → 1 | PASS |
| `RETURN_TO_ANCHOR` | RETURN | EVIDENCE, CHARACTER | opacity reveal plus uniform 1.05 → 1 settle | PASS |
| `DRAW_CONNECTION` | CONNECT relation emitter | RELATION only | SVG stroke dash path reveal | PASS |
| `SETTLE_HOLD` | SETTLE | EVIDENCE, CHARACTER | uniform scale 1.025 → 1 | PASS |
| `DRAW_UNDERLINE` | HIGHLIGHT_REGION emitter | UNDERLINE only | procedural width reveal | PASS |
| `LABEL_REVEAL` | CALLOUT emitter | CALLOUT only | opacity plus 24px x return | PASS |

## Gap found and closed

Before MPH-001, a CONNECT shot sent `DRAW_CONNECTION` both to the Evidence layer and to the RELATION layer. Only the RELATION SVG actually drew a connection, so the Evidence declaration was ornamental metadata. The compiler now resolves supporting Evidence or Character context to `FADE_IN` and reserves `DRAW_CONNECTION` for RELATION. The semantic remains CONNECT.

`MATCHED_WIPE` previously had no generic Renderer behavior. It is retained because COMPARE is a real semantic need and is now implemented as an observable deterministic clip reveal on EVIDENCE. It is not an alias for fade.
