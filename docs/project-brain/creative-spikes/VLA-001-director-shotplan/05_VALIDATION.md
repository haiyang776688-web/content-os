# VLA-001 · Validation

## Deterministic and contract checks

- Adapter output contains no geometry, CSS, font-size or raw animation fields.
- Script IDs, segment IDs, Fact IDs, asset IDs, region IDs and hashes are validated.
- `PROVE` / `DEMONSTRATE` select Evidence as PRIMARY.
- Character presence requires an explicit Character Role.
- one-primary compilation invariant passes for every generated shot.
- every generated ShotPlan field has a compiler, review, validation or provenance consumer.
- the compiler owns all geometry and emits explicit layers/primitives.
- renderer source contains no Visual Job, Visual Mode, Shot Type or Evidence Treatment policy branch.
- rejected and stale review revisions block final rendering.

## Automated validation

- VRE-001 + VLA-001 targeted Python tests: 9 passed.
- Remotion TypeScript check: PASS.
- Repository regression excluding the known contradictory baseline assertion: 224 passed, 1 deselected, 1 warning.
- Test A decoded audio equals VGB-002 F2: PASS.
- Test A exact duration/frame count: PASS.
- Test B duration range, job diversity, evidence use and mode change: PASS.

The complete suite still reports the pre-existing failure `test_visual_binding_change_stales_edt_but_interface_language_does_not`: the test expects a NUMBER-pattern fixture to emit no CHARACTER after attaching XIAO-Y, while the frozen baseline's `NUMBER_EMPHASIS` resolution permits a character composition. The same isolated assertion failed before VLA-001 and this branch does not modify that production resolver or test.

## Visual review

Both reviewed contact sheets and sampled final-render sheets were inspected. Test A preserves F2's evidence/character responsibility handoffs. Test B alternates six shot types, uses evidence/diagram as the information carrier in the middle sequence, and returns to XIAO-Y only for defined transition, responsibility and summary functions. Neither result rotates generic page templates.

This review is VLA-001 engineering validation, not H3 or H4.
