# Motion Design Contract

The semantic contract lives in `vnext/phase2/experimental/motion_design_v1.py`.

```text
MotionDesignPlan
  source_shot_plan_id
  phrases[]

MotionPhrase
  phrase_id
  shot_id
  intent
  motion_primary
  motion_secondary[]
  motion_background[]
  phases[]

MotionPhase
  role: PRIMARY | SECONDARY | BACKGROUND
  phase_semantic: ANTICIPATION | PRIMARY_ACTION | IMPACT |
                  SECONDARY_RESPONSE | SETTLE | HOLD
  relative_order: BEFORE_PRIMARY | WITH_PRIMARY | AFTER_PRIMARY
  strength: SUBTLE | NORMAL | STRONG
```

The semantic artifact contains no frame count, millisecond duration, scale, translation, pixels, easing curve, spring stiffness, CSS or raw animation code. Director and ShotPlan continue to express WHAT and WHY. The Motion Design Contract expresses qualitative dynamic structure.

## Four phrases

| Phrase | Semantic progression |
| --- | --- |
| EXPLAIN | primary reveal → supporting response → settle |
| FOCUS | anticipation → primary focus action → secondary response → settle |
| IMPACT_WARN | anticipation → impact → secondary response → settle |
| CONNECT | restrained source context → relationship draw → explanatory response → settle |

The contract does not add Renderer primitives. Every generated clip still passes the MPH-001 primitive capability contract.
