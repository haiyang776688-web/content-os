"""Rebuild the bounded hardening handoff from actual verification evidence."""
import json,re,shutil
from pathlib import Path
from collections import Counter
from vnext.phase2.hardening.providers import matrix,ALL_CAPS
from vnext.phase2.hardening.voices import voices
from vnext.phase2.hardening.capabilities import migrate
from vnext.secrets.store import SecretStore
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def write(path,value):(ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
log=(ROOT/'examples/hardening/current_regression.txt').read_text()
m=re.search(r'(\d+) passed',log)
if not m or 'failed' in log:raise RuntimeError('CURRENT_REGRESSION_MUST_PASS')
count=int(m[1]);road=read('CAPABILITY_ROADMAP.json');status=Counter(x['status'] for x in road['capabilities'])
if status!={'READY':13,'IMPLEMENTING':11}:raise RuntimeError('UNEXPECTED_STATUS_UPGRADE')
rows=[
 ('DAG','Only prerequisites block construction; 24 capabilities + 5 primitives'),
 ('CLAIM_EVIDENCE','Exact locators and hashes, per-claim binding, stale cascade, coverage decisions and H2 audit veto'),
 ('VISUAL_RESOLVER','Existing 12 templates / 48 actions / 33 elements resolve into derived RVC and canonical EDT'),
 ('PROVIDER_TRUTH','Actual adapter mapping governs assignment; unsupported protocols disabled; successful calls verify only exercised capabilities'),
 ('COST_BUDGET_FALLBACK','Append attempt ledger, transactional USD estimates, project/daily/attempt veto, capability and privacy safe fallback'),
 ('AUDIO_CLOCK','Physical audio hash/duration and approved script validation; exact provider timestamps or explicit alignment; beat/subtitle retiming'),
 ('VOICE_ADAPTERS','Local argv bridge and explicit custom cloud JSON contract; local clone never cloud fallback'),
 ('GEOMETRY_QA','Eleven deterministic checks with font metrics, image alpha bounds and declared overlap exceptions'),
 ('DEPENDENCY_MANIFEST','Pinned file identity, missing/hash mismatch detection, explicit same-hash relink and model/prompt/skill tracking'),
 ('ARTIFACT_STATE','Separate latest / dependencies valid / usable; invalid latest revisions veto production'),
 ('SOURCE_TOOL_BOUNDARY','Untrusted source boundary and formal research operations; local document execution produces Source, no automatic Fact'),
 ('PREVIEW_I18N_COMPATIBILITY','Same resolver/scene for Preview and Remotion; locale stays presentation only')]
road['architecture_hardening']={'completed':True,'date':'2026-09-27','bounded_checks':[{'area':a,'status':'READY','bounded_behavior':b} for a,b in rows],
 'regression_tests_passed':count,'original_capability_status_counts':dict(status),'live_verified_real_providers':0,'live_verified_real_voices':0,
 'mock_only':['model quality review evidence','video QA evidence','diagnostic voice and manual gate fixtures'],
 'formal_production_pressure_test_completed':False,'stop_condition':'Architecture hardening complete; no Phase 3 or new capability expansion. Real 60–90s pressure test remains future work.'}
# Correct obsolete descriptions without upgrading their capability status.
updates={
 'CAP-007':('SOURCE → exact EVIDENCE_REF → FACT → CLAIM_UNIT v2 → SCRIPT；来源变更传播，coverage疑似声明和独立审计/H2否决已接通','旧版本可读但不自动转换成strict证据；detector为启发式，事实语义和来源可信度仍需独立审计/人工'),
 'CAP-009':('Beat时长保持导演意图；正式时序由hash绑定的AudioTimingMap重定时','无timestamp时必须显式对齐；没有自动强制对齐/ASR；phrase内字幕拆分记录比例估算，不伪称词级对齐'),
 'CAP-011':('八种语义Pattern经VisualResolver接入现有12 XVT/48 XACT/33 ELM、字体/媒体/Style，产出RVC后生成EDT','各模板具备确定性基础版式；复杂动作序列、对象跟踪和高级布局仍未完成；本轮只有一个组合实际短渲染'),
 'CAP-018':('基础生产校验及11项geometry检查已接入：安全区、裁切/溢出、碰撞、字幕、字号、密度和静帧；模板可声明合法重叠','字体advances/alpha bbox为确定性几何近似，非浏览器字形像素认证；密度/静帧阈值不替代语义或审美判断，复杂motion检查仍有限'),
 'CAP-022':('原字体扫描/快照/字重/fallback/预览保留，Geometry与DependencyManifest消费同字体字节；可按hash显式Relink','无完整字体迁移包/许可管理/预设体验；不分发系统字体；剪映字体损失仍保留')}
for item in road['capabilities']:
 if item['capability_id'] in updates:item['implemented'],item['known_limitations']=updates[item['capability_id']]
write('CAPABILITY_ROADMAP.json',road);migrate(ROOT)
truth=matrix(SecretStore());voice=voices()
write('PROVIDER_CAPABILITY_MATRIX.json',{'schema_version':1,'generated_at':'2026-09-27','snapshot_scope':'Local configuration at handoff. Refresh through Workbench for current truth; no live call was made for this snapshot.',
 'capabilities':ALL_CAPS,'structured_output_note':'Client-side JSON validation and schema repair; native JSON_SCHEMA is not implemented.',
 'workers':truth,'voice_registry_separate':True,'voices':voice,'real_provider_live_verified_count':sum(x['live_verified'] for x in truth.values()),
 'real_voice_live_verified_count':sum(x['live_verified'] for x in voice),
 'limitations':['No Anthropic/Gemini executable adapter','No model discovery adapter','No native tool calling/streaming/audio-input mapping','Custom cloud TTS is a bridge contract, not a certified vendor implementation','Stub adapter tests do not prove real provider acceptance']})
closure=ROOT/'CONTENT_OS_VNEXT_PHASE2_CLOSURE_REPORT.md';archive=ROOT/'docs/CAP023_CAP024_CLOSURE_REPORT.md';archive.parent.mkdir(exist_ok=True)
if not archive.exists():shutil.copy2(closure,archive)
diagnostic=read('examples/hardening/DIAGNOSTIC_REPORT.json');protection=read('examples/hardening/READONLY_PROTECTION_REPORT.json');frozen=read('examples/hardening/frozen_phase1_regression.json')
dicts={lang:read('vnext/i18n/'+lang+'.json') for lang in ('zh-CN','en-US')};keys=len(dicts['zh-CN']);tokens=len(read('vnext/i18n/registry.json')['canonical_tokens'])
report=f'''# Content OS vNext Phase 2 — Architecture Hardening Closure

日期：2026-09-27。当前同一工作目录增量实施完成 A–U 的 bounded behavior，并按 V/Stop Condition 停止扩展。未新建源码项目、未重写 Core、未进入 Phase 3。CAP-023/CAP-024 保留，原验收报告在 `docs/CAP023_CAP024_CLOSURE_REPORT.md`；原 Preview 诊断在 `examples/phase2/`。

## 状态四个维度

| 维度 | 当前结果 | 含义 |
|---|---|---|
| READY | 原24项中13项，状态未升级 | 仅代表各项Roadmap明示的有限行为已实现并测试 |
| IMPLEMENTING | 原24项中11项，状态未降低或升级 | 高级布局、完整编辑/调度/字体体验等既有缺口仍在 |
| LIVE_VERIFIED | 真实模型0、真实声音0；真实MiniMax视频QA未验证 | 本轮未发真实provider请求、未上传clone或视频、未消费模型额度 |
| MOCK_ONLY | 审计质量/视频QA/诊断音/自动Gate fixture | 证明状态、权限、接口和否决机制，不证明真实内容质量或用户批准 |

Architecture Hardening 的12个范围在 Roadmap 单独列为 bounded READY，不转换原24项状态。`phase2_complete=false`。未来真实60–90秒压力测试尚未执行；H3/H4未替用户批准。

## 正式实现与执行路径

1. Capability关系拆成 prerequisites / consumers / integrates_with / optional_integrations。仅prerequisites参与阻塞；24能力+5primitive形成29节点DAG。CAP-022/018互相消费或集成不再形成建造循环；i18n没有生产依赖。
2. 严格模式显式启用，Source→EvidenceRef→Fact→ClaimUnit→Script逐级绑定。TEXT段落/span、PDF page/span、WEB snapshot/span、AUDIO/VIDEO区间与transcript均校验exact excerpt和SHA256。新版本沿依赖使Fact/Claim/Audit/H2失效，不silent rebinding。旧项目保持可读，不伪造其证据；启用strict会同时启用Phase2，无法从Phase1 H2绕过。
3. 数字/百分比/日期/人名/组织/产品/归因/排名/时效声明触发 UNREGISTERED_CLAIM_CANDIDATE，所有段落均扫描；既有claim flag不能绕过。Audit/Human逐候选有理由判定，detector不自动创建Fact。V2独立审计必须覆盖每个claim，事实类不得审成NON_FACTUAL；H2重复执行该否决。此检测为启发式，不能保证识别所有自然语言事实或证明Fact语义真实。
4. DirectorIR保留语义意图，不允许像素字段或真实文件路径。VisualResolver解析SemanticPattern、现有12 XVT模板、48 XACT动作、33 ELM、Media、Typography和Style。derived RVC记录layout/z-order/transforms/timing/motions/safe_area/overlap_allowed，随后生成canonical EDT。无重复生产真源。
5. CAP-023与Remotion都使用同一个CompositionResolver和Composition.tsx，消费EDT及其pinned RVC/AudioMap/Typography。最新不可用EDT仅能带warning做投影，不能用于生产。预览不会回写上游或偷偷刷新依赖。现有用户项目不自动生成strict artifacts。
6. Provider Truth明确registered/configured/adapter_implemented/credentials/model_discovered/capability_verified/live_verified/probe。OpenAI-compatible文本和本地JSON校验真实可执行；原生JSON_SCHEMA/工具/streaming/audio-input不冒称支持。Anthropic/Gemini无适配器，UI显示“已登记／适配器未实现”。MiniMax特定配置的M3视觉映射为实现合同，尚无真实调用验收。Role选择及fallback检查实际adapter能力，VideoQA不能降级文本。
7. 每次模型attempt、schema repair retry、cache、fallback和Voice执行都有append-only Model Run Ledger。SQLite是重建/查询投影。估价与服务返回货币成本分开；只返回tokens不会冒称actual，未报价是UNKNOWN而非免费。UTF8保守输入估计、输出cap与多模态报价进入预留；项目/UTC日/单次上限在事务中执行，无报价或历史未知支出时配置预算会BLOCK。价格为人工配置USD估价，不是实时供应商报价。
8. DISABLED / ASK / AUTO_SAFE执行真实分支；ASK需当次确认，AUTO_SAFE只用显式配置、相同Required Capability且隐私允许的备用。真人模型失败不转Mock。模型/endpoint/prompt/fallback配置进入角色执行快照和请求幂等键，更换配置使旧执行失效；UI locale不参与。
9. Voice Registry独立于Model。本地argv JSON bridge不启动shell、不调用cloud fallback；clone/reference profile不能以CLOUD模式上传。CustomCloudTTS提供显式JSON桥接合同，受隐私和预算阻断。本地配置程序由用户信任，network_allowed=false是合同，不是操作系统网络沙箱。已有真实clone未执行，VOICE production acceptance为false。
10. ApprovedScript→实际VOICE→AudioTimingMap→Beat retiming→Subtitle→EDT。Map核对物理audio SHA/ffprobe duration、H2脚本、逐segment coverage/order、phrase文本/区间和provenance。Provider原始timestamps保留并精确匹配segment才自动映射；跨segment或缺timestamp必须显式alignment。预配音Storyboard允许无Map，正式Render必须有可用Map与accepted Voice，解决先分镜后配音循环。Mock/Test alignment不可作为正式成片。
11. 字幕读取AudioMap，单行白字、无背景、轻阴影、底部安全区；超宽按phrase重切，记录phrase内比例拆分，禁止自动双行。没有自动强制对齐或声称词级准确；原始word timestamps保存用于后续进一步精确对齐。
12. 11项Geometry检查接入QA：safe_area_overflow、text_clipping、character_crop、media_crop、element_outside_canvas、character_text_collision、media_text_collision、subtitle_overlap、min_readable_font_size、excessive_information_density、persistent_static_visual。使用pinned字体advances、shared geometry、图片contain/alpha bbox与模板overlap_allowed。旧诊断新几何项保留warning兼容；strict blockers实际否决。字体测量是几何近似，密度/静帧为阈值warning，不是完整字形像素或视觉质量认证。
13. ResearchTool正式支持六类operation合同；本轮local DOCUMENT_READ/SNAPSHOT执行，限制项目目录和文件大小，真实Tool Result形成Source，不把模型总结直接当Fact。远程SEARCH/FETCH_PAGE/SCREENSHOT/IMAGE_SEARCH仍BLOCKED。所有role/source上下文标UNTRUSTED_SOURCE_DATA并明确SYSTEM与SOURCE边界；此控制不宣称LLM对prompt injection绝对免疫。
14. ProjectDependencyManifest跟踪pack全部文件、pinned fonts、media、voice、prompt/skill/model config；状态RESOLVED/MISSING/HASH_MISMATCH/RELINK_REQUIRED。人工Relink只能接受相同expected SHA，解析器实际消费该位置。不按同名文件替换，不修改immutable artifact。UI locale不改变manifest/config哈希。完整可搬迁项目/字体分发包尚未提供。
15. Store拆分is_latest_revision / dependencies_valid / is_usable_input。最新BLOCKED/FAILED/STALE/DIRTY/DRAFT均不能供生产使用；依赖hash、revision、状态、项目与循环递归校验。旧is_current保留兼容，不再承担生产入口全部判断。

## 最终验收证据

| 验收 | 本轮实际结果 | 文件 |
|---|---|---|
| Current Phase1+Phase2+CAP023/024+Hardening | {count} passed，1条Starlette/httpx弃用提示；其中新增{count-78}例 | examples/hardening/current_regression.txt |
| Phase1 frozen regression | 隔离副本12 passed，冻结目录{frozen['protected_files']}个文件未变 | frozen_phase1_regression.txt / .json |
| JS/TS | workbench/phase2/hardening syntax与Remotion TypeScript通过 | BUILD_VERIFICATION.json |
| DAG与Evidence negatives | 循环/self-dependency/consumer/optional；span/hash/unsupported绑定/复发失效/claim type/H2 | vnext/tests/test_phase2_hardening.py |
| Provider / Cost / Budget / Fallback | unsupported protocol、schema retry/cache追加、Unknown、并发预留、ASK/DISABLED、VideoQA veto | 同上 |
| RVC/Audio/Geometry/Relink | deterministic outputs、同Preview/Render props、physical audio hash/duration、所有权、碰撞和missing/hash relink | 同上 |
| 实际短渲染 | Director估时{diagnostic['director_estimate']}秒→音频{diagnostic['duration']}秒/{diagnostic['frames']}帧；角色+Check元素+单行字幕真实输出 | DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.mp4 / .png |
| 正式生产负例 | Mock音被VOICE_PRODUCTION_NOT_ACCEPTED否决；短片仅诊断fixture | DIAGNOSTIC_REPORT.json |
| 浏览器 | 架构检查中文/English、unsupported provider truth、保留未提交预算/JSON/operation；旧Player播放/暂停 | UI_ZH.png / UI_EN.png / PREVIEW_COMPATIBILITY.png |
| 历史保护 | 2原项目config/artifacts/stages/logs哈希相同；85 pack文件未变；3冻结ZIP SHA未变 | READONLY_PROTECTION_REPORT.json |

短诊断在temporary Store执行，直接Remotion CLI渲染作为fixture，不绕过正式Gate宣称成片。不是用户项目、不是克隆口播、不是60–90秒production pressure test。Preview/Render输入完全一致与投影只读已验证；本轮没有重新完成所有浏览器/编码像素级比较，旧CAP023报告的SSIM证据单独保留。

UI中央字典两种语言各{keys}个key，{tokens}个canonical token；key集合一致。新增“架构检查”面板显示Provider/Voice truth、成本、预算、manifest和产物三个状态，提供owner校验的strict/Evidence/CandidateDecision/AudioMap/Relink/Research操作。JSON合同编辑仍是工程控制台体验，并非完整向导。

## 继续使用与交接

本机：`CONTENT_OS_DATA=phase2_preview_data .venv/bin/python -m uvicorn vnext.apps.workbench.server:app --host 127.0.0.1 --port 8766`；新机器见README。模型密钥仅backend环境变量，程序不会自动读取.env。

新strict任务先显式“启用严格合同”，登记Source/Evidence/Fact/ClaimUnit v2，经覆盖判定和独立Audit/H2后设计IR、RVC和预配音Storyboard，批准分镜再执行真实Voice或导入与脚本对应的Voice，创建有效AudioMap后重建EDT并重新审查受影响画面。没有timestamp时必须提交可验证alignment，不靠估算放行。

本交付为单用户localhost；actor校验不是账户认证或多租户授权。本轮没有真实发布、反向剪映导入、高级NLE、调色、多机位、AE动画、云协作、新Pack或AI字体。既有剪映版本验收保留历史证据，未在本轮重做原生编辑；字体/阴影等导出损失未消失。原11项IMPLEMENTING不会被此报告掩盖。

收敛后停止扩系统。下一轮应使用真实模型、获得授权且配置可执行的真实克隆声音、真实资料做60–90秒压力测试；只修该测试实际暴露的问题。本轮未提前替用户执行或宣称该测试通过。
'''
closure.write_text(report)
(ROOT/'HARDENING_WORK_STATE.md').write_text(f'# Phase 2 Architecture Hardening 当前交接\n\n2026-09-27，本轮bounded范围已完成。{count}项当前回归、12项冻结Phase1回归通过；短诊断{diagnostic["duration"]}秒实际渲染。源码仍为原Phase2项目。真实provider/clone/VideoQA live验证均为0。\n\n完整现状见CONTENT_OS_VNEXT_PHASE2_CLOSURE_REPORT.md、CAPABILITY_ROADMAP.json、DEPENDENCY_GRAPH.json、PROVIDER_CAPABILITY_MATRIX.json。原项目/Pack/冻结ZIP保护证据见examples/hardening/READONLY_PROTECTION_REPORT.json。\n\nStop Condition：不进入Phase3，不继续添加抽象能力。后续真实60–90秒压力测试尚未执行。\n')
print(json.dumps({'tests_passed':count,'status_counts':dict(status),'i18n_keys':keys,'canonical_tokens':tokens}))
