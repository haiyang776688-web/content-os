"""Read current, valid storyboard; build a human review document without approving it."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from vnext.storage.store import Store
from vnext.core.preflight import check

ROOT=Path(__file__).resolve().parents[1]
store=Store(ROOT/'phase2_preview_data');pid='PRJ-bba515713057';out=ROOT/'examples/activation'
board=store.latest(pid,'STORYBOARD');ir=store.latest(pid,'DIRECTOR_IR');edt=store.latest(pid,'EDT')
if not board or not store.is_usable_input(board['artifact_id']):raise ValueError('CURRENT_STORYBOARD_REQUIRED')
timing=store.latest(pid,'AUDIO_TIMING_MAP');formal=bool(timing and store.is_usable_input(timing['artifact_id']))
validation=check(store,pid,edt['artifact_id'],require_audio=formal)
if not validation['ok']:raise ValueError('STORYBOARD_PREFLIGHT_FAILED')
gate=store.latest(pid,'STORYBOARD_GATE')
approved=bool(gate and store.is_usable_input(gate['artifact_id']) and gate['payload']['all_beats_approved'] and any(d['artifact_id']==board['artifact_id'] for d in gate['dependencies']))
duration=max(c['timeline_out'] for c in edt['payload']['clips'])
entries=board['payload']['entries'];beats={b['beat_id']:b for b in ir['payload']['beats']}
compositions={c['beat_id']:c for c in store.latest(pid,'RESOLVED_VISUAL_COMPOSITION')['payload']['compositions']}
names={'CHARACTER_EXPLAIN_KEYWORD':'人物讲解关键词','THREE_POINT_SUMMARY':'三点总结','CHARACTER_ACTION_SEQUENCE':'动作与步骤','A_B_COMPARE':'左右对比','TIMELINE_PROCESS':'流程步骤'}
files=[]
for e in entries:
 for image_path in e['images']:
  path=Path(image_path)
  with Image.open(path) as image:
   image.verify()
  with Image.open(path) as image:
   if image.size!=(1920,1080):raise ValueError('UNEXPECTED_STORYBOARD_SIZE')
  files.append({'beat_id':e['beat_id'],'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resolution':'1920x1080'})
for n in range((len(entries)+5)//6):
 sheet=Image.new('RGB',(1280,1160),'#e8e8e8');draw=ImageDraw.Draw(sheet)
 for i,e in enumerate(entries[n*6:(n+1)*6]):
  with Image.open(e['images'][1]) as image:
   thumbnail=image.convert('RGB');thumbnail.thumbnail((620,349))
  x=10+(i%2)*640;y=30+(i//2)*380;sheet.paste(thumbnail,(x,y));draw.text((x,y-20),e['beat_id']+' / '+e['pattern_id'],fill='#111111')
 sheet.save(out/f'STORYBOARD_CONTACT_{n+1}.jpg',quality=95)
lines=['# 分镜审查：让视觉时间线跟着声音工作','',
 f"当前分镜第 {board['revision']} 版：{board['artifact_id']}。五个场景，九段已批准脚本，18 个视觉节拍，36 张实际渲染图；1920 × 1080。",'',
 f"H2 已确认。当前分镜 Storyboard Gate {'已确认' if approved else '尚未确认'}。此文档不代替人工批准。",'',
 '本版按用户提供的 XIAO-Y 模板参考增量改版：白底黑字、黄色划线和红色重点；8种构图、13个人物动作，全身/脸部特写/左右镜头交替。要点编号逐条出现，对比用灰黄区分。中文采用本机真实600字重，字幕缩短为45屏，最长16字，保留白字阴影和固定基线。','',
 (f'正式本地克隆配音实测 {duration:.3f} 秒。画面按九段实测音频重定时；同一段内两个节拍按已批准导演节奏比例分配。字幕采用段落边界，字幕按标点拆短句，长句按字符与字号上限进一步拆分，时间按字符数比例分配，不宣称逐词精确对齐。' if formal else f'当前总时长 {duration:g} 秒为导演估计，用于配音前的画面设计。字幕也是暂定排布，本次只确认内容、构图和可读性。正式本地克隆配音后，将用实测音频重定时并更新字幕；不能以本分镜证明 60–90 秒或声画同步。'),'',
 ('第2版配音前设计和第3版配音后分镜均有真实用户批准，历史Gate保留。用户随后要求参考XIAO-Y模板、避免PPT感，本版更新视觉与排版，复用已批准脚本和已生成的本地克隆音频；当前分镜需要用户确认，正式成片另需H3，发布另需H4。' if formal else '批准当前分镜将允许生成正式本地克隆配音。最终成片另需 H3，发布另需 H4。'),'',
 f"| 节拍 | {'音频时钟时间' if formal else '暂定时间'} | 模板 | 画面要点 |",'|---|---|---|---|']
for e in entries:
 b=beats[e['beat_id']];c=compositions[e['beat_id']];t=c['timing']
 labels=' / '.join(s['text'].replace('|','／') for s in c['text_slots'])
 lines.append(f"| {e['beat_id']} | {t['start']:.3f}–{t['end']:.3f} 秒 | {names.get(b['pattern_id'],b['pattern_id'])} | {labels} |")
lines+=['','## 总览','']
for n in range((len(entries)+5)//6):lines +=[f'![分镜总览 {n+1}]({out/f"STORYBOARD_CONTACT_{n+1}.jpg"})','']
lines+=['## 全部分镜原图','']
for e in entries:
 lines +=[f"### {e['beat_id']} · {names.get(e['pattern_id'],e['pattern_id'])}",'',f"画面关键词：{e['keyword']}。",'']
 for index,image_path in enumerate(e['images']):lines +=[f'![{e["beat_id"]} {"入场" if index==0 else "完整显示"}]({image_path})','']
(out/'STORYBOARD_REVIEW.md').write_text('\n'.join(lines)+'\n')
(out/'STORYBOARD_VERIFICATION.json').write_text(json.dumps({'project_id':pid,'storyboard_artifact_id':board['artifact_id'],'revision':board['revision'],'director_ir_id':ir['artifact_id'],'edt_artifact_id':edt['artifact_id'],'entries':len(entries),'images':len(files),'files':files,'preflight':validation,'human_approved':approved,'timing_source':'AUDIO_TIMING_MAP' if formal else 'DIRECTOR_ESTIMATE','duration':duration,'formal_voice_generated':formal},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'storyboard':board['artifact_id'],'revision':board['revision'],'images':len(files),'prevoice_preflight':validation,'review':str(out/'STORYBOARD_REVIEW.md')},ensure_ascii=False))
