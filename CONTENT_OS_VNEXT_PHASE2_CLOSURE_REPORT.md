# Content OS vNext Phase 2 — Architecture Hardening Closure

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
| Current Phase1+Phase2+CAP023/024+Hardening | 126 passed，1条Starlette/httpx弃用提示；其中新增48例 | examples/hardening/current_regression.txt |
| Phase1 frozen regression | 隔离副本12 passed，冻结目录186个文件未变 | frozen_phase1_regression.txt / .json |
| JS/TS | workbench/phase2/hardening syntax与Remotion TypeScript通过 | BUILD_VERIFICATION.json |
| DAG与Evidence negatives | 循环/self-dependency/consumer/optional；span/hash/unsupported绑定/复发失效/claim type/H2 | vnext/tests/test_phase2_hardening.py |
| Provider / Cost / Budget / Fallback | unsupported protocol、schema retry/cache追加、Unknown、并发预留、ASK/DISABLED、VideoQA veto | 同上 |
| RVC/Audio/Geometry/Relink | deterministic outputs、同Preview/Render props、physical audio hash/duration、所有权、碰撞和missing/hash relink | 同上 |
| 实际短渲染 | Director估时10秒→音频2.96秒/89帧；角色+Check元素+单行字幕真实输出 | DIAGNOSTIC_AUDIO_CLOCK_FIXTURE.mp4 / .png |
| 正式生产负例 | Mock音被VOICE_PRODUCTION_NOT_ACCEPTED否决；短片仅诊断fixture | DIAGNOSTIC_REPORT.json |
| 浏览器 | 架构检查中文/English、unsupported provider truth、保留未提交预算/JSON/operation；旧Player播放/暂停 | UI_ZH.png / UI_EN.png / PREVIEW_COMPATIBILITY.png |
| 历史保护 | 2原项目config/artifacts/stages/logs哈希相同；85 pack文件未变；3冻结ZIP SHA未变 | READONLY_PROTECTION_REPORT.json |

短诊断在temporary Store执行，直接Remotion CLI渲染作为fixture，不绕过正式Gate宣称成片。不是用户项目、不是克隆口播、不是60–90秒production pressure test。Preview/Render输入完全一致与投影只读已验证；本轮没有重新完成所有浏览器/编码像素级比较，旧CAP023报告的SSIM证据单独保留。

UI中央字典两种语言各605个key，210个canonical token；key集合一致。新增“架构检查”面板显示Provider/Voice truth、成本、预算、manifest和产物三个状态，提供owner校验的strict/Evidence/CandidateDecision/AudioMap/Relink/Research操作。JSON合同编辑仍是工程控制台体验，并非完整向导。

## 继续使用与交接

本机：`CONTENT_OS_DATA=phase2_preview_data .venv/bin/python -m uvicorn vnext.apps.workbench.server:app --host 127.0.0.1 --port 8766`；新机器见README。模型密钥仅backend环境变量，程序不会自动读取.env。

新strict任务先显式“启用严格合同”，登记Source/Evidence/Fact/ClaimUnit v2，经覆盖判定和独立Audit/H2后设计IR、RVC和预配音Storyboard，批准分镜再执行真实Voice或导入与脚本对应的Voice，创建有效AudioMap后重建EDT并重新审查受影响画面。没有timestamp时必须提交可验证alignment，不靠估算放行。

本交付为单用户localhost；actor校验不是账户认证或多租户授权。本轮没有真实发布、反向剪映导入、高级NLE、调色、多机位、AE动画、云协作、新Pack或AI字体。既有剪映版本验收保留历史证据，未在本轮重做原生编辑；字体/阴影等导出损失未消失。原11项IMPLEMENTING不会被此报告掩盖。

收敛后停止扩系统。下一轮应使用真实模型、获得授权且配置可执行的真实克隆声音、真实资料做60–90秒压力测试；只修该测试实际暴露的问题。本轮未提前替用户执行或宣称该测试通过。
