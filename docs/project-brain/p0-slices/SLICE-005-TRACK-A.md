# Slice 5 · Track A browser regression

**Date:** 2026-09-29  
**Branch:** `p0/gui-only-e2e-interim`  
**Status:** PASS for the disposable provider-boundary regression; this is not live provider or human production approval.  
**Council:** D-001 remains OPEN/PENDING; `DECISIONS.md` was not changed.

Track A runs the ordinary Workbench against an isolated, disposable `CONTENT_OS_DATA` directory. The test-only launcher `vnext/tests/p0_provider_boundary.py` must be explicitly enabled with `CONTENT_OS_P0_TRACK_A=1`. It replaces only the model invocation and TTS synthesis methods at the gateway/provider boundary. Research, fact creation, script contracts, independent audit, director, storyboard stills, voice assembly, audio clock, final EDT, Remotion render, mechanical QA, Visual QA processing, H3 and export still use the normal application path. The fake model labels its metadata `P0_FAKE_PROVIDER_BOUNDARY`; the fake voice records `live_verified=false` and generates audible 440 Hz WAV segments. The fake visual finding explicitly says that no external model reviewed the video. This harness must never be represented as live provider validation.

## Browser run

Starting from empty project `PRJ-fd1f72f6c8a5` ("P0 Track A · 12秒复测"), browser actions created the project, imported a three-line synthetic source, created three cited facts, made and audited a three-segment script, recorded test H2, generated a three-beat director version, selected XIAO-Y, selected a Chinese-capable font, generated formal stills, recorded the storyboard gate, generated three fake-boundary voice segments, and built the final editable EDT. The GUI timecode changed from the provisional 30 seconds to `00:00:12:00` based on measured audio. The same EDT produced `ART-9ec82648fbd64c61` as a real Remotion MP4. `ffprobe` found H.264 video, AAC audio, 1920×1080 at 30 fps, 12.053333 seconds.

Mechanical QA returned `PASS_WITH_RISK` with `MOTION_REPETITION` and `KEYWORD_PATTERN_REPETITION`. The first Visual QA attempt was correctly blocked with `LOCAL_ONLY_ASSET_IN_VIDEO`. In this **disposable fake-provider test copy only**, the browser changed the selected XIAO-Y still asset from `LOCAL_ONLY` to `ASK_BEFORE_UPLOAD` using the existing media-policy UI; the voice asset stayed `LOCAL_ONLY`. The browser then confirmed the single review attempt. The patched gateway made no external model call; Visual QA returned `FAKE_PROVIDER_VISUAL_REVIEW` and `PASS_WITH_RISK`. The review pack listed all three risks. `P0_TEST_HARNESS` acknowledged each and recorded H3 `APPROVE_WITH_RISK`; the stored result showed `publish_authorized=false`. This is a test record, not the user's approval of a production film or H4 authorization.

The Deliver page exposed a working MP4 download and, after creating EXPORT artifact `ART-f41d9ed3f9944b91`, a Jianying ZIP download. Downloads were saved as `ContentOS-PRJ-fd1f72f6c8a5-ART-9ec82648fbd64c61.mp4` and `ContentOS-PRJ-fd1f72f6c8a5-ART-f41d9ed3f9944b91-Jianying.zip` in the user's Downloads folder. `unzip -t` passed. This confirms a transferable package, not that Jianying has opened this particular draft or preserved every visual effect.

## Failures found and fixed

The first empty-project run exposed a font-coverage problem: the default CJK-classified font lacked characters used by the script. Formal still preflight correctly failed `FONT_GLYPH_MISSING`, but the GUI had hidden its font selector after the first choice. The selector now remains available, prefers `Heiti SC` where present, and checks glyph coverage before applying. The first fake TTS returned silence, and real render preflight correctly failed `VOICE_LONG_SILENCE`. The test provider now emits an audible tone; the failed first project remains a diagnostic rather than a success claim. Final VOICE provenance derives `live_verified` from actual segment provenance, so fake audio cannot be mislabeled live.

Track A's browser path was exercised manually through the GUI, with deterministic provider responses and isolated data. It is repeatable using the test launcher and documented steps, but it is **not** yet an unattended browser automation script. Track B must independently prove fresh live providers, real local clone voice, real MiniMax visual review and H3 on a new 60–90 second topic. No H4 or real publication was attempted.
