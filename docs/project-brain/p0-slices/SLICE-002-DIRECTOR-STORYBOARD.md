# Slice 2 · Director → Storyboard → Preview → Gate

**Date:** 2026-09-28
**Branch:** `p0/gui-only-e2e-interim`
**Status:** PASS for the isolated browser path through Storyboard Gate; P0 GUI-Only E2E and Track A/B remain unproven.
**Council:** D-001 remains OPEN/PENDING; `DECISIONS.md` was not changed.

## Implemented

- The ordinary Visual page now presents Director scenes and beats, approved script text, XIAO-Y action, visual pattern, imported asset choices, keyword and pattern-specific text fields. It sends only the supported `SET_BEAT` changes, with `expected_revision`; no raw IR JSON is needed. Undo uses the existing CommandBus cursor.
- Quick preview uses the existing browser composition monitor and a derived provisional EDT. Formal Remotion storyboard stills are generated separately, immediately before the human Storyboard Gate. Voice already present disables this provisional rebuild path.
- A project without a typography profile can choose a locally indexed CJK font in the Visual page; this creates a project font snapshot through the existing typography command. The detailed typography page remains available.
- Director/EDT regeneration now refuses to overwrite a newer human-edited revision by default (`HUMAN_EDITS_PRESENT`). A discard requires explicit GUI confirmation and an exact `expected_revision`. The Director role path checks both before and after its model call.
- Storyboard generation from the GUI binds the expected Director and EDT artifact IDs. Gate approval binds the generated Storyboard artifact. A fullwidth colon in provisional captions was found to violate storyboard preflight; deterministic caption splitting now removes it.

## Browser evidence (isolated data copy)

The same synthetic test project from Slice 1, `PRJ-26c9693f0aff`, continued from H2 through the normal browser controls. It selected the existing local XIAO-Y pack and style, then GLM `glm-4.7` produced a real `DIRECTOR_IR` v1. The Visual page displayed 21 Beats and the current XIAO-Y action catalog without presenting raw IR as the primary UI. Changing B01's XIAO-Y action and keyword through the Beat card produced `DIRECTOR_IR` v2 (`ART-19a0569c714b46c0`).

The first quick preview attempt exposed a missing typography profile. The browser selected a local Hiragino Sans GB face and created the profile/font snapshot, then generated a provisional EDT. The first formal storyboard attempt failed deterministic preflight on `SUBTITLE_PUNCTUATION` because `：` was not split; after the targeted fix and preview refresh, the browser generated `EDT` `ART-6a25a4f87d6e41c3`, approximately 80 seconds at the provisional clock. It then generated 42 Remotion stills for the 21 Beats (first-to-last image mtime span approximately 67.1 seconds), wrote a `STORYBOARD` v1, and used a clearly labeled **P0_TEST_HARNESS** reviewer to approve the synthetic board. `STORYBOARD_GATE` `ART-abf8737bbf424e42` became READY/APPROVE, and the workflow projection advanced to Voice/Audio Timing. This is test approval of synthetic material, not a user's approval of a production video.

All browser actions operated on `/tmp/content-os-p0-spikes.6d6PKf`, a copy of project data. No production `phase2_preview_data` was modified and no new sensitive media was sent to a cloud provider. The original known regression project remains intact.

## Frontend architecture checkpoint

The workflow still projects state from persisted Project/Artifact/Gate records. `app.phase2State` is a read-only fetch for pattern options and stage data, not another writable workflow state. In this browser path, edits, preview refresh, still generation, Gate, and page reload all found their current revision; no event binding or state synchronization failure was observed. The Visual UI was added as one scoped module plus small Workbench integration, rather than adding another set of global variables.

There is a concrete maintainability risk: `workbench.js` still has a large combined action handler, and the older Phase 2 dialog still exposes a parallel technical storyboard surface. The new Visual page is the normal path; cleanup of the technical surface can be considered after P0. This checkpoint finds no evidence requiring a frontend framework migration, so the current framework is retained.

## Remaining

- This EDT is provisional. A fresh formal Voice and AudioTimingMap have not yet been produced for this project, so there is no Final Editable EDT, MP4, QA, H3, or deliverable.
- Formal storyboard stills are still a synchronous long HTTP request; Slice 4 must move them to the minimal persistent job contract.
- The 21-Beat Director output is lengthy for an approximately 80-second preview. Editorial and visual quality of this test plan are not accepted merely because the Gate API was exercised.
