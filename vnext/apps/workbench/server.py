"""Local vNext workbench API. No login or cloud upload in Phase 1."""
from __future__ import annotations

import json
import os
import time
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from vnext.contracts import ErrorCandidate, Job, ModelMessage, ModelRequest, ProjectConfig, Role, RuleRecord, VoiceRequest, utc_now
from vnext.core.editing import Editing, import_script_text
from vnext.core.governance import Governance
from vnext.core.jobs.engine import JobEngine
from vnext.core.preflight import check
from vnext.core.runtime import Runtime, SCRIPT_SCHEMA
from vnext.gateways.model.gateway import ModelGateway
from vnext.gateways.voice.gateway import VoiceGateway
from vnext.exporters.jianying.adapter import JianyingExporter
from vnext.media.library.service import EXTENSIONS, MediaLibrary
from vnext.media.resolver.service import MediaResolver
from vnext.registries.catalog import ROLE_CONTRACTS, WORKERS, load_packs, worker_options
from vnext.renderers.remotion.adapter import RemotionAdapter
from vnext.storage.store import Store


ROOT = Path(__file__).resolve().parents[3]
DATA = Path(os.environ.get("CONTENT_OS_DATA") or ROOT / "data").expanduser().resolve()
store = Store(DATA)
runtime = Runtime(store)
editing = Editing(store)
media = MediaLibrary(store)
governance = Governance(store)
jobs = JobEngine(store)
@asynccontextmanager
async def lifespan(_app):
    jobs.recover_orphans()
    yield

app = FastAPI(title="Content OS vNext", version="0.2.0-preview", lifespan=lifespan)
from vnext.phase2.api import attach
attach(app,store,ROOT,runtime)
from vnext.providers.api import attach as attach_settings
attach_settings(app,store,ROOT,runtime)


def fail(error: Exception):
    if isinstance(error, PermissionError):
        raise HTTPException(403,str(error)) from error
    if isinstance(error, KeyError):
        raise HTTPException(404, str(error)) from error
    from vnext.secrets.secure import redact
    raise HTTPException(400, redact(str(error))) from error


class ProjectIn(BaseModel):
    name: str = Field(min_length=1)
    topic: str = ""
    content_type: Literal["EXPLAINER", "COMMENTARY", "TUTORIAL"] = "EXPLAINER"
    content_language: str = "zh-CN"
    subtitle_language: str = "zh-CN"


class ConfigIn(BaseModel):
    character_pack: str | None = None
    element_pack: str | None = None
    fallback_policy: str | None = None
    fallback_workers: list[str] | None = None
    budget: dict[str,float | None] | None = None
    model_pricing: dict[str,dict[str,float]] | None = None
    style_pack: str | None = None
    voice_profile: str | None = None
    render_profile: str | None = None
    interface_language: str | None = None
    content_language: str | None = None
    subtitle_language: str | None = None
    privacy_mode: str | None = None


class ScriptIn(BaseModel):
    text: str
    source: str = "HUMAN_EDIT"
    mode: str = "USE_AS_SCRIPT"


class WorkerIn(BaseModel):
    worker_id: str


class RunIn(BaseModel):
    source_artifact_ids: list[str]
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    config: dict = Field(default_factory=dict)


class FolderIn(BaseModel):
    path: str


class RelinkIn(BaseModel):
    path: str


class MediaSelectionIn(BaseModel):
    media_need: str
    mode: str = "SUGGEST"
    selected_asset_id: str | None = None


class EditIn(BaseModel):
    operation: str
    arguments: dict = Field(default_factory=dict)


class ChangeRequestIn(BaseModel):
    target_artifact_id: str
    from_role: str
    reason: str


class EvalIn(BaseModel):
    input_text: str = Field(min_length=1)
    role: Role = Role.SCRIPT_PRIMARY
    workers: list[str] = Field(min_length=2, max_length=2)


class VoiceLabIn(BaseModel):
    text: str = Field(min_length=1)
    profiles: list[str] = Field(min_length=1)


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "vnext/apps/workbench/index.html").read_text()


@app.get("/workbench.js")
def javascript():
    return FileResponse(ROOT / "vnext/apps/workbench/workbench.js", media_type="application/javascript")

@app.get("/script-workflow.js")
def script_workflow_javascript():
    return FileResponse(ROOT / "vnext/apps/workbench/script-workflow.js", media_type="application/javascript")

@app.get("/workflow-projection.js")
def workflow_projection_javascript():
    return FileResponse(ROOT / "vnext/apps/workbench/workflow-projection.js", media_type="application/javascript")


@app.get("/workbench.css")
def css():
    return FileResponse(ROOT / "vnext/apps/workbench/workbench.css", media_type="text/css")


@app.get("/api/i18n/{language}")
def i18n(language: str):
    if language not in ("zh-CN", "en-US"):
        raise HTTPException(404, "LANGUAGE_NOT_FOUND")
    return json.loads((ROOT / "vnext/i18n" / f"{language}.json").read_text())


@app.get("/api/pack-asset")
def pack_asset(path: str):
    resolved = (ROOT / path).resolve()
    asset_root = (ROOT / "assets").resolve()
    if asset_root not in resolved.parents or not resolved.is_file():
        raise HTTPException(404, "PACK_ASSET_NOT_FOUND")
    return FileResponse(resolved)


@app.get("/api/catalog")
def catalog():
    return {"roles": [x.model_dump(mode="json") for x in ROLE_CONTRACTS.values()],
            "workers": [x.model_dump(mode="json") for x in WORKERS.values()],
            "characters": load_packs(ROOT, "characters"), "styles": load_packs(ROOT, "styles"),
            "voices": __import__("vnext.phase2.hardening.voices",fromlist=["voices"]).voices(store)}


@app.get("/api/worker-options/{role}")
def options(role: Role):
    return worker_options(role)


@app.get("/api/projects")
def projects():
    return [x.model_dump(mode="json") for x in store.projects()]


@app.post("/api/projects")
def create_project(value: ProjectIn):
    try:
        return store.create_project(value.name, topic=value.topic, content_type=value.content_type,
            content_language=value.content_language,
            subtitle_language=value.subtitle_language).model_dump(mode="json")
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}")
def project_detail(project_id: str):
    try:
        project = store.get_project(project_id)
        return {"project": project.model_dump(mode="json"), "artifacts": store.artifacts(project_id),
                "jobs": [x.model_dump(mode="json") for x in store.jobs(project_id)], "logs": store.logs(project_id),
                "media": [x.model_dump(mode="json") for x in media.assets(project_id)],
                "governance": {"candidates": store.artifacts(project_id, "ERROR_CANDIDATE"),
                    "errors": governance.events(project_id, "error_events.jsonl"),
                    "rules": store.artifacts(project_id, "RULE"),
                    "current_rules": governance.current_rules(project_id)}}
    except Exception as error:
        fail(error)


@app.patch("/api/projects/{project_id}/config")
def config(project_id: str, values: ConfigIn):
    try:
        current = store.get_project(project_id)
        changes = values.model_dump(exclude_unset=True)
        candidate = ProjectConfig.model_validate({**current.model_dump(), **changes})
        if candidate.phase2_enabled:
            from vnext.phase2.configuration import visual_payload
            visual_payload(candidate)
        store.save_project(candidate)
        from vnext.phase2.hardening.dependencies import Dependencies
        Dependencies(store).pin_config(project_id)
        if candidate.phase2_enabled:
            from vnext.phase2.configuration import visual_config
            visual_config(store,project_id)
        return candidate.model_dump(mode="json")
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/script")
def script(project_id: str, value: ScriptIn):
    try:
        return editing.script(project_id, value.text, value.source, value.mode)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/script/import")
async def script_import(project_id: str, request: Request, filename: str = Query(...), mode: str = Query(...)):
    try:
        body = await request.body()
        if len(body) > 10_000_000:
            raise ValueError("SCRIPT_TOO_LARGE")
        text = import_script_text(filename, body)
        return editing.script(project_id, text, "IMPORTED:" + Path(filename).name, mode)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/h2/{artifact_id}")
def approve_h2(project_id: str, artifact_id: str, risk_acknowledged: bool = False):
    try:
        result=runtime.approve_h2(project_id, artifact_id, risk_acknowledged=risk_acknowledged)
        if store.get_project(project_id).phase2_enabled:
            from vnext.phase2.stages import StageCache
            StageCache(store).record(project_id,'H2',[artifact_id,store.latest(project_id,'AUDIT')['artifact_id']],store.get_artifact(result['artifact_id']))
        return result
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/workers/{role}")
def worker(project_id: str, role: Role, value: WorkerIn):
    try:
        return runtime.select_worker(project_id, role, value.worker_id)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/run/{role}")
def run(project_id: str, role: Role, value: RunIn):
    try:
        if store.get_project(project_id).phase2_enabled and role.value in ('RESEARCH','SCRIPT_PRIMARY','SCRIPT_EDITOR','AUDIT','DIRECTOR'):
            from vnext.phase2.stages import StageCache
            from vnext.phase2.knowledge import Knowledge
            snapshot=Knowledge(store).snapshot(project_id,role.value,value.config.get('skill_layers'))
            current=store.get_project(project_id)
            return StageCache(store).run(project_id,role.value,[*value.source_artifact_ids,snapshot['artifact_id']],
                lambda:runtime.run(project_id,role,value.source_artifact_ids,request_id=value.request_id,config=value.config),
                config=value.config,worker=current.worker_assignments.get(role.value,ROLE_CONTRACTS[role].default_worker),
                prompt=ROLE_CONTRACTS[role].prompt_id,skills=snapshot['output_hash'])
        return runtime.run(project_id, role, value.source_artifact_ids, request_id=value.request_id, config=value.config)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/change-request")
def change_request(project_id: str, value: ChangeRequestIn):
    try:
        return runtime.change_request(project_id, value.target_artifact_id, value.from_role, value.reason)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/media/folder")
def link_folder(project_id: str, value: FolderIn):
    try:
        return jobs.execute(project_id, "MEDIA_INDEX", lambda: [x.model_dump(mode="json")
            for x in media.add_folder(project_id, Path(value.path))])
    except Exception as error:
        fail(error)

@app.post("/api/projects/{project_id}/media/import")
async def import_media(project_id: str, request: Request):
    """Copy a browser-selected file into the project's controlled media workspace."""
    try:
        project = store.get_project(project_id)
        filename = Path(request.query_params.get("filename", "")).name
        suffix = Path(filename).suffix.lower()
        if not filename or filename in (".", "..") or suffix not in EXTENSIONS:
            raise ValueError("MEDIA_TYPE_UNSUPPORTED")
        destination = DATA / "projects" / project_id / "uploads" / (uuid.uuid4().hex + suffix)
        destination.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        try:
            with destination.open("xb") as output:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 500_000_000:
                        raise ValueError("FILE_TOO_LARGE")
                    output.write(chunk)
            if not size:
                raise ValueError("EMPTY_MEDIA_FILE")
            item = await run_in_threadpool(media.register, project_id, destination, EXTENSIONS[suffix],
                "user", project.privacy_mode, "PROJECT_UPLOAD", filename)
            if Path(item.original_path) != destination:
                destination.unlink(missing_ok=True)
            store.event(project_id, "MEDIA_IMPORTED", asset_id=item.asset_id, filename=filename, size=size)
            return item.model_dump(mode="json")
        except Exception:
            destination.unlink(missing_ok=True)
            raise
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/media/{asset_id}/relink")
def relink(project_id: str, asset_id: str, value: RelinkIn):
    try:
        return media.relink(project_id, asset_id, Path(value.path)).model_dump(mode="json")
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/media/relink-folder")
def relink_folder(project_id: str, value: FolderIn):
    try:
        return jobs.execute(project_id, "MEDIA_RELINK", lambda: [x.model_dump(mode="json")
            for x in media.relink_folder(project_id, Path(value.path))])
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/media/select")
def select_media(project_id: str, value: MediaSelectionIn):
    try:
        if store.get_project(project_id).phase2_enabled:
            from vnext.phase2.production import CommandBus
            result=CommandBus(store).execute(project_id,'MEDIA_SELECTION','SELECT',value.model_dump())
            from vnext.phase2.stages import StageCache
            return StageCache(store).record(project_id,'MEDIA',[],result)
        return MediaResolver(store).select(project_id, value.media_need, value.mode, value.selected_asset_id)
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}/media/{asset_id}/file")
def media_file(project_id: str, asset_id: str, thumbnail: bool = False, proxy: bool = False):
    item = next((x for x in media.assets(project_id) if x.asset_id == asset_id), None)
    if not item:
        raise HTTPException(404, "MEDIA_NOT_FOUND")
    if proxy and not item.proxy_path:
        raise HTTPException(404, "MEDIA_PROXY_NOT_READY")
    path = Path(item.thumbnail_path if thumbnail and item.thumbnail_path else
                item.proxy_path if proxy and item.proxy_path else item.original_path)
    if not path.is_file():
        raise HTTPException(404, "MEDIA_OFFLINE")
    return FileResponse(path)


@app.post("/api/projects/{project_id}/timeline")
def create_timeline(project_id: str):
    try:
        if store.get_project(project_id).phase2_enabled:
            from vnext.phase2.production import CommandBus
            return CommandBus(store).execute(project_id,'EDT','GENERATE',{})
        return editing.create_timeline(project_id)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/timeline/edit")
def edit_timeline(project_id: str, value: EditIn):
    try:
        from vnext.phase2.production import CommandBus
        return CommandBus(store).execute(project_id,'EDT',value.operation,value.arguments)
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}/preflight")
def preflight(project_id: str):
    project = store.get_project(project_id)
    if not project.timeline_artifact_id:
        return {"ok": False, "issues": ["TIMELINE_MISSING"]}
    return check(store, project_id, project.timeline_artifact_id)


@app.post("/api/projects/{project_id}/voice")
def synthesize(project_id: str, value: VoiceRequest):
    try:
        gate=None
        if store.get_project(project_id).phase2_enabled:
            from vnext.phase2.production import Production
            gate=Production(store).require_storyboard(project_id)
            approved=store.get_artifact(store.get_project(project_id).h2_script_artifact_id)
            if value.text!=approved['payload']['text']:raise ValueError('VOICE_MUST_USE_APPROVED_SCRIPT_TEXT')
        def operation():
            from vnext.phase2.hardening.voices import governed_voice
            voice = governed_voice(store,project_id,value,DATA / 'projects' / project_id / 'voice')
            item = media.register(project_id, Path(voice.audio_path), "AUDIO", "VOICE", "LOCAL_ONLY", source="GENERATED_VOICE")
            from vnext.phase2.hardening.evidence import strict
            authorization=None
            if gate and strict(store,project_id):
                authorization=store.create_artifact(project_id,'VOICE_AUTHORIZATION',{'storyboard_gate_id':gate['artifact_id'],'storyboard_gate_hash':gate['output_hash'],'h2_script':store.get_project(project_id).h2_script_artifact_id},role='HUMAN',dependencies=[store.dependency(store.get_project(project_id).h2_script_artifact_id)])
            artifact = store.create_artifact(project_id, "VOICE", {**voice.model_dump(mode="json"), "media_asset_id": item.asset_id}, role="VOICE",
                worker=value.voice_profile, provider=voice.provider, model=voice.model,
                dependencies=([store.dependency(store.get_project(project_id).h2_script_artifact_id)] if store.get_project(project_id).h2_script_artifact_id else []) + ([store.dependency(authorization.artifact_id)] if authorization else [store.dependency(gate['artifact_id'])] if gate else []))
            result=artifact.model_dump(mode="json")
            if voice.phrase_timestamps or voice.word_timestamps:
                from vnext.phase2.hardening.audio import AudioClock
                try:
                    timing=AudioClock(store).from_voice(project_id,artifact.artifact_id)
                    result['audio_timing_artifact_id']=timing['artifact_id']
                except ValueError as error:
                    result['alignment_required']=str(error)
                    store.event(project_id,'AUDIO_ALIGNMENT_REQUIRED',voice_artifact_id=artifact.artifact_id,reason=str(error))
            else:result['alignment_required']='VOICE_TIMING_ALIGNMENT_REQUIRED'
            return result
        result=jobs.execute(project_id, "VOICE", operation)
        if gate:
            from vnext.phase2.stages import StageCache
            StageCache(store).record(project_id,'VOICE',[store.get_project(project_id).h2_script_artifact_id,gate['artifact_id']],result,
                config=value.model_dump(),worker=value.voice_profile)
        return result
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}/voice/{artifact_id}/file")
def voice_file(project_id: str, artifact_id: str):
    artifact = store.get_artifact(artifact_id)
    if artifact["project_id"] != project_id or artifact["artifact_type"] != "VOICE":
        raise HTTPException(404, "VOICE_NOT_FOUND")
    return FileResponse(artifact["payload"]["audio_path"], media_type="audio/wav")


@app.post("/api/projects/{project_id}/render/still")
def render_still(project_id: str):
    try:
        project = store.get_project(project_id)
        if not project.timeline_artifact_id:
            raise ValueError("TIMELINE_MISSING")
        key = "RENDER_STILL:" + project.timeline_artifact_id
        validation=check(store,project_id,project.timeline_artifact_id)
        if not validation['ok']:raise ValueError('PREFLIGHT_FAILED:'+','.join(validation['issues']))
        previous = store.job_by_key(project_id, key)
        if previous and previous.state == "COMPLETED" and previous.artifact_id and store.is_usable_input(previous.artifact_id) and Path(store.get_artifact(previous.artifact_id)['payload']['preview_path']).is_file():
            return store.get_artifact(previous.artifact_id)
        job = Job(job_id=previous.job_id if previous else "JOB-" + uuid.uuid4().hex[:12], request_id=uuid.uuid4().hex,
            project_id=project_id, kind="RENDER", state="RUNNING", idempotency_key=key, started_at=utc_now())
        store.save_job(job)
        try:
            result = RemotionAdapter(ROOT, store).still(project_id, project.timeline_artifact_id)
            store.save_job(job.model_copy(update={"state": "COMPLETED", "artifact_id": result["artifact_id"], "finished_at": utc_now()}))
            return result
        except Exception as error:
            store.save_job(job.model_copy(update={"state": "FAILED", "error": str(error), "finished_at": utc_now()}))
            raise
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}/render/{artifact_id}/file")
def render_file(project_id: str, artifact_id: str):
    artifact = store.get_artifact(artifact_id)
    if artifact["project_id"] != project_id or artifact["artifact_type"] != "RENDER":
        raise HTTPException(404, "RENDER_NOT_FOUND")
    return FileResponse(artifact["payload"]["preview_path"], media_type=artifact["payload"].get("media_type", "image/png"))


@app.get("/api/projects/{project_id}/render/{artifact_id}/download")
def download_render(project_id: str, artifact_id: str):
    try:
        artifact = store.get_artifact(artifact_id)
        if artifact["project_id"] != project_id or artifact["artifact_type"] != "RENDER" or artifact["payload"].get("media_type") != "video/mp4":
            raise KeyError("VIDEO_RENDER_NOT_FOUND")
        path = Path(artifact["payload"]["preview_path"])
        if not path.is_file():
            raise KeyError("VIDEO_FILE_NOT_FOUND")
        return FileResponse(path, media_type="video/mp4", filename=f"ContentOS-{project_id}-{artifact_id}.mp4")
    except Exception as error:
        fail(error)


@app.post('/api/projects/{project_id}/render/still-job')
def render_still_job(project_id: str):
    try:
        target = store.get_project(project_id).timeline_artifact_id
        if not target:
            raise ValueError('TIMELINE_MISSING')
        def run():
            validation = check(store, project_id, target)
            if not validation['ok']:
                raise ValueError('PREFLIGHT_FAILED:' + ','.join(validation['issues']))
            return RemotionAdapter(ROOT, store).still(project_id, target)
        return jobs.submit(project_id, 'P0_RENDER_STILL', target,
            run, idempotency_key='P0_RENDER_STILL:' + target, stage='Validating and rendering still',
            current_target=lambda: store.get_project(project_id).timeline_artifact_id).model_dump()
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/render/video")
def render_video(project_id: str):
    try:
        project = store.get_project(project_id)
        if not project.timeline_artifact_id:
            raise ValueError("TIMELINE_MISSING")
        key = "RENDER_VIDEO:" + project.timeline_artifact_id
        validation=check(store,project_id,project.timeline_artifact_id)
        if not validation['ok']:raise ValueError('PREFLIGHT_FAILED:'+','.join(validation['issues']))
        if project.phase2_enabled:
            from vnext.phase2.production import Production,mechanical
            Production(store).require_storyboard(project_id)
            if mechanical(store,project_id,project.timeline_artifact_id,True)['verdict']=='FAIL':raise ValueError('MECHANICAL_QA_VETO')
        previous = store.job_by_key(project_id, key)
        if previous and previous.state == "COMPLETED" and previous.artifact_id and store.is_usable_input(previous.artifact_id) and Path(store.get_artifact(previous.artifact_id)['payload']['preview_path']).is_file():
            return store.get_artifact(previous.artifact_id)
        job = Job(job_id=previous.job_id if previous else "JOB-" + uuid.uuid4().hex[:12], request_id=uuid.uuid4().hex,
            project_id=project_id, kind="RENDER_VIDEO", state="RUNNING", idempotency_key=key, started_at=utc_now())
        store.save_job(job)
        try:
            result = RemotionAdapter(ROOT, store).video(project_id, project.timeline_artifact_id)
            store.save_job(job.model_copy(update={"state": "COMPLETED", "artifact_id": result["artifact_id"], "finished_at": utc_now()}))
            if project.phase2_enabled:
                from vnext.phase2.stages import StageCache
                StageCache(store).record(project_id,'RENDER',[project.timeline_artifact_id,store.latest(project_id,'STORYBOARD_GATE')['artifact_id']],result)
            return result
        except Exception as error:
            store.save_job(job.model_copy(update={"state": "FAILED", "error": str(error), "finished_at": utc_now()}))
            raise
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/render/video-job")
def render_video_job(project_id: str):
    try:
        project = store.get_project(project_id)
        target = project.timeline_artifact_id
        if not target:
            raise ValueError('TIMELINE_MISSING')
        def run():
            validation = check(store, project_id, target)
            if not validation['ok']:
                raise ValueError('PREFLIGHT_FAILED:' + ','.join(validation['issues']))
            if project.phase2_enabled:
                from vnext.phase2.production import Production, mechanical
                Production(store).require_storyboard(project_id)
                if mechanical(store, project_id, target, True)['verdict'] == 'FAIL':
                    raise ValueError('MECHANICAL_QA_VETO')
            result = RemotionAdapter(ROOT, store).video(project_id, target)
            if project.phase2_enabled and store.get_project(project_id).timeline_artifact_id == target:
                from vnext.phase2.stages import StageCache
                gate = store.latest(project_id, 'STORYBOARD_GATE')
                StageCache(store).record(project_id, 'RENDER', [target, gate['artifact_id']], result)
            return result

        return jobs.submit(project_id, 'P0_RENDER_VIDEO', target, run,
            idempotency_key='P0_RENDER_VIDEO:' + target, stage='Validating and rendering video',
            current_target=lambda: store.get_project(project_id).timeline_artifact_id).model_dump()
    except Exception as error:
        fail(error)


@app.get('/api/projects/{project_id}/jobs/{job_id}')
def project_job(project_id: str, job_id: str):
    try:
        store.get_project(project_id)
        job = next((job for job in store.jobs(project_id) if job.job_id == job_id), None)
        if not job:
            raise KeyError('JOB_NOT_FOUND')
        return job.model_dump()
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/jianying/export")
def jianying_export(project_id: str):
    try:
        project = store.get_project(project_id)
        if not project.timeline_artifact_id:
            raise ValueError("TIMELINE_MISSING")
        return jobs.execute(project_id, "JIANYING_EXPORT", lambda:
            JianyingExporter(store).export_transfer_bundle(project_id, project.timeline_artifact_id))
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}/jianying/export/{artifact_id}/download")
def download_jianying(project_id: str, artifact_id: str):
    try:
        artifact = store.get_artifact(artifact_id)
        if artifact["project_id"] != project_id or artifact["artifact_type"] != "EXPORT":
            raise KeyError("EXPORT_NOT_FOUND")
        project_root = (store.root / "projects" / project_id).resolve()
        source = Path(artifact["payload"]["path"]).resolve()
        if not source.is_dir() or not source.is_relative_to(project_root):
            raise KeyError("EXPORT_DIRECTORY_NOT_FOUND")
        native = Path(artifact["payload"]["native_draft_path"]).resolve()
        if not native.is_dir():
            raise KeyError("NATIVE_DRAFT_NOT_FOUND")
        delivery = project_root / "deliveries"
        delivery.mkdir(parents=True, exist_ok=True)
        target = delivery / f"{artifact_id}.zip"
        if not target.is_file():
            temporary = delivery / f"{artifact_id}.{uuid.uuid4().hex}.tmp"
            try:
                with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                    for file in source.rglob("*"):
                        if file.is_file() and not file.is_symlink():
                            bundle.write(file, "transfer/" + file.relative_to(source).as_posix())
                    if not native.is_relative_to(source):
                        for file in native.rglob("*"):
                            if file.is_file() and not file.is_symlink():
                                bundle.write(file, "native_draft/" + file.relative_to(native).as_posix())
                    bundle.writestr("README.txt", "Content OS one-way Jianying transfer. The native draft may reference original local media and fonts by path; relink them after moving machines. Read transfer/JIANYING_EXPORT_REPORT.json for mapping losses. This package does not verify opening in Jianying.\n")
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        return FileResponse(target, media_type="application/zip", filename=f"ContentOS-{project_id}-{artifact_id}-Jianying.zip")
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/model-eval")
def model_eval(project_id: str, value: EvalIn):
    try:
        store.get_project(project_id)
        outputs = []
        for worker_id in value.workers:
            choice = next((x for x in worker_options(value.role) if x["worker_id"] == worker_id), None)
            if not choice or choice["disabled"]:
                raise ValueError("WORKER_UNAVAILABLE:" + worker_id)
            started = time.monotonic()
            request = ModelRequest(role=value.role, worker_profile=worker_id,
                system_prompt="Return JSON with text. Keep source claims unchanged.",
                messages=[ModelMessage(role="user", content=value.input_text)],
                response_schema=SCRIPT_SCHEMA, prompt_version="MODEL_EVAL_V1")
            result = ModelGateway().invoke(request,store=store,project_id=project_id)
            outputs.append({"worker": worker_id, "output": result.structured_output,
                "latency_ms": round((time.monotonic() - started) * 1000),
                "usage": result.usage, "cost": None, "schema_status": "PASS"})
        artifact = store.create_artifact(project_id, "MODEL_EVAL", {"input": value.input_text, "role": value.role.value,
            "outputs": outputs, "human_decision": None}, role="HUMAN", prompt_version="MODEL_EVAL_V1")
        return artifact.model_dump(mode="json")
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/voice-lab")
def voice_lab(project_id: str, value: VoiceLabIn):
    try:
        project = store.get_project(project_id)
        results = []
        for profile in value.profiles:
            request = VoiceRequest(text=value.text, language=project.content_language, voice_profile=profile)
            from vnext.phase2.hardening.voices import governed_voice
            voice = governed_voice(store,project_id,request,DATA / 'projects' / project_id / 'voice_lab')
            results.append(voice.model_dump(mode="json"))
        artifact = store.create_artifact(project_id, "VOICE_LAB", {"text": value.text, "results": results}, role="HUMAN")
        return artifact.model_dump(mode="json")
    except Exception as error:
        fail(error)


@app.get("/api/projects/{project_id}/voice-lab/{artifact_id}/{index}/file")
def voice_lab_file(project_id: str, artifact_id: str, index: int):
    artifact = store.get_artifact(artifact_id)
    if artifact["project_id"] != project_id or artifact["artifact_type"] != "VOICE_LAB":
        raise HTTPException(404, "VOICE_LAB_NOT_FOUND")
    try:
        path = artifact["payload"]["results"][index]["audio_path"]
    except IndexError:
        raise HTTPException(404, "VOICE_LAB_RESULT_NOT_FOUND")
    return FileResponse(path, media_type="audio/wav")


@app.get("/api/projects/{project_id}/governance")
def governance_state(project_id: str):
    store.get_project(project_id)
    return {"candidates": store.artifacts(project_id, "ERROR_CANDIDATE"),
            "errors": governance.events(project_id, "error_events.jsonl"),
            "rule_events": governance.events(project_id, "rule_events.jsonl"),
            "rules": store.artifacts(project_id, "RULE"),
            "current_rules": governance.current_rules(project_id)}


@app.post("/api/projects/{project_id}/audit/candidates")
def error_candidate(project_id: str, value: ErrorCandidate):
    try:
        return governance.submit_candidate(project_id, value)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/evolution/errors/{candidate_artifact_id}/confirm")
def confirm_error(project_id: str, candidate_artifact_id: str):
    try:
        return governance.confirm_error(project_id, candidate_artifact_id)
    except Exception as error:
        fail(error)


@app.post("/api/projects/{project_id}/evolution/rules")
def save_rule(project_id: str, value: RuleRecord):
    try:
        return governance.save_rule(project_id, value)
    except Exception as error:
        fail(error)


@app.get('/program-monitor')
def program_monitor():
    return FileResponse(ROOT/'vnext/apps/workbench/monitor.html')

@app.get('/monitor.bundle.js')
def monitor_bundle():
    return FileResponse(ROOT/'vnext/apps/workbench/monitor.bundle.js',media_type='application/javascript')

@app.get('/i18n.js')
def i18n_module():
    return FileResponse(ROOT/'vnext/apps/workbench/i18n.js',media_type='application/javascript')

@app.get('/preview.js')
def preview_module():
    return FileResponse(ROOT/'vnext/apps/workbench/preview.js',media_type='application/javascript')

@app.get('/storyboard-workflow.js')
def storyboard_workflow_module():
    return FileResponse(ROOT/'vnext/apps/workbench/storyboard-workflow.js',media_type='application/javascript')

@app.get('/timeline-workflow.js')
def timeline_workflow_module():
    return FileResponse(ROOT/'vnext/apps/workbench/timeline-workflow.js',media_type='application/javascript')

@app.get('/timeline-state.js')
def timeline_state_module():
    return FileResponse(ROOT/'vnext/apps/workbench/timeline-state.js',media_type='application/javascript')


@app.get('/jobs-ui.js')
def jobs_ui_module():
    return FileResponse(ROOT/'vnext/apps/workbench/jobs-ui.js',media_type='application/javascript')

@app.get('/qa-delivery.js')
def qa_delivery_module():
    return FileResponse(ROOT/'vnext/apps/workbench/qa-delivery.js',media_type='application/javascript')

@app.get('/api/projects/{project_id}/preview')
def preview_projection(project_id:str,frame:int=0,selected_clip_id:str|None=None,safe_area:bool=False):
    try:
        from vnext.renderers.remotion.resolver import CompositionResolver
        edt_id=store.get_project(project_id).timeline_artifact_id
        if not edt_id: raise ValueError('TIMELINE_MISSING')
        return CompositionResolver(ROOT,store).frame(project_id,edt_id,frame,selected_clip_id,safe_area)
    except Exception as error: fail(error)

@app.get('/api/preview-assets/{cache_key}/{filename}')
def preview_asset(cache_key:str,filename:str):
    public=(ROOT/'vnext/renderers/remotion/project/public').resolve()
    path=(public/cache_key/filename).resolve()
    if not cache_key.startswith('PREVIEW-') or path.parent.parent!=public or not path.is_file():
        raise HTTPException(404,'MEDIA_NOT_FOUND')
    return FileResponse(path)
