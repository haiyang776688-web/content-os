# Content OS 当前状态（给项目成员）

> **Open-source archive notice (2026-10-12):** Active development is paused and the public snapshot is based on the validated MDC baseline, not the later P0 GUI experiment branch described below. This file is retained as a dated historical state record. For the publishable current status, use the repository `README.md`, `LOCAL_PROJECT_INVENTORY.md`, and `docs/MAINTAINER_HANDOFF.md`. GUI-001 remains incomplete in the public snapshot.


**核对日期：**2026-09-29。  
**知识主分支：**`main`。  
**当前 P0 实现分支：**`p0/gui-only-e2e-interim`，核对 commit `323f7a2376efcfcfd1643a3e9d15333e084c1739`。  
**阶段：**仍属于 vNext Phase 2 / P0 GUI-Only E2E 收敛，不进入 Phase 3。

当前状态必须区分：
1. `main` 上的 Project Brain / Council；
2. P0 实现分支上的实际代码与 Track A/B 验收；
3. 工程链路通过与创作质量通过。

纠错后的完整交接见 [2026-09-29 P0 GUI-Only E2E 交接](HANDOFF_2026-09-29_P0_GUI_E2E.md)。最新 Council / WorkBuddy / Track B 交叉复核见 [2026-09-29 Council 综合复核](discussions/COUNCIL_SYNTHESIS_2026-09-29.md)，该文件仍是待 Claude 复核的 Proposal/Synthesis，不是正式 Decision。

## 最新已验证进展

### P0 实现分支

`p0/gui-only-e2e-interim` 已实现并记录：

- Project → Source/Media → Fact → Script → Audit → H2；
- Director → Storyboard → Preview → Gate；
- Fresh Voice → Audio Timing → Final Editable EDT；
- 本地 background jobs、single-flight、refresh recovery、orphan recovery、retry / stale render；
- Mechanical QA / Visual QA / H3 risk acknowledgment；
- MP4 下载与 Jianying transfer ZIP 下载；
- Track A deterministic provider-boundary browser regression；
- Track B fresh live GUI acceptance。

这些能力当前**尚未全部合入 main**。

### Track B fresh live run

从空项目 `PRJ-ce790ce1fcc8` 通过普通 GUI 完成：

- 真实 DeepSeek Research；
- 7 个 Fact 人工确认；
- 真实 DeepSeek Script；
- 独立 GLM Audit PASS；
- 测试 H2；
- 真实 GLM Director；
- Storyboard；
- 本地克隆声音 `YU_LOCAL_V1`；
- `AUDIO_TIMING_MAP`；
- Final Editable EDT；
- 1080p/30fps Remotion MP4；
- Mechanical QA；
- 真实 MiniMax-M3 **VISUAL_ONLY** QA；
- Review Pack；
- 测试 H3；
- MP4 下载；
- Jianying transfer ZIP 下载。

最终 Track B 修正版视频：

- 61.461333 秒；
- 1920×1080 / 30 fps；
- H.264/AAC；
- Voice 61.400 秒；
- MiniMax `audio_transmitted=false`。

### 测试

实现分支验收记录：`pytest -q vnext/tests` **205 passed**，1 条既有 Starlette/httpx deprecation warning。

本次上传快照复核：

- **205 tests collected**；
- 新 P0 / XIAO-Y 重点测试 **23 passed in 7.03s**；
- 本次沙箱未在 90 秒窗口内重新跑完全量 205 项，因此不要把完整 205 passed 归因于本次外部复核。

## 当前真正的产品状态

### 工程 GUI 链路

**Track B engineering acceptance：PASS。**

普通用户路径已经有真实 fresh-project GUI 验收证据，不再是“只能靠内部 API/JSON 才能走完”。

但：

- Track A / B 目前是人工浏览器验收，不是 unattended browser automation suite；
- D-001 尚未完成用户最终 ACCEPT；
- P0 实现分支尚未 reconcile 到 main。

### 创作质量

**FAIL / pending redesign。**

Track B 仍出现：

- PPT / slide-like 稀疏感；
- 大面积白底 + 少量文字；
- XIAO-Y pose 重复；
- 实际平台 overlay / occlusion 演示不足；
- text-only reveal 偏快；
- visual rhythm / balance 不足。

当前代码复核不支持把 Creative FAIL 单独归因于 Prompt 或 Renderer。已确认的结构性因素包括：

- Track B 题材本身没有实际 media/evidence，media-required Director patterns 因此不可用；
- Director 的 template / semantic_pattern 被锁定，由 Resolver 决定布局；
- VisualResolver 在未显式 action_id 时使用首个 semantic-intent 匹配，存在确定性 pose 重复；
- 当前 Remotion Composition 的持续 motion / transition 词汇较少（属于当前实现限制，不是 Remotion framework 限制）；
- 多个 Beat / Scene 语义字段没有进入 Resolver→pixels 消费链；
- Storyboard Gate 以静态 still 为主，无法充分提前观察 temporal/rhythm 问题。

因此当前最佳解释是「题材/证据供给 × Director × Resolver × motion vocabulary × QA/Gate」的多因子问题。Mechanical QA / MiniMax `PASS_WITH_RISK` 与测试 H3 不能覆盖用户已明确的“拒绝 PPT 感”产品标准。

### Jianying

Track B 已生成并下载 Jianying ZIP，`unzip -t` 通过。

但**尚未证明该 Track B bundle 已在剪映真实打开并保持预期编辑效果**。不要把 archive validation 写成 target-editor acceptance。

### H3 / H4

Track B H3 reviewer 为 `P0_TEST_HARNESS`：

- 是 GUI E2E 测试记录；
- 不是用户对视频的最终创作批准；
- `publish_authorized=false`；
- H4 未授权；
- 无真实平台发布。

## 仍未解决的核心问题

### D-002 / Q-009：Audio-First Director Pipeline

Track B 仍沿用 `Director → Storyboard → Voice → AudioTimingMap`，但最新复核收窄了问题定义。

Track B 实际为 **7 segments / 7 beats（1:1）**。当前 `AudioTimingMap` 已把每个 segment 的真实音频起止绑定到最终 EDT，因此 Track B 本次 beat 外边界已经由真实音频决定。真正仍需区分的是：

- 1:N segment 内 beat 的「切在哪里」：当前按 `timing_intent` 比例分配；可测试 phrase/word anchor；
- 字幕 phrase 内的字符比例拆分；
- Director 在 Voice 之前决定 beat 数/密度，即「切几刀」：只有 Voice-before-Director / Audio-first 可能从决策源头改变。

因此 D-002 下一步应比较：

`A current retime vs B phrase/word anchor vs C full Audio-first`

而不是直接假定必须新增 Narration Units 或直接重排整条主链。Narration Units 是否需要独立 Artifact 仍未证明。

### D-003 / Q-010：Role Prompt & Quality Contract

当前多模型调用已能运行，但核心角色 Prompt 仍过薄、职责/审核标准不够严格。Track B 的创作质量 FAIL 进一步证明：

> schema compliance / provider success != production quality。

需要继续建立 Role Prompt Pack、Quality Rubric、Hard Fail、Self-check、Model Adapter 与 Prompt Qualification。

### Q-004：DeepSeek Red Team

设计上 DeepSeek 是独立 Red Team；实现分支 Track B 实际使用 DeepSeek Research/Script、GLM Audit。此冲突仍未解决，不能由一次 Track B 运行反向改写 DEC-003。

## Main / P0 分支分叉

本次核对：

- 分支已持续分叉：在本轮综合复核写入前的基线 `main@504ecc4` 上，P0 相对 main 为 ahead 10 / behind 28；本轮新增 Project Brain 文档会继续增加 main 的 behind 计数，因此合并前必须重新运行 `compare main...p0/gui-only-e2e-interim`，不要把该计数当永久状态。
- merge base：`674957813b5efea39e8cc3e61621245808ccacc7`。

main 有较新的 Council / D-002 / D-003 / Q-010 文档；P0 branch 有较新的 GUI 实现。

因此不能强制移动 main ref，也不能称 P0 branch 的代码已经全部在 main。

## 历史样片

`PRJ-bba515713057` 的 84.821 秒样片继续保留为 known regression case：

- 机械 QA PASS；
- MiniMax VISUAL_ONLY `PASS_WITH_RISK`；
- 用户历史 H3 `APPROVE_WITH_RISK`；
- H4 未授权。

它不再是最新 P0 GUI fresh-project acceptance 的主证据。

## Council 复核补充

- `WB-001-independent-gap-review` 提供了高价值 Repo Audit，但若干 severity / causality 过度；其 first-match pose、write-only fields、Storyboard Gate temporal blind spot、Prompt 无 budget 等代码事实已复核成立。
- `WB-002-glm53-independent-review` 已主动更正 reviewer 身份：它并非真实 GLM 5.3 独立评审，而是同一 WorkBuddy 底层模型在更严格证据方法下的第二次复核。其技术证据可用，但不能作为模型族能力对比。
- MiniMax 当前更适合定位为 static visual / semantic reviewer；`fps=1` 对亚秒 reveal、transition、micro-rhythm 证据不足。Track B 的真实 MiniMax finding 有信息量，不能写成“接近零”。
- Track C 的 45MB QA 上限按 Track B 当前码率不是 3–5 分钟已证明 blocker；Storyboard stills 是耗时风险；300s render timeout 是优先实测的候选风险。
- P0 Renderer 为字幕无条件绘制深色衬底，但 EDT metadata / Mechanical QA 仍保留旧背景规则，出现 renderer pixels 与可追踪规则真源的漂移，需后续收敛。

## 明确未完成

- D-001 用户最终决策 / Synthesis；
- D-002 Audio-first 结论与实现；
- D-003 Prompt Governance 结论与实现；
- Track C 3–5 分钟稳定性；
- unattended browser E2E automation；
- Track B 的真实 Jianying-open 验收；
- 完整字段级人工修改 merge/rebase；
- 完整跨机资产/项目恢复；
- H4 / 平台发布；
- 完整 Analytics GUI；
- 逐词强制对齐、骨骼动画、口型同步仍非已完成能力。

更新本文件时遵循：
**当前代码/commit/测试/真实产物 > 当前 Project Brain > 旧顶层交接文档 > 历史讨论。**
