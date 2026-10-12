"""Runs inside the already installed local CosyVoice Python; no network or reference upload."""
import sys,json,hashlib,os,tempfile,subprocess,contextlib
v=json.load(sys.stdin);cfg=v['config'];path=cfg['reference_audio']
if hashlib.sha256(open(path,'rb').read()).hexdigest()!=cfg['reference_audio_sha256']:raise RuntimeError('REFERENCE_HASH_MISMATCH')
sys.path.insert(0,cfg['runtime_path']);sys.path.insert(1,cfg['legacy_matcha_path'])
with contextlib.redirect_stdout(sys.stderr):
 from cosyvoice.cli.cosyvoice import CosyVoice3
 from cosyvoice.utils.common import set_all_random_seed
 import torch,soundfile as sf
 model=CosyVoice3(cfg['model_path'],fp16=False);set_all_random_seed(cfg['seed_base'])
 chunks=[x['tts_speech'].cpu() for x in model.inference_zero_shot(v['text'],cfg['reference_text'],cfg['reference_audio'],stream=False,speed=cfg['speed'])]
 waveform=torch.cat(chunks,dim=1).squeeze(0).numpy()
 sf.write(v['output_path'],waveform,model.sample_rate,subtype='PCM_16')
print(json.dumps({'audio_path':v['output_path'],'model':cfg['model_id']}))
