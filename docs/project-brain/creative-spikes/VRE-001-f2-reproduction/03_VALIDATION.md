# VRE-001 · Validation

## Technical comparison

| Measure | VRE-001 automated reproduction | VGB-002 F2 Gold Master |
| --- | --- | --- |
| Resolution | 1920×1080 | 1920×1080 |
| FPS | 30 | 30 |
| Frames | 574 | 574 |
| Container duration | 19.178667 s | 19.178667 s |
| Decoded audio SHA-256 | `a4b438037280fe1abeaf0f78ef11737cbf1ce54e759e32bbd038098373c4995b` | same |
| Caption cues | 6, continuous | 6, continuous |
| Fact ID | intact | intact |
| Output SHA-256 | `4bbb37c27d1a01799c317165cccf54a53dee50cd3cb1a004e9706e2ab066195a` | `97bda94eab6fda8be603270405f211894be2bacb06ad1385cd241c2882bd0f1c` |

The different output hash is expected: this is a semantic reproduction through the new compiler, not a coordinate-level copy.

## Contract checks

- 10 shots cover 0.00–19.12 with no gap or overlap.
- each shot has exactly one compiled PRIMARY layer;
- every evidence layer retains source asset ID, source hash, named region and treatment;
- every character layer retains Character Role and resolved action ID;
- all Motion Semantic values used by the plan compile to explicit primitives;
- ShotPlan contains no pixel geometry;
- Remotion renderer contains no Shot Type/Visual Job/Visual Mode policy branch;
- invalid Visual Job/Shot Type and XIAO-Y/Role combinations are rejected.

## Focused visual review

The generated one-second contact sheet and full-resolution frames at 0.5, 3.8, 6.7, 8.4, 10.6, 12.2, 14.0, 16.4 and 18.2 seconds were compared with F2.

| Success criterion | Result | Observation |
| --- | --- | --- |
| Evidence clarity comparable | PASS | import, candidate rule, not-Fact rule, human review, source relation and Fact ID remain readable at their narrative points |
| Character role correct | PASS | guide, reaction, responsibility, transition and summary use distinct registered actions/placement |
| Protagonist correct | PASS | character leads only the intended interruption/responsibility shots; evidence or diagram leads the rest |
| Shot sequence logically equivalent | PASS | intro→evidence→boundary→reaction→return→human→source→relation→Fact ID→settle is preserved |
| No subtitle defects | PASS | six frozen cues are continuous; no wording change or visible collision in sampled frames |
| No page-template slideshow | PASS | evidence remains the shared visual space; reaction returns to its cause and relation flows into Fact ID |

This is an agent visual reproduction review, not a new H3 decision and not publication authorization.

## Automated tests

- VRE-001 contract/compiler tests: **5 passed**.
- Remotion TypeScript check: **PASS**.
- Static Architecture Review assertions: **PASS**.
- Full `vnext/tests` run: **220 passed, 1 failed**. The remaining failure is the pre-existing `test_visual_binding_change_stales_edt_but_interface_language_does_not`: its baseline assertion says a NUMBER-pattern fixture cannot produce a character, while the same baseline Resolver explicitly allows `CHARACTER_CENTER` for NUMBER after a character pack is attached. VRE-001 does not modify either file; the failure was repeated in isolation and is recorded rather than repaired outside this scope.
