"""Production cache regressions use measured local fixture audio, never paid APIs."""
from pathlib import Path
import wave
import pytest
from vnext.tests.test_phase2 import env
from vnext.phase2.production import Production
from vnext.phase2.stages import StageCache
from vnext.phase2.hardening.audio import AudioClock
from vnext.media.library.service import MediaLibrary
from vnext.migration.legacy import sha


def test_first_audio_clock_invalidates_estimated_edt_cache(env, tmp_path):
    store, pid, _, script, *_ = env
    production = Production(store)
    cache = StageCache(store)
    operation = lambda: production.generate_edt(pid)
    first = cache.run(pid, 'EDT', production.edt_inputs(pid), operation)
    assert cache.run(pid, 'EDT', production.edt_inputs(pid), operation)['stage_cache_hit']
    audio = tmp_path / 'measured.wav'
    with wave.open(str(audio), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(b'\x00\x00' * 24000 * 3)
    media = MediaLibrary(store).register(pid, audio, 'AUDIO', 'VOICE', 'LOCAL_ONLY')
    voice = store.create_artifact(pid, 'VOICE', {
        'media_asset_id': media.asset_id, 'audio_path': str(audio), 'duration': 3,
        'status': 'READY', 'provenance': {'segment_measurements': [{
            'segment_id': 'SEG1', 'path': str(audio), 'sha256': sha(audio), 'duration': 3}]}},
        role='VOICE', dependencies=[store.dependency(script['artifact_id'])])
    timing = AudioClock(store).create(pid, {
        'audio_artifact_id': voice.artifact_id, 'script_artifact_id': script['artifact_id'],
        'audio_hash': media.hash, 'duration': 3,
        'provenance': {'method': 'MEASURED_SEGMENT_BOUNDARIES', 'worker': 'LOCAL_FIXTURE', 'version': '1'},
        'entries': [{'audio_id': media.asset_id, 'segment_id': 'SEG1', 'start': 0,
                     'end': 3, 'duration': 3, 'phrase_ranges': [{'text': script['payload']['text'],
                                                              'start': 0, 'end': 3}]}]}, 'ALIGNMENT')
    second = cache.run(pid, 'EDT', production.edt_inputs(pid), operation)
    assert second['artifact_id'] != first['artifact_id']
    assert timing['artifact_id'] in second['payload']['source_artifacts']
    assert max(c['timeline_out'] for c in second['payload']['clips']) == 3
    assert any(c['track'] == 'VOICE' for c in second['payload']['clips'])
    assert all(c['metadata']['timing_source'] == 'AUDIO_TIMING_MAP'
               for c in second['payload']['clips'] if c['track'] == 'SUBTITLE')
    assert cache.run(pid, 'EDT', production.edt_inputs(pid), operation)['stage_cache_hit']
    blocked = store.create_artifact(pid, 'AUDIO_TIMING_MAP', timing['payload'],
                                   role='ALIGNMENT', status='BLOCKED')
    with pytest.raises(ValueError, match='STALE_OR_BLOCKED_INPUT'):
        cache.run(pid, 'EDT', production.edt_inputs(pid), operation)


def test_visual_binding_change_regenerates_cached_edt(env):
    store, pid, *_ = env
    production = Production(store)
    cache = StageCache(store)
    operation = lambda: production.generate_edt(pid)
    first = cache.run(pid, 'EDT', production.edt_inputs(pid), operation)
    project = store.get_project(pid)
    project.render_profile = 'preview-720p'
    store.save_project(project)
    second = cache.run(pid, 'EDT', production.edt_inputs(pid), operation)
    assert first['artifact_id'] != second['artifact_id']
    assert (second['payload']['width'], second['payload']['height']) == (1280, 720)
    assert cache.run(pid, 'EDT', production.edt_inputs(pid), operation)['stage_cache_hit']
