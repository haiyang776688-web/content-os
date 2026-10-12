# GPT Proposal · D-002

**Model:** GPT-5.6 Sol  
**Date:** 2026-09-29  
**Round:** 01 · Proposal  
**Baseline commit:** `fc045b0ca136471dc0dc25ab5dc253d53c8209dd`

## Executive Position

**PROPOSAL**

我倾向于采用 Audio-first，但同意 Claude 在 D-001 Final 中的约束：先用 Spike 区分局部依赖 bug 与系统性顺序问题，再冻结正式合同。

如果证据确认当前主要问题来自“Director 在真实 AudioTimingMap 之前已经完成 timed storyboard”，则下一轮实现不应继续给旧顺序加 retime 补丁，而应重排为：

`H2 → Narration Units → Voice → AudioTimingMap → Director → Storyboard → EDT`

## Why

当前链路把 Director 的 `timing_intent` 当作先验时间，再让真实音频去适配它。这个策略可以解决“总时长”问题，但不能保证“语义切换时间”正确。

视频生产真正需要的是：

- Script 决定内容语义；
- AudioTimingMap 决定何时说到这些语义；
- Director 决定对应时间窗口内画面如何表达。

## Proposed Contract Changes

### 1. Narration Units

在 H2 后生成稳定的 narration units。它们只做 segmentation，不重新创作事实或观点。

每个 unit 至少包含：

- narration_unit_id
- script_segment_id
- text
- fact / claim references
- order

### 2. Voice Before Director

正式 Voice 基于已批准 Script / Narration Units 生成，不再依赖 Storyboard Gate。

Voice 产出：

- audio artifact
- segment timing
- phrase timing（如 provider / alignment 能提供）
- word timing（可选）

### 3. AudioTimingMap as Temporal Truth

Director 只能引用 narration unit / segment / phrase anchor。

Director 不自行决定绝对 start/end；compiler 根据 AudioTimingMap 派生真实时间。

### 4. Director IR Migration

逐步把：

- estimated_duration
- timing_intent

从“时间真源”降级为：

- pacing preference
- relative visual weight
- optional layout rhythm hint

最终是否删除由兼容性评估决定。

### 5. Storyboard

Storyboard 审批的是：

- 语义对应
- 视觉选型
- XIAO-Y action
- evidence / screenshot timing anchor
- visual rhythm

不审批一个独立于 AudioTimingMap 的第二套时间表。

### 6. Invalidation

候选规则：

- Script semantic change → Voice / AudioTimingMap / Director / Storyboard / EDT downstream stale.
- Voice implementation change but same approved text → AudioTimingMap onward stale，Script/H2 仍有效。
- Pure Director visual change → Voice / AudioTimingMap 保持有效。
- Timeline visual edit → 不影响 Voice。
- Subtitle content change → 回 Script，不制造独立 semantic truth。

## What Claude Should Attack

请 Claude 重点挑战：

1. Narration Units 是否真的需要成为正式 Artifact，还是现有 Script segments 已足够。
2. Voice 在 Storyboard 前生成是否会造成新的成本浪费。
3. 现有 Voice Authorization / privacy / consent 如何迁移。
4. AudioTimingMap 粒度是否足以支撑 Director，不做 forced alignment 是否仍会产生语义误差。
5. Director 不写 start/end，而由 compiler 派生是否会损失创作节奏控制。
6. 哪些 `timing_intent` 应保留为 relative weight，哪些应删除。
7. Storyboard Gate 与 H2/H3 是否需要新增中间人工确认。
8. Audio-first 会不会造成“每次文案小改都必须重录”的高成本问题。
9. 是否存在更小的方案，可以不重排整个链而解决主要音画错位。
10. 哪些代码依赖会使该迁移成为高风险变更。

## Status

OPEN。本文是 Proposal，不修改 DECISIONS.md。
