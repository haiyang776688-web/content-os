# Slice 4b · QA → H3 → Deliver

**Date:** 2026-09-29  
**Branch:** `p0/gui-only-e2e-interim`  
**Status:** Isolated synthetic GUI path passed through downloadable MP4 and Jianying transfer ZIP. Real MiniMax review and Track A/B remain open.  
**Council:** D-001 remains OPEN/PENDING; `DECISIONS.md` was not changed.

The ordinary QA page now shows mechanical and visual verdicts, issues, actual review worker/provider, and review scope. H3 has explicit `APPROVE`, `APPROVE_WITH_RISK` and `REJECT` decisions. Each listed risk needs its own checkbox for risk approval. The existing backend review contract still validates the decision and acknowledgments. The UI states that H3 does not authorize H4, and displays the stored `publish_authorized` value. The Deliver page exposes a real MP4 download and, only after an `EXPORT` artifact exists, a Jianying ZIP download with local path and mapping limitations.

## Browser evidence

On isolated project `PRJ-26c9693f0aff`, the browser ran Mechanical QA `ART-6a4ae6c33e414b43` with `PASS_WITH_RISK` / `MOTION_REPETITION`. For this synthetic regression only, the browser explicitly changed the Video QA worker to MOCK before running it; Video QA `ART-e3a6f007f89e47be` records `MOCK_VISUAL_QA` and says MiniMax did not review the video. This is not evidence of live MiniMax quality.

The browser built Review Pack `ART-0f20c3db60604aeb` containing both risks. A plain `APPROVE` was rejected by the GUI. The browser then checked both risks and submitted `APPROVE_WITH_RISK` using the clearly labeled `P0_TEST_HARNESS` identity. The resulting H3 showed `publish_authorized=false`. This is a test record, not user approval of a production video.

The Deliver page downloaded `ContentOS-PRJ-26c9693f0aff-ART-4ec64635817f4046.mp4`. The browser then exported Jianying artifact `ART-38251e8938c04cdb` and downloaded `ContentOS-PRJ-26c9693f0aff-ART-38251e8938c04cdb-Jianying.zip`. The ZIP integrity check passed. It includes a transfer manifest, subtitles, report, editable native draft files and a README. Original media and fonts may still be referenced through local paths; the target editor has not been opened for this specific export. The GUI shows the export limitation rather than claiming perfect native fidelity.

The new download endpoint test checks actual MP4/ZIP bytes, attachment headers, ZIP members and project scoping. The full suite reports **201 passed**, zero failed and one Starlette/httpx deprecation warning. JavaScript syntax, i18n key parity and diff checks passed.

## Remaining

The synthetic GUI chain is not Track A because it used real providers earlier and a product-level MOCK Video QA, and it exceeds the 10–15 second Track A duration. It is not Track B because the topic was reused from a synthetic source, duration is 93 seconds and visual QA was MOCK. Build a deterministic fake at the provider boundary for Track A, then run Track B on a never-used topic with real providers, local voice, real render and MiniMax visual review within the approved media policy. H4 and platform publication remain out of scope.
