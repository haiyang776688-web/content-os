# D-002 · Audio-First Director Pipeline

**Discussion ID:** D-002  
**Date:** 2026-09-29  
**Topic:** Audio-First Director Pipeline  
**Baseline commit:** `fc045b0ca136471dc0dc25ab5dc253d53c8209dd`  
**Final Status:** OPEN

## Why Now

用户在真实生产链中观察到一个系统性返工问题：

> Director 先基于文案估算时长并设计分镜；真实配音完成后，音频时长与分镜预估经常不一致。即使之后通过 retime 把总时长勉强拉齐，画面切换点仍可能与真正说到对应语义的时间点不一致，最终在 QA 暴露音画错位并触发返工。

这会浪费模型调用、Storyboard 渲染与后续 QA 成本，并且说明当前链路的 temporal truth 可能放错位置。

## Current Evidence

### FACT / CURRENT_IMPLEMENTATION

当前实现中：

- Director IR 使用 `timing_intent` / `estimated_duration` 形成预估时序。
- Voice 当前需要 Storyboard Gate 已批准后才进入正式生产。
- `AUDIO_TIMING_MAP` 在 Voice 后建立。
- AudioClock 会把已有视觉 composition 依据音频区间重新 retime；这可以修正总时间，但不天然保证视觉切换点与真实 narration 语义边界一致。

### Relevant Project Brain

`OPEN_QUESTIONS.md` 已登记 Q-009，提出候选主链：

`H2 Script → Narration Units → Voice → AudioTimingMap → Director → Storyboard → Final EDT → Render/QA`

并提出职责分离：

- Writer = semantic truth
- Voice / AudioTimingMap = temporal truth
- Director = visual truth

### Prior Claude Input

D-001 的 `04_CLAUDE_FINAL.md` 已明确指出：

- Q-009 与原 P0 Slice 顺序存在真实冲突。
- 不应未经验证就直接把 Audio-first 当成已确认架构。
- 建议在 Slice 0 先做 Spike 3，区分根因究竟是：
  1. 局部 dependency invalidation bug；
  2. 还是 Director-before-Voice 的系统性顺序问题。
- 如果证据指向系统性顺序问题，应优先讨论流程重排，而不是在旧顺序上不断补丁。

## Question

是否应把 Content OS 的 production master clock 从“Director 的估算时长”迁移到“真实 Voice / AudioTimingMap”，使 Director 在真实 narration timing 已确定后再设计视觉？

需要回答：

1. Voice 是否应移动到 Director / Storyboard 之前？
2. 是否需要新增稳定的 `NARRATION_UNITS` 合同？
3. Director IR 是否应逐步移除或降级 `timing_intent` / `estimated_duration`？
4. Director 应绑定 segment / narration unit / phrase 中的哪一级？
5. audio start/end 应由 Director填写，还是由 compiler 从 AudioTimingMap 派生？
6. Storyboard Gate 应审批视觉语义，还是也审批已绑定的真实时间窗口？
7. 用户修改 Script 后，哪些 Voice / Audio / Director / Storyboard 产物必须失效？
8. 纯视觉修改后，是否应保持 Voice / AudioTimingMap 有效？
9. 如何避免“先生成昂贵 Voice，随后 Script 又大改”造成新的浪费？
10. Audio-first 是否会影响 DEC-005（EDT 唯一可编辑时间线）或现有 H2/H3 责任边界？

## Candidate Architecture

**PROPOSAL（尚非 Decision）**

```text
Research / Fact Pack
        ↓
Writer
        ↓
Audit / Red Team
        ↓
H2 Script Approval
        ↓
Narration Units
        ↓
Voice
        ↓
Audio Alignment
        ↓
AudioTimingMap  ← temporal master clock
        ↓
Director
        ↓
Storyboard
        ↓
Storyboard Gate
        ↓
Final Editable EDT
        ↓
Render
        ↓
Mechanical QA
        ↓
Visual QA
        ↓
H3
```

Director 不再决定“这段应该 4.5 秒”，而是消费已确定的 narration timing，并决定“在这段真实时间里应该展示什么”。

## Required Evidence Before Decision

在形成正式 Decision 前，至少验证：

### Spike A · Dependency Root Cause

实测：
- Voice 已存在后修改纯视觉 Beat；
- 当前系统是否错误失效 Voice；
- 根因是 dependency graph 过粗，还是旧流程顺序本身。

### Spike B · Fresh Audio Mapping

全新项目：
- Script → Voice → AudioTimingMap；
- 确认 segment / phrase timing 能稳定产生；
- 确认没有依赖已有 Storyboard 才能成立的不可拆约束。

### Spike C · Director With Real Timing

用同一份 script：
- 让 Director 消费真实 AudioTimingMap；
- 对比旧 `timing_intent + retime`；
- 检查音画语义切点、返工次数和 QA issue。

## Constraints

- 不修改 DECISIONS.md，除非用户在 Synthesis 后明确 ACCEPT。
- 不因为 Audio-first 就建立第二条 editable timeline。
- 不让 Voice 决定“说什么”；Script 仍是 semantic truth。
- 不让 Director 改写 Script 或 Audio timing。
- 不通过简单拉伸视觉来伪装语义同步。
- 不在缺乏真实 evidence 的情况下宣布 Audio-first 已完成。

## Human Decision Required

最终至少需要用户决定：

1. 是否正式采用 Audio-first 主链。
2. Narration Units 是否成为正式中间产物。
3. 是否把 AudioTimingMap 定义为 production temporal master clock。
4. Director IR timing 字段如何迁移。
5. Script 修改后 Voice 重生成的最小边界。
