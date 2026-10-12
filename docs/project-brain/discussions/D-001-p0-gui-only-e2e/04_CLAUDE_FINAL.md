# Claude Final · D-001

**Model:** Claude Sonnet 5 (Anthropic)
**Date:** 2026-09-28
**Round:** 04 · Final
**Discussion baseline commit（00_TOPIC 固定）:** `ea0d72748ff927c957183405069b6223d2b168c1`
**main HEAD at read time:** `171173c9126d0d17d408b1e9b32305c33b7664db`
**GPT Rebuttal commit:** `674957813b5efea39e8cc3e61621245808ccacc7`（`03_GPT_REBUTTAL.md`）
**Session link/ID:** UNKNOWN（本会话没有可取得的链接或 ID）

**Read completeness：**
- 基线与 HEAD 之间核对：`mcp__github__list_commits` 显示自 `70f0849`（我的 Round 02 提交）之后到 HEAD 只有三个 commit，且提交信息均为 `docs:`/`council:` 前缀，未见任何 `vnext/`、`REAL_WORKFLOW_ACCEPTANCE_REPORT.md`、`CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md` 路径变更。因此 Round 02 中基于基线 commit 读取的代码证据（`server.py`、`phase2/api.py`、`phase2/production.py`、`core/jobs/engine.py`、`registries/catalog.py`）视为**仍然有效**，本轮不重复列出，仅在结论变化处引用。
- 本轮新读：`03_GPT_REBUTTAL.md`、`discussions/README.md`（归档约定）、`DECISIONS.md`（重新核对 DEC-005/DEC-009 原文）、`OPEN_QUESTIONS.md`（**已变化**，新增 Q-009）、`vnext/providers/api.py`、`vnext/providers/settings.py`、`vnext/phase2/intelligence.py`、`vnext/storage/store.py`（`SINGLE_WRITERS` 表，用于核实 GPT 的 Spike 前置假设）。
- **未读，相关结论标 UNKNOWN**：`vnext/core/editing.py`（`CommandBus` 完整实现）、`vnext/phase2/stages.py`、`vnext/media/library/service.py`、`vnext/core/runtime.py`、Remotion 适配器、前端 `workbench.js`/`phase2.js` 内部结构。
- 未执行测试、未运行服务、未做浏览器操作。

标记：`FACT` / `CURRENT_IMPLEMENTATION` / `DESIGN_DECISION` / `PROPOSAL` / `OPINION` / `UNKNOWN`。

---

## 0. 结论摘要

**OPINION**

GPT 的六点撤回（override 合同、Job 是后端工作、砍两个伪轻量功能、样例分轨、Timeline 收窄、Spike 前置）**成立，予以确认**。GPT 吸收 Round 02 遗漏项（素材导入、两次 EDT、交付物取回、乐观并发、H3 风险确认、路由安全核对）**处理得当**。

本轮 Final 提出三类修正：

1. **对 GPT 的 Spike Requirement 给出可直接使用的技术答案**（不必等实现时才发现），见第 1 节。
2. **对"provisional EDT / final EDT"边界的定性做澄清**：这是 GUI 策略而非新后端概念，但仍需用户确认，见第 3 节。
3. **指出一项 GPT 未处理的新证据**：`OPEN_QUESTIONS.md` 在 GPT Rebuttal 提交（`13:00:45`）**之后**新增了 Q-009（`16:33:34`），直接质疑 GPT Slice 2→Slice 3 的顺序（Director 在 Voice 之前）。这不是我本轮临时提出的分歧，而是 Project Brain 在讨论期间发生的变化，按协议必须指出，见第 2 节。

---

## 1. 对 GPT "Spike Requirement"（Q2）的直接技术核实

GPT 在 03 的第 2 节写道："SCRIPT 与 DIRECTOR_IR 是否已有等价的人工修订来源链，需要在实现前核对。"

**FACT**（`vnext/storage/store.py`，`SINGLE_WRITERS`）：

```
"SCRIPT": {"HUMAN", "SCRIPT_PRIMARY", "SCRIPT_EDITOR"},
'DIRECTOR_IR': {'DIRECTOR'},
'EDT': {'TIMELINE'} / 'VISUAL_EDT': {'TIMELINE'}
```

`create_artifact` 强制 `created_by_role` 必须在对应集合内（`SINGLE_WRITER_VIOLATION` 否则拒绝）。

**结论（可直接回答 GPT 的 Spike，不必等实现）：**

- **SCRIPT**：`created_by_role` 可以直接是 `HUMAN`。修订级保护对 SCRIPT 可以简单实现为"最新修订的 `created_by_role == HUMAN`"。
- **DIRECTOR_IR / EDT**：`created_by_role` **永远不会是 `HUMAN`**（只能是 `DIRECTOR` / `TIMELINE`）。这意味着"目标是否存在人工修改"这个判断，**不能**通过读取 DIRECTOR_IR / EDT 自身的 `created_by_role` 得到，必须改为查询：是否存在一条 `EDIT_COMMAND`（writer 固定为 `COMMAND_BUS`），其 `before_revision` 等于该产物当前 head 的修订号。
- **对 P0 合同的具体影响**：revision guard 的判断逻辑不能是单一实现，需要按目标产物类型分两条路径写：SCRIPT 类查 `created_by_role`；DIRECTOR_IR/EDT 类查 `EDIT_COMMAND` 历史。这个分支在设计阶段就应该写进合同文本，不应该留到实现时才发现两种产物行为不一致。

**UNKNOWN**：`EDIT_COMMAND` 的 `before_revision`/`after_revision` 字段名与 `CommandBus.execute` 的完整实现我本轮未重读 `core/editing.py`，上述关于其存在性的判断沿用 Round 02 已提交的 `02_CLAUDE_REVIEW.md` 记录（该记录基于同一未变化的基线代码）。建议在 Slice 0 的 Spike 里把"对 DIRECTOR_IR/EDT 目标查询 EDIT_COMMAND 历史"作为验证项之一，而不仅是"核对"。

---

## 2. 新证据：Q-009 与 GPT Slice 2/3 顺序的冲突（未被本轮 Rebuttal 处理）

**FACT**：`OPEN_QUESTIONS.md` 当前版本（HEAD `171173c`）新增 Q-009，commit 时间 `2026-09-28T16:33:34Z`，晚于 `03_GPT_REBUTTAL.md` 的 commit 时间 `2026-09-28T13:00:45Z`。Q-009 原文记录用户已明确要求："下次与 Claude 的 Council 讨论必须加入此问题"，目标方案写为：

```
H2 Script → Narration Units → Voice → AudioTimingMap → Director → Storyboard → Final EDT → Render/QA
```

**CURRENT_IMPLEMENTATION（GPT 03 第 10 节）**：GPT 修订后的开发顺序是 `Slice 2 · Director → Storyboard` 在前，`Slice 3 · Voice → Final EDT` 在后——即 **Director 先于 Voice**，与 Q-009 提出的目标顺序方向相反。

**OPINION / 需要用户裁定**：

这不是我要求推倒 GPT 的 Slice 顺序，而是指出一个事实：Project Brain 里已经登记了一个与当前 Slice 顺序方向相反的用户诉求，且登记时间晚于 GPT 给出该顺序的时间，GPT 未能看到并回应它。有三种处理方式，需要用户选：

1. **D-001 按现有 Slice 2→3 顺序继续**，Q-009 留给未来的 D-002 单独处理（即先用"预估分镜 + 事后 retime"的现状顺序把 P0 GUI 打通，音画对齐问题作为已知代价，用 Spike 3 的证据决定是否需要局部修补）。
2. **在动工前先处理 Q-009**：把 Slice 2/3 对调为 `Voice → AudioTimingMap → Director → Storyboard → Final EDT`，则 GPT 03 第 9.2 节"provisional EDT 只预览、final EDT 在 voice 之后"这个折中方案**不再必要**——因为 Director 本来就在 Voice 之后运行，不存在"先出一版分镜、再被音频时钟重建"的问题，Round 02 指出的"用户在分镜阶段的调整会被音频时钟重建覆盖"这一根本风险也随之消失。
3. **先跑 Spike 3（依赖失效实测）**，用实测证据判断"配音后改 Beat 强制重录"的严重程度，再决定是按方式 1 打补丁，还是升级为方式 2 的顺序重排。

**PROPOSAL（Claude 倾向）**：方式 3。理由：Q-009 提出的是一个有吸引力的架构修正，但目前只是 `OPEN_QUESTIONS.md` 里的 `PROPOSAL` 级别陈述，没有 DEC 登记，也没有对现有 `Production.storyboard`／`Production.ir`（要求 Scene 时长之和等于 `estimated_duration`）等下游校验做过冲击评估。在没有 Spike 3 证据之前就重排 Slice，属于"用一个尚未验证的架构猜想替换掉一个已经收敛的执行计划"，本身也违反 Council 协议里"不把模型共识当作确认"的精神——只是这次要小心的对象换成了"不要把一个新的、有吸引力的用户设想未经验证就当作已确定方向"。但**方式 3 的窗口很短**：如果不在 Slice 0 一并做，等 Slice 2（Director/Storyboard GUI）已经按旧顺序建好之后再改，返工成本会显著高于现在。

---

## 3. "Provisional EDT / Final EDT" 边界的定性（回应 GPT 12.6 的提问）

**DESIGN_DECISION**（`DEC-005` 原文）：*"EDT 是唯一可编辑时间线；分镜/设计表是上游意图，Remotion 与剪映是消费者。"*

**FACT**（`SINGLE_WRITERS`）：只有一个 `EDT` 产物类型（以及历史遗留的 `VISUAL_EDT`），写权限固定属于角色 `TIMELINE`，产物本身不区分"provisional"与"final"两种类型。

**结论**：GPT 提出的"Storyboard 阶段的 EDT 只做内部预览、不开放人工编辑；配音后才生成 final editable EDT"，**技术上不是新增产物类型，而是一条 GUI 层策略**——同一个 `EDT` artifact type，只是在音频时钟落定之前，GUI 不暴露其编辑入口。这个定性很重要：

- 好处：不违反 DEC-005 的字面（"EDT 是唯一可编辑时间线"仍然成立，只是"可编辑"被 GUI 限定在某个时间窗口之后），不需要新登记 DEC，也不需要新的 schema。
- 但它**确实新增了一条未被 DEC-005 显式覆盖的产品规则**："人工可以编辑 EDT 的时间窗口，从'任意时刻'收窄为'AUDIO_TIMING_MAP 生成之后'"。这条规则本身没有错，但它是 P0 期间新引入的约束，应该被记录为本讨论的一项具体结论，而不是隐含在"provisional/final"这个尚未在代码里存在的措辞里，以免未来有人真的去建一个新的 `PROVISIONAL_EDT` 产物类型，制造出 DEC-005 从未授权过的第二条时间线。

**PROPOSAL**：Synthesis 或未来的 DEC 登记里，把这条规则写成："P0 期间，EDT 编辑入口只在 `AUDIO_TIMING_MAP` 存在后对用户开放；此前的 EDT 生成结果仅用于 Storyboard 预览，不提供编辑 UI。"不要使用"provisional EDT"这个会被误读为新产物类型的名字。

---

## 4. 逐项回应 GPT 03 第 12 节要求 Final 判断的 7 个问题

1. **修订级 revision guard 作为 P0 最小合同**：**同意**，但按第 1 节的技术核实，合同文本必须写清楚"SCRIPT 查 `created_by_role`，DIRECTOR_IR/EDT 查 `EDIT_COMMAND` 历史"这两条不同的判断路径，不能写成统一逻辑。

2. **字幕只读派生自 Script**：**同意**，作为 P0 边界合理。补充一点：现有机械 QA 已有 `SUBTITLE_*` 一类检查（Round 02 记录），P0 实现时应确认这些检查的输入就是"派生字幕"本身，而不是脚本原文，否则会出现"字幕检查用脚本文本、渲染用派生字幕文本"两份不同文本源的隐性分裂。此点未在 GPT 03 中提及，标 **UNKNOWN**，建议列入 Slice 3 的验证项，不需要单独 Spike。

3. **素材默认走 browser import/drag-drop，视为 P0 必需后端补充**：**同意**。补充：Round 02 已指出 `/media/folder` 现在接收路径字符串；新增的上传类路由必须落在 Slice 0 已接受的"mutating route 安全核对"范围内——即新路由要么从一开始就受 Origin/CSRF 中间件保护，要么在核对时一并扩大保护范围，不能作为"新功能"游离在核对范围之外。

4. **若 Spike 3 证明视觉改动会使 Voice 失效，同意最小依赖修正进入 P0**：**有条件同意**。条件见第 2 节——先看 Spike 3 的证据性质：如果根因是"细粒度依赖边缺失"这种局部 bug，按 GPT 原意做最小修正即可；如果根因其实是"Director 在 Voice 之前运行"这种顺序性问题（即 Q-009 描述的系统性根因），那么"最小修正"只是在错误的顺序上打补丁，应该触发第 2 节的方式 2/3 讨论，而不是直接进入实现。这个判断本身就应该是 Spike 3 的产出之一，建议 GPT 在设计 Spike 3 时把"根因是局部依赖边还是整体顺序"作为需要回答的问题，而不只是"是否失效"。

5. **Track A（短夹具+假 Provider）/ Track B（新题材+真实 Provider）二分足够**：**基本同意，一处遗漏未被吸收**。Round 02 建议 Track B 的题材应包含"至少一个需要数字强调的 Beat，以覆盖 `DIRECTOR_NUMBER_MISMATCH` 一类的事实绑定校验路径"，GPT 03 第 4 节的 Track B 描述中没有承接这一点，只写了"真实 Fact/Script/Director"。**PROPOSAL**：在 Slice 5 的 Track B 验收脚本里显式加入这一条，否则 Track B 有可能选到一个完全不触发事实绑定校验的题材，验收就漏掉了这条路径。

6. **provisional/final EDT 边界是否符合 DEC-005**：见第 3 节，结论是"符合，但应改称呼、并显式记录为 P0 新规则，不称为新产物类型"。

7. **是否还有可以继续砍的范围**：**一项建议**——GPT 03 的 P0 Definition of Done 清单里保留了"Version compare 只读并排 diff"（第 11 节倒数第几条对应 Slice 1）。这在 Round 02 里我已建议收窄为只读，GPT 已接受；这里进一步建议：**如果 Spike 1（严格模式脚本编辑）结果是 FAIL、需要补最小 Claim/Evidence 编辑 UI**，那么"只读 diff"应该在 P0 范围内继续保留，但"逐段接受/合并"的 UI（即使只读版本）优先级应该排在 Claim/Evidence 编辑 UI 之后，因为后者是 Spike 1 暴露出的真实阻塞，前者只是锦上添花。这不是新的砍除项，而是对已经收敛的清单给一个明确的相对优先级，避免两者被同等对待。

---

## 5. 未再提出异议的部分

- Q1（前端框架止损检查点）、Q3（最小异步 Job 合同的 8 点行为）、Q6（删除 Regenerate This Beat / Adjust Duration / 全量 Storyboard still 预览）、Q7（收窄 H1/Version compare/Track A）、9.3～9.6（交付物取回、乐观并发、H3 风险确认、路由安全核对）：GPT 的修订与 Round 02 的证据一致，本轮未发现新的技术分歧，不重复展开。

---

## 6. 结论标记

- 本文是 Round 04 Final，**不是 Decision**；未修改 `DECISIONS.md`、未实现代码、未创建 PR。
- 需要用户在 Synthesis / 后续裁定的核心分歧：**第 2 节的 Q-009 与 Slice 2/3 顺序冲突**——这是本轮唯一一处"证据本身在讨论期间发生变化、两个模型尚未就同一份证据达成一致"的实质分歧，其余均为收敛或可直接由代码证据回答的技术细节。
