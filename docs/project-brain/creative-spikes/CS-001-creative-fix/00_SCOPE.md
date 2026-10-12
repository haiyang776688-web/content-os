# CS-001 · Creative Fix Spike 1 scope

Date: 2026-09-29

Implementation baseline: `p0/gui-only-e2e-interim` at `323f7a2376efcfcfd1643a3e9d15333e084c1739`

Knowledge baseline: `origin/main`, merged without conflicts as `f61c7a35863cbd02ba3e33afcb661db1e0b12172`
Branch: `p0/creative-fix-spike-1`

The spike tests whether small changes to XIAO-Y pose selection, existing template choice, restrained continuous motion and Director guidance improve a fresh short video's actual pixels. It is an experiment, not a new architecture or a formal creative approval. The controlled run uses a fresh project and registered Workbench screenshots. It keeps script, facts, voice and source media fixed when comparing visual revisions where practical.

Allowed changes: the existing VisualResolver and Remotion renderer, Director instructions and media contract, local storyboard contact sheet, Mechanical QA repetition warnings, regression tests and this experiment record. The media contract's pre-existing `MediaAsset.kind` bug was repaired because it blocked the controlled screenshot test.

Out of scope: moving from Remotion to HyperFrames; an audio-first pipeline rewrite; new Narration Units; a general PromptComposer; 3–5 minute Track C; H4, publication, analytics, platform profiles, 9:16, Jianying architecture and changes to `DECISIONS.md`. H2 and storyboard-gate actions made by a test operator are test evidence only, not the user's approval of the film.

Pass criteria are deliberately dual: code and GUI/render/QA must work, and the actual MP4 must receive visual review against the documented Track B findings. Track B's render was unavailable for direct side-by-side viewing in this checkout, so the comparison must state that limit. A failed creative result remains a valid experiment result.
