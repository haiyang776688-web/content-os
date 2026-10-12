# Director IR write-only field audit

Scope: code inspection on this branch, 2026-09-29. “No runtime consumer found” means no use in the current Resolver/Renderer/QA path was found; these fields still participate in schema validation, storage, history and UI display where listed. This is a candidate cleanup list, not permission to delete fields in CS-001.

| Field | Producer | Current consumer | Status | Candidate action |
| --- | --- | --- | --- | --- |
| `Scene.purpose` | Director | DirectorIR validation and stored artifact | No production consumer found | Retain until compatibility/migration test |
| `Scene.density` | Director/default | DirectorIR validation and stored artifact | No production consumer found | Retain; examine with future density QA design |
| `Beat.purpose` | Director | Storyboard card header; validation/storage | GUI review only | Retain for human review; avoid claiming render effect |
| `Beat.visual_focus` | Director | DirectorIR validation and stored artifact | No production consumer found | Retain until a tested consumer or safe removal |
| `Beat.visual_form` | Director | DirectorIR validation and stored artifact | No production consumer found | Retain until a tested consumer or safe removal |
| `Beat.retention_function` | Director/default | DirectorIR validation and stored artifact | No production consumer found | Retain; do not imply retention optimization |
| `Beat.phrase_id` | Director/default | DirectorIR validation and stored artifact | No AudioClock/Renderer mapping found | Retain until D-002 evidence is reviewed |

Active consumer fields include `pattern_id`, `slots`, `character_intent`, `character_action_id`, `reveal_order`, `motion_intent`, `script_segment_id` and `timing_intent`. `Scene.beat_ids` controls order. The audit deliberately does not remove existing schema fields, because older artifacts and editor paths may depend on them.
