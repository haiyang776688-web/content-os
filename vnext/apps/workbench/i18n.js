// Central presentation boundary. Canonical values, user text, model IDs and hashes never change.
export const translate=(app,key)=>app.dict[key]??key;
export function present(app,value){
  if(value===null||value===undefined)return '—';
  const token=String(value);const direct=app.dict['enum.'+token];if(direct)return direct;
  for(const [prefix,key] of [['STAGE_','p2.stagePrefix'],['ROLE_ASSIGNMENT_','p2.roleAssignment'],['SOURCE_','p2.sourcePrefix']])if(token.startsWith(prefix))return translate(app,key)+' · '+(app.dict['enum.'+token.slice(prefix.length)]??'');
  for(const prefix of ['EFFECTIVE_SKILL_SNAPSHOT_','ASSET_INTELLIGENCE_'])if(token.startsWith(prefix))return translate(app,prefix==='EFFECTIVE_SKILL_SNAPSHOT_'?'p2.skills':'media')+' · '+present(app,token.slice(prefix.length));
  if(/^(ART-|PRJ-|XACT-)/.test(token)||/_V\d+$/.test(token))return token;
  if(/^[A-Z][A-Z_0-9]+$/.test(token))return translate(app,'unknownLabel');
  return token;
}
const brands={OPENAI:'OpenAI',DEEPSEEK:'DeepSeek',DOUBAO:'Doubao',GLM:'GLM',MINIMAX:'MiniMax',GEMINI:'Gemini',ANTHROPIC:'Anthropic',QWEN:'Qwen',KIMI:'Kimi',GROK:'Grok'};
export function brand(app,value){return brands[String(value).toUpperCase()]??(['custom_openai','local_openai'].includes(value)?present(app,value.toUpperCase()):null)??(['mock','MOCK','Mock','Mock alternate','MOCK_ALT'].includes(value)?present(app,value==='Mock alternate'?'MOCK_ALT':String(value).toUpperCase()):value??'—');}
export function errorText(app,error){const text=String(error),token=text.split(':')[0].replace(/^['"]|['"]$/g,'');return app.dict['error.'+token]??(Object.values(app.dict).includes(text)?text:translate(app,'technicalError'));}
export function rawHtml(app,value,esc){return `<details class="raw-data"><summary>${esc(translate(app,'raw'))}</summary><pre>${esc(typeof value==='string'?value:JSON.stringify(value,null,2))}</pre></details>`;}
export function summaryHtml(app,value,esc){
  if(!value)return `<p class="muted">${esc(translate(app,'noData'))}</p>`;
  if(Array.isArray(value))return value.map(x=>summaryHtml(app,x,esc)).join('');
  if(typeof value!=='object')return esc(errorText(app,value));
  const payload=value.payload??value;let rows=[];
  for(const [key,label] of [['artifact_type','metadata'],['current_status','status'],['stage','workflow'],['state','state'],['verdict','report.verdict'],['decision','report.verdict']])if((value[key]??payload[key])!==undefined)rows.push(`${translate(app,label)}: ${present(app,value[key]??payload[key])}`);
  if(value.artifact_id)rows.push(value.artifact_id);
  if(value.revision)rows.push(`${translate(app,'revision')}: ${value.revision}`);
  if(payload.ok!==undefined)rows.push(`${translate(app,'report.verdict')}: ${present(app,payload.ok?'PASS':'FAIL')}`);
  for(const item of [...(payload.issues??payload.findings??[]),...(payload.risks??[])]){
    if(typeof item==='string')rows.push(app.dict['error.'+item.split(':')[0]]??translate(app,'findingDetail'));else rows.push([present(app,item.severity??'WARNING'),app.dict['error.'+(item.code??'')]??translate(app,'findingDetail'),item.owner?present(app,item.owner):''].filter(Boolean).join(' · '));
  }
  if(payload.all_beats_approved!==undefined)rows.push(present(app,payload.all_beats_approved?'APPROVED':'PENDING'));
  if(payload.publish_authorized===false)rows.push(translate(app,'report.noPermission'));
  if(!rows.length)rows.push(translate(app,'success'));
  return `<div class="localized-summary">${rows.map(row=>`<div>${esc(row)}</div>`).join('')}</div>`;
}
export function snapshotInputs(root){return [...root.querySelectorAll('input,textarea,select')].map(e=>({id:e.id,selector:e.id?'#'+e.id:('['+[...e.attributes].find(a=>a.name.startsWith('data-'))?.name+'="'+[...e.attributes].find(a=>a.name.startsWith('data-'))?.value+'"]'),value:e.value,checked:e.checked,selectionStart:e.selectionStart,selectionEnd:e.selectionEnd}));}
export function restoreInputs(root,values){for(const v of values){const e=root.querySelector(v.selector);if(!e||e.type==='file')continue;e.value=v.value;if('checked'in e)e.checked=v.checked;if(e.tagName==='TEXTAREA'&&v.selectionStart!==null)e.setSelectionRange(v.selectionStart,v.selectionEnd);}}
