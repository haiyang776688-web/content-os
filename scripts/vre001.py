"""Compile, render and verify the isolated VRE-001 vertical slice."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from vnext.phase2.experimental.visual_language_v1 import compile_fixture

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'vnext/renderers/remotion/project'
INPUT=ROOT/'docs/project-brain/creative-spikes/VRE-001-f2-reproduction/evidence/input.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path):
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',path]))
    video=next(s for s in data['streams'] if s['codec_type']=='video')
    audio_hash=subprocess.check_output(['ffmpeg','-v','error','-i',path,'-map','0:a:0','-f','hash','-hash','sha256','-']).decode().strip()
    return {'duration':data['format']['duration'],'frames':int(video['nb_frames']),
            'resolution':[video['width'],video['height']],'fps':video['r_frame_rate'],
            'audio_hash':audio_hash,'file_sha256':sha(path),'bytes':Path(path).stat().st_size}


def compile_output(output):
    return compile_fixture(INPUT,ROOT,PROJECT/'public',output)


def render(output,browser):
    compile_output(output)
    target=output/'VRE-001-F2-Reproduction.mp4'
    with (output/'render.log').open('w') as log:
        subprocess.run([PROJECT/'node_modules/.bin/remotion','render','src/vre001-index.tsx',
            'VRE001F2Reproduction',target,'--props',output/'remotion-props.json','--codec','h264',
            '--concurrency','2','--browser-executable',browser],cwd=PROJECT,stdout=log,
            stderr=subprocess.STDOUT,check=True)
    return target


def verify(output,baseline):
    target=output/'VRE-001-F2-Reproduction.mp4'
    report=probe(target);gold=probe(baseline)
    props=json.loads((output/'remotion-props.json').read_text())
    plan=json.loads((output/'shot-plan.json').read_text())
    diagnostics=json.loads((output/'compiler-diagnostics.json').read_text())
    assert (report['resolution'],report['fps'],report['frames'])==([1920,1080],'30/1',574)
    assert report['audio_hash']==gold['audio_hash']
    assert abs(float(report['duration'])-float(gold['duration']))<.001
    subtitles=[c for c in props['clips'] if c['track']=='SUBTITLE']
    assert len(subtitles)==6 and subtitles[-1]['metadata']['text'].endswith('Fact ID')
    assert all(abs(a['timeline_out']-b['timeline_in'])<.000001 for a,b in zip(subtitles,subtitles[1:]))
    shots=[s for beat in plan['beats'] for s in beat['shots']]
    assert len(shots)==10 and diagnostics['primary_contract_pass']
    result={'status':'TECHNICAL_PASS_PENDING_HUMAN_VISUAL_REVIEW','render':report,
            'gold_master':{'path':str(baseline),'sha256':gold['file_sha256']},
            'contract':{'shot_count':10,'one_primary':True,'frozen_audio':True,
            'caption_count':6,'fact_id_intact':True,'visual_mode':'BRAND_BALANCED'},
            'creative_checks':{'evidence_clarity':'PENDING_HUMAN_REVIEW','character_role':'CONTRACT_PASS',
            'protagonist':'CONTRACT_PASS','shot_sequence':'CONTRACT_PASS',
            'subtitle_defects':'TECHNICAL_PASS','ppt_feeling':'PENDING_HUMAN_REVIEW'}}
    (output/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['compile','render','verify'])
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--browser',default='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    args=parser.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=True)
    if args.action=='compile':compile_output(args.output)
    elif args.action=='render':render(args.output,args.browser)
    else:
        if not args.baseline:parser.error('--baseline is required')
        verify(args.output,args.baseline.resolve())
