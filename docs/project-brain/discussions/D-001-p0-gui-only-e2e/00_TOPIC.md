# D-001 · P0 GUI-Only E2E Execution Plan

**Discussion ID:** D-001  
**Date:** 2026-09-28  
**Topic:** P0 GUI-Only E2E Execution Plan  
**Baseline commit:** `ea0d72748ff927c957183405069b6223d2b168c1`  
**Final Status:** OPEN

## Why Now

Content OS 已经具备大量后端、版本化产物、Director IR、EDT、Remotion、机械 QA、MiniMax 视觉 QA 和剪映单向导出基础，但当前最大的产品缺口仍是：普通用户不能仅靠 GUI，从立项一直完成到可交付视频。继续增加 Agent、平台发布、Analytics 或大规模编辑器能力，会扩大系统面积而不解决当前主瓶颈。

## Relevant Project State

本轮以 `ea0d72748ff927c957183405069b6223d2b168c1` 为固定事实快照。

已读取：

- `docs/project-brain/PROJECT_CONTEXT_MASTER.md`
- `docs/project-brain/PRODUCT_TASTE.md`
- `docs/project-brain/CURRENT_STATE.md`
- `docs/project-brain/IMPLEMENTATION_STATE.md`
- `docs/project-brain/DECISIONS.md`
- `docs/project-brain/REJECTED_IDEAS.md`
- `docs/project-brain/OPEN_QUESTIONS.md`
- `docs/project-brain/ROADMAP.md`
- `REAL_WORKFLOW_ACCEPTANCE_REPORT.md`
- `CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md`

已确认基线事实：

- 当前工程是 **vNext Phase 2.1 Provider Activation / Phase 2 Preview-Hardening**，尚未进入 Phase 3。
- 当前 P0 已由 DEC-008 确认为 **GUI-Only E2E**。
- 当前真实样片约 **84.821 秒，1080p/30fps**；机械 QA PASS，MiniMax 无声视觉 QA PASS_WITH_RISK，H3 APPROVE_WITH_RISK。
- 当前全量测试记录为 **189 passed**。
- 当前 GUI 对多个阶段已有入口，但仍存在原始 JSON、内部 API 依赖、数值型时间线操作和未闭环步骤。
- 当前样片没有 `EXPORT` 产物；剪映单向导出器“存在且有历史验收”不等于“当前样片已经完成剪映交接”。
- H4、真实平台发布和完整 Analytics GUI 不属于当前已经完成的能力。
- 人工修改必须保留最终权（DEC-009），但 AI 再生成与用户修改的 Override/Rebase 合同尚未冻结。

## Question

在**不推倒现有 Content OS、不把 P0 扩成完整剪辑器或发布系统**的前提下：

> 为了尽快实现“普通用户不打开 Terminal、不改 JSON、不调用内部 API，从新建项目一路完成到可交付视频与可选剪映草稿”的 GUI-Only E2E，下一阶段应该：
>
> 1. 先做什么？
> 2. 哪些现有能力只需要接入 GUI，而不应该重写？
> 3. 哪些能力必须补最小合同才能进入 P0？
> 4. 哪些内容应该明确暂缓？
> 5. 怎样定义一个可重复、不可偷调内部 API 的真实 E2E 验收？

## Constraints

- 不重写现有 Core，除非发现无法跨过的真实阻塞。
- 不把“框架迁移”作为 P0 前提；Q-001 保持开放，除非证据证明现有结构无法完成 E2E。
- 不构建完整 OpenCut/Premiere 级编辑器。
- 不把 H4、真实平台发布、完整 Analytics 纳入 P0。
- 不增加 Hook/Retention/Humanize 等独立 Agent。
- Remotion 继续仅作为渲染/执行引擎（DEC-001）。
- EDT 继续作为唯一可编辑时间线（DEC-005）。
- 人工修改不能被 AI 再生成静默覆盖（DEC-009）。
- XIAO-Y 一致性与避免 PPT 感属于质量约束，但本议题重点是 **P0 产品闭环的最小实现路径**，不是重做整个视觉系统。

## Human Decision Required

本轮结束后至少需要用户决定：

1. 是否接受 Council 收敛出的 P0 开发顺序。
2. 是否接受 P0 的“最小人工修改保护”合同。
3. 是否接受 P0 E2E 使用当前约 85 秒真实样片作为黄金验收样例，并在 P0 完成后另跑 3–5 分钟稳定性验收。
4. 是否接受将 H4 / Publish / 完整 Analytics / 框架迁移 / 完整 NLE 能力明确排除在 P0 之外。
