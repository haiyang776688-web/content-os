# D-003 · Role Prompt & Quality Contract System

**Discussion ID:** D-003  
**Date:** 2026-09-29  
**Topic:** Role Prompt & Quality Contract System  
**Baseline commit:** `fc045b0ca136471dc0dc25ab5dc253d53c8209dd`  
**Final Status:** OPEN

## Why Now

当前多个模型已经接入 Content OS，但实际输出质量不稳定。用户明确指出：

- 各角色提示词不完整；
- 职责边界不清；
- 审核标准不严；
- 模型容易自由发挥；
- 产出效果明显低于预期。

这不是单纯的“模型能力不足”，而是角色治理与 Prompt Contract 不成熟。

## Current Evidence

### CURRENT_IMPLEMENTATION

当前仓库已经有：

- `ROLE_CONTRACTS`
- `prompt_id`
- `prompt_version`
- Skill Snapshot
- response schema
- Model Gateway
- provider / worker assignment

但核心 Prompt 仍明显偏薄。

例如 `vnext/registries/catalog.py` 中：

- `SCRIPT_PRIMARY_V1` 基本只要求返回 JSON、事实可追溯；
- `SCRIPT_EDITOR_V1` 只要求润色且不改事实；
- `AUDIT_V1` 只要求独立审查并返回 PASS / FAIL / PASS_WITH_RISK；
- `DIRECTOR_V1` 只要求返回 DirectorPlan 并禁止像素布局；
- `VIDEO_QA_V1` 只要求审视频并报告问题。

另外，运行路径中还存在散落的 hardcoded system prompt：

- Research 在 `vnext/providers/workflow.py` 中动态拼 prompt；
- Director 又通过 `director_contract.py` 附加合同；
- Visual QA 在 `intelligence.py` 中使用另一段极短 system prompt。

因此当前状态更接近：

> 有 schema、有 role 名称，但缺少完整“岗位制度”。

## Core Problem

模型目前知道“输出什么结构”，但并不总是清楚：

- 自己是谁；
- 自己拥有什么权力；
- 自己不能改什么；
- 输入中谁是真源；
- 什么叫高质量；
- 哪些错误必须 FAIL；
- 什么情况应该退回上游；
- 输出前要自检什么。

结果是强模型也会“更聪明地自由发挥”。

## Question

是否应建立统一的 **Role Prompt Pack + Model Adapter + Quality Rubric** 系统，使业务规则由角色定义、模型差异由 adapter 处理，而不是为每个 provider 复制一整套逐渐漂移的 Prompt？

## Constraints

- 角色规则必须 provider-agnostic。
- Model-specific Prompt 只能做表达/格式/推理习惯适配，不能改变业务责任边界。
- Prompt 不能取代 deterministic validation。
- 不把所有规则堆进一个超长 system prompt。
- 不让不同角色重复拥有同一事实修改权。
- 不把 schema compliance 当成质量合格。
- 不修改 DECISIONS.md，除非 Council 完成并由用户明确接受。

## Roles In Scope

P0 / 当前阶段先覆盖：

1. RESEARCH
2. SCRIPT_PRIMARY / Writer
3. SCRIPT_EDITOR / Humanizer
4. AUDIT / Red Team
5. DIRECTOR
6. VIDEO_QA / Visual QA

MEDIA_RESOLVER、ANALYTICS、EVOLUTION 可在核心六个稳定后再扩展。

## Candidate Prompt Pack Structure

每个角色至少具有：

1. ROLE IDENTITY
2. MISSION
3. AUTHORITY / OWNERSHIP
4. INPUT CONTRACT
5. SOURCE OF TRUTH
6. MUST DO
7. MUST NOT
8. QUALITY RUBRIC
9. HARD FAIL CONDITIONS
10. OUTPUT CONTRACT
11. SELF CHECK
12. ESCALATION / RETURN-TO-OWNER RULES

模型运行时组合：

```text
Content OS Constitution
        ↓
Role Prompt Pack
        ↓
Project / XIAO-Y Profile
        ↓
Current Skill Snapshot
        ↓
Task Context
        ↓
Model-specific Adapter
        ↓
Output Schema
        ↓
Self-check / Quality Rubric
```

## Prompt Governance Requirements

- Prompt Pack 有稳定 ID 与版本。
- 每次产物记录 role / provider / model / prompt pack version / skill snapshot。
- Prompt 修改必须可追踪。
- Prompt Pack 需要 qualification suite，不靠“看起来不错”上线。
- Prompt Pack 状态建议至少：EXPERIMENTAL / QUALIFIED / PRODUCTION_READY。
- Prompt Rubric 与 Mechanical QA / deterministic validator 明确分工。

## Relation to Other Open Issues

- Q-004：DeepSeek Red Team 的设计定位与当前 worker mapping 不一致。D-003 不应静默解决模型分配，但需要提供“角色与模型解耦”的 Prompt 基础设施。
- Q-009 / D-002：Director Prompt 必须最终遵守 Audio-first 的时间真源边界；在 D-002 未决前，D-003 不应把旧 `timing_intent` 固化成永久导演职责。

## Human Decision Required

最终至少需要用户决定：

1. 是否采用 Role Prompt Pack 作为正式 Prompt 架构。
2. 是否允许 model-specific adapter。
3. 六个核心角色的责任边界。
4. Prompt Qualification Suite 是否成为上线门槛。
5. 哪些质量规则属于 Prompt，哪些必须落 deterministic QA。
