# Model Council v0 · 研发讨论协议

**建立日期：**2026-09-28。Model Council 是 ChatGPT（GPT）与 Claude 围绕同一份 Content OS Project Brain 进行结构化讨论的**研发协作约定**，不是 Content OS 的产品功能、生产 Agent 或自动模型调用服务。当前由工作窗口协调资料读取、轮次传递和归档；本协议不要求 GPT API、Claude API 或自动桥接。

## 共同事实源与证据顺序

[Project Brain](PROJECT_CONTEXT_MASTER.md) 是两个模型共同使用的项目事实源。模型不得仅凭自己的聊天历史、上轮摘要或另一个模型的说法判断当前实现状态。每次讨论开始前，**GPT 与 Claude 各自**至少读取当前 `main` 分支上的下列文件，并在发言中记下所用 commit SHA、文件路径与读取日期：

1. [PROJECT_CONTEXT_MASTER.md](PROJECT_CONTEXT_MASTER.md)
2. [PRODUCT_TASTE.md](PRODUCT_TASTE.md)
3. [CURRENT_STATE.md](CURRENT_STATE.md)
4. [IMPLEMENTATION_STATE.md](IMPLEMENTATION_STATE.md)
5. [DECISIONS.md](DECISIONS.md)
6. [REJECTED_IDEAS.md](REJECTED_IDEAS.md)
7. [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)

项目状态发生冲突时，证据优先级为：**当前代码、测试与真实产物 > 当前 Project Brain > 历史文档 > 模型记忆**。如果 Project Brain 与更高优先级证据冲突，要指出具体路径、版本和证据，不能静默改写任何一方。无法核实的事项标为 `UNKNOWN`。设计意图和产品取向需要保留其已确认来源，不能由代码现状反向推断用户改了主意。工作窗口为同一讨论固定一个基准 commit SHA；若 `main` 在讨论中前进，先核对变更并让双方重读受影响文件，再继续评估。

## 发言标记与审查责任

每项重要陈述都标明性质；同一段同时涉及多种性质时分开陈述：

| 标记 | 含义 | 最低依据 |
| --- | --- | --- |
| `FACT` | 可由来源直接核对的项目事实或证据结果 | 文件/产物路径、测试记录或可重复检查 |
| `CURRENT_IMPLEMENTATION` | 当前代码、配置、GUI 与真实运行各自已经做到的范围 | 代码位置、运行结果；明确区分代码存在与 GUI 可用 |
| `DESIGN_DECISION` | 用户已明确确认且登记在 `DECISIONS.md` 的方向 | DEC ID；不得把模型共识当作确认 |
| `PROPOSAL` | 尚待评估或用户决定的改动建议 | 目标、收益、代价和验证方式 |
| `OPINION` | 模型的判断或偏好 | 说明推理与所依赖的前提 |
| `UNKNOWN` | 证据缺失、相互矛盾或尚未决定 | 说明缺什么证据、谁能决定 |

GPT 和 Claude 都必须主动检查并指出：错误前提、逻辑漏洞、过度设计、重复模块、隐藏成本、与现有实现的冲突，以及与 [PRODUCT_TASTE](PRODUCT_TASTE.md) 的冲突。禁止互相客套或简单附和。同意时说明依据与适用边界；不同意时给出可核对的证据、具体反例或代价。模型分歧不采用多数票；事实由证据决定，取舍由用户决定。

## 默认轮次与停止条件

默认最多进行以下五步，由工作窗口按 [讨论归档约定](discussions/README.md) 保存对应文件：

`GPT Proposal → Claude Review → GPT Rebuttal → Claude Final → Synthesis`

`00_TOPIC.md` 在首轮前固定讨论范围。每一轮只基于共同事实源、已归档的上一轮文字与可核对证据发言。Claude Review 必须检查 GPT Proposal；GPT Rebuttal 只回应实质异议；Claude Final 对仍有分歧的点给出最终评估；Synthesis 分开保留共识、分歧和待用户决定项。完成 Synthesis 后停止，不自动增加模型互评轮次；如需继续，由用户明确指定新范围或开启新 Discussion。

## 决策保护

**Proposal 不等于 Decision。**GPT 与 Claude 均无权自行修改 [DECISIONS.md](DECISIONS.md)，工作窗口也不能把模型共识自动升级为正式决策。讨论完成但用户尚未明确表态时，`05_SYNTHESIS.md` 的 `Final Status` 必须为 `READY_FOR_HUMAN_DECISION`；不能写入 `DECISIONS.md`。

只有用户对具体结论明确说出 `ACCEPT`（或同等明确的接受表述）后，工作窗口才可新增 `DEC-XXX`，记录讨论 ID、被接受的具体范围、日期、理由、影响组件及用户确认依据。部分接受只登记被接受部分，其余仍作为 Proposal/分歧留在讨论目录，`Final Status` 在剩余事项未决时保持 `READY_FOR_HUMAN_DECISION`。用户拒绝或后续决策取代时，保留原始讨论和状态变化记录，不篡改历史。项目正式决策与实际实现是否一致，仍按 [IMPLEMENTATION_STATE](IMPLEMENTATION_STATE.md) 分开核验。
