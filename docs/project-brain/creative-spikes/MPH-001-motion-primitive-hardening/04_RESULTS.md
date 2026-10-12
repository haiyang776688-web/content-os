# Results

## Contract and Gallery

- Declared primitives: 11
- Implemented Renderer consumers: 11
- Declared but unrendered: 0
- Emitted but unknown: 0
- Silent unsupported combinations: 0
- Gallery primitive validations: 10 / 10 PASS
- `MATCHED_WIPE`: implemented, retained
- `DRAW_CONNECTION`: RELATION-only and primitive-gated

## Aspect Ratio

- VLA Test A: 15 registered assets checked, 0 issues
- VLA Test B: 10 registered assets checked, 0 issues
- `ASSET_ASPECT_RATIO_DISTORTED`: 0 BLOCKER findings

## VLA

- Test A Known F2: PASS
- Test B Unseen Content: PASS
- Storyboard Gate: APPROVED for both
- Test B retained its two existing human pre-render edits
- No PPT regression found in reviewed contact sheets

## FAI and tests

- FAI targeted regression: 14 passed, 1 dependency deprecation warning
- MPH/VLA targeted regression: 25 passed
- TypeScript no-emit check: PASS
- Full repository run: 261 passed, 1 known nondeterministic baseline failure, 1 dependency deprecation warning

The named failure is `test_visual_binding_change_stales_edt_but_interface_language_does_not`. Five isolated repetitions on the integration baseline produced 2 passes / 3 failures; five on MPH produced 4 passes / 1 failure. This independently reproduces the task's allowed `KNOWN_BASELINE_FAILURE` and has no motion code-path dependency. Evidence: [known-baseline-flake-reproduction.json](evidence/known-baseline-flake-reproduction.json).

No new full-suite failure was found. Production timing default remains `CURRENT`.
