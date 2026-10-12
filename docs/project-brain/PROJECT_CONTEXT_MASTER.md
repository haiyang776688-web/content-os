# Content OS · 项目共享大脑入口

> **Open-source archive notice (2026-10-12):** Active development is paused and the public snapshot is based on the validated MDC baseline, not the later P0 GUI experiment branch described below. This file is retained as a dated historical state record. For the publishable current status, use the repository `README.md`, `LOCAL_PROJECT_INVENTORY.md`, and `docs/MAINTAINER_HANDOFF.md`. GUI-001 remains incomplete in the public snapshot.


> 新模型第一次进入本项目，先读本文件，再读 [产品取向](PRODUCT_TASTE.md)、[当前状态](CURRENT_STATE.md)、[实现核验](IMPLEMENTATION_STATE.md)、[已确认决策](DECISIONS.md)。本目录是项目知识层，不是运行时配置、代码或新的规则库。

**记录日期：**2026-09-29。  
**知识主分支：**`main`。  
**活动 P0 实现分支：**`p0/gui-only-e2e-interim@323f7a2`。  
**当前工程阶段：**vNext Phase 2 / P0 GUI-Only E2E 收敛；未进入 Phase 3。

最新纠错交接： [2026-09-29 P0 GUI-Only E2E](HANDOFF_2026-09-29_P0_GUI_E2E.md)。

## 它是什么、为什么做

Content OS 是面向自媒体内容生产的本地 Web 工作台。目标是把资料、事实、脚本、导演意图、人物/素材、分镜、声音、时间线、渲染、质检与复盘接成可追溯流程，让普通创作者能用 AI 提速，同时保留人的创作判断和修改权。

它不是“几个模型轮流聊天”，也不以 Agent 数量作为完成度。

当前已存在 FastAPI 工作台、版本化 artifact、角色/模型适配层、XIAO-Y registry、Remotion 渲染和单向剪映 exporter。P0 实现分支已经用 Track A / Track B 证明 fresh-project GUI 工程链可以从空项目走到 MP4 / QA / 测试 H3 / 下载；但创作质量、Audio-first 顺序、角色 Prompt 治理和长视频稳定性仍未收敛。

## 最新验收层级

必须区分四种“通过”：

1. **Contract / test pass**：schema、validator、pytest 等机器约束通过。
2. **Engineering GUI pass**：普通 GUI 路径可以完成生产动作。
3. **Creative acceptance**：用户认可画面、节奏、XIAO-Y 表现和成片效果。
4. **Publish authorization**：H4 / 对外发布授权。

Track B 当前只达到：
- 1：是；
- 2：是；
- 3：**否，creative FAIL / pending redesign**；
- 4：否。

任何模型不得把前两项推断成后两项。

## 当前关键样本

### Track B fresh live GUI sample

活动分支 fresh project `PRJ-ce790ce1fcc8`：

- 新题材；
- 真实 DeepSeek Research/Script；
- GLM Audit/Director；
- 本地 cloned voice；
- AudioTimingMap；
- Final EDT；
- real Remotion render；
- Mechanical QA；
- MiniMax-M3 VISUAL_ONLY QA；
- test H3；
- MP4/Jianying bundle 下载。

最终视频约 61.46 秒。

这是**工程 GUI acceptance sample**，不是创作批准样片。

### 84.821 秒历史样片

`PRJ-bba515713057` 继续保留为 regression case。它有旧 Phase 2.1 的真实生产/H3 历史，但不再代表最新 fresh-project P0 GUI 状态。

## XIAO-Y 与产品标准

XIAO-Y 是固定人物品牌，不是通用白板小人。现有注册表含 48 动作、12 模板、33 元素和白底黑线、黄/红重点色风格约束。

用户明确拒绝：
- PPT 感；
- 机械动作；
- 通用白板替代；
- 稀疏无意义的白底文字页；
- 只满足 schema 但缺乏视觉叙事的输出。

Track B 创作质量 FAIL 是当前最重要的真实信号之一。

## 生产链与权责

现行代码仍大体遵循：

`Research → Script/H2 → Director/Storyboard → Voice/AudioTiming → EDT → Render/QA → H3`

但这个顺序正在被 D-002 / Q-009 正式挑战。

候选 Audio-first：

`Research → Script/H2 → Narration Units → Voice → AudioTimingMap → Director → Storyboard → Final EDT → Render/QA → H3`

在用户正式 ACCEPT 前，两者必须标记为：
- current implementation；
- proposed architecture；

不能混写。

主要长期原则仍来自 [DECISIONS](DECISIONS.md)：
- Remotion 只执行/渲染；
- EDT 是唯一可编辑时间线；
- Jianying 单向导出；
- H3 != H4；
- 人保留修改权；
- XIAO-Y consistency；
- DeepSeek Red Team / MiniMax Visual QA 是设计定位，但实现可能仍有 divergence。

## 当前两个优先 Council

### D-002 · Audio-First Director Pipeline

解决 temporal truth 的位置：
- Director 是否应在 Voice 后；
- AudioTimingMap 是否成为 master clock；
- Narration Units 是否需要；
- 视觉修改与 Voice 依赖如何解耦。

### D-003 · Role Prompt & Quality Contract

解决“模型接进来但没有岗位制度”：
- Role Prompt Pack；
- Source of Truth；
- Must / Must Not；
- Hard Fail；
- Quality Rubric；
- Self-check；
- Model Adapter；
- Prompt Qualification Suite。

## 当前分支关系

`main` 与 `p0/gui-only-e2e-interim` 已分叉：
- main 有较新的 Council / Project Brain；
- P0 branch 有较新的 GUI 实现。

后续 reconcile 时必须保留双方内容，不允许强制移动 ref 覆盖任一侧历史。

## 知识可信度与更新方法

状态事实优先级：

**当前代码 / commit / 数据库 / 测试 / 真实运行 > 当前 Project Brain > 旧交接文档 > 历史讨论。**

设计意图、产品取向和正式决定不能由代码现状反推。

以下必须分别记录：
- 代码存在；
- GUI 可操作；
- provider live verified；
- engineering acceptance；
- creative acceptance；
- publish authorization。

冲突写进 [CURRENT_STATE](CURRENT_STATE.md) 与 [OPEN_QUESTIONS](OPEN_QUESTIONS.md)，不静默覆盖。无法核对写 `UNKNOWN`。GPT/Claude 讨论先进入 [discussions](discussions/README.md)，只有用户明确确认才进入 [DECISIONS](DECISIONS.md)。
