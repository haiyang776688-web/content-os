"""Voice provider boundary. Mock WAV is a test signal, not spoken TTS."""
from __future__ import annotations

import math
import struct
import uuid
import wave
from pathlib import Path

from vnext.contracts import VoiceArtifact, VoiceRequest


class VoiceGateway:
    def synthesize(self, request: VoiceRequest, output_dir: Path, *, privacy='LOCAL_ONLY', upload_confirmed=False) -> VoiceArtifact:
        from vnext.providers.tts import native_execute,list_profiles
        native=next((p for p in list_profiles() if p['profile']==request.voice_profile and p['configured']),None)
        if native:return native_execute(request,output_dir,privacy,upload_confirmed)
        if request.voice_profile not in ("MOCK_VOICE_V1", "MOCK_VOICE_ALT_V1"):
            from vnext.phase2.hardening.voices import execute
            return execute(request,output_dir,privacy,upload_confirmed)
        if request.output_format != "wav":
            raise RuntimeError("MOCK_SUPPORTS_WAV_ONLY")
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_id = "VOI-" + uuid.uuid4().hex[:12]
        path = output_dir / f"{artifact_id}.wav"
        duration = max(0.4, min(8.0, len(request.text) * 0.08))
        frames = int(duration * request.sample_rate)
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(request.channels)
            audio.setsampwidth(2)
            audio.setframerate(request.sample_rate)
            for index in range(frames):
                frequency = 440 if request.voice_profile == "MOCK_VOICE_V1" else 523
                value = int(1600 * math.sin(2 * math.pi * frequency * index / request.sample_rate))
                audio.writeframesraw(struct.pack("<h", value) * request.channels)
        return VoiceArtifact(voice_artifact_id=artifact_id, provider="mock", model="test-tone-v1",
            voice_profile=request.voice_profile, audio_path=str(path), duration=duration,
            sample_rate=request.sample_rate, channels=request.channels, status="MOCK")
