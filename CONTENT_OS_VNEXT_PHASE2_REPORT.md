# Content OS vNext Phase 2 — 实现与验收报告

> 本文件保留原22项 Preview 验收范围；2026-09-26增量的 CAP-023/CAP-024、78项测试和实际UI/短片证据见 `CONTENT_OS_VNEXT_PHASE2_CLOSURE_REPORT.md`。最终状态以24项Roadmap为准。

当前交付是可运行的 Phase 2 Preview。22 项均已登记；部分核心实现可验收，仍有 IMPLEMENTING 项，不能宣称 Phase 2 全部完成。没有进入 Phase 3，也没有制作正式 4 分钟视频。

## 可复查证据

- 60 秒诊断项目：`PRJ-b417f4c7957a`；视频、12张分镜、Source/Fact/IR/EDT/QA/Review 样本在 `examples/phase2/`。
- 字体项目：`PRJ-3e7963af47cc`；三种字体家族、五个文件、多字重、Italic/TTC/Variable，PNG 和10秒 MP4。
- 所有模型是 MOCK；440Hz 测试音不是口播。H2、Storyboard、诊断 H3 为 SIMULATED TEST FIXTURE，不代表用户批准。
- 独立审计的失败是受控 Mock Finding；修复后新版本再审验证 Gate 合同，不能作为模型实际识错质量证明。分镜 REJECT→APPROVE 验证阻断和路由，没有伪称实际完成视觉返工。
- 中途激活08规则后，旧主稿和Editor阶段正确 DIRTY；修复后的Script / Audit / H2 / Director及下游有效。
- 测试：55 项自动化测试通过；包含12项Phase1回归。JavaScript语法和Remotion TypeScript检查通过。Starlette/httpx有一条弃用提示。详见验证日志。
- Legacy没有在本轮原地执行测试；Phase1曾记录的Legacy测试结果不能当作本轮新结果。

## 闭环与权限

生产角色提交 ERROR_CANDIDATE，只有08确认后追加 Error Ledger；同规范化摘要复发关联旧error_id，重复确认同candidate保持幂等。规则生命周期和四类规则集只由08写入，RULE_CATALOG将所有有效规则编译为生产依赖，防止第一次激活规则未使旧快照失效。
Root cause支持DATA/MODEL/TOOL/PROCESS/HUMAN/UNKNOWN。Blind Review只传原资料、事实、候选文本与审查标准，不传主模型解释或其他审计意见。FAIL自动创建责任Owner的Change Request，H2被否决；PASS_WITH_RISK需要明确接受风险。
本地权限为模块/角色校验和UI写入面，适用于可信单用户localhost。尚没有账户身份验证、用户级授权或多租户隔离；不能将此开发服务公开部署并声称具备用户身份安全。

## 21 CAPABILITY ACCEPTANCE MATRIX + CAP-022

每项的Contract、UI、Artifact、Tests、Known limitations和Deferred如下；READY只覆盖明确描述的有限能力。

### CAP-001 Writing Rules · READY

- **Implemented?** 08 版本化规则、下一轮快照读取、HARD 防覆盖已实现
- **Contract?** contracts/WRITINGRULE_SCHEMA.json, contracts/RULESET_SCHEMA.json
- **UI?** 08 正式规则 JSON 编辑器；其他页面只读
- **Artifact?** WRITING_RULE_SET / RULE_CATALOG
- **Tests?** `test_hard_override_and_soft_resolution`, `test_rule_set_revision_is_append_only_and_next_snapshot_reads_it`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 没有自动规则推荐；规则为项目级，跨项目继承待实现
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-002 Hook Rules · READY

- **Implemented?** 七种 Hook 类型和约束进入生产上下文
- **Contract?** contracts/HOOKRULESET_SCHEMA.json
- **UI?** 08 Hook 配置；生产读取快照
- **Artifact?** HOOK_RULE_SET
- **Tests?** `test_rule_set_revision_is_append_only_and_next_snapshot_reads_it`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 模型是否写出高质量 Hook 仍需真实审计与人工判断
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-003 Retention Rules · IMPLEMENTING

- **Implemented?** 规则快照、Beat retention_function 和分层 reveal 已接通
- **Contract?** contracts/RETENTIONRULESET_SCHEMA.json, contracts/BEAT_SCHEMA.json
- **UI?** 08 配置；Director 表显示 reveal / retention
- **Artifact?** RETENTION_RULE_SET / DIRECTOR_IR
- **Tests?** `test_hard_override_and_soft_resolution`, `test_director_ir_missing_slot_no_pixels_and_owner`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 尚未完整实现规则驱动的节奏优化与全部复杂转场；不能保证留存效果
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-004 Editorial Voice · READY

- **Implemented?** 文风与声音配置分离并版本化
- **Contract?** contracts/EDITORIALVOICEPROFILE_SCHEMA.json
- **UI?** 08 文风配置；Script 快照只读
- **Artifact?** EDITORIAL_VOICE
- **Tests?** `test_rule_set_revision_is_append_only_and_next_snapshot_reads_it`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 此能力不合成音频；真实本地配音执行器未迁入
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-005 Humanize Integrity · IMPLEMENTING

- **Implemented?** 保守数字、实体、极性、Fact 绑定变化检测；新版本必须重审
- **Contract?** contracts/BOUNDSCRIPT_SCHEMA.json
- **UI?** 事实 / 脚本页 Humanize；BLOCKED / 审计状态
- **Artifact?** SCRIPT / AUDIT / SCRIPT_GATE
- **Tests?** `test_humanize_numeric_change_blocks_h2`, `test_blind_review_rejects_other_opinions_and_h2_mock_risk`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 代码不能证明自然语言语义等价；规则覆盖有限；Doubao 真实调用未验收
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-006 Layered Skills · IMPLEMENTING

- **Implemented?** 六层解析顺序、HARD 禁覆盖、SOFT 覆盖记录、生产快照依赖
- **Contract?** contracts/SKILLLAYER_SCHEMA.json, contracts/EFFECTIVESKILLSNAPSHOT_SCHEMA.json
- **UI?** 阶段 / 历史显示版本、层次和覆盖
- **Artifact?** EFFECTIVE_SKILL_SNAPSHOT_<ROLE>
- **Tests?** `test_hard_override_and_soft_resolution`, `test_role_run_keeps_run_layer_snapshot_and_does_not_resolve_over_it`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** ROLE / PROJECT / CHARACTER_STYLE 层可通过请求传入，尚无完整图形化管理与自动目录装载
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-007 Fact Pack / Source Ledger · READY

- **Implemented?** 必填、来源存在性、Fact ID、SUPPORTED、数值引用、来源变更传播
- **Contract?** contracts/FACTPACK_SCHEMA.json, contracts/SOURCE_SCHEMA.json, contracts/BOUNDSCRIPT_SCHEMA.json
- **UI?** 事实 / 脚本页；JSON 新版本
- **Artifact?** FACT_PACK / SOURCE_<ID> / source_ledger.jsonl
- **Tests?** `test_source_ledger_append_and_selective_source_revision`, `test_bound_script_negative`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 来源证据由用户提供；没有自动联网采集，也不证明来源内容本身真实
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-008 Scene · READY

- **Implemented?** 场景职责、脚本范围、时长和 Beat 成员校验
- **Contract?** contracts/SCENE_SCHEMA.json, contracts/DIRECTORIR_SCHEMA.json
- **UI?** 导演表 Scene / Beat 分组
- **Artifact?** DIRECTOR_IR.scenes
- **Tests?** `test_director_ir_missing_slot_no_pixels_and_owner`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** Scene 为 IR 内正式对象，不是独立数据库实体；分组质量需审查
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-009 Beat · READY

- **Implemented?** 脚本段、场景、Pattern、视觉重点、时长、Reveal 可追溯
- **Contract?** contracts/BEAT_SCHEMA.json, contracts/DIRECTORIR_SCHEMA.json
- **UI?** 导演表逐 Beat 修改
- **Artifact?** DIRECTOR_IR.beats
- **Tests?** `test_director_ir_missing_slot_no_pixels_and_owner`, `test_media_lock_and_source_range_survive_ir_generation`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 词级音频对齐和完整 phrase 生成待实现
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-010 Director + Design Table · READY

- **Implemented?** IR 是语义真源；设计表为投影；改表形成新 IR 和命令
- **Contract?** contracts/DIRECTORIR_SCHEMA.json
- **UI?** 导演 / 分镜表；Pattern / Keyword / Motion / Slots 编辑
- **Artifact?** DIRECTOR_IR + derived design_table
- **Tests?** `test_edit_owner_revision_conflict_and_font_undo_redo`, `test_director_ir_missing_slot_no_pixels_and_owner`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 高级卡片编辑仍是 JSON Slots；部分导演意图仅供审查
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-011 Visual Pattern Library · IMPLEMENTING

- **Implemented?** 八个具名 Pattern、必填 Slots、基础版式、文字 Reveal
- **Contract?** contracts/VISUALPATTERN_SCHEMA.json
- **UI?** 八种 Pattern 下拉选择；真实分镜
- **Artifact?** DIRECTOR_IR / EDT / registry
- **Tests?** `test_director_ir_missing_slot_no_pixels_and_owner`, `test_media_lock_and_source_range_survive_ir_generation`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** ACTION_SEQUENCE、SCREEN_DETAIL 等仍为基础表达；尚未完整实现动作逐项切换、对象跟踪和高级布局
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-012 Director IR · READY

- **Implemented?** ID/成员/脚本/时长/Pattern 约束，禁止像素和字体绑定
- **Contract?** contracts/DIRECTORIR_SCHEMA.json
- **UI?** 导演 JSON / 表格；只读版本历史
- **Artifact?** DIRECTOR_IR
- **Tests?** `test_plain_import_cannot_bypass_bound_script_and_director_has_no_font_ids`, `test_director_ir_missing_slot_no_pixels_and_owner`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 转场与 Slots 部分为开放字典；复杂语义需人工审查
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-013 Timeline Canonical Model V2 · READY

- **Implemented?** Scene/Beat/IR/Origin/EditSource/Pattern provenance；V1 保守升级；原素材范围保留
- **Contract?** contracts/EDT_SCHEMA.json, contracts/EDTCLIP_SCHEMA.json
- **UI?** 多轨时间轴；来源和版本信息
- **Artifact?** EDT / VISUAL_EDT
- **Tests?** `test_edt_v1_upgrade_preserves_ranges_and_does_not_infer_bindings`, `test_media_lock_and_source_range_survive_ir_generation`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** V1 无法自动补出语义绑定；迁移由离线工具显式执行；高级 NLE 不在本轮
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-014 Unified Edit Commands · IMPLEMENTING

- **Implemented?** Script/IR/EDT/MediaSelection/Typography 共用命令、乐观版本检查、多步 Undo / Redo
- **Contract?** contracts/EDITCOMMAND_SCHEMA.json
- **UI?** 时间轴、Director 和 Typography 编辑；Undo / Redo
- **Artifact?** EDIT_COMMAND / edit_cursors / append events
- **Tests?** `test_multi_step_undo_redo_and_new_edit_clears_redo`, `test_edit_owner_revision_conflict_and_font_undo_redo`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** Sources、Facts、正式规则与 Config 仍走各自拥有者版本 API；模型生成已记命令，但所有生成动作尚未接入撤销栈
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-015 Asset Intelligence · IMPLEMENTING

- **Implemented?** 真实 ffmpeg 场景/关键帧；标注及人工 Transcript 检索；可选本地向量适配器；显式 M3 图像描述接口
- **Contract?** contracts/MEDIAASSET_SCHEMA.json, contracts/VIRTUALCLIP_SCHEMA.json
- **UI?** 素材页本地切分、标注、隐私与检索
- **Artifact?** ASSET_INTELLIGENCE_<ID> / keyframes / virtual_clips
- **Tests?** `test_asset_privacy_scene_caption_transcript_and_optional_semantic_search`, `test_media_caption_retains_model_provenance_and_changed_original_blocks`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 自动 ASR 未实现；本地向量模型未安装，真实模型未验收；自动描述无 UI 按钮；关键帧最多20，云描述最多3
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-016 Stage Cache · IMPLEMENTING

- **Implemented?** 输入、配置、Worker、Prompt、Skill Hash；缓存、DIRTY、失败续跑；历史主稿仅供 Editor 回放
- **Contract?** contracts/STAGESTATE_SCHEMA.json
- **UI?** 阶段 / 历史十四阶段
- **Artifact?** STAGE_<NAME> / rebuildable SQLite projection
- **Tests?** `test_stage_cache_late_resume_rebuild_and_input_change`, `test_stage_resume_reuses_primary_after_editor_supersedes_canonical_script`, `test_stage_running_is_live_and_replacing_input_does_not_stale_own_stage`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 没有全自动调度器、后台队列、取消；部分检查为 fresh record；各阶段由用户/API 发起
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-017 Storyboard Gate · READY

- **Implemented?** 同版本所有 Beat 获批才能配音/渲染；音频加入不误失效；视觉变更必须重审
- **Contract?** contracts/DIRECTORIR_SCHEMA.json, contracts/ARTIFACT_SCHEMA.json
- **UI?** 每 Beat 真实起止帧；批准/退回；部分批准 API
- **Artifact?** STORYBOARD / STORYBOARD_GATE / CHANGE_REQUEST
- **Tests?** `test_storyboard_gate_is_visual_specific_and_new_ir_invalidates`, `test_storyboard_rejection_routes_to_director`, `test_storyboard_partial_approval_accumulates_only_for_same_board`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 当前自动诊断的审核人均为模拟；UI 以全量批准为主；局部批准使用 API
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-018 Mechanical QA · IMPLEMENTING

- **Implemented?** Fact/依赖/H2/素材/音频/字幕/字体/重叠字幕/静帧/持久Header 等基础确定性检查
- **Contract?** contracts/QAREPORT_SCHEMA.json
- **UI?** QA 页机械检查与 Owner Finding
- **Artifact?** MECHANICAL_QA / CHANGE_REQUEST
- **Tests?** `test_mechanical_qa_subtitle_and_voice_veto`, `test_font_snapshot_glyph_strict_fallback_missing`, `test_visual_binding_change_stales_edt_but_interface_language_does_not`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 尚无所有元素的几何碰撞、安全区及复杂信息密度检查；动作/运动表现检查仍有限
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-019 MiniMax Visual QA · IMPLEMENTING

- **Implemented?** M3 视频输入映射；先机械 QA；时间戳/Owner 输出校验；FAIL 只退回不改稿；本地隐私策略阻断上传
- **Contract?** contracts/MODELREQUEST_SCHEMA.json, contracts/CONTENTBLOCK_SCHEMA.json, contracts/QAREPORT_SCHEMA.json
- **UI?** QA 页 Mock / MiniMax Worker、健康状态及上传确认
- **Artifact?** VIDEO_QA / CHANGE_REQUEST
- **Tests?** `test_minimax_gateway_maps_video_and_never_uploads_local`, `test_videoqa_veto_timestamp_privacy_and_review_freshness`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 真实请求未运行，无 API key；本轮全部视频审查结果为 Mock；视频内联大小受限
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-020 Review Pack · READY

- **Implemented?** 引用原产物 ID/hash、Script diff、QA/字体/导出损失、过期阻断；H3 与发布权限分离
- **Contract?** contracts/ARTIFACT_SCHEMA.json, contracts/QAREPORT_SCHEMA.json
- **UI?** QA / 终稿页；引用列表与风险确认
- **Artifact?** REVIEW_PACK / REVIEW_GATE
- **Tests?** `test_videoqa_veto_timestamp_privacy_and_review_freshness`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** H3 自动诊断只是模拟；vNext 的 H1/H4 正式界面与平台发布 API 尚未实现
- **Deferred?** 没有本项核心阻断；限制如上。

### CAP-021 Jianying Exporter · IMPLEMENTING

- **Implemented?** 原素材/范围、独立文字、音轨、静态变换；白底主轨避免磁吸吞空档；EXACT/APPROXIMATED/UNSUPPORTED
- **Contract?** contracts/EDT_SCHEMA.json, contracts/VIRTUALCLIP_SCHEMA.json
- **UI?** Render 原生导出按钮；损失报告
- **Artifact?** EXPORT / native draft / transfer sidecars
- **Tests?** `test_native_canvas_preserves_foreground_gaps_and_reports_font_losses`, `test_native_export_original_ranges_audio_text_and_degradation`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 本机11.5-beta5可打开/编辑/保存/重开/导出；字体和阴影未映射；裁切/运动/Reveal/锁定不完整；其他版本及反向导入未实现
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

### CAP-022 Font Intelligence / Typography System · IMPLEMENTING

- **Implemented?** TTF/OTF/TTC faces、变量轴、hash/缺字/fallback、八角色、命令撤销、同字体缓存字节供浏览器和 Remotion；三字体完整诊断
- **Contract?** contracts/FONTRECORD_SCHEMA.json, contracts/FONTROLE_SCHEMA.json, contracts/TYPOGRAPHYPROFILE_SCHEMA.json
- **UI?** 字体页扫描/导入/搜索/分类/来源筛选/排序/五角色实时预览/Undo/Redo；Apply 后正式写入
- **Artifact?** FONT_REGISTRY cache / TYPOGRAPHY_PROFILE / PROJECT_FONT_SNAPSHOT
- **Tests?** `test_fonts_scan_cache_ttc_duplicate_faces_and_hash_changes`, `test_font_snapshot_glyph_strict_fallback_missing`, `test_edit_owner_revision_conflict_and_font_undo_redo`, `test_phase2_http_permissions_and_font_preview_is_read_only`。测试位于 `vnext/tests/`；真实渲染另有脚本证据。
- **Known limitations?** 尚无预设切换及可搬迁字体依赖包；剪映会替换字体但已明确报告；不分发系统字体文件
- **Deferred?** 是，上述缺口保留在当前Phase 2，未冒充完成。

## 原生剪映与字体

本轮新草稿：`${EXTERNAL_VOLUME}/剪映草稿/JianyingPro Drafts/ContentOS-EXP-3e9232ba31`。
剪映11.5.0-beta5原生UI已验证打开、独立文字修改、保存、重开和本地视频导出；准确结果以 `examples/phase2/JIANYING_NATIVE_REGRESSION_RESULT.json` 为准。编辑后的Native文字仅留在导出工程，未反向修改Content OS的Script/IR/EDT。
原始EXPORT不可变，初次生成时native_project_open_verified=false。后续人工/UI验证另存证据，不回写历史JSON。字体/阴影损失仍为UNSUPPORTED，尺寸字重间距为APPROXIMATED；可编辑不等于与Remotion画面完全一致。
本地字体字节只存在用户数据缓存，不进入源码压缩包、不上传模型、不自动安装商业字体。样本的绝对路径为本机证据，复制到另一台机器后需要重新扫描字体、Relink素材和重跑。

## 真实模型配置与证据边界

Backend only环境变量见README和.env.example。OpenAI-compatible文本接口已提供，可为Research/Primary/Editor/Audit/Director选择Worker。未配置Worker显示不可用，不静默转Mock。真实提供商可用性和输出质量未被本次Mock验证覆盖。
MiniMax M3 IMAGE/VIDEO映射按[官方OpenAI兼容API文档](https://platform.minimax.io/docs/api-reference/text-openai-api)实现，合同测试使用网络Stub；本次没有上传视频或调用真实MiniMax。LOCAL_ONLY阻断，ASK_BEFORE_UPLOAD需项目与素材允许且单次明确确认。
本地sentence-transformers适配器仅允许已安装本地模型目录，不自动下载。当前未安装该可选依赖和模型，检索演示默认人工标注/Transcript关键词匹配。自动ASR仍缺失。

## 仍需继续的Phase 2工作

优先关闭Visual Pattern完整表达、Mechanical几何/安全区检查、全编辑命令及全阶段调度、CAP-022预设/筛选/可搬迁依赖体验，再以真实模型和真实配音验收。H1/H4、平台发布接口、后台任务队列、反向剪映导入不在本轮已完成范围。
CREATIVE_POLICY仍最高；Analytics只产观察/假设，不升级规则。没有发布授权，也没有任何平台发布。用户实际Storyboard/H3验收待执行。
