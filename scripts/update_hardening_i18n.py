import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
pairs={
'registered':('已登记','Registered'),'notImplemented':('适配器未实现','Adapter not implemented'),
'open':('架构检查','Architecture checks'),'title':('Phase 2 完整性控制台','Phase 2 integrity console'),
'yes':('是','Yes'),'no':('否','No'),'strict':('严格证据与音频时序已启用；旧产物仍可查看，需要按新合同重新验证。','Strict evidence and audio timing enabled; legacy artifacts remain viewable and require revalidation.'),
'legacy':('当前为旧版诊断模式。真实生产前请启用严格合同并补齐证据、逐项声明及音频对齐。','Legacy diagnostic mode. Enable strict contracts and provide evidence, claims and audio alignment before real production.'),
'truthNotice':('未执行的真实模型、真实配音与视频审计保持未验证。测试音和 Mock 不能作为生产验收。','Unexecuted live models, voices and video audits remain unverified. Test tones and Mock are not production acceptance.'),
'providers':('模型适配器状态','Model adapter truth'),'voices':('声音服务状态','Voice service truth'),
'worker':('模型服务','Worker'),'adapter':('适配器已实现','Adapter implemented'),'configured':('配置完整','Configured'),'caps':('实际映射能力','Implemented mappings'),'live':('真实调用验证','Live verified'),
'mock':('仅模拟','Mock only'),'unverified':('未执行真实验收','Live acceptance pending'),
'budget':('预算与备用模型','Budgets and fallback'),'project':('项目上限','Project limit'),'daily':('每日上限（UTC）','Daily limit (UTC)'),'single_run':('单次上限','Single attempt limit'),
'fallback':('故障备用策略','Fallback policy'),'fallbackWorkers':('备用 Worker ID（逗号分隔）','Fallback worker IDs (comma separated)'),
'pricing':('按 Worker ID 配置报价。input_per_million / output_per_million 是每百万 token 的 USD 估价；多模态需额外 image_per_input / audio_per_input / video_per_input。留空不代表免费：启用预算后没有可用估价会阻止调用。','Pricing by worker ID: input_per_million / output_per_million in USD; multimodal also requires image_per_input / audio_per_input / video_per_input. Empty means unknown, not free. Budgets block calls without an estimate.'),
'ledger':('模型调用账本','Model run ledger'),'role':('部门','Role'),'status':('状态','Status'),'estimate':('估计成本','Estimated cost'),'actual':('服务返回成本','Provider cost'),'retry':('重试次数','Retry count'),'cache':('缓存命中','Cache hit'),'unknown':('未知','Unknown'),
'manifest':('项目依赖文件','Project dependency files'),'states':('产物可用性','Artifact usability'),'artifact':('产物','Artifact'),'latest':('最新版本','Latest revision'),'valid':('依赖有效','Dependencies valid'),'usable':('可供生产使用','Usable input'),
'operations':('完整性操作','Integrity operations'),'ownerNotice':('每个操作按责任部门校验。启用严格合同、预算与 Relink 由人工负责；Evidence 仅研究部门可写；疑似声明由审计或人工判定；音频时序仅配音或对齐模块可写。','Each operation checks its owner. Humans control strict mode, budgets and relink; Research owns Evidence; Audit/Human decides claim candidates; Voice/Alignment owns timing.'),
'enable':('启用严格合同','Enable strict contracts'),'evidence':('登记证据定位','Register evidence span'),'claim-decision':('审查疑似声明','Review claim candidates'),'audio-timing':('登记音频对齐','Register audio alignment'),'relink':('按哈希重连文件','Relink by hash'),'research-tool':('读取研究资料','Read research source'),'execute':('执行所选操作','Execute selected operation'),'saved':('设置已保存','Settings saved'),
'enableHelp':('提交空对象即可。启用后新 Script 必须使用 ClaimUnit v2；真实渲染必须具备音频主时钟。','Submit an empty object. New scripts require ClaimUnit v2 and formal render requires the audio master clock.'),
'evidenceHelp':('填写 evidence_id、source_id、locator、excerpt 及两个 SHA256；必须与当前来源精确相符。','Provide evidence_id, source_id, locator, excerpt and both SHA256 hashes; they must exactly match the current source.'),
'claim-decisionHelp':('填写 report_id、reviewer、decisions；所有候选都需注明 NON_CLAIM 或 REGISTER_CLAIM 及理由。','Provide report_id, reviewer, decisions. Every candidate requires NON_CLAIM or REGISTER_CLAIM and a reason.'),
'audio-timingHelp':('提交 AUDIO_TIMING_MAP：绑定已批准脚本与实际 Voice，记录对齐方法、版本、执行者和逐段 phrase_ranges。','Submit AUDIO_TIMING_MAP bound to the approved Script and actual Voice; include alignment method, version, worker and phrase_ranges per segment.'),
'manifestHelp':('提交空对象，冻结当前依赖的文件身份；不会自动替换丢失文件。','Submit an empty object to pin dependency identities; missing files are never substituted.'),
'relinkHelp':('填写 asset_id 与 path。只接受与已冻结 expected_hash 完全一致的文件。','Provide asset_id and path. Only files matching the pinned expected_hash are accepted.'),
'research-toolHelp':('填写 tool、arguments、request_id。本轮可读取项目目录内的本地文档；SEARCH 等未配置的远程操作明确返回 BLOCKED。','Provide tool, arguments and request_id. Local documents inside the project directory are implemented; unconfigured remote operations such as SEARCH return BLOCKED.')}
tokens={'VISION':('视觉输入','Vision'),'JSON_SCHEMA':('原生结构约束','Native JSON schema'),'VOICE_AUTHORIZATION':('配音授权快照','Voice authorization snapshot'),'MODEL_EXECUTION_CONFIG':('模型执行配置','Model execution config'),'ALIGNMENT':('音频对齐','Alignment'),
'ADAPTER_NOT_IMPLEMENTED':('适配器未实现','Adapter not implemented'),'CONFIGURED_NOT_VERIFIED':('已配置，未验证','Configured, unverified'),'MOCK_ONLY':('仅模拟','Mock only'),
'LOCAL_CLONED_VOICE':('本地克隆声音','Local cloned voice'),'CLOUD_TTS':('云端配音','Cloud TTS'),'RESOLVED':('已解析','Resolved'),'HASH_MISMATCH':('哈希不一致','Hash mismatch'),'RELINK_REQUIRED':('需要重连','Relink required'),'RESERVED':('已预留预算','Reserved'),
'DISABLED':('禁用备用','Disabled'),'ASK':('先经人工确认','Ask'),'AUTO_SAFE':('同能力安全备用','Auto safe')}
reg=json.loads((ROOT/'vnext/i18n/registry.json').read_text())
for lang,n in [('zh-CN',0),('en-US',1)]:
 p=ROOT/'vnext/i18n'/(lang+'.json');d=json.loads(p.read_text())
 for key,val in pairs.items():d['hard.'+key]=val[n]
 for key,val in tokens.items():d['enum.'+key]=val[n]
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
reg['keys']=sorted(d);reg['canonical_tokens']=sorted(set(reg['canonical_tokens'])|set(tokens));(ROOT/'vnext/i18n/registry.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
