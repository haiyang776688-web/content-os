# FAI-001 Fault Matrix

The automated fault suite is `vnext/tests/test_fai001_alignment_runtime.py`.

| Case | Expected behavior | Result |
|---|---|---|
| Valid cached artifact | reuse exact artifact; do not invoke engine twice | PASS |
| Audio hash changes | old alignment becomes STALE | PASS |
| Approved Script changes | old alignment becomes STALE | PASS |
| Model identity changes | cache identity changes; old artifact becomes STALE | PASS |
| Alignment configuration changes | cache identity changes; old artifact becomes STALE | PASS |
| Model missing | status `NOT_AVAILABLE`; effective CURRENT | PASS |
| Model hash corrupt | status `NOT_AVAILABLE`; effective CURRENT | PASS |
| User cancellation | terminal `CANCELLED`; effective CURRENT | PASS |
| Server/process interruption | orphan RUNNING job becomes FAILED; retry succeeds | PASS |
| Coverage below threshold | artifact blocked; consumer remains CURRENT | PASS |
| Stored artifact body/hash mismatch | artifact refused and marked STALE | PASS |

Additional contract regressions also pass:

- project default is `CURRENT` and reports `NOT_REQUIRED`;
- READY alignment without approved bindings remains effectively CURRENT;
- Sample A retains the same 18 Beat IDs and applies only TG-004 and TG-007;
- opt-in EDT cache identity includes usable alignment/binding artifacts and excludes stale alignment;
- role ownership prevents non-ALIGNMENT writers from creating timing maps and non-HUMAN/DIRECTOR writers from creating bindings.

The focused alignment suite contains 14 passing tests. The wider frozen-TCU/job/provider/i18n regression group contains 75 passing tests.

The repository-wide run reached **245 passed / 1 failed** after providing the existing Remotion dependencies to this isolated worktree. The remaining failure is `test_visual_binding_change_stales_edt_but_interface_language_does_not`; the same isolated test also fails on the frozen TCU baseline at `8a42a83`, because that legacy fixture receives a CHARACTER track after enabling the XIAO-Y pack while its assertion expects no character. FAI-001 does not alter that visual-template behavior and does not patch the frozen baseline issue.
