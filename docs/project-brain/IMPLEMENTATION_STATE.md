# 实现状态核验

> **Open-source archive notice (2026-10-12):** Active development is paused and the public snapshot is based on the validated MDC baseline, not the later P0 GUI experiment branch described below. This file is retained as a dated historical state record. For the publishable current status, use the repository `README.md`, `LOCAL_PROJECT_INVENTORY.md`, and `docs/MAINTAINER_HANDOFF.md`. GUI-001 remains incomplete in the public snapshot.


**核对日期：**2026-09-29。  
本表同时标注 `main` 与活动实现分支 `p0/gui-only-e2e-interim@323f7a2`，避免把分支能力误写成已合入 main。状态含义：
- `IMPLEMENTED`：限定范围的代码与证据存在；
- `PARTIAL`：可用子集存在但未达到完整目标；
- `PLANNED`：设计存在、实现不完整；
- `NOT_STARTED`：未找到可执行实现。

**代码存在 ≠ GUI 可用 ≠ 工程验收 ≠ 创作质量验收。**

| 能力 | 当前代码 / 运行证据 | 实现状态 | GUI / 验收状态 |
| --- | --- | --- | --- |
| Project / Source / Media import | P0 branch Slice 1：新建项目含 topic/content type；file picker / drag-drop；受控 media workspace | **IMPLEMENTED on P0 branch** | **PASS（Slice 1）**；未合 main |
| Fact / Evidence | strict Evidence / Fact Pack / Claim 绑定已有；Track B GUI 人工确认 7 Facts | **IMPLEMENTED（结构与校验）** | **PARTIAL→usable**；完整研究工作台仍未做 |
| Writer / Script revision | P0 branch strict segment editor、Claim↔Fact、formal SCRIPT revision、expected_revision | **PARTIAL**：主链可用；复杂 rebase 未做 | **PASS（Slice 1 / Track B）** |
| Script Editor / Humanizer | 角色与基础合同存在；语义变化退回机制有基础 | **PARTIAL** | Prompt/质量标准仍弱，D-003 OPEN |
| Audit / Red Team | 独立 Audit、Claim review、H2；Track B GLM Audit PASS | **PARTIAL** | 工程路径通过；DeepSeek Red Team 设计定位未落实现（Q-004） |
| Skill / Rule Snapshot | Effective Skill Snapshot、08 写入边界等基础存在 | **PARTIAL** | 生命周期/治理 GUI 未完全闭环 |
| Narrative Scene/Beat | Scene/Beat/Director IR 合同存在 | **PARTIAL** | 能运行，但创作质量未达标 |
| Director / Storyboard | P0 branch Beat cards、SET_BEAT、preview、正式 still job、Gate；当前 Director schema 锁定 template/semantic_pattern，layout 由 Resolver 决定 | **PARTIAL** | **PASS（工程路径）**；创作控制面偏窄；Track B Creative FAIL；D-002/D-003 OPEN |
| Director IR | versioned Scene/Beat/Pattern/Slot | **IMPLEMENTED（当前合同）** | timing ownership 可能被 D-002 改写 |
| XIAO-Y Asset System | 48 actions / 12 templates / 33 elements；Track B 使用；未显式 action_id 时 Resolver 取首个 semantic-intent 匹配 | **PARTIAL** | 一致性可用；存在 deterministic pose repetition；缺 allocator / partial repetition QA |
| Voice | Track B real local `YU_LOCAL_V1`，61.400s | **PARTIAL** | **PASS（Track B）**；长期 registry/consent Q-006 未闭环 |
| AudioTimingMap | 真实 Voice 后建立；Final EDT 使用；segment 真实边界已绑定；1:N segment 内 beat 仍按 timing_intent 比例分配 | **IMPLEMENTED（当前合同）** | Track B 7 segments / 7 beats，因此本次 beat 外边界已音频精确绑定；D-002 评估 anchor vs Audio-first |
| EDT / Timeline | P0 branch Final Editable EDT、visual edit、undo、revision guard、stale invalidation | **PARTIAL** | **PASS（工程路径）**；非完整 NLE |
| Human edit protection | expected_revision、HUMAN_EDITS_PRESENT、explicit discard、stale protection | **PARTIAL** | revision-level 可用；字段级 merge/rebase 未做 |
| Background Jobs | P0 branch in-process thread + SQLite job state、single-flight、orphan→SERVER_RESTARTED、retry、refresh | **IMPLEMENTED（P0 最小合同）** | **PASS（Slice 4a / Track B）**；不是分布式 durable queue |
| Remotion Render | Track B 61.461333s real 1080p/30fps render；当前 Composition 主要为一次性 reveal/slide/scale/marker，缺丰富持续 motion / transition | **IMPLEMENTED（现范围）** | **PASS（Track B 工程）**；视觉词汇是 Content OS 当前实现限制，不是 Remotion framework 限制 |
| Mechanical QA | Track B 检出 MOTION_REPETITION 等；当前不覆盖 partial pose repetition；P0 subtitle renderer 已加深色衬底但 QA metadata 规则仍保留旧约束 | **IMPLEMENTED（现规则）** | **PASS_WITH_RISK**；存在 pixels / metadata truth drift；不代表创作质量通过 |
| MiniMax Visual QA | Track B real MiniMax-M3, VISUAL_ONLY, audio not transmitted；gateway video fps=1 | **PARTIAL** | 静态构图/文字密度/white-space 有实测价值；亚秒 motion/transition/rhythm 证据弱；D-003 OPEN |
| H3 Review | risk list + acknowledgment + APPROVE/APPROVE_WITH_RISK/REJECT | **IMPLEMENTED on P0 branch** | Track B **测试 H3**；不是用户创作批准；H4=false |
| MP4 delivery | browser download + SHA match | **IMPLEMENTED on P0 branch** | **PASS（Track B）** |
| Jianying one-way export | EXPORT + downloadable ZIP + archive integrity | **IMPLEMENTED（bundle generation）** | **PARTIAL**：Track B 未做真实 Jianying-open/edit 验收 |
| Track A | provider-boundary fake + real app path + real short Remotion render | **IMPLEMENTED as test harness** | **PASS（人工 browser regression）**；非 live-provider acceptance |
| Track B | fresh topic + real DeepSeek/GLM/local voice/Remotion/MiniMax | **IMPLEMENTED as acceptance run** | **Engineering PASS / Creative FAIL** |
| Browser automation | 当前 Track A/B 为人工浏览器操作 | **PLANNED/PARTIAL** | unattended E2E 尚未证明 |
| Prompt Governance | RoleContract / prompt_id/version / scattered system prompts | **PARTIAL** | **不足**：D-003 / Q-010 |
| Audio-first Pipeline | Q-009 / D-002 proposal | **NOT IMPLEMENTED** | 当前 Track B 仍 Director-before-Voice |
| H1 executable gate | P0 仅实现 New Project，不等同完整 H1 | **NOT_STARTED/PARTIAL** | 不应误写为 H1 已完成 |
| H4 / Publish | 无真实 platform publish | **NOT_STARTED** | `publish_authorized=false` |
| Analytics GUI | 底层概念有，完整 GUI 无 | **PARTIAL backend / NOT_STARTED GUI** | 未闭环 |

## 可重复核验

### GitHub 分支事实

- active P0 branch：`p0/gui-only-e2e-interim`
- HEAD：`323f7a2376efcfcfd1643a3e9d15333e084c1739`
- Track B record：`docs/project-brain/p0-slices/SLICE-006-TRACK-B.md`
- 分支持续 diverged；本轮综合复核写入前基线 `main@504ecc4` 时 P0 相对 main 为 ahead 10 / behind 28。后续 main 文档提交会改变 behind 数，合并前需重新 compare。
- merge base：`674957813b5efea39e8cc3e61621245808ccacc7`

### 测试

P0 branch 记录：**205 passed** + 1 known deprecation warning。

上传快照的独立复核：
- 205 tests collected；
- P0/XIAO-Y 新重点集 **23 passed in 7.03s**；
- 本次沙箱没有完成全量 205 tests 重跑，因此完整 205 passed 仍以 branch 验收记录为证据。

### Track B

- fresh project：`PRJ-ce790ce1fcc8`
- final render：`ART-1d0f5aab9283447d`
- duration：61.461333s
- Mechanical QA：PASS_WITH_RISK
- MiniMax Visual QA：`ART-36c5967ba89e466f`, VISUAL_ONLY
- H3：`ART-db463ee38dbe432b` by `P0_TEST_HARNESS`
- `publish_authorized=false`
- EXPORT：`ART-31fc96ae936a4486`
- Jianying ZIP archive validated；target-editor open 未验证

## 重要限制

- 工程 GUI 路径通过不能替代用户创作验收；
- MiniMax verdict 不能覆盖 PRODUCT_TASTE；
- 61 秒通过不能推出 3–5 分钟稳定量产；
- P0 branch 能力不能描述成“main 已实现”；
- 旧 84 秒样片和 Phase 2.1 文档是历史证据，不是最新 P0 状态。
