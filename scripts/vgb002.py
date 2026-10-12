"""Render and verify the isolated VGB-002 fusion candidates."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'vnext/renderers/remotion/project'
PUBLIC = PROJECT / 'public/PREVIEW-VGB001'
OUTPUT_NAMES = {
    'F1': 'VGB-002-F1-EvidenceHeavy.mp4',
    'F2': 'VGB-002-F2-BrandBalanced.mp4',
}


def run(args):
    return subprocess.check_output([str(a) for a in args], cwd=PROJECT)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path):
    data = json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))
    video = next(s for s in data['streams'] if s['codec_type'] == 'video')
    audio_hash = run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:a:0', '-f', 'hash', '-hash', 'sha256', '-']).decode().strip()
    return {
        'duration': data['format']['duration'],
        'frames': int(video['nb_frames']),
        'resolution': [video['width'], video['height']],
        'fps': video['r_frame_rate'],
        'audio_hash': audio_hash,
        'file_sha256': sha(path),
        'bytes': Path(path).stat().st_size,
    }


def render(output, browser):
    for direction, composition in [('F1', 'VGB002F1'), ('F2', 'VGB002F2')]:
        target = output / OUTPUT_NAMES[direction]
        with (output / f'{direction}-render.log').open('w') as log:
            subprocess.run([
                PROJECT / 'node_modules/.bin/remotion', 'render', 'src/vgb002-index.tsx', composition, target,
                '--codec', 'h264', '--concurrency', '2', '--browser-executable', browser,
            ], cwd=PROJECT, stdout=log, stderr=subprocess.STDOUT, check=True)
        print(f'{direction}: rendered', flush=True)


def verify(output, baseline):
    baseline_results = [probe(baseline / f'VGB-001-{direction}.mp4') for direction in ('A', 'B')]
    assert len({x['audio_hash'] for x in baseline_results}) == 1, 'VGB-001 A/B audio differs'
    reports = []
    for direction, name in OUTPUT_NAMES.items():
        report = {'direction': direction, **probe(output / name)}
        assert (report['resolution'], report['fps'], report['frames']) == ([1920, 1080], '30/1', 574)
        assert report['audio_hash'] == baseline_results[0]['audio_hash'], f'{direction} audio differs from VGB-001'
        assert report['duration'] == baseline_results[0]['duration'], f'{direction} duration differs from VGB-001'
        reports.append(report)
    source = (PROJECT / 'src/vgb001/shared.tsx').read_text()
    cues = re.findall(r"\{text:'([^']*)',startMs:(\d+),endMs:(\d+),timestampMs:null,confidence:null\}", source)
    assert len(cues) == 6 and cues[-1][0].endswith('Fact ID')
    assert all(int(a[2]) == int(b[1]) for a, b in zip(cues, cues[1:])), 'caption gap/overlap'
    expected = '研究页允许从本地文件导入资料模型提取的原文候选需要操作者确认候选引文不会自动成为已核实 Fact这一步必须由人来把关Fact Pack 把选中的事实与来源绑定脚本里的事实性主张要引用已有 Fact ID'
    assert ''.join(c[0] for c in cues) == expected, 'caption wording changed'
    for required in ('voice.wav', 'font.otf', 'research.png', 'script.png', 'point.png', 'serious.png', 'surprise.png'):
        assert (PUBLIC / required).is_file(), f'missing frozen input {required}'
    result = {
        'status': 'TECHNICAL_PASS_NOT_CREATIVE_ACCEPTANCE',
        'baseline': 'VGB-001 A/B',
        'source_interval': [5.56, 24.68],
        'source_content_duration': 19.12,
        'renders': reports,
        'baseline_audio_hash': baseline_results[0]['audio_hash'],
        'captions': {'cue_count': 6, 'wording_preserved': True, 'no_gaps_or_overlaps': True, 'fact_id_intact': True},
        'human_visual_choice': 'PENDING',
    }
    (output / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['render', 'verify'])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--browser', default='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.action == 'render':
        render(args.output, args.browser)
    else:
        if not args.baseline:
            parser.error('--baseline is required for verify')
        verify(args.output, args.baseline.resolve())
