# Asset and Third-Party Notice

## MIT-covered material

The repository source code and project-owned documentation are released under the root [MIT License](LICENSE).

The project owner has identified the XIAO-Y character master, the 48-action XIAO-Y pack and the registered XIAO-Y element SVG pack stored under `assets/` as original project assets and has chosen to release those copies under the same MIT License. This statement applies only to the copies actually present in this public repository.

## Material not relicensed by this repository

The root MIT License does not relicense:

- Python, Node or browser dependencies;
- Remotion, Chrome/Chromium, ffmpeg, Whisper or other external tools/models (Remotion is governed by its own license, not the root MIT);
- system fonts or third-party fonts;
- third-party screenshots, logos, platform UI, stock media or user-supplied evidence;
- voice providers, local cloned voices or voice reference media;
- Jianying/CapCut or its draft format;
- external model/provider APIs and outputs.

Those items remain subject to their own licenses and service terms. Dependency names in lockfiles or adapters are references, not bundled grants.

## Sanitization decisions

The public snapshot excludes:

- the real local cloned-voice profile and all voice/reference audio;
- Provider live-verification snapshots;
- cached font binaries;
- model weights and caches;
- experimental MP4/WAV renders and contact sheets;
- historical UI/evidence screenshots whose independent redistribution rights were not established.

Small PNGs under `fixtures/creative-spike-1-evidence/` and `examples/hardening/DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.png` are synthetic solid-color fixtures generated specifically for this open-source snapshot. They contain no third-party UI or user data.

Before adding any external asset, document its source, license, permitted redistribution scope and required attribution. If those facts are unknown, keep the asset outside Git and mark it as an optional external input.
