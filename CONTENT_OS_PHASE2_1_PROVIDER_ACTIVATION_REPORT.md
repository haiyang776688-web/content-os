# Content OS Phase 2.1 Provider Activation · 当前增量状态

更新2026-09-28：当前XIAO-Y动态讲解第5版分镜已获用户批准，Gate ART-1161bdc7bf2b4403 已登记。正式1080p成片 ART-af53e1287e9e44c8 已生成（84.821秒），机械QA v3 PASS，工作台已完整播放至结尾。用户允许当前13张图片的限定上传及一次MiniMax无声视觉审查；真实Video QA ART-c16619f572da4846 返回PASS_WITH_RISK，终审包ART-3c05fee5a13d41b6已生成。复核发现模型唯一WARNING所称时段与画面不符。用户回复“通过”后，H3 ART-98b97704be3f4aa2 已按APPROVE_WITH_RISK登记；H4未授权，未发布。189项全量测试通过。详见CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md与examples/activation/style_review/FORMAL_REVIEW.md。下列原Provider验证记录是先前实测历史。

## 先前Provider接入与配音记录（历史快照）

# Content OS Phase 2.1 Provider Activation 实施报告

日期：2026-09-27。范围：在现有 Phase 2 Hardening 源码和数据库上增量实施，未进入 Phase 3。普通用户的正式入口为 Workbench → 设置；配置、角色、隐私、费用和声音全部通过 GUI 操作。

## 当前结果

Provider Activation 的基础功能已实现并真实验证：DeepSeek、豆包、GLM、MiniMax 文本/结构化调用成功；MiniMax 视频输入烟测成功；多条自定义 OpenAI-compatible 服务的注册、Keychain、连接测试、角色选用和正式研究运行已接通。当前实际自定义服务“小Y 研究备用 · DeepSeek”已通过真实研究验收，并通过 GUI 切回内置 DeepSeek。

2026-09-27的压力测试阶段完成到正式本地配音与配音后分镜：当时第2版Gate ART-afca11ffce3a407e已记录；九段435字完整稿由本机 CosyVoice3 生成，实测84.76秒，所有分段与主音频哈希/时长验证通过。AudioTimingMap ART-de11de6cee654e77、EDT v4 ART-08e3f9d2408649d8将18个节拍重定时并生成14个单行字幕片段。当时第3版分镜 ART-909b326b8e484416 已在浏览器加载。这些是历史版本，当前正式成片与QA状态见上文。

## 实现与验证状态

| 范围 | 状态 | 实际边界 |
|---|---|---|
| 设置中心五页 / 双语 / GUI配置 | IMPLEMENTED、TESTED | 英文与中文、未提交输入、无明文密钥回传 |
| macOS Keychain | IMPLEMENTED、TESTED、LIVE_VERIFIED | 实际凭据重启后可继续读取，稳定 provider_id 为主键 |
| 四家内置文本服务 | LIVE_VERIFIED | 均真实返回并解析结构化 JSON；并未验证每项声明能力 |
| 自定义 OpenAI-compatible | LIVE_VERIFIED | 真实创建、连接测试、研究角色运行、完整最新产物 provenance |
| MiniMax 视频输入 | LIVE_VERIFIED | 先前烟测通过；2026-09-28当前正式成片无声视觉QA亦完成，返回PASS_WITH_RISK，模型意见已独立复核 |
| 联网搜索与网页快照 | LIVE_VERIFIED | Bing 公共 RSS / FFmpeg 公开页面，资料为 UNTRUSTED_SOURCE_DATA，未自动创建事实 |
| Privacy / Budget / Fallback | IMPLEMENTED、TESTED | 一次性绑定确认，未知费用策略，预算拦截，不降为 Mock |
| 本地克隆声音 | LIVE_VERIFIED | CosyVoice3 正式九段配音84.76秒，物理音频和时钟已核验 |
| MiniMax 原生 TTS | LIVE_VERIFIED | 实际 4.39 秒普通音色试听；未替换本地声音 |
| 豆包原生 TTS | IMPLEMENTED、TESTED | 真实请求 HTTP 401，当前声音权限未验证 |
| 完整 60–90 秒真实生产 | PENDING_RETIMED_STORYBOARD_GATE | 不能以既有 Mock 片或试听代替 |
| 更多协议 / Custom Headers / 跨平台安全存储 | DEFERRED | 私有协议需要 Adapter；不宣称任意 API 自动兼容 |
| 未测试的模型能力 | DECLARED_ONLY / UNKNOWN | 手工声明不等于验证；以能力矩阵为准 |
| 既有 Mock 诊断 | MOCK_ONLY | 明确保留作诊断，不是正式入口强制选择 |

## 本轮真实调用暴露并修复的问题

主模型与润色模型曾产生合并 text / Claim span 合同错误，非法结果未被接纳。增加明确合同说明与仅确定性的派生字段处理：总 text 必须等于段落拼接，声明位置只可从唯一的原句匹配得到，不修改事实、类型或含义。缺失、歧义与不支持的事实仍拒绝。

润色改变措辞后，原有语义保护正确阻断稿件。新增责任部门“提交返工稿”操作，创建新版本、重验 Evidence / Fact / Claim 并要求独立审计；没有解除旧稿 BLOCKED 或自动批准。最新稿 ART-bef1d4cecaf94b5d 已获 ART-8ba25609781440e8 盲审 PASS，19 条声明全部 SUPPORTED。

MiniMax 国际 API 地址对本次凭据鉴权失败，用户 GUI 配置改为中国区后通过。TTS 最初的音色 ID 返回 2054，修正为官方音色 ID 后实际成功；失败仍保留在费用账本。错误音色有独立、脱敏的用户提示。豆包文本与声音权限分开记录，不伪装声音接口可用。

真实导演调用暴露锁定稿件 ID 缺失、虚构素材 ID、模式必填 slot 未约束的输入合同缺口。现已发送精确产物 ID、注册资源清单，并在请求 JSON Schema 中固定脚本、限定资源与模式必填项；没有修改或补造模型返回的业务内容。增加真实协议路径的回归测试，包含虚构引用和缺失 slot 的拒绝。

实际分镜渲染前的机械检查发现三处 character_text_collision：COMPARE_SPLIT 允许小人物，但没有配置专用位置，解析器落回标准左侧人物。现为该既有模板配置下方居中的小人物，未改模板包或放宽 QA；重建 EDT v2 后预配音 preflight PASS、无阻断。EDT 阶段缓存加入布局指纹，修复后不会复用旧布局，旧产物仍保留。新增回归验证真实角色包与两栏长中文均可完整摆放。

人工检查实际分镜后发现白底字幕偏淡，已通过 GUI 仅加强当前任务 SUBTITLE 黑色阴影，保留白字、无底板与固定基线。字体、时间线和分镜均创建新版本；过期分镜在普通页面不再出现批准按钮。

本轮实际配音还暴露 EDT 缓存遗漏首次出现的 AudioTimingMap 与 Visual Config 等输入，导致可能重用导演估计时长。缓存现包含音频时钟、视觉绑定和有效素材选择，无效音频时钟直接阻断；新增两项回归验证首次音频加入、720p配置变化与重复运行缓存，实际GUI已生成84.76秒EDT v4。

本地克隆声音保持本机生成。云视觉 QA 使用无音轨副本，记录原片和审查副本哈希，禁止把本地克隆音轨随成片传到云端；本地机械 QA 仍检查原片音频。

## 保护和回归

179 项当前测试通过，包含原 126 项测试和新增 53 项；未修改旧测试来适配结果。冻结 Phase 1 副本运行 12 项通过、186 个冻结文件不变。Remotion TypeScript 检查及前端语法检查通过。两个受保护旧任务的语义哈希、85 个角色/动作/Elements/模板相关文件保持不变，证据见 examples/activation/PROTECTED_BASELINES.json。实际配置密钥扫描未在项目源码、报告、数据库、日志或产物中发现原文。

原 24 项 Capability 与其 29 节点 DAG 保留基线；扩展登记独立写入 UPDATED_CAPABILITY_ROADMAP.json，CAP-025–028 进入 33 节点无环 DAG。CAP-025、028 为有限范围 READY；CAP-026、027 仍 IMPLEMENTING，Phase 2 仍未整体完成。

## 交付文件

- PROVIDER_LIVE_VERIFICATION.json：实际服务和声音状态快照，不新增调用。
- PROVIDER_CAPABILITY_MATRIX.json：按能力区分 VERIFIED / DECLARED / UNKNOWN。
- CUSTOM_PROVIDER_ACCEPTANCE.json：自定义服务实际研究与完整 provenance。
- SECURITY_SECRET_STORE_REPORT.md：密钥、安全边界和已知限制。
- REAL_WORKFLOW_ACCEPTANCE_REPORT.md：本条真实内容推进与待确认环节。
- UPDATED_CAPABILITY_ROADMAP.json：完整扩展 Capability 登记。
- docs/PROVIDER_SETTINGS_USER_GUIDE.md：普通用户 GUI 使用路径。
- examples/activation/：脚本、回归、联网、保护检查和非敏感运行证据。

本机服务运行于 http://127.0.0.1:8766/。环境变量仅保留开发者、CI、Headless 备用，不是产品日常配置入口。
