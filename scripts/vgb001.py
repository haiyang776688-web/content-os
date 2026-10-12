"""Isolated VGB-001 media preparation/render/integrity checks; never writes project state."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'vnext/renderers/remotion/project'
PUBLIC = PROJECT / 'public/PREVIEW-VGB001'


def run(args):
    return subprocess.check_output([str(a) for a in args], cwd=PROJECT)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(source_props, output):
    from PIL import Image
    PUBLIC.mkdir(parents=True, exist_ok=True)
    props = json.loads(source_props.read_text())
    voice = next(c for c in props['clips'] if c['track'] == 'VOICE')
    voice_path = PROJECT / 'public' / voice['asset_src']
    rows = []
    for name in ('research', 'script'):
        source = ROOT / f'fixtures/creative-spike-1-evidence/{name}.png'
        target = PUBLIC / f'{name}.png'
        shutil.copy2(source, target)
        rows.append({'name': name, 'source': str(source.relative_to(ROOT)), 'sha256': sha(target), 'operation': 'BYTE_COPY'})
    actions = ROOT / 'assets/packs/character/XIAO-Y_Action_Pack_v2_Production_48/actions'
    for name, prefix in [('point', 'XACT-007'), ('think', 'XACT-025'), ('serious', 'XACT-044'), ('surprise', 'XACT-030')]:
        source = next(actions.glob(prefix + '_*.png'))
        im = Image.open(source).convert('RGBA')
        bbox = im.getbbox()
        im.crop(bbox).save(PUBLIC / f'{name}.png')
        rows.append({'name': name, 'source': str(source.relative_to(ROOT)), 'source_sha256': sha(source), 'sha256': sha(PUBLIC/f'{name}.png'), 'alpha_crop': bbox})
    font = PROJECT / 'public' / props['fonts'][0]['src']
    shutil.copy2(font, PUBLIC / 'font.otf')
    run(['ffmpeg', '-y', '-v', 'error', '-i', voice_path, '-af', 'atrim=start=5.56:end=24.68,asetpts=PTS-STARTPTS', '-c:a', 'pcm_s16le', PUBLIC / 'voice.wav'])
    script_path = source_props.parent.parent / 'artifacts/SCRIPT/v0003-ART-278087e926034f3b.json'
    script = json.loads(script_path.read_text())
    segments = [s for s in script['payload']['segments'] if s['segment_id'] in ['SEG-02','SEG-03','SEG-04']]
    manifest = {'source_script_sha256': sha(script_path), 'source_segments': segments, 'source_interval': [5.56, 24.68], 'duration': 19.12, 'fps': 30, 'frames': 574, 'canvas': [1920,1080], 'source_props_sha256': sha(source_props), 'source_voice_sha256': sha(voice_path), 'trimmed_voice_sha256': sha(PUBLIC/'voice.wav'), 'font_sha256': sha(PUBLIC/'font.otf'), 'script_id': 'ART-278087e926034f3b', 'voice_id':'ART-7ef0a1a38f894364', 'assets': rows}
    (output/'input-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    return manifest


def render(output, browser):
    for direction in 'ABC':
        with (output/f'{direction}-render.log').open('w') as log:
            subprocess.run([str(PROJECT/'node_modules/.bin/remotion'),'render','src/vgb001-index.tsx',f'VGB001{direction}',str(output/f'VGB-001-{direction}.mp4'),'--codec','h264','--concurrency','2','--browser-executable',browser],cwd=PROJECT,stdout=log,stderr=subprocess.STDOUT,check=True)
        print(f'{direction}: rendered', flush=True)


def verify(output):
    reports=[]
    for direction in 'ABC':
        path=output/f'VGB-001-{direction}.mp4'
        probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',path]))
        video=next(s for s in probe['streams'] if s['codec_type']=='video')
        digest=run(['ffmpeg','-v','error','-i',path,'-map','0:a:0','-f','hash','-hash','sha256','-']).decode().strip()
        assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))==(1920,1080,'30/1',574)
        reports.append({'direction':direction,'duration':probe['format']['duration'],'frames':int(video['nb_frames']),'resolution':[video['width'],video['height']],'fps':video['r_frame_rate'],'audio_hash':digest,'file_sha256':sha(path),'bytes':path.stat().st_size})
    assert len({r['audio_hash'] for r in reports})==1,'A/B/C audio differs'
    assert len({r['duration'] for r in reports})==1,'A/B/C durations differ'
    source = (PROJECT/'src/vgb001/shared.tsx').read_text()
    cues = re.findall(r"\{text:'([^']*)',startMs:(\d+),endMs:(\d+),timestampMs:null,confidence:null\}", source)
    assert len(cues)==6 and int(cues[0][1])==0 and int(cues[-1][2])==19120
    assert all(int(a[2])==int(b[1]) for a,b in zip(cues,cues[1:])), 'caption gap/overlap'
    assert cues[-1][0].endswith('Fact ID'), 'Fact ID split or truncated'
    expected='研究页允许从本地文件导入资料模型提取的原文候选需要操作者确认候选引文不会自动成为已核实 Fact这一步必须由人来把关Fact Pack 把选中的事实与来源绑定脚本里的事实性主张要引用已有 Fact ID'
    assert ''.join(c[0] for c in cues)==expected,'caption wording changed'
    manifest=json.loads((output/'input-manifest.json').read_text())
    original=''.join(s['text'] for s in manifest['source_segments'])
    assert original.replace('，','').replace('。','')==expected,'captions differ from frozen source script'
    assert manifest['trimmed_voice_sha256']==sha(PUBLIC/'voice.wav'),'prepared voice changed'
    assert manifest['font_sha256']==sha(PUBLIC/'font.otf'),'prepared font changed'
    for a in manifest['assets']:
        assert a['sha256']==sha(PUBLIC/(a['name']+'.png')),'prepared image changed'
    result={'status':'TECHNICAL_PASS_NOT_CREATIVE_ACCEPTANCE','renders':reports,'captions':{'cue_count':6,'wording_preserved':True,'no_gaps_or_overlaps':True,'fact_id_intact':True},'human_visual_choice':'PENDING','playback_review':'dense sampling + full-resolution keyframes, not uninterrupted real-time audiovisual viewing'}
    (output/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','render','verify'])
    parser.add_argument('--source-props',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--browser',default='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    args=parser.parse_args(); args.output=args.output.resolve(); args.output.mkdir(parents=True,exist_ok=True)
    if args.action=='prepare':
        if not args.source_props: parser.error('--source-props required for prepare')
        print(json.dumps(prepare(args.source_props.resolve(),args.output),ensure_ascii=False,indent=2))
    elif args.action=='render':render(args.output,args.browser)
    else:verify(args.output)
