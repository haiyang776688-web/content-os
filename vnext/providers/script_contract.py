"""Derive duplicated text and offsets from producer-owned segments, preserving all claim semantics."""
import copy

def prepare(payload):
 result=copy.deepcopy(payload);changes=[]
 if result.get('contract_version')!=2 or not result.get('segments'):return result,changes
 joined='\n'.join(s['text'] for s in result['segments'])
 if result.get('text')!=joined:result['text']=joined;changes.append('TEXT_DERIVED_FROM_SEGMENTS')
 segments={s['segment_id']:s['text'] for s in result['segments']}
 for c in result.get('claim_units',[]):
  text=segments.get(c['segment_id'],'');span=c['text_span'];quote=c['claim_text']
  if text[span['start']:span['end']]==quote:continue
  if not quote or text.count(quote)!=1:raise ValueError('CLAIM_SPAN_MISMATCH')
  start=text.index(quote);c['text_span']={'start':start,'end':start+len(quote)};changes.append('EXACT_CLAIM_SPAN_DERIVED:'+c['claim_id'])
 return result,changes
