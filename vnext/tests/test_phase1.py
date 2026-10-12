import hashlib
import json
import wave
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from vnext.contracts import ErrorCandidate, RuleRecord, SCHEMAS, Role, VoiceRequest
from vnext.core.editing import Editing, import_script_text
from vnext.core.governance import Governance
from vnext.core.preflight import check
from vnext.core.runtime import Runtime, WorkflowError
from vnext.exporters.jianying.adapter import JianyingExporter
from vnext.gateways.model.gateway import GatewayError, ModelGateway
from vnext.gateways.voice.gateway import VoiceGateway
from vnext.media.library.service import MediaLibrary
from vnext.registries.catalog import worker_options
from vnext.renderers.remotion.adapter import RemotionAdapter
from vnext.storage.store import Store

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def setup(tmp_path):
    store = Store(tmp_path / 'data')
    project = store.create_project('test', character_pack='XIAO-Y_V1')
    return store, project.project_id


def test_schemas_and_i18n():
    for model in SCHEMAS.values():
        Draft202012Validator.check_schema(model.model_json_schema())
    zh = json.loads((ROOT / 'vnext/i18n/zh-CN.json').read_text())
    en = json.loads((ROOT / 'vnext/i18n/en-US.json').read_text())
    assert set(zh) == set(en)


def test_migration_byte_identity():
    result = json.loads((ROOT / 'migration/LEGACY_MIGRATION_RESULT.json').read_text())
    assert result['actions_verified'] == 48 and result['elements_verified'] == 33
    assert len(result['copied']) == 81
    for item in result['copied']:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']


def test_revision_stale_append_only_and_single_writer(setup):
    store, pid = setup
    edit = Editing(store)
    first = edit.script(pid, 'alpha')
    downstream = store.create_artifact(pid, 'DIRECTOR_PLAN', {'beats': []}, role='DIRECTOR', dependencies=[store.dependency(first['artifact_id'])])
    old_path = next((store.root / 'projects' / pid / 'artifacts' / 'SCRIPT').glob('v0001-*.json'))
    original = old_path.read_bytes()
    second = edit.script(pid, 'beta')
    assert first['revision'] == 1 and second['revision'] == 2
    assert old_path.read_bytes() == original
    assert not store.is_current(first['artifact_id'])
    assert store.get_artifact(downstream.artifact_id)['current_status'] == 'STALE'
    with pytest.raises(PermissionError):
        store.create_artifact(pid, 'RULE', {'x': 1}, role='ANALYTICS')
    lines = (store.root / 'projects' / pid / 'events.jsonl').read_text().splitlines()
    assert any(json.loads(x)['kind'] == 'ARTIFACT_STALE' for x in lines)


def test_h2_audit_gates_and_worker_revision(setup):
    store, pid = setup
    script = Editing(store).script(pid, 'A factual statement')
    runtime = Runtime(store)
    store.create_artifact(pid, 'AUDIT', {'verdict': 'FAIL', 'findings': ['unverified']}, role='AUDIT', dependencies=[store.dependency(script['artifact_id'])])
    with pytest.raises(WorkflowError, match='AUDIT_FAIL'):
        runtime.approve_h2(pid, script['artifact_id'])
    store.create_artifact(pid, 'AUDIT', {'verdict': 'PASS_WITH_RISK', 'risk': 'Limited source'}, role='AUDIT', dependencies=[store.dependency(script['artifact_id'])])
    with pytest.raises(WorkflowError, match='RISK_ACKNOWLEDGMENT_REQUIRED'):
        runtime.approve_h2(pid, script['artifact_id'])
    runtime.approve_h2(pid, script['artifact_id'], risk_acknowledged=True)
    assert next(x for x in worker_options(Role.VIDEO_QA) if x['worker_id'] == 'DEEPSEEK')['disabled']
    assignment1 = runtime.select_worker(pid, Role.DIRECTOR, 'MOCK')
    assignment2 = runtime.select_worker(pid, Role.DIRECTOR, 'MOCK')
    assert assignment2['revision'] == assignment1['revision'] + 1
    plan = runtime.run(pid, Role.DIRECTOR, [script['artifact_id']], request_id='same')
    again = runtime.run(pid, Role.DIRECTOR, [script['artifact_id']], request_id='same')
    assert again['artifact_id'] == plan['artifact_id']
    assert plan['prompt_version'] == 'DIRECTOR_V1'
    assert plan['dependencies'][0]['artifact_id'] == script['artifact_id']
    timeline = Editing(store).create_timeline(pid)
    runtime.run(pid, Role.DIRECTOR, [script['artifact_id']], request_id='new-director-revision')
    assert store.get_artifact(timeline['artifact_id'])['current_status'] == 'STALE'


def test_gateway_bounded_repair(monkeypatch):
    from vnext.contracts import ModelMessage, ModelRequest
    monkeypatch.setenv('CUSTOM_OPENAI_BASE_URL', 'http://localhost/v1')
    monkeypatch.setenv('CUSTOM_OPENAI_API_KEY', 'secret')
    monkeypatch.setenv('CUSTOM_OPENAI_MODEL', 'test')
    seen = []
    def fake(url, key, body):
        seen.append(body['messages'])
        value = 'not-json' if len(seen) == 1 else '{"text":"ok"}'
        return {'choices': [{'message': {'content': value}, 'finish_reason': 'stop'}], 'usage': {'total_tokens': 2}}
    monkeypatch.setattr(ModelGateway, '_post', staticmethod(fake))
    request = ModelRequest(role=Role.SCRIPT_PRIMARY, worker_profile='CUSTOM_OPENAI', system_prompt='test',
        messages=[ModelMessage(role='user', content='input')], response_schema={'type':'object','required':['text'],'properties':{'text':{'type':'string'}}}, prompt_version='SCRIPT_PRIMARY_V1')
    result = ModelGateway().invoke(request)
    assert result.structured_output == {'text': 'ok'} and len(seen) == 2
    assert 'secret' not in json.dumps(result.model_dump())


def test_content_addressable_model_cache(tmp_path):
    from vnext.contracts import ModelMessage, ModelRequest
    request = ModelRequest(role=Role.SCRIPT_PRIMARY, worker_profile='MOCK', system_prompt='test',
        messages=[ModelMessage(role='user', content='same input')],
        response_schema={'type':'object','required':['text'],'properties':{'text':{'type':'string'}}},
        prompt_version='SCRIPT_PRIMARY_V1')
    gateway = ModelGateway(cache_dir=tmp_path)
    first = gateway.invoke(request)
    second = gateway.invoke(request)
    assert first.structured_output == second.structured_output
    assert 'CACHE_HIT' in second.warnings
    assert len(list(tmp_path.glob('*.json'))) == 1


def test_media_voice_timeline_export(setup, tmp_path):
    store, pid = setup
    editing = Editing(store)
    script = editing.script(pid, 'A short script')
    Runtime(store).approve_h2(pid, script['artifact_id'])
    source = ROOT / 'assets/packs/character/XIAO-Y_Action_Pack_v2_Production_48/actions/XACT-001_neutral_stand.png'
    folder = tmp_path / 'linked'; folder.mkdir()
    target = folder / 'renamed.png'; target.write_bytes(source.read_bytes())
    media = MediaLibrary(store)
    registered = media.add_folder(pid, folder)
    assert len(registered) == 1 and registered[0].hash == hashlib.sha256(source.read_bytes()).hexdigest()
    moved = tmp_path / 'moved.png';target.rename(moved)
    assert media.assets(pid)[0].status == 'MISSING'
    assert media.relink(pid, registered[0].asset_id, moved).status == 'RELINKED'
    voice = VoiceGateway().synthesize(VoiceRequest(text='hello',language='en-US',voice_profile='MOCK_VOICE_V1'),tmp_path/'voice')
    with wave.open(voice.audio_path) as sound: assert sound.getframerate() == 24000
    timeline = editing.create_timeline(pid)
    with pytest.raises(ValueError):
        editing.edit_timeline(pid, 'MOVE', {'clip_id':'unknown'})
    added = editing.edit_timeline(pid, 'ADD', {'track':'MEDIA','asset_id':registered[0].asset_id,'source_out':5,'timeline_out':5})
    changed = editing.edit_timeline(pid, 'MOVE', {'clip_id':added['payload']['clips'][0]['clip_id'],'timeline_in':1,'timeline_out':6})
    undone = editing.edit_timeline(pid, 'UNDO', {})
    assert undone['payload']['clips'][0]['timeline_in'] == 0
    redone = editing.edit_timeline(pid, 'REDO', {})
    assert redone['payload']['clips'][0]['timeline_in'] == 1
    marked = editing.edit_timeline(pid, 'MARKER', {'at': 2.0})
    snapped = editing.edit_timeline(pid, 'SNAP', {'clip_id': redone['payload']['clips'][0]['clip_id'], 'at': 2.1})
    assert snapped['payload']['clips'][0]['timeline_in'] == 2.0
    assert marked['payload']['markers'][0]['at'] == 2.0
    assert check(store,pid,snapped['artifact_id'])['ok']
    bundle = JianyingExporter(store).export_transfer_bundle(pid,snapped['artifact_id'])
    assert bundle['mapping'][0]['classification'] == 'EXACT'
    assert bundle['native_project_open_verified'] is False
    prepared = RemotionAdapter(ROOT,store).prepare(pid,snapped['artifact_id'])
    assert prepared['props']['clips'][0]['asset_src']


def test_script_import_modes(tmp_path):
    assert import_script_text('a.md', '你好'.encode()) == '你好'
    with pytest.raises(ValueError): import_script_text('a.exe', b'bad')
    store = Store(tmp_path)
    pid = store.create_project('x').project_id
    result = Editing(store).script(pid, 'reference', mode='USE_AS_REFERENCE')
    assert result['artifact_type'] == 'SCRIPT_REFERENCE'
    assert store.get_project(pid).h2_script_artifact_id is None


def test_evolution_single_writer_recurrence_and_rules(setup):
    store, pid = setup
    governance = Governance(store)
    first = governance.submit_candidate(pid, ErrorCandidate(summary='Wrong source citation',root_cause='DATA',submitted_by_role='SCRIPT_PRIMARY'))
    with pytest.raises(PermissionError):
        governance.confirm_error(pid, first['artifact_id'], actor_role='ANALYTICS')
    confirmed = governance.confirm_error(pid, first['artifact_id'])
    second = governance.submit_candidate(pid, ErrorCandidate(summary='  wrong   source citation ',root_cause='DATA',submitted_by_role='VIDEO_QA'))
    recurred = governance.confirm_error(pid, second['artifact_id'])
    assert recurred['kind'] == 'ERROR_RECURRED' and recurred['error_id'] == confirmed['error_id']
    ledger = store.root / 'projects' / pid / 'audit/error_events.jsonl'
    before = ledger.read_bytes()
    assert len(before.splitlines()) == 2
    rule = dict(rule_id='R-1',text='Cite source IDs',scope='SCRIPT',priority='HIGH',owner='EVOLUTION',reason='Repeated citation error',related_error=confirmed['error_id'],exceptions=[])
    governance.save_rule(pid, RuleRecord(**rule,lifecycle='CREATED'))
    assert 'Cite source IDs' not in governance.current_rules(pid)
    governance.save_rule(pid, RuleRecord(**rule,lifecycle='ACTIVE'))
    assert 'Cite source IDs' in governance.current_rules(pid)
    class CaptureGateway(ModelGateway):
        captured = None
        def invoke(self, request):
            self.captured = request.system_prompt
            return super().invoke(request)
    gateway = CaptureGateway()
    script = Editing(store).script(pid, 'Next task')
    runtime = Runtime(store, gateway)
    runtime.approve_h2(pid, script['artifact_id'])
    runtime.select_worker(pid, Role.DIRECTOR, 'MOCK')
    runtime.run(pid, Role.DIRECTOR, [script['artifact_id']], request_id='next')
    assert 'Cite source IDs' in gateway.captured
    with pytest.raises(ValueError): governance.save_rule(pid, RuleRecord(**rule,lifecycle='CREATED'))
    governance.save_rule(pid, RuleRecord(**rule,lifecycle='DEPRECATED'))
    assert 'Cite source IDs' not in governance.current_rules(pid)
    assert ledger.read_bytes() == before


def test_http_workbench_minimal_chain(tmp_path, monkeypatch):
    import importlib
    from fastapi.testclient import TestClient
    import vnext.apps.workbench.server as server
    monkeypatch.setenv('CONTENT_OS_DATA', str(tmp_path / 'api_data'))
    monkeypatch.setenv('OPENAI_API_KEY', 'DO_NOT_EXPOSE_THIS_KEY')
    server = importlib.reload(server)
    client = TestClient(server.app)
    assert client.get('/').status_code == 200
    assert 'DO_NOT_EXPOSE_THIS_KEY' not in client.get('/api/catalog').text
    created = client.post('/api/projects', json={'name':'Integration'}).json()
    pid = created['project_id']
    assert 'DO_NOT_EXPOSE_THIS_KEY' not in client.get(f'/api/projects/{pid}').text
    assert client.patch(f'/api/projects/{pid}/config',json={'character_pack':'XIAO-Y_V1','style_pack':'XIAO-Y_STYLE_V1','voice_profile':'MOCK_VOICE_V1'}).status_code == 200
    assert client.post(f'/api/projects/{pid}/workers/AUDIT',json={'worker_id':'MOCK'}).status_code == 200
    assert client.post(f'/api/projects/{pid}/workers/DIRECTOR',json={'worker_id':'MOCK'}).status_code == 200
    script = client.post(f'/api/projects/{pid}/script',json={'text':'A short demo script'}).json()
    script_id = script['artifact_id']
    audit = client.post(f'/api/projects/{pid}/run/AUDIT',json={'source_artifact_ids':[script['artifact_id']]}).json()
    assert audit['payload']['verdict'] == 'PASS'
    assert client.post(f'/api/projects/{pid}/h2/{script_id}').status_code == 200
    director = client.post(f'/api/projects/{pid}/run/DIRECTOR',json={'source_artifact_ids':[script['artifact_id']]}).json()
    assert director['artifact_type'] == 'DIRECTOR_PLAN'
    timeline = client.post(f'/api/projects/{pid}/timeline',json={}).json()
    assert timeline['payload']['clips'] == []
    edited = client.post(f'/api/projects/{pid}/timeline/edit',json={'operation':'ADD','arguments':{'track':'TEXT','timeline_in':0,'timeline_out':5,'source_out':5,'metadata':{'text':'Hello'}}}).json()
    assert edited['revision'] == 2
    assert client.get(f'/api/projects/{pid}/preflight').json()['ok']
    still = client.post(f'/api/projects/{pid}/render/still',json={})
    assert still.status_code == 200, still.text
    render_id = still.json()['artifact_id']
    assert client.get(f'/api/projects/{pid}/render/{render_id}/file').status_code == 200
    voice = client.post(f'/api/projects/{pid}/voice',json={'text':'hello','language':'en-US','voice_profile':'MOCK_VOICE_V1'})
    assert voice.status_code == 200 and voice.json()['payload']['status'] == 'MOCK'
    voice_media_id = voice.json()['payload']['media_asset_id']
    voice_clip = client.post(f'/api/projects/{pid}/timeline/edit',json={'operation':'ADD','arguments':{
        'track':'VOICE','asset_id':voice_media_id,'timeline_in':0,'timeline_out':1,'source_in':0,'source_out':1}})
    assert voice_clip.status_code == 200
    video = client.post(f'/api/projects/{pid}/render/video',json={})
    assert video.status_code == 200, video.text
    video_path = Path(video.json()['payload']['preview_path'])
    assert video_path.is_file() and video_path.stat().st_size > 1000
    import subprocess
    probe = subprocess.run(['ffprobe','-v','error','-select_streams','a','-show_entries','stream=codec_name','-of','csv=p=0',str(video_path)],capture_output=True,text=True)
    assert probe.stdout.strip()
    comparison = client.post(f'/api/projects/{pid}/model-eval',json={
        'input_text':'same input','role':'SCRIPT_PRIMARY','workers':['MOCK','MOCK_ALT']})
    assert comparison.status_code == 200 and len(comparison.json()['payload']['outputs']) == 2
    lab = client.post(f'/api/projects/{pid}/voice-lab',json={
        'text':'same text','profiles':['MOCK_VOICE_V1','MOCK_VOICE_ALT_V1']})
    assert lab.status_code == 200 and len(lab.json()['payload']['results']) == 2


def test_native_export_original_ranges_audio_text_and_degradation(setup, tmp_path):
    from vnext.exporters.jianying.native import native_draft
    from vnext.contracts import EDT, EDTClip, MediaAsset
    store, pid = setup
    source = tmp_path / 'original.mp4'; source.write_bytes(b'local test original')
    audio = tmp_path / 'voice.wav'; audio.write_bytes(b'local test voice')
    assets = {key: MediaAsset(asset_id=key, project_id=pid, type=kind, original_path=str(path),
        hash=hashlib.sha256(path.read_bytes()).hexdigest(), duration=10, resolution='1280x720',
        created_at='2026-09-26', source='MANUAL', owner='HUMAN') for key, path, kind in [('v',source,'VIDEO'),('a',audio,'AUDIO')]}
    edt = EDT(edt_id='EDT-test', project_id=pid, revision=1, clips=[
        EDTClip(clip_id='v',track='VIDEO',asset_id='v',source_in=2,source_out=4,timeline_in=1,timeline_out=3,position={'x':.75,'y':.25},scale=.5),
        EDTClip(clip_id='a',track='VOICE',asset_id='a',source_in=1,source_out=3,timeline_out=2),
        EDTClip(clip_id='t',track='SUBTITLE',source_out=2,timeline_out=2,metadata={'text':'editable'},motion={'name':'fade'}),
        EDTClip(clip_id='gap',track='ELEMENT',source_out=2,timeline_out=2)])
    path = tmp_path / 'draft'
    before = source.read_bytes(), audio.read_bytes()
    result = native_draft(edt,assets,path,'test')
    assert result['native_jianying_draft'] and not result['native_project_open_verified']
    draft = json.loads((path/'draft_content.json').read_text())
    assert Path(draft['materials']['videos'][0]['path']) == source
    segment = draft['tracks'][0]['segments'][0]
    assert segment['source_timerange'] == {'start':2_000_000,'duration':2_000_000}
    assert segment['target_timerange'] == {'start':1_000_000,'duration':2_000_000}
    assert segment['clip']['transform'] == {'x':.5,'y':.5}
    assert draft['materials']['audios'][0]['path'] == str(audio)
    assert json.loads(draft['materials']['texts'][0]['content'])['text'] == 'editable'
    assert [x['classification'] for x in result['mapping']] == ['EXACT','EXACT','APPROXIMATED','UNSUPPORTED']
    assert (source.read_bytes(),audio.read_bytes()) == before
    with pytest.raises(FileExistsError): native_draft(edt,assets,path,'overwrite forbidden')


def test_split_preserves_source_range_for_changed_playback_rate(setup):
    store, pid = setup
    editing = Editing(store)
    script = editing.script(pid, 'source range test')
    Runtime(store).approve_h2(pid,script['artifact_id'])
    editing.create_timeline(pid)
    added = editing.edit_timeline(pid,'ADD',{'track':'VIDEO','source_in':2,'source_out':10,'timeline_in':0,'timeline_out':4})
    split = editing.edit_timeline(pid,'SPLIT',{'clip_id':added['payload']['clips'][0]['clip_id'],'at':1})
    left,right = split['payload']['clips']
    assert left['source_out'] == right['source_in'] == 4
    assert right['source_out'] == 10
