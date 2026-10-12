# VLA-001 · Storyboard Review

The review projection shows, for every beat and shot:

- narration;
- Visual Job;
- Visual Mode;
- Shot Type;
- PRIMARY;
- evidence asset and registered region;
- Evidence Treatment;
- Character Role;
- Motion Semantic;
- representative frame.

The generated standalone review page exposes editable semantic fields and `Reject`, `Export edits` and `Approve` actions. Geometry fields are absent. The Python gate contract applies an atomic list of semantic edits, revalidates the complete ShotPlan, binds the review to the revised plan hash, supports rejection, and raises `STORYBOARD_APPROVAL_REQUIRED` unless an approval matches the exact plan revision.

The exercised order was:

1. adapter generates an initial ShotPlan;
2. compiler emits pre-render props;
3. Remotion renders representative stills only;
4. review operator checks the contact sheet and semantic table;
5. edits are applied and the whole plan is revalidated;
6. representative stills are regenerated;
7. the reviewed plan hash is approved;
8. final MP4 rendering is allowed.

The reviewer recorded in this spike is `VLA_SPIKE_REVIEW_OPERATOR`. This is engineering evidence that the gate works. It is not user H3 approval and does not authorize publication.

## Post-review aspect-ratio hardening

After the human distortion finding, the projection was extended to show every registered visual asset's intrinsic ratio, fit mode, crop region and `PRESERVE` policy. Approval and render authorization now require a passing `ASSET_ASPECT_RATIO_INVARIANT` report; `ASSET_ASPECT_RATIO_DISTORTED / BLOCKER` disables approval. The original review evidence remains historical. The replacement evidence and root-cause record are in `POST_REVIEW_ASSET_DISTORTION.md`.
