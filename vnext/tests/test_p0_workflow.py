"""The P0 browser flow keeps project input and media within its local workspace."""
import importlib
import copy
import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from vnext.phase2.production import CommandBus
from vnext.phase2.production import Production, human_edits_present, subtitle_chunks
from vnext.core.runtime import Runtime
from vnext.contracts import Role, EDTClip
from vnext.core.editing import Editing
from vnext.storage.store import Store
from vnext.phase2.visual_state import visual_revision
from vnext.phase2.hardening.audio import AudioClock
from vnext.tests.test_phase2_hardening import evidence_env, clock_env
from vnext.tests.test_phase2 import env


def test_project_creation_and_browser_media_import(tmp_path, monkeypatch):
    monkeypatch.setenv("CONTENT_OS_DATA", str(tmp_path / "content-data"))
    import vnext.apps.workbench.server as server
    server = importlib.reload(server)
    with TestClient(server.app) as client:
        created = client.post("/api/projects", json={"name": "GUI project", "topic": "来源如何核验",
            "content_type": "EXPLAINER"})
        assert created.status_code == 200
        project = created.json()
        assert project["topic"] == "来源如何核验"
        assert project["content_type"] == "EXPLAINER"
        pid = project["project_id"]
        text = "这是一份用户本地资料。".encode()
        external = tmp_path / "external-source.txt"
        external.write_bytes(text)
        linked = server.media.register(pid, external, "DOCUMENT", "HUMAN", "LOCAL_ONLY")
        imported = client.post(f"/api/projects/{pid}/media/import?filename=source.txt",
            content=text, headers={"Content-Type": "application/octet-stream"})
        assert imported.status_code == 200
        asset = imported.json()
        assert asset["asset_id"] != linked.asset_id
        assert asset["asset_id"].startswith("MED-")
        assert asset["display_name"] == "source.txt"
        assert asset["type"] == "DOCUMENT"
        assert asset["source"] == "PROJECT_UPLOAD"
        path = Path(asset["original_path"])
        assert path.is_relative_to(tmp_path / "content-data" / "projects" / pid / "uploads")
        assert path.read_bytes() == text
        repeat = client.post(f"/api/projects/{pid}/media/import?filename=source.txt",
            content=text, headers={"Content-Type": "application/octet-stream"})
        assert repeat.json()["asset_id"] == asset["asset_id"]
        assert client.get(f"/api/projects/{pid}/media/{asset['asset_id']}/file").content == text
        detail = client.get(f"/api/projects/{pid}").json()
        assert any(item["asset_id"] == asset["asset_id"] for item in detail["media"])
        refused = client.post(f"/api/projects/{pid}/media/import?filename=script.exe", content=b"x")
        assert refused.status_code == 400
        assert "MEDIA_TYPE_UNSUPPORTED" in refused.text


def test_gui_script_command_keeps_claim_binding_and_rejects_stale_revision(evidence_env):
    store, pid, knowledge, *_, script_payload = evidence_env
    initial = knowledge.bound_script(pid, script_payload)
    revised = copy.deepcopy(script_payload)
    revised["text"] += "."
    revised["segments"][0]["text"] = revised["text"]
    bus = CommandBus(store)
    saved = bus.execute(pid, "SCRIPT", "REPLACE_SCRIPT", {"payload": revised},
        actor="HUMAN", actor_type="HUMAN", expected_revision=initial["artifact_id"])
    assert saved["revision"] == initial["revision"] + 1
    assert saved["payload"]["claim_units"][0]["fact_ids"] == ["F1"]
    assert store.latest(pid, "CLAIM_COVERAGE_REPORT")["payload"]["issues"] == []
    with pytest.raises(ValueError, match="EDIT_REVISION_CONFLICT"):
        bus.execute(pid, "SCRIPT", "REPLACE_SCRIPT", {"payload": revised},
            actor="HUMAN", actor_type="HUMAN", expected_revision=initial["artifact_id"])
    assert store.latest(pid, "SCRIPT")["artifact_id"] == saved["artifact_id"]


def test_workflow_projection_requires_voice_bound_final_edt():
    module = (Path(__file__).resolve().parents[1] / "apps/workbench/workflow-projection.js").as_uri()
    script = f"""import {{workflowProjection}} from {json.dumps(module)};
const ready=(kind,id,payload={{}},dependencies=[])=>({{artifact_type:kind,artifact_id:id,revision:1,current_status:'READY',payload,dependencies}});
const artifacts=[ready('SOURCE_LOCAL-1','SRC'),ready('FACT_PACK','F'),ready('SCRIPT','S'),
  ready('AUDIT','A'),ready('H2_GATE','H'),ready('DIRECTOR_IR','D'),
  ready('STORYBOARD_GATE','B',{{all_beats_approved:true}}),ready('VOICE','V'),
  ready('AUDIO_TIMING_MAP','T'),ready('EDT','E',{{clips:[{{track:'VOICE'}}]}},[{{artifact_id:'OLD_VOICE'}}])];
const detail={{project:{{h2_script_artifact_id:'S'}},artifacts}};
const before=workflowProjection(detail).stage;
artifacts.at(-1).dependencies=[{{artifact_id:'V'}}];
const after=workflowProjection(detail).stage;
console.log(JSON.stringify([before,after]));"""
    result = subprocess.run(["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == ["timeline", "render"]


def test_director_regeneration_requires_explicit_discard_after_human_edit(evidence_env):
    store, pid, knowledge, *_, script_payload = evidence_env
    script = knowledge.bound_script(pid, script_payload)
    runtime = Runtime(store)
    runtime.select_worker(pid, Role.AUDIT, "MOCK")
    runtime.run(pid, Role.AUDIT, [script["artifact_id"]], request_id="p0-director-audit")
    runtime.approve_h2(pid, script["artifact_id"], True)
    payload = {"script_artifact_id": script["artifact_id"],
        "scenes": [{"scene_id": "SC1", "purpose": "Explain", "script_range": ["SEG1"],
            "narrative_function": "EXPLAIN", "retention_goal": "VALUE", "estimated_duration": 5,
            "beat_ids": ["B1"]}],
        "beats": [{"beat_id": "B1", "scene_id": "SC1", "script_segment_id": "SEG1",
            "purpose": "Explain", "visual_focus": "Alpha", "visual_form": "KEYWORD",
            "pattern_id": "CHARACTER_EXPLAIN_KEYWORD", "keyword": "Alpha", "timing_intent": 5,
            "slots": {"keyword": "Alpha"}}]}
    first = Production(store).ir(pid, payload)
    edited = CommandBus(store).execute(pid, "DIRECTOR_IR", "SET_BEAT",
        {"beat_id": "B1", "changes": {"keyword": "Alpha idea"}},
        expected_revision=first["artifact_id"])
    assert human_edits_present(store, pid, "DIRECTOR_IR")
    runtime.select_worker(pid, Role.DIRECTOR, "MOCK")
    with pytest.raises(Exception, match="HUMAN_EDITS_PRESENT"):
        runtime.run(pid, Role.DIRECTOR, [script["artifact_id"]],
            request_id="p0-director-protect", config={"expected_revision": edited["artifact_id"]})
    with pytest.raises(ValueError, match="HUMAN_EDITS_PRESENT"):
        CommandBus(store).execute(pid, "DIRECTOR_IR", "REPLACE_IR", {"payload": payload},
            actor="DIRECTOR", actor_type="AGENT", expected_revision=edited["artifact_id"])
    with pytest.raises(ValueError, match="EDIT_REVISION_CONFLICT"):
        CommandBus(store).execute(pid, "DIRECTOR_IR", "REPLACE_IR",
            {"payload": payload, "discard_human_edits": True},
            actor="DIRECTOR", actor_type="AGENT", expected_revision=first["artifact_id"])
    regenerated = CommandBus(store).execute(pid, "DIRECTOR_IR", "REPLACE_IR",
        {"payload": payload, "discard_human_edits": True},
        actor="DIRECTOR", actor_type="AGENT", expected_revision=edited["artifact_id"])
    assert regenerated["revision"] == edited["revision"] + 1


def test_preview_regeneration_preserves_human_timeline_edit_unless_discarded(env):
    store, pid, _, _, _, edt, *_ = env
    bus = CommandBus(store)
    edited = bus.execute(pid, "EDT", "MARKER", {"at": 2.0},
        expected_revision=edt["artifact_id"])
    with pytest.raises(ValueError, match="HUMAN_EDITS_PRESENT"):
        bus.execute(pid, "EDT", "GENERATE", {}, expected_revision=edited["artifact_id"])
    assert store.latest(pid, "EDT")["artifact_id"] == edited["artifact_id"]
    rebuilt = bus.execute(pid, "EDT", "GENERATE", {"discard_human_edits": True},
        expected_revision=edited["artifact_id"])
    assert rebuilt["artifact_id"] != edited["artifact_id"]


def test_provisional_subtitles_strip_fullwidth_colon_before_storyboard_preflight():
    assert subtitle_chunks("最后提醒一句：字幕要清楚，画面要一致。") == [
        "最后提醒一句", "字幕要清楚", "画面要一致"]


def test_human_visual_timeline_edit_keeps_audio_clock_dependency(clock_env):
    store, pid, script, voice, timing = clock_env
    clock = AudioClock(store).create(pid, timing, "ALIGNMENT")
    clip = EDTClip(clip_id="voice", track="VOICE", asset_id=voice["payload"]["media_asset_id"],
        source_out=timing["duration"], timeline_out=timing["duration"])
    dependencies = Editing(store)._dependencies(pid, script["artifact_id"], [clip])
    assert {item.artifact_id for item in dependencies} >= {voice["artifact_id"], clock["artifact_id"]}


def test_final_timeline_projection_requires_voice_and_audio_timing_dependencies():
    module = (Path(__file__).resolve().parents[1] / "apps/workbench/timeline-state.js").as_uri()
    script = f"""import {{finalEditableEdt}} from {json.dumps(module)};
const item=(type,id,payload={{}},dependencies=[])=>({{artifact_type:type,artifact_id:id,current_status:'READY',payload,dependencies}});
const voice=item('VOICE','V',{{media_asset_id:'M'}}),clock=item('AUDIO_TIMING_MAP','T');
const edt=item('EDT','E',{{clips:[{{track:'VOICE',asset_id:'M'}}]}},[{{artifact_id:'V'}}]);
const detail={{project:{{timeline_artifact_id:'E'}},artifacts:[voice,clock,edt]}};
const before=finalEditableEdt(detail);edt.dependencies.push({{artifact_id:'T'}});
const after=finalEditableEdt(detail);console.log(JSON.stringify([before,after]));"""
    result = subprocess.run(["node", "--input-type=module", "-e", script],
        capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == [False, True]


def test_approved_storyboard_is_not_invalidated_by_downstream_audio_retime(tmp_path):
    store = Store(tmp_path)
    pid = store.create_project('visual approval boundary').project_id
    director = store.create_artifact(pid, 'DIRECTOR_IR', {'v': 1}, role='DIRECTOR').model_dump()
    payload = {'fps': 30, 'width': 1920, 'height': 1080,
        'clips': [{'track': 'TEXT', 'timeline_in': 0, 'timeline_out': 4, 'metadata': {'text': 'same'}}]}
    visual = visual_revision(store, pid, payload)
    board = store.create_artifact(pid, 'STORYBOARD', {'ir_hash': director['output_hash']},
        role='STORYBOARD', dependencies=[store.dependency(visual['artifact_id'])]).model_dump()
    gate = store.create_artifact(pid, 'STORYBOARD_GATE', {'all_beats_approved': True,
        'ir_hash': director['output_hash']}, role='HUMAN',
        dependencies=[store.dependency(board['artifact_id'])]).model_dump()
    # A new derived composition and audio clock may retime downstream clips.
    store.create_artifact(pid, 'RESOLVED_VISUAL_COMPOSITION', {'timing': 'audio'},
        role='VISUAL_RESOLVER')
    retimed = {**payload, 'clips': [{**payload['clips'][0], 'timeline_out': 5}]}
    assert visual_revision(store, pid, retimed)['artifact_id'] == visual['artifact_id']
    assert store.is_usable_input(gate['artifact_id'])
    # An upstream Director change is different: its approval really expires.
    store.create_artifact(pid, 'DIRECTOR_IR', {'v': 2}, role='DIRECTOR')
    assert visual_revision(store, pid, retimed)['artifact_id'] != visual['artifact_id']
    assert not store.is_usable_input(gate['artifact_id'])
