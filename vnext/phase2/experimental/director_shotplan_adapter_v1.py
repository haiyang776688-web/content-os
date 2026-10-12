"""VLA-001 opt-in DirectorIR -> ShotPlan adapter and pre-render review gate.

This module is intentionally outside the production path.  It translates the
existing geometry-free DirectorIR into the experimental DEC-011 ShotPlan.  The
adapter decides editorial semantics; ``VisualCompiler`` remains the only owner
of coordinates, sizes, crop pixels, typography sizes and animation parameters.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from vnext.contracts import StrictModel
from vnext.phase2.contracts import DirectorIR
from vnext.phase2.experimental.visual_language_v1 import (
    ALLOWED_SHOTS,
    EVIDENCE_SHOTS,
    CharacterRole,
    MotionSemantic,
    Protagonist,
    ProtagonistKind,
    Shot,
    ShotBeat,
    ShotPlan,
    ShotType,
    Treatment,
    VREInput,
    VisualJob,
    VisualMode,
    mechanical_asset_aspect_ratio_qa,
    mechanical_motion_primitive_qa,
)


class FactEvidenceBinding(StrictModel):
    fact_id: str
    statement: str
    evidence_asset_ids: list[str] = Field(min_length=1)


class DirectorShotPlanInput(StrictModel):
    source: VREInput
    director_ir: DirectorIR
    facts: list[FactEvidenceBinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def coherent(self):
        if self.director_ir.script_artifact_id != self.source.script_id:
            raise ValueError("DIRECTOR_SCRIPT_MISMATCH")
        segments = {segment.segment_id: segment for segment in self.source.segments}
        fact_ids = {fact.fact_id for fact in self.facts}
        evidence_ids = {asset.asset_id for asset in self.source.assets if asset.kind == "EVIDENCE"}
        for segment in self.source.segments:
            if not set(segment.fact_ids) <= fact_ids:
                raise ValueError("SCRIPT_FACT_MISSING")
        for fact in self.facts:
            if not set(fact.evidence_asset_ids) <= evidence_ids:
                raise ValueError("FACT_EVIDENCE_NOT_REGISTERED")
        for beat in self.director_ir.beats:
            if beat.script_segment_id not in segments:
                raise ValueError("DIRECTOR_SEGMENT_MISSING")
            media_id = beat.slots.get("media_asset_id")
            if media_id and media_id not in evidence_ids:
                raise ValueError("DIRECTOR_EVIDENCE_NOT_REGISTERED")
        return self


def _contains(value: str, *needles: str) -> bool:
    normalized = value.casefold()
    return any(needle.casefold() in normalized for needle in needles)


class DirectorShotPlanAdapter:
    """Deterministic M1 policy projection from ordinary Director beats."""

    @staticmethod
    def _asset_for(beat, segment, facts: dict[str, FactEvidenceBinding]) -> str | None:
        explicit = beat.slots.get("media_asset_id")
        if explicit:
            return explicit
        for fact_id in segment.fact_ids:
            fact = facts.get(fact_id)
            if fact and fact.evidence_asset_ids:
                return fact.evidence_asset_ids[0]
        return None

    @staticmethod
    def _job(beat, evidence_id: str | None) -> VisualJob:
        language = " ".join((beat.purpose, beat.visual_focus, beat.visual_form,
                             beat.character_intent, beat.keyword, beat.pattern_id))
        if beat.pattern_id == "A_B_COMPARE" or _contains(language, "compare", "对比", "前后"):
            return "COMPARE"
        if _contains(language, "transition", "转场", "承接", "进入下一"):
            return "TRANSITION"
        if beat.pattern_id == "CHARACTER_REACTION_MEDIA" or _contains(language, "react", "反应", "意外", "等等"):
            if _contains(language, "warn", "风险", "警告", "不能", "必须", "责任"):
                return "WARN"
            return "REACT"
        if _contains(beat.visual_form, "relation", "关系", "binding", "绑定"):
            return "EXPLAIN"
        if beat.pattern_id == "THREE_POINT_SUMMARY":
            return "SUMMARIZE"
        if evidence_id and (beat.pattern_id in ("SCREEN_DETAIL", "NUMBER_EMPHASIS") and _contains(
                language, "prove", "证明", "依据", "显示", "可见")):
            return "PROVE"
        if _contains(language, "warn", "风险", "警告", "不能", "必须", "别等", "昂贵"):
            return "WARN"
        if beat.pattern_id in ("TIMELINE_PROCESS", "CHARACTER_ACTION_SEQUENCE") or _contains(
                language, "demonstrate", "show", "演示", "展示", "步骤", "怎么"):
            return "DEMONSTRATE" if evidence_id else "EXPLAIN"
        if evidence_id and _contains(language, "prove", "证明", "依据", "显示", "可见"):
            return "PROVE"
        if _contains(language, "summary", "总结", "收束", "结论"):
            return "SUMMARIZE"
        return "EXPLAIN"

    @staticmethod
    def _region(source: VREInput, evidence_id: str | None, beat) -> str | None:
        if not evidence_id:
            return None
        asset = next(asset for asset in source.assets if asset.asset_id == evidence_id)
        if not asset.regions:
            return None
        language = " ".join((beat.purpose, beat.visual_focus, beat.visual_form,
                             beat.keyword, json.dumps(beat.slots, ensure_ascii=False))).casefold()
        scored: list[tuple[int, str]] = []
        for region_id, region in asset.regions.items():
            terms = [region_id, region.label, *region.keywords]
            score = sum(2 if term.casefold() in language else 0 for term in terms if term)
            score += sum(1 for term in terms if term and any(piece in language for piece in term.casefold().split()))
            scored.append((score, region_id))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return scored[0][1]

    @staticmethod
    def _mode(job: VisualJob, evidence_id: str | None) -> VisualMode:
        if evidence_id and job in ("PROVE", "DEMONSTRATE", "COMPARE"):
            return "EVIDENCE_HEAVY"
        return "BRAND_BALANCED"

    @staticmethod
    def _shot_type(job: VisualJob, beat, evidence_id: str | None, region_id: str | None) -> ShotType:
        if job == "PROVE":
            return "EVIDENCE_HIGHLIGHT" if region_id else "EVIDENCE_CONTEXT"
        if job == "DEMONSTRATE":
            return "EVIDENCE_FOCUS" if evidence_id else "CHARACTER_EXPLAIN"
        if job == "COMPARE":
            return "EVIDENCE_COMPARE" if evidence_id else "RELATION_EXPLAIN"
        if job == "REACT":
            return "CHARACTER_REACTION"
        if job == "WARN":
            if evidence_id and beat.pattern_id == "SCREEN_DETAIL":
                return "EVIDENCE_HIGHLIGHT"
            return "CHARACTER_RESPONSIBILITY"
        if job == "TRANSITION":
            return "CHARACTER_INTRO"
        if job == "SUMMARIZE":
            return "EVIDENCE_HIGHLIGHT" if evidence_id else "SUMMARY"
        if evidence_id and _contains(beat.visual_form, "relation", "关系", "binding", "绑定"):
            return "RELATION_EXPLAIN"
        if evidence_id:
            return "EVIDENCE_CONTEXT"
        return "CHARACTER_EXPLAIN"

    @staticmethod
    def _treatment(shot_type: ShotType, region_id: str | None) -> Treatment | None:
        if shot_type not in EVIDENCE_SHOTS:
            return None
        if shot_type == "EVIDENCE_COMPARE":
            return "BEFORE_AFTER"
        if shot_type == "RELATION_EXPLAIN":
            return "RELATION"
        if shot_type == "EVIDENCE_HIGHLIGHT":
            return "HIGHLIGHT_REGION" if region_id else "FULL_CONTEXT"
        if shot_type == "EVIDENCE_DETAIL":
            return "DETAIL_CROP" if region_id else "FULL_CONTEXT"
        if shot_type == "EVIDENCE_FOCUS":
            return "FOCUS_REGION" if region_id else "FULL_CONTEXT"
        return "FULL_CONTEXT"

    @staticmethod
    def _role(job: VisualJob, shot_type: ShotType, has_evidence: bool, index: int) -> CharacterRole:
        if job == "TRANSITION":
            return "GUIDE" if index == 0 else "TRANSITION"
        if job == "REACT":
            return "REACTION"
        if job == "WARN" and shot_type == "CHARACTER_RESPONSIBILITY":
            return "RESPONSIBILITY"
        if job == "SUMMARIZE":
            return "SUMMARY"
        if shot_type == "CHARACTER_EXPLAIN":
            return "EXPLAINER"
        return "NONE"

    @staticmethod
    def _motion(job: VisualJob, shot_type: ShotType) -> MotionSemantic:
        if job == "COMPARE":
            return "COMPARE"
        if job == "REACT":
            return "INTERRUPT"
        if job == "WARN":
            return "RETURN" if shot_type == "EVIDENCE_HIGHLIGHT" else "INTERRUPT"
        if job == "TRANSITION":
            return "REVEAL"
        if job == "SUMMARIZE":
            return "SETTLE"
        if shot_type == "RELATION_EXPLAIN":
            return "CONNECT"
        if job == "DEMONSTRATE":
            return "FOLLOW"
        return "FOCUS"

    @staticmethod
    def _protagonist(shot_type: ShotType, role: CharacterRole, has_evidence: bool) -> Protagonist:
        if shot_type == "RELATION_EXPLAIN":
            return Protagonist(primary="DIAGRAM", background=["EVIDENCE"] if has_evidence else [])
        if shot_type in EVIDENCE_SHOTS:
            return Protagonist(primary="EVIDENCE", supporting=["XIAOY"] if role != "NONE" else [])
        if role != "NONE":
            return Protagonist(primary="XIAOY", supporting=["EVIDENCE"] if has_evidence else [])
        return Protagonist(primary="TEXT", supporting=["EVIDENCE"] if has_evidence else [])

    @staticmethod
    def _callout(beat) -> str | None:
        value = (beat.keyword or beat.visual_focus).strip().replace("\n", " ")
        if not value:
            return None
        return value[:16]

    def adapt(self, item: DirectorShotPlanInput, plan_id: str) -> ShotPlan:
        segments = {segment.segment_id: segment for segment in item.source.segments}
        facts = {fact.fact_id: fact for fact in item.facts}
        durations = [beat.timing_intent for beat in item.director_ir.beats]
        scale = item.source.duration / sum(durations)
        cursor = 0.0
        shot_beats: list[ShotBeat] = []
        for index, beat in enumerate(item.director_ir.beats):
            segment = segments[beat.script_segment_id]
            evidence_id = self._asset_for(beat, segment, facts)
            job = self._job(beat, evidence_id)
            region_id = self._region(item.source, evidence_id, beat)
            mode = self._mode(job, evidence_id)
            shot_type = self._shot_type(job, beat, evidence_id, region_id)
            role = self._role(job, shot_type, bool(evidence_id), index)
            treatment = self._treatment(shot_type, region_id)
            if evidence_id and treatment is None:
                treatment = "DETAIL_CROP" if region_id else "FULL_CONTEXT"
            motion = self._motion(job, shot_type)
            start = cursor
            cursor = item.source.duration if index == len(durations) - 1 else round(cursor + durations[index] * scale, 6)
            protagonist = self._protagonist(shot_type, role, bool(evidence_id))
            shot = Shot(
                shot_id=f"{plan_id}-S{index + 1:02d}",
                shot_type=shot_type,
                start=start,
                end=cursor,
                protagonist=protagonist,
                evidence_asset_id=evidence_id,
                evidence_treatment=treatment,
                evidence_region_id=region_id if treatment not in (None, "FULL_CONTEXT") else None,
                character_role=role,
                semantic_focus=beat.visual_focus,
                motion_semantic=motion,
                callout=self._callout(beat),
            )
            if shot_type not in ALLOWED_SHOTS[job]:
                raise ValueError(f"ADAPTER_POLICY_INVALID:{job}:{shot_type}")
            shot_beats.append(ShotBeat(
                beat_id=beat.beat_id,
                script_segment_id=beat.script_segment_id,
                visual_job=job,
                visual_mode=mode,
                shots=[shot],
            ))
        return ShotPlan(plan_id=plan_id, source_script_id=item.source.script_id,
                        visual_mode="BRAND_BALANCED", beats=shot_beats)


ReviewStatus = Literal["DRAFT", "REJECTED", "APPROVED"]


class ReviewFrame(StrictModel):
    shot_id: str
    path: str
    time: float = Field(ge=0)


class ShotPlanEdit(StrictModel):
    beat_id: str
    shot_id: str | None = None
    changes: dict[str, Any]
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def safe(self):
        beat_fields = {"visual_job", "visual_mode"}
        shot_fields = {"shot_type", "protagonist", "evidence_asset_id", "evidence_region_id",
                       "evidence_treatment", "character_role", "semantic_focus",
                       "motion_semantic", "callout"}
        allowed = beat_fields | shot_fields
        if not self.changes or not set(self.changes) <= allowed:
            raise ValueError("REVIEW_EDIT_FIELD_FORBIDDEN")
        forbidden_nested = {"x", "y", "width", "height", "crop", "font_size", "css",
                            "animation", "position", "scale", "scale_x", "scale_y"}
        if any(key in forbidden_nested for key in self.changes):
            raise ValueError("REVIEW_GEOMETRY_FORBIDDEN")
        if self.shot_id is None and not set(self.changes) <= beat_fields:
            raise ValueError("REVIEW_SHOT_ID_REQUIRED")
        return self


class StoryboardReview(StrictModel):
    review_id: str
    plan_id: str
    plan_sha256: str
    status: ReviewStatus = "DRAFT"
    reviewer: str | None = None
    rejection_reason: str | None = None
    frames: list[ReviewFrame] = Field(default_factory=list)
    edits: list[dict[str, Any]] = Field(default_factory=list)
    asset_checks: list[dict[str, Any]] = Field(default_factory=list)
    mechanical_qa: dict[str, Any] = Field(default_factory=lambda: {
        "verdict": "NOT_RUN", "check": "STORYBOARD_MECHANICAL_GATE", "issues": []})


def plan_sha256(plan: ShotPlan) -> str:
    payload = json.dumps(plan.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _asset_checks(props: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for clip in props.get("clips", []):
        metadata = clip.get("metadata", {})
        if metadata.get("geometry_kind") != "REGISTERED_ASSET":
            continue
        checks.append({
            "shot_id": clip.get("ir_node_id"), "asset_id": clip.get("asset_id"),
            "asset_kind": metadata.get("asset_kind"),
            "intrinsic_width": metadata.get("intrinsic_width"),
            "intrinsic_height": metadata.get("intrinsic_height"),
            "intrinsic_aspect_ratio": metadata.get("intrinsic_aspect_ratio"),
            "fit_mode": metadata.get("fit_mode"),
            "crop_region": metadata.get("source_region"),
            "aspect_ratio_policy": metadata.get("aspect_ratio_policy"),
        })
    return checks


def attach_compiler_review_data(review: StoryboardReview,
                                props: dict[str, Any]) -> StoryboardReview:
    value = review.model_copy(deep=True)
    value.asset_checks = _asset_checks(props)
    aspect = mechanical_asset_aspect_ratio_qa(props)
    motion = mechanical_motion_primitive_qa(props)
    value.mechanical_qa = {
        "verdict": "PASS" if aspect["verdict"] == motion["verdict"] == "PASS" and
        props.get("motion_design_qa", {"verdict": "PASS"})["verdict"] == "PASS" else "FAIL",
        "check": "STORYBOARD_MECHANICAL_GATE",
        "checks": {"asset_aspect_ratio": aspect, "motion_primitive": motion,
                   "motion_design": props.get("motion_design_qa", {
                       "verdict": "NOT_RUN", "check": "MOTION_DESIGN_CONTRACT", "issues": []})},
        "issues": [*aspect["issues"], *motion["issues"],
                   *props.get("motion_design_qa", {}).get("issues", [])],
    }
    return value


def create_review(plan: ShotPlan, frames: list[ReviewFrame] | None = None,
                  props: dict[str, Any] | None = None) -> StoryboardReview:
    review = StoryboardReview(review_id=f"REVIEW-{plan.plan_id}", plan_id=plan.plan_id,
                              plan_sha256=plan_sha256(plan), frames=frames or [])
    return attach_compiler_review_data(review, props) if props is not None else review


def apply_review_edits(plan: ShotPlan, review: StoryboardReview,
                       edits: list[ShotPlanEdit]) -> tuple[ShotPlan, StoryboardReview]:
    if review.status != "DRAFT" or review.plan_sha256 != plan_sha256(plan):
        raise ValueError("REVIEW_REVISION_CONFLICT")
    value = copy.deepcopy(plan.model_dump())
    for edit in edits:
        beat = next((beat for beat in value["beats"] if beat["beat_id"] == edit.beat_id), None)
        if not beat:
            raise ValueError("REVIEW_BEAT_NOT_FOUND")
        if edit.shot_id is None:
            beat.update(edit.changes)
        else:
            shot = next((shot for shot in beat["shots"] if shot["shot_id"] == edit.shot_id), None)
            if not shot:
                raise ValueError("REVIEW_SHOT_NOT_FOUND")
            shot.update(edit.changes)
        review.edits.append(edit.model_dump())
    revised = ShotPlan.model_validate(value)
    review.plan_id = revised.plan_id
    review.plan_sha256 = plan_sha256(revised)
    review.asset_checks = []
    review.mechanical_qa = {"verdict":"NOT_RUN", "check":"STORYBOARD_MECHANICAL_GATE", "issues":[]}
    return revised, review


def reject_review(plan: ShotPlan, review: StoryboardReview, reviewer: str, reason: str) -> StoryboardReview:
    if review.plan_sha256 != plan_sha256(plan):
        raise ValueError("REVIEW_REVISION_CONFLICT")
    value = review.model_copy(deep=True)
    value.status = "REJECTED"
    value.reviewer = reviewer
    value.rejection_reason = reason
    return value


def approve_review(plan: ShotPlan, review: StoryboardReview, reviewer: str) -> StoryboardReview:
    if review.status != "DRAFT" or review.plan_sha256 != plan_sha256(plan):
        raise ValueError("REVIEW_REVISION_CONFLICT")
    if review.mechanical_qa.get("verdict") != "PASS" or any(
            issue.get("severity") == "BLOCKER" for issue in review.mechanical_qa.get("issues", [])):
        issue = next(iter(review.mechanical_qa.get("issues", [])), {})
        raise ValueError(issue.get("code", "STORYBOARD_MECHANICAL_GATE_FAILED"))
    value = review.model_copy(deep=True)
    value.status = "APPROVED"
    value.reviewer = reviewer
    return value


def require_approved(plan: ShotPlan, review: StoryboardReview) -> None:
    if review.status != "APPROVED" or review.plan_sha256 != plan_sha256(plan):
        raise ValueError("STORYBOARD_APPROVAL_REQUIRED")
    if review.mechanical_qa.get("verdict") != "PASS" or any(
            issue.get("severity") == "BLOCKER" for issue in review.mechanical_qa.get("issues", [])):
        issue = next(iter(review.mechanical_qa.get("issues", [])), {})
        raise ValueError(issue.get("code", "STORYBOARD_MECHANICAL_GATE_FAILED"))


def review_summary(source: VREInput, plan: ShotPlan, review: StoryboardReview) -> dict[str, Any]:
    narration = {segment.segment_id: segment.text for segment in source.segments}
    rows = []
    for beat in plan.beats:
        for shot in beat.shots:
            frame = next((frame.path for frame in review.frames if frame.shot_id == shot.shot_id), None)
            asset_checks = [check for check in review.asset_checks if check.get("shot_id") == shot.shot_id]
            rows.append({
                "beat_id": beat.beat_id,
                "shot_id": shot.shot_id,
                "narration": narration[beat.script_segment_id],
                "visual_job": beat.visual_job,
                "visual_mode": beat.visual_mode,
                "shot_type": shot.shot_type,
                "primary": shot.protagonist.primary,
                "evidence_asset": shot.evidence_asset_id,
                "evidence_region": shot.evidence_region_id,
                "evidence_treatment": shot.evidence_treatment,
                "character_role": shot.character_role,
                "motion_semantic": shot.motion_semantic,
                "representative_frame": frame,
                "asset": ", ".join(str(check.get("asset_id")) for check in asset_checks) or None,
                "intrinsic_ratio": ", ".join(
                    f'{check.get("intrinsic_aspect_ratio"):.6f}' for check in asset_checks) or None,
                "fit_mode": ", ".join(str(check.get("fit_mode")) for check in asset_checks) or None,
                "crop_region": [check.get("crop_region") for check in asset_checks],
                "aspect_policy": ", ".join(
                    str(check.get("aspect_ratio_policy")) for check in asset_checks) or None,
                "asset_render_checks": asset_checks,
            })
    return {"review": review.model_dump(), "rows": rows, "distributions": {
        "visual_jobs": dict(Counter(row["visual_job"] for row in rows)),
        "visual_modes": dict(Counter(row["visual_mode"] for row in rows)),
        "shot_types": dict(Counter(row["shot_type"] for row in rows)),
        "evidence_treatments": dict(Counter(row["evidence_treatment"] for row in rows if row["evidence_treatment"])),
        "character_roles": dict(Counter(row["character_role"] for row in rows if row["character_role"] != "NONE")),
    }}


def write_review_html(source: VREInput, plan: ShotPlan, review: StoryboardReview,
                      target: Path) -> None:
    """Write a self-contained editable review surface; it never writes production state."""
    summary = review_summary(source, plan, review)
    encoded = json.dumps(summary, ensure_ascii=False).replace("</", "<\\/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">
<title>VLA-001 Storyboard Review</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0e1415;color:#f5f5f2;font:15px/1.5 -apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif}}
header{{position:sticky;top:0;z-index:4;padding:20px 28px;background:#11191bcc;border-bottom:1px solid #344044;backdrop-filter:blur(12px)}}
h1{{margin:0;font-size:28px}}.meta{{color:#aab5b7}}main{{padding:24px 28px 80px;display:grid;gap:18px}}
.card{{display:grid;grid-template-columns:420px 1fr;gap:24px;padding:18px;background:#182224;border:1px solid #344044;border-radius:14px}}
.frame{{width:100%;aspect-ratio:16/9;object-fit:cover;background:#070a0b;border-radius:8px}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
label{{display:block;color:#9fb0b3;font-size:12px}}select,input,textarea{{width:100%;margin-top:3px;padding:8px;background:#0e1415;color:#fff;border:1px solid #465458;border-radius:6px}}
.narration{{grid-column:1/-1;padding:12px;border-left:4px solid #ffc800;background:#11191b}}.actions{{display:flex;gap:12px;position:fixed;right:28px;bottom:24px}}
button{{border:0;border-radius:8px;padding:12px 18px;font-weight:800;cursor:pointer}}.approve{{background:#ffc800}}.reject{{background:#ef3b30;color:white}}.export{{background:#e8eeee}}
.badge{{display:inline-block;padding:3px 8px;border-radius:999px;background:#263235;color:#d9e2e3;margin-right:8px}}
@media(max-width:1000px){{.card{{grid-template-columns:1fr}}.grid{{grid-template-columns:1fr 1fr}}}}
</style></head><body><header><h1>VLA-001 · Storyboard Review</h1><div class=\"meta\">Render 前语义检查；所有几何仍由 Visual Compiler 负责。</div></header>
<main id=\"cards\"></main><div class=\"actions\"><button class=\"reject\" onclick=\"finish('REJECTED')\">拒绝</button><button class=\"export\" onclick=\"finish('DRAFT')\">导出修改</button><button id=\"approve\" class=\"approve\" onclick=\"finish('APPROVED')\">批准</button></div>
<script id=\"payload\" type=\"application/json\">{encoded}</script><script>
const data=JSON.parse(document.getElementById('payload').textContent);const cards=document.getElementById('cards');
const qaPass=data.review.mechanical_qa?.verdict==='PASS';document.getElementById('approve').disabled=!qaPass;
const opts=(value,values)=>values.map(v=>`<option ${{v===value?'selected':''}}>${{v}}</option>`).join('');
const jobs=['PROVE','DEMONSTRATE','EXPLAIN','COMPARE','REACT','WARN','TRANSITION','SUMMARIZE'];
const modes=['BRAND_BALANCED','EVIDENCE_HEAVY'];const shots=['CHARACTER_INTRO','CHARACTER_EXPLAIN','CHARACTER_REACTION','CHARACTER_RESPONSIBILITY','EVIDENCE_CONTEXT','EVIDENCE_FOCUS','EVIDENCE_DETAIL','EVIDENCE_HIGHLIGHT','EVIDENCE_COMPARE','RELATION_EXPLAIN','KEYWORD_PUNCTUATION','SUMMARY','END_CARD'];
const primary=['EVIDENCE','XIAOY','TEXT','NUMBER','COMPARISON','DIAGRAM'];const treatments=['','FULL_CONTEXT','FOCUS_REGION','DETAIL_CROP','HIGHLIGHT_REGION','DIM_NON_FOCUS','CALLOUT','RELATION','BEFORE_AFTER'];
const roles=['NONE','GUIDE','EXPLAINER','REACTION','WARNING','RESPONSIBILITY','TRANSITION','SUMMARY'];const motion=['FOCUS','REVEAL','FOLLOW','COMPARE','INTERRUPT','RETURN','CONNECT','SETTLE'];
data.rows.forEach((r,i)=>{{const el=document.createElement('section');el.className='card';el.dataset.i=i;el.innerHTML=`<div><img class=\"frame\" src=\"${{r.representative_frame||''}}\"><p><span class=\"badge\">${{r.beat_id}}</span><span class=\"badge\">${{r.shot_id}}</span></p></div><div class=\"grid\"><div class=\"narration\"><b>Narration</b><br>${{r.narration}}</div><label>Visual Job<select data-k=\"visual_job\">${{opts(r.visual_job,jobs)}}</select></label><label>Visual Mode<select data-k=\"visual_mode\">${{opts(r.visual_mode,modes)}}</select></label><label>Shot Type<select data-k=\"shot_type\">${{opts(r.shot_type,shots)}}</select></label><label>PRIMARY<select data-k=\"primary\">${{opts(r.primary,primary)}}</select></label><label>Evidence asset<input data-k=\"evidence_asset\" value=\"${{r.evidence_asset||''}}\"></label><label>Evidence region<input data-k=\"evidence_region\" value=\"${{r.evidence_region||''}}\"></label><label>Evidence Treatment<select data-k=\"evidence_treatment\">${{opts(r.evidence_treatment||'',treatments)}}</select></label><label>Character Role<select data-k=\"character_role\">${{opts(r.character_role,roles)}}</select></label><label>Motion Semantic<select data-k=\"motion_semantic\">${{opts(r.motion_semantic,motion)}}</select></label><label>Asset<input readonly value=\"${{r.asset||'—'}}\"></label><label>Intrinsic ratio<input readonly value=\"${{r.intrinsic_ratio||'—'}}\"></label><label>Fit mode<input readonly value=\"${{r.fit_mode||'—'}}\"></label><label>Crop region<textarea readonly>${{r.crop_region?JSON.stringify(r.crop_region):'—'}}</textarea></label><label>Aspect policy<input readonly value=\"${{r.aspect_policy||'—'}}\"></label></div>`;cards.appendChild(el)}});
function finish(status){{const rows=[...document.querySelectorAll('.card')].map(card=>{{const base={{...data.rows[Number(card.dataset.i)]}};card.querySelectorAll('[data-k]').forEach(x=>base[x.dataset.k]=x.value||null);return base}});const reason=status==='REJECTED'?prompt('拒绝原因（必填）'):null;if(status==='REJECTED'&&!reason)return;const blob=new Blob([JSON.stringify({{status,rejection_reason:reason,base_plan_sha256:data.review.plan_sha256,rows}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='storyboard-review-decision.json';a.click();URL.revokeObjectURL(a.href)}}
</script></body></html>""", encoding="utf-8")
