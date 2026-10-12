"""Keep Track A's adapter-boundary fake honest and audible."""

import json
import wave
from array import array

from vnext.contracts import ModelMessage, ModelRequest, Role, VoiceRequest
from vnext.gateways.model.gateway import ModelGateway
from vnext.tests.p0_provider_boundary import fake_model, fake_voice


def test_track_a_research_boundary_uses_supplied_source(tmp_path):
    request = ModelRequest(
        role=Role.RESEARCH,
        worker_profile="DEEPSEEK",
        system_prompt="Track A",
        messages=[ModelMessage(role="user", content=json.dumps({"sources": [
            {"source_id": "SRC-1", "content": "First evidence.\nSecond evidence."}
        ]}))],
        prompt_version="P0_TRACK_A",
    )
    result = fake_model(ModelGateway(cache_dir=tmp_path), request)
    assert [p["excerpt"] for p in result.structured_output["proposals"]] == [
        "First evidence.", "Second evidence.",
    ]
    assert result.provider_metadata["provider"] == "P0_FAKE_PROVIDER_BOUNDARY"


def test_track_a_voice_boundary_is_audible_and_not_live(tmp_path):
    request = VoiceRequest(text="Track A test segment", language="zh-CN", voice_profile="YU_LOCAL_V1")
    artifact = fake_voice(None, request, tmp_path)
    assert artifact.status == "READY"
    assert artifact.provenance["live_verified"] is False
    with wave.open(artifact.audio_path) as audio:
        assert audio.getnchannels() == 1
        assert audio.getframerate() == 48000
        assert audio.getnframes() == 4 * 48000
        samples = array("h")
        samples.frombytes(audio.readframes(audio.getnframes()))
    assert max(samples) > 1000
    assert min(samples) < -1000
