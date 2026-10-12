# Results

## Architecture

- Director / ShotPlan remain geometry-free: PASS
- Motion Design contract contains qualitative semantics only: PASS
- Visual Compiler owns frames, offsets, curves and numeric strength realization: PASS
- Renderer remains a numeric execution layer: PASS
- MPH primitive capability contract remains authoritative: PASS
- Motion Design production default: DISABLED
- Timing production default: CURRENT

## Mechanical QA

Implemented BLOCKER codes:

- `MOTION_PRIMARY_MISSING`
- `MOTION_PRIMARY_CONFLICT`
- `SECONDARY_RESPONSE_WITHOUT_OFFSET`
- `MOTION_PHASE_INVALID_ORDER`
- `MOTION_DESIGN_UNSUPPORTED_PRIMITIVE`
- `MOTION_DESIGN_ASPECT_RATIO_VIOLATION`

Final experiment result: 4 phrases compiled, 4 Shots checked, 0 issues.

## A/B and invariants

- same Script / Audio / ShotPlan / Visual Jobs / Shot Types: PASS
- same assets / geometry / Shot timing: PASS
- only variable is Motion Design: PASS
- decoded A/B audio equal: PASS
- deterministic repeated compile: PASS
- registered assets checked: 5
- aspect-ratio issues: 0
- primitive QA: 11 declared, 11 implemented, 0 issues

## Regression

- Targeted MDC + MPH + VLA + FAI: 47 passed, 0 failed, 1 dependency warning
- TypeScript no-emit: PASS
- Full repository suite: 270 passed, 0 failed, 1 dependency warning
- VLA Test A: PASS; rendered contact sheet byte-identical to MPH baseline
- VLA Test B: PASS; rendered contact sheet byte-identical to MPH baseline
- VLA default Motion Design state: `DISABLED / NOT_RUN`
- FAI production default: `CURRENT`

The known nondeterministic baseline test did not fail in this full-suite run. No new regression was found.
