# Slice 3 · Fresh Voice → Audio Timing → Final Editable EDT

**Date:** 2026-09-29
**Branch:** `p0/gui-only-e2e-interim`
**Status:** PASS for the isolated browser path through Final EDT and visual edit/undo. Render, QA, H3, delivery, Track A/B remain unproven.
**Council:** D-001 remains OPEN/PENDING; `DECISIONS.md` was not changed.

## Implemented

- The ordinary Timeline page treats the pre-voice EDT as a storyboard preview. It offers the Final Editable EDT action only after formal VOICE and AUDIO_TIMING_MAP exist. The final EDT binds both directly and contains the measured voice clip and script-derived subtitles.
- The Final Timeline page exposes preview/playhead, scene and Beat jump, visual clip selection, asset replacement for media/video tracks, visual position/scale/opacity and undo. Every write passes `expected_revision`. It does not offer voice/subtitle move, trim, duration or independent subtitle body editing.
- A visual-only EDT edit or undo now retains the current VOICE and AUDIO_TIMING_MAP dependencies. A human-approved Storyboard Gate stays bound to its upstream visual snapshot when final audio retiming and downstream Timeline edits occur. Director changes still invalidate that approval.

## Browser evidence

The isolated synthetic project `PRJ-26c9693f0aff` was created from an empty project in Slice 1 and continued via normal browser controls. It selected existing local clone profile `YU_LOCAL_V1`; the UI produced formal VOICE `ART-52f558ec699e4207` and AUDIO_TIMING_MAP `ART-793c470cc6324758`. This operation took about 14 minutes and blocked its HTTP request, confirming the Slice 4 background-job priority. No new sensitive media was sent to a cloud provider.

The browser then generated Final EDT v3 `ART-1a009dab317342d0`, measured at 92.96 seconds, with direct dependencies on both VOICE and AUDIO_TIMING_MAP. This first retime exposed a pre-fix dependency issue: the existing Storyboard Gate became stale because its old VISUAL_EDT depended on a newly superseded resolved composition. The regression was fixed for future projects; this pre-fix test project regenerated formal stills and used the clearly labeled `P0_TEST_HARNESS` reviewer to approve Storyboard Gate v2 `ART-a43774ceb6114d0b`. This was synthetic test approval, not user acceptance of a production video.

Using the new Timeline page, the browser changed B01's character X position to 0.25, producing EDT v4 `ART-ed0cf9e70a224381`, then used Undo to produce v5 `ART-3af53ceccbb44a5d`. A read-only artifact check confirmed the latest EDT, VOICE, AUDIO_TIMING_MAP, STORYBOARD and STORYBOARD_GATE are all usable; EDT v5 directly depends on both audio artifacts. The current Storyboard Gate remained valid through the downstream visual edit and undo. The 92.96-second synthetic result exceeds the later Track B target range and does not constitute Track B acceptance.

## Remaining

- Voice and formal Storyboard Still are still synchronous requests. Slice 4 must return durable job IDs quickly and support refresh, retry, single-flight and restart recovery.
- No MP4, mechanical/visual QA, H3, downloadable delivery, or all-new Track B project has been verified yet.
