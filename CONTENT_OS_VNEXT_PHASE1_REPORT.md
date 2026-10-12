# Content OS vNext · Phase 1 交付与验收报告

日期：2026-09-26  
状态：**架构与六个基础运行里程碑已完成本机验收，其中模型与声音链使用 Mock。** 剪映原生工程已在本机 11.5.0-beta5 中打开、编辑、保存后重开，并导出含有效音轨的诊断视频；这不代表所有剪映版本或全部特性兼容。

## 1. Legacy 基线与隔离

Legacy 来源：`${EXTERNAL_VOLUME}/AI味检测/xiao-y-remotion-calibration/content-os-core-with-xiao-y-hd-assets`。该目录作为只读迁移源，vNext 不导入其运行时代码、不向其中写入文件，也不覆盖历史 Artifact。vNext 使用自己的 Python 包、SQLite、HTML 工作台、素材包和 Remotion 工程。当前目录不是 Git 仓库，因此采用独立目录隔离，没有创建分支。

迁移输入包含 Core v0.1.3.2、AR-0004、VM-0003、XVT、VBP、Legacy Voice 配置以及 Remotion 参考工程。迁移脚本先验证 AR-0004 manifest，再复制 **48 个 XACT PNG 和 33 个 Element SVG**，复制后再次逐项验证 SHA-256；81 项全部匹配。另复制角色母版，并将 Character、Style、Element、Template、Voice Profile 分开注册。原始 PNG/SVG 无需重新生成或修改。`migration/LEGACY_MIGRATION_RESULT.json` 保存逐文件结果。Legacy Voice 的模型和运行环境未迁移，注册状态为 `UNAVAILABLE`。

Legacy 原测试在本轮开始时运行：**480 passed, 1 failed**。失败项是 `tests/test_remotion_calibration.py::test_all_original_project_files_and_tests_byte_identical`：早期 `BASELINE_VERIFICATION.json` 固定了 README.md 的旧 SHA，但现有 README.md 已被后续生产工作更新，因而哈希不符。这是当前 Legacy 输入自身的回归状态；vNext 未修改该文件，也未为通过测试而覆盖历史快照。

## 2. 实现范围

| 层 | Implemented | Tests / evidence | Known issues / Deferred |
|---|---|---|---|
| Architecture | `ARCHITECTURE.md`、`WORKFLOW_CONSTITUTION.md`；Role 与 Worker 分离；EDT 为时间线真相源；Legacy 隔离 | 源码层无 Legacy 运行时依赖 | 复杂组织级权限不在 Phase 1 |
| Contracts | 统一 Pydantic 契约及导出的 JSON Schema：Role、Model/Voice/Tool Gateway、Artifact、Project、Character、Style、Element、Voice Profile、Media Asset/Selection、EDT、DirectorPlan、Job、Rule、Error Candidate | JSON Schema 元检查通过 | 特定 Provider 的多模态映射待实现 |
| Storage / Artifact Graph | SQLite 投影、不可变版本文件、append-only 项目事件/错误事件/规则事件、依赖哈希与自动 STALE、单写者保护 | 修订、历史文件不变、STALE、权限测试通过 | SQLite 提交与 JSONL 追加暂非单一原子事务 |
| Gateway / Runtime | OpenAI-compatible Chat Completions 真适配器；DeepSeek/Doubao/OpenAI/GLM/MiniMax 配置状态；结构化 JSON 验证与最多一次修复；Mock；Capability Filter；内容寻址模型缓存；持久化 Job | 模拟真实 HTTP 适配、重试、缓存、幂等测试通过 | 未使用真实 API Key 做在线调用；Anthropic/Gemini 原生协议、多模态、工具调用映射待实现；Job 同步执行 |
| Script / H2 / Audit | TXT/MD/DOCX/PDF 导入、显式导入模式、人工编辑新版本、Mock 独立审计、FAIL 与 PASS_WITH_RISK/H2 门禁、Director 仅消费锁定脚本 | API 链路及风险确认测试通过 | AI 润色/重写模式只记录意图，尚未自动执行；Mock 审计不具备事实判断能力 |
| Governance | 错误候选由各部门提交；Evolution/08 唯一写 error/rule ledger；归一化重复摘要关联原 error_id；规则生命周期和 CURRENT_RULES；下一次 Role Run 读取有效规则 | 单写者、复发、规则生命周期、下一轮读取测试通过 | 复发判断目前是确定性摘要归一化，不做语义相似自动合并；无登录/RBAC |
| Media / Voice | 关联素材文件夹、SHA 身份、元数据、缩略图、前 30 秒视频代理、原素材保留、按哈希重新定位；Mock Voice Gateway 生成 WAV 并注册为音频素材 | 图片关联/重定位、WAV 检查、Voice→EDT→MP4 音轨测试通过 | Mock 是测试音而非口播；真实本地或云 TTS、完整视频语义索引待实现 |
| EDT / Render | 修订式时间线；Move/Trim/Split/Delete/Duplicate/Replace/Lock/Hide/Mute/Marker/Snap/Undo/Redo；预检；EDT→Remotion 静帧与 MP4 | 实际 PNG、MP4 生成，FFprobe 检出音频流；TypeScript 类型检查通过 | Undo/Redo 为基础版本；高级 NLE、字体/特性全量预检待完善 |
| Workbench / i18n | 本地 HTML 控制台；顶栏项目/角色/风格/声音/渲染/语言；13 个流程节点与 Labs；主工作区、检查器、Jobs/Logs/History；中英文字典；三个独立语言字段 | 浏览器实际创建项目并选择角色；JS 语法检查通过 | 若窗口很窄，布局仍以桌面宽度为主；未做完整无障碍审计 |
| Jianying | EDT → 原生 JSON 草稿 + 原媒体/source range + VOICE + 可编辑文字/字幕 + 基本变换；转移侧文件与降级报告；EXPORT Artifact | 本机剪映 11.5.0-beta5 打开/编辑/保存后重开通过；实际导出 4 秒 MOV，检测到非静音 AAC 音轨；原生映射测试通过 | 字体样式近似；crop/motion/reveal/锁定未完整映射；其他版本未验收；每个新导出仍需视觉检查 |

## 3. 六个运行里程碑

1. **Workbench Shell：通过。** 中文/EN 切换、项目创建、XIAO-Y Character/Style/Voice Pack 选择、Workflow 节点、Worker Capability Filter、Provider 状态、Artifact Revision、H2、媒体文件夹、空 EDT、Jobs/Logs 均可用。更换 Worker 生成新的 `ROLE_ASSIGNMENT_<ROLE>` Artifact 修订。
2. **Script → H2 → Director → EDT → Remotion：通过。** Mock Director 输出符合 DirectorPlan Schema，Remotion 使用 EDT props 渲染出真实静帧。
3. **Voice → EDT → Preview：通过（Mock）。** Mock Voice 生成 WAV，作为音频素材进入 VOICE 轨；Remotion MP4 中检测到音频流。它不代表真人声音质量或真实 TTS 接通。
4. **Media Library Minimum：通过。** 本地目录链接、图片/视频注册、Asset ID、SHA、元数据、缩略图、短代理、预览、手动选择和哈希 Relink 均已实现。
5. **Lightweight Timeline：通过基础验收。** Media/Character/Text/Subtitle/Voice 轨存在，Move、Trim、Split、Replace、Undo、Redo 可通过 UI/API 工作；高级剪辑和更深层 Undo/Redo 行为未验收。
6. **Jianying Native Project POC：通过本机基础验收。** 使用用户提供的 `${EXTERNAL_VOLUME}/剪映草稿/JianyingPro Drafts` 作为只读结构参考；只新建验收草稿，没有覆盖原草稿。本机 `${EXTERNAL_VOLUME}/VideoFusion-macOS.app` 实际显示剪映专业版 11.5.0-beta5。原生导出工程已打开，文字被人工改为“Content OS — 编辑验收通过”，关闭重开后保持修改。另一个工程直接引用 6 秒诊断原视频的 2–4 秒及测试音的 1–3 秒，文字和字幕保持独立可编辑轨；导出 4 秒 MOV 后检测到 H.264 + AAC，音频 mean -27.1 dB / max -21.0 dB。详见 `JIANYING_NATIVE_POC_REPORT.json`。每次新导出默认 `native_project_open_verified=false`，只有经过实际 UI 验证的样例报告为 true，避免把 writer 验证当成每个项目已验证。

## 4. 测试与产物

本轮 vNext 自动化结果：`pytest vnext/tests -q` **12 passed**（交付目录中最终复测通过）；Workbench JS 语法检查通过；Remotion TypeScript 类型检查通过。集成测试实际走 HTTP 项目创建、Mock Audit、H2、Director、EDT、PNG、MP4、Mock Voice 音轨和 API Key 不出现在浏览器响应。旧 Legacy 测试单独保留，不与 vNext 测试目录混用。

样例产物：`examples/PHASE1_MINIMAL_PREVIEW.png`、`examples/PHASE1_MOCK_TONE_PREVIEW.mp4`、`examples/ContentOS_NATIVE_AUDIO_ACCEPTANCE.mov`；前两项由 EDT→Remotion 真实生成，声音为测试音；第三项由剪映原生工程真实导出。`examples/jianying_source_media/` 为人工生成的测试图案视频和测试音，可用 `python -m vnext.exporters.jianying.demo` 在新机器重新生成草稿，避免沿用旧绝对素材路径。

主要产物：`contracts/*.json`、`registries/*`、`assets/*`、`migration/LEGACY_MIGRATION_RESULT.json`、`vnext/`、`README.md`。用户数据默认在运行时 `data/` 生成，不打包进源码。浏览器追加验收确认：时间线位置编辑生成 EDT v4，并将旧 Render 标记 STALE；重新渲染生成 READY 的 Render v2；点击“导出剪映原生草稿”后创建 READY 的 EXPORT v1 和完成的导出 Job。

每个项目的事件历史位于 `data/projects/<project_id>/events.jsonl`，错误和规则日志位于其 `audit/` 子目录。

## 5. 仍需后续阶段处理

- 剪映其他版本兼容、字体/裁剪/动画/锁定映射、更全面的原生导出回归；保留 EDT 单向出口，不回写剪映。
- 真实 DeepSeek/Doubao/OpenAI/GLM/MiniMax 在线适配验证；MiniMax 视频审计、Anthropic/Gemini 原生协议、Tool Gateway 外部搜索/截图实现。
- 真实本地/云 TTS、声音授权与声线质量验收；完整 ASR、语义素材索引、Web 证据搜索。
- 异步队列、取消/重试、预算门禁和实际费用；数据库与 JSONL 的更强事务恢复；更完整的快照/Undo/Redo。
- H1/H3/H4 与完整发布链、自动平台发布、账号与团队权限；Phase 1 不开始自动生产 4 分钟视频。

验收建议：先按 `README.md` 在本地启动，检查新建项目、Mock 链、XIAO-Y 素材包和规则读取。剪映原生 POC 的本机基础验收已补齐；真实模型、真实口播、高级剪辑和全版本剪映兼容仍留待后续阶段。
