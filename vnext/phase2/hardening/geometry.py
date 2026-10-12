"""Deterministic bounding-box QA using the shared composition's CSS geometry.
Font advances are mechanical approximations, not a browser shaping certification.
"""
import math
from pathlib import Path
from functools import lru_cache
from vnext.phase2.contracts import QAItem

@lru_cache(maxsize=64)
def metrics(path):
    from fontTools.ttLib import TTFont
    font=TTFont(path);cmap=font.getBestCmap() or {};u=font['head'].unitsPerEm
    advances={c:font['hmtx'][glyph][0]/u for c,glyph in cmap.items()};font.close();return advances

def measure_text(store,text,role):
    snap=None
    # Exact font face path from the snapshot; no cloud font resolution.
    with store.connection() as db:
        rows=db.execute("SELECT data FROM artifacts WHERE artifact_type='PROJECT_FONT_SNAPSHOT' ORDER BY rowid DESC").fetchall()
    import json
    for row in rows:
        found=next((f for f in json.loads(row['data'])['payload']['fonts'] if f['font_id']==role.get('font_id')),None)
        if found and Path(found['preview_path']).is_file():snap=found;break
    widths=metrics(snap['preview_path']) if snap else {}
    size=role.get('size',40);lines=text.split('\n')
    width=max((sum(widths.get(ord(c),1 if ord(c)>255 else .6)*size for c in line)+max(0,len(line)-1)*role.get('letter_spacing',0) for line in lines),default=0)
    return width,len(lines)*size*role.get('line_height',1.15)

def checks(store,pid,edt,strict=False):
    profile=store.latest(pid,'TYPOGRAPHY_PROFILE');roles=(profile or {}).get('payload',{}).get('roles',{})
    from vnext.media.library.service import MediaLibrary
    assets={a.asset_id:a for a in MediaLibrary(store).assets(pid)}
    issues=[];boxes=[];W,H=edt.width,edt.height
    def issue(code,c,owner='TIMELINE',warning=False):
        severity='WARNING' if warning or not strict else 'BLOCKER'
        issues.append(QAItem(code=code,severity=severity,owner=owner,description=c.clip_id+' deterministic geometry check'))
    for c in edt.clips:
        if c.hidden or c.track not in ('TEXT','SUBTITLE','CHARACTER','ELEMENT','MEDIA','VIDEO'):continue
        text=c.track in ('TEXT','SUBTITLE');role=roles.get('SUBTITLE' if c.track=='SUBTITLE' else c.metadata.get('typography_role','BODY'),{})
        meta=c.metadata.get('box',{});w=W*meta.get('width',.38 if c.track=='CHARACTER' else .9 if c.track=='SUBTITLE' else .36 if c.pattern_id=='A_B_COMPARE' else .5 if (c.pattern_id or '').startswith('CHARACTER_') and text else .8)
        h=H*meta.get('height',.8)
        if text:
            tw,th=measure_text(store,c.metadata.get('text',''),role)
            lines=max(1,math.ceil(tw/max(1,w))) if c.track!='SUBTITLE' else 1
            h=th*lines;w=min(w,tw) if lines==1 else w
            if c.track=='SUBTITLE' and tw>W*meta.get('width',.9):issue('text_clipping',c,'SUBTITLE')
            if h>H*.6:issue('text_clipping',c,'TYPOGRAPHY')
            if role.get('size',40)<H*.022:issue('min_readable_font_size',c,'TYPOGRAPHY')
        else:
            asset=assets.get(c.asset_id);resolution=asset.resolution if asset else None
            if resolution and not c.metadata.get('portrait_window'):
                try:
                    iw,ih=map(float,resolution.split('x'))
                    if iw>0 and ih>0:
                        ratio=min(w/iw,h/ih);w,h=iw*ratio,ih*ratio
                except ValueError:pass
        w*=c.scale;h*=c.scale;x=c.position.get('x',.5)*W;y=c.position.get('y',.5)*H
        # Alpha bbox calibration prevents transparent padding from creating phantom collisions.
        cal=c.metadata.get('calibration',{}).get('content_bbox')
        left,top=x-w/2,y-h/2
        if cal:left+=w*cal['x'];top+=h*cal['y'];w*=cal['w'];h*=cal['h']
        box=(left,top,left+w,top+h);boxes.append((c,box))
        allowed=c.metadata.get('overlap_allowed',[])
        if any(v<0 or v>=1 for v in c.crop.values()):issue('media_crop' if c.track!='CHARACTER' else 'character_crop',c)
        if c.crop and any(v>0 for v in c.crop.values()) and not c.metadata.get('crop_allowed'):
            issue('character_crop' if c.track=='CHARACTER' else 'media_crop',c)
        if any(v<0 for v in box[:2]) or box[2]>W or box[3]>H:
            code='element_outside_canvas' if c.track=='ELEMENT' else 'character_crop' if c.track=='CHARACTER' else 'media_crop' if c.track in ('MEDIA','VIDEO') else 'text_clipping'
            if [c.track,c.track] not in allowed:issue(code,c)
        # Subtitle baseline has its own frozen bottom placement policy (.91 center).
        bottom=H*.96 if c.track=='SUBTITLE' else H*.9
        if box[0]<W*.05 or box[2]>W*.95 or box[1]<H*.05 or box[3]>bottom:
            if [c.track,c.track] not in allowed:issue('safe_area_overflow',c)
        if c.timeline_out-c.timeline_in>15 and c.motion.get('kind','HOLD')=='HOLD':issue('persistent_static_visual',c,'DIRECTOR',True)
    def overlaps(a,b):return min(a[2],b[2])-max(a[0],b[0])>2 and min(a[3],b[3])-max(a[1],b[1])>2
    for i,(a,ab) in enumerate(boxes):
        for b,bb in boxes[i+1:]:
            if a.beat_id and b.beat_id and a.beat_id!=b.beat_id:continue
            if min(a.timeline_out,b.timeline_out)<=max(a.timeline_in,b.timeline_in):continue
            pair=[a.track,b.track];allow=a.metadata.get('overlap_allowed',[])+b.metadata.get('overlap_allowed',[])
            if pair in allow or pair[::-1] in allow:continue
            if not overlaps(ab,bb):continue
            if 'SUBTITLE' in pair:code='subtitle_overlap';owner='SUBTITLE'
            elif 'TEXT' in pair and 'CHARACTER' in pair:code='character_text_collision';owner='TIMELINE'
            elif 'TEXT' in pair and any(x in pair for x in ('MEDIA','VIDEO')):code='media_text_collision';owner='TIMELINE'
            else:continue
            issue(code,a,owner)
    times=sorted({c.timeline_in for c,_ in boxes}|{c.timeline_out for c,_ in boxes})
    for t in times:
        active=[c for c,_ in boxes if c.timeline_in<=t<c.timeline_out and c.track=='TEXT']
        if len(active)>6 or sum(len(c.metadata.get('text','')) for c in active)>150:
            issue('excessive_information_density',active[0],'DIRECTOR',True);break
    return [x.model_dump() for x in issues]
