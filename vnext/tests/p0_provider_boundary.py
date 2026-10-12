"""Track A only: fake model and voice adapters at their provider boundaries.

Launch against disposable CONTENT_OS_DATA. No model or TTS network call can pass
through these patched boundaries. The ordinary Workbench and its contracts run.
"""
from __future__ import annotations

import json
import math
import os
import uuid
import wave
from array import array
from pathlib import Path

from jsonschema import validate

from vnext.contracts import ModelResult, VoiceArtifact, utc_now
from vnext.gateways.model.gateway import ModelGateway
from vnext.gateways.voice.gateway import VoiceGateway


def fake_model(self, request, attempt_hook=None):
    if request.role.value == 'RESEARCH':
        user = json.loads(request.messages[0].content)
        sources = user['sources']
        proposals = []
        for source in sources:
            paragraphs = [line.strip() for line in source['content'].splitlines() if line.strip()]
            proposals.extend({'source_id': source['source_id'], 'excerpt': line} for line in paragraphs)
        data = {'text': '\n'.join(p['excerpt'] for p in proposals), 'proposals': proposals}
    elif request.role.value == 'VIDEO_QA':
        context = json.loads(request.messages[0].content)
        data = {'verdict': 'PASS_WITH_RISK', 'issues': [{'code': 'FAKE_PROVIDER_VISUAL_REVIEW',
            'severity': 'WARNING', 'owner': 'HUMAN', 'description': 'Track A provider-boundary fake; no external model reviewed this video',
            'start': 0, 'end': 0}], 'mock': False, 'checked_artifact_id': context['checked_artifact_id']}
    else:
        data = self._mock(request).structured_output
    if request.response_schema:
        validate(data, request.response_schema)
    return ModelResult(text=json.dumps(data, ensure_ascii=False), structured_output=data,
        provider_metadata={'provider': 'P0_FAKE_PROVIDER_BOUNDARY', 'provider_id': request.worker_profile,
            'model': 'P0_FAKE', 'model_id': 'P0_FAKE', 'adapter_version': 'P0_TEST_BOUNDARY',
            'attempts': 1, 'timestamp': utc_now()}, warnings=['P0_FAKE_PROVIDER_BOUNDARY'])


def fake_voice(self, request, output_dir, *, privacy='LOCAL_ONLY', upload_confirmed=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / ('P0-FAKE-' + uuid.uuid4().hex[:12] + '.wav')
    duration = 4.0
    with wave.open(str(path), 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(48000)
        frames = int(duration * 48000)
        samples = array('h', (int(1600 * math.sin(2 * math.pi * 440 * i / 48000)) for i in range(frames)))
        audio.writeframes(samples.tobytes())
    return VoiceArtifact(voice_artifact_id=path.stem, provider='P0_FAKE_PROVIDER_BOUNDARY',
        model='P0_FAKE_VOICE', voice_profile=request.voice_profile, audio_path=str(path),
        duration=duration, sample_rate=48000, channels=1, status='READY',
        provenance={'adapter': 'P0_TEST_BOUNDARY', 'live_verified': False,
            'timestamp': utc_now(), 'usage': {}})


def main():
    if not os.environ.get('CONTENT_OS_P0_TRACK_A') == '1':
        raise SystemExit('CONTENT_OS_P0_TRACK_A=1 is required')
    if not os.environ.get('CONTENT_OS_DATA') or not Path(os.environ['CONTENT_OS_DATA']).is_dir():
        raise SystemExit('An existing disposable CONTENT_OS_DATA directory is required')
    ModelGateway._invoke_uncached = fake_model
    VoiceGateway.synthesize = fake_voice
    import uvicorn
    uvicorn.run('vnext.apps.workbench.server:app', host='127.0.0.1', port=int(os.environ.get('CONTENT_OS_P0_PORT', '8768')))


if __name__ == '__main__':
    main()
