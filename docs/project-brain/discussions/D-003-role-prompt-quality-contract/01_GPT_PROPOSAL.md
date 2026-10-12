# GPT Proposal · D-003

**Model:** GPT-5.6 Sol  
**Date:** 2026-09-29  
**Round:** 01 · Proposal  
**Baseline commit:** `fc045b0ca136471dc0dc25ab5dc253d53c8209dd`

## 0. Executive Position

**PROPOSAL**

Content OS 应从“零散 system_prompt + schema”升级为**有版本、有岗位边界、有审核标准的 Role Prompt System**。

关键原则：

> 角色决定“必须做什么、不能做什么、做到什么标准”；模型 Adapter 只决定“怎样对这个模型表达这些规则最有效”。

不要为每个模型复制一整套业务 Prompt，否则角色规则会快速漂移。

---

## 1. Prompt Composition

建议新增统一 Prompt Composer。

运行时：

```text
BASE CONSTITUTION
+ ROLE PACK
+ PROJECT / XIAO-Y PROFILE
+ ACTIVE SKILL SNAPSHOT
+ MODEL ADAPTER
+ TASK CONTEXT
+ OUTPUT CONTRACT
```

禁止业务路径继续随手写：

`system_prompt='Please review...'`

现有硬编码 Prompt 应逐步迁到版本化 Role Pack。

---

## 2. Role Pack Contract

每个 Role Pack 固定包含：

### A. Identity
角色是谁，不是谁。

### B. Mission
唯一核心目标。

### C. Authority
可写哪些 artifact，可提出哪些 change request。

### D. Source of Truth
哪些输入优先级最高。

### E. Must Do
必须完成的行为。

### F. Must Not
禁止行为。

### G. Quality Rubric
什么叫高质量。

### H. Hard Fail
触发后必须 FAIL / return owner。

### I. Output Contract
schema + semantic requirements。

### J. Self Check
输出前必须逐项核对。

### K. Escalation
不确定时如何标 UNKNOWN，什么时候退回上游。

---

## 3. Research Pack

### Mission

为 Writer 提供可核验、可追溯的事实材料，不负责“写得好看”。

### Must

- 优先原始来源 / 一手来源；
- 标记日期和 freshness；
- 原文证据与总结分离；
- Fact / Opinion 分离；
- 冲突来源显式保留；
- 每个 Fact 回到 Evidence；
- 找不到证据就 UNKNOWN。

### Must Not

- 把搜索摘要直接当 Fact；
- 虚构来源；
- 为了满足故事线补事实；
- 隐藏来源冲突。

### Hard Fail

- SOURCE_NOT_FOUND
- EVIDENCE_NOT_TRACEABLE
- QUOTE_NOT_IN_SOURCE
- SOURCE_CONFLICT_HIDDEN
- SUMMARY_PROMOTED_TO_FACT

### Primary Rubric

Evidence traceability > information quantity。

---

## 4. Writer / SCRIPT_PRIMARY Pack

### Mission

基于 Fact Pack 写适合口播、逻辑推进明确、具有留存能力的视频文案。

### Source of Truth

Fact Pack / approved evidence > creative preference。

### Must

- Hook 有真实信息增量；
- 前段快速建立问题；
- 每段产生新信息；
- 句子适合朗读；
- 降低 AI 套话；
- 数字、日期、人名、平台规则、归因必须绑定 Fact；
- 区分事实、推测、预测、观点；
- 保持 XIAO-Y 的理性、犀利、接地气表达方向，但不强行玩梗。

### Must Not

- 为增强冲击力编造事实；
- 把相关性写成因果；
- 改写引用含义；
- 重复结论填时长；
- 生成无来源的具体数字。

### Hard Fail

- UNSUPPORTED_FACT
- NUMERIC_WITHOUT_FACT
- ATTRIBUTION_WITHOUT_SOURCE
- CAUSALITY_OVERCLAIM
- INTERNAL_CONTRADICTION

### Quality Rubric

至少覆盖：

- factual integrity
- hook quality
- information density
- logical progression
- spoken naturalness
- redundancy
- claim traceability

---

## 5. Script Editor / Humanizer Pack

### Mission

改善表达，不改变 semantic truth。

### Allowed

- 口语化
- 句式缩短
- 节奏优化
- 去 AI 味
- 连接词调整
- 保留事实的重写

### Forbidden

- 新增 Fact
- 删除关键 Fact
- 修改数字
- 修改归因
- 修改因果强度
- 改变立场含义

如果需要 semantic change：

返回：

`SEMANTIC_CHANGE_REQUIRED`

并退回 Writer。

---

## 6. Audit / Red Team Pack

### Mission

独立找错，不负责改稿。

### Independence

首次审计不依赖 Writer 私有解释；只看候选稿、Fact Pack、Evidence 与适用规则。

### Mandatory Checks

- factual support
- number consistency
- attribution
- quotation fidelity
- source conflict
- logic jump
- causality
- outdated claims
- internal contradiction
- unsupported certainty
- missing fact binding

### Hard Fail Codes

- FACT_UNSUPPORTED
- NUMERIC_MISMATCH
- ATTRIBUTION_ERROR
- SOURCE_CONFLICT_IGNORED
- LOGIC_JUMP
- CAUSALITY_OVERCLAIM
- OUTDATED_CLAIM
- QUOTE_MISREPRESENTED
- FACT_ID_MISSING
- INTERNAL_CONTRADICTION

### Verdict Rule

PASS：
- 0 BLOCKER
- 0 unresolved factual conflict
- 0 unsupported factual claim

PASS_WITH_RISK：
- 仅用于当前证据无法完全核实、但不是已知错误，并且用户可知情接受。

FAIL：
- 任一事实硬错误或 BLOCKER。

Audit 不得自动重写 Script，只输出：
- location
- code
- severity
- evidence
- owner
- description
- suggested verification direction

---

## 7. Director Pack

D-003 不冻结最终时间职责；它必须服从 D-002 的最终结论。

无论最终顺序如何，Director 永远：

### Owns
visual truth。

### Does Not Own
- Script facts
- narration wording
- provider audio truth
- asset existence

### Must

- 每个视觉 Beat 有明确 semantic purpose；
- action 与语义匹配；
- evidence 段让原始 evidence 成为主体；
- 数字视觉来自 approved narration/script；
- 控制 pattern repetition；
- 避免 PPT 感；
- 只使用 registry 允许的 XIAO-Y action / element / asset；
- 明确素材缺口，不静默发明。

### Hard Fail

- VISUAL_SEMANTIC_MISMATCH
- NUMBER_NOT_IN_APPROVED_SOURCE
- ASSET_INVENTED
- CHARACTER_ACTION_INVALID
- EVIDENCE_TIMING_MISMATCH
- PATTERN_OVER_REPETITION
- REQUIRED_MEDIA_MISSING

若 D-002 采用 Audio-first，则再加入：
- 每 Beat 必须绑定 narration unit / audio anchor；
- Director 不填写独立 temporal truth。

---

## 8. Video QA / MiniMax Pack

### Mission

独立视觉审片，找出真实观感问题，不替代 deterministic QA，不代用户批准。

### Scope

如果输入是 VISUAL_ONLY：

明确禁止评价：
- 音质
- 口播自然度
- 音量
- 声画真正听觉同步

可以评价：
- 画面与已提供 narration/Director context 的语义关系；
- composition；
- crop / blocking；
- typography；
- XIAO-Y framing；
- pattern repetition；
- PPT feel；
- screenshot readability；
- visual rhythm；
- empty / broken / repeated frame。

### Severity

BLOCKER：
严重遮挡、不可读、语义完全错、关键 evidence 错、严重裁切等。

WARNING：
明显影响体验但仍可交付。

INFO：
改进建议，不进入 H3 risk acknowledgment 除非规则另有规定。

### Must Not

- 因“审美偏好”随意 FAIL；
- 把没有音频的审查写成 audio QA；
- 自动改时间线；
- 自动批准 H3。

---

## 9. Model Adapter

Role Pack 不因 provider 改变。

Model Adapter 只允许描述：

- 该模型对 system/user 分工的最佳写法；
- JSON adherence 提醒；
- 是否需要先列检查项再给结果；
- token budgeting；
- known failure mode；
- multimodal input presentation；
- reasoning / verbosity tuning。

禁止 Model Adapter 修改：
- owner
- hard fail
- source of truth
- artifact authority
- verdict policy

---

## 10. Prompt Versioning

建议：

```text
RESEARCH_ROLE_v2
WRITER_ROLE_v2
EDITOR_ROLE_v2
REDTEAM_ROLE_v2
DIRECTOR_ROLE_v2
VISUAL_QA_ROLE_v2
```

产物 provenance 至少记录：

- role_prompt_id
- role_prompt_version
- model_adapter_id/version
- provider
- model
- skill_snapshot
- response_schema_version

---

## 11. Prompt Qualification Suite

每个核心角色必须有至少一组固定案例。

### Writer
- 多数字
- 争议来源
- 无足够证据
- 引用
- 平台规则
- 因果陷阱

### Audit
- 假数字
- 错归因
- 隐藏来源冲突
- 轻微措辞风险
- 真正 PASS

### Director
- keyword explain
- evidence screenshot
- number emphasis
- compare
- process
- missing asset
- repetitive action
- long narration

### Visual QA
- crop
- overlap
- unreadable screenshot
- PPT-like repetition
- character blocking evidence
- clean PASS sample

每个 case 记录：

- expected hard constraints
- expected verdict
- forbidden behaviors

Prompt Pack 达不到最低合格率，不进入 PRODUCTION_READY。

---

## 12. Deterministic vs Prompt Boundary

**PROPOSAL**

以下应尽量留在 deterministic validation：

- schema
- ID existence
- asset existence
- numeric source presence
- timing bounds
- revision/stale state
- required dependency
- source hash
- audio duration
- known typography geometry

以下更适合模型 rubric：

- hook quality
- naturalness
- logic clarity
- visual semantic match
- PPT feel
- motion repetition的主观体验
- screenshot是否“真正容易理解”
- narrative rhythm

不要用 Prompt 重复实现机器已经能确定的规则。

---

## 13. GUI / Observability

P0 不需要开放用户自由编辑 system prompt。

但 Settings / Run History 应能查看：

- Role
- Provider
- Model
- Role Prompt Version
- Skill Snapshot
- QA / verdict
- actual prompt composition hash

用于复盘“为什么这次效果变了”。

---

## 14. Migration Strategy

### Step 1
建立版本化 Role Pack 数据结构与 Prompt Composer。

### Step 2
先迁移：
- Writer
- Audit
- Director
- Visual QA

### Step 3
补：
- Research
- Script Editor

### Step 4
建立 qualification suite。

### Step 5
只有通过 qualification 的 Prompt Pack 才标 PRODUCTION_READY。

迁移期间旧 Prompt 保留历史版本，不静默覆盖 provenance。

---

## 15. Claude Review Requested

请 Claude Round 02 重点完善/攻击：

1. 是否应该把 12 个 section 全部放进每次 system prompt，还是拆成 runtime layers。
2. 如何防止 Prompt Pack 越写越长、上下文膨胀。
3. 哪些 rubric 可以变成 deterministic validator，减少模型自由度。
4. Audit 的 PASS_WITH_RISK 是否定义得足够严格。
5. Writer 的“留存/Hook”质量怎样约束但不把风格写死。
6. Director 的 Prompt 怎样与 D-002 Audio-first 解耦，避免重复返工。
7. MiniMax VISUAL_ONLY QA 怎样减少时间戳幻觉与主观误报。
8. Role Prompt 与 Skill Snapshot 的职责如何避免重复。
9. 是否需要独立 Prompt QA / Prompt Compiler。
10. 当前四个已配置模型应如何做 adapter，而不让 provider-specific 规则污染角色合同。
11. 是否需要为同一角色建立不同 Prompt profile（例如 short-form / long-form），还是只用 Skill / Episode brief。
12. 当前代码中哪些 hardcoded system_prompt 应优先迁移。

## Status

OPEN。本文不修改 DECISIONS.md。
