# Model Council 讨论归档约定

本目录保存 GPT、Claude 围绕同一个 GitHub Project Brain 的结构化讨论。先读 [Council 协议](../COUNCIL_PROTOCOL.md)。讨论原文和综合结论是研发资料，不是产品运行配置；模型建议不自动成为 [正式决策](../DECISIONS.md)。每轮由工作窗口协调，不调用 GPT/Claude API 自动对话。

## 一个议题，一个目录

每次正式讨论新建独立目录 `D-XXX-topic/`，`XXX` 为递增三位编号，`topic` 为简短英文小写连字符名称。不要复用 ID。目录固定包含：

```text
D-XXX-topic/
├── 00_TOPIC.md
├── 01_GPT_PROPOSAL.md
├── 02_CLAUDE_REVIEW.md
├── 03_GPT_REBUTTAL.md
├── 04_CLAUDE_FINAL.md
└── 05_SYNTHESIS.md
```

`00_TOPIC.md` 至少逐项记录 `Discussion ID`、`Date`、`Topic`、`Why Now`、`Relevant Project State`、`Question`、`Constraints`、`Human Decision Required`。其中 `Relevant Project State` 要列本轮读取的 `main` commit SHA、Project Brain 文件路径、当前代码/测试/产物证据及未核实项。工作窗口先固定问题和约束，再开始第一轮。

`01` 至 `04` 保存各模型对应轮次的原文，或明确标为摘要的内容。每份记录标注模型、日期、会话链接/ID（若可取得）、使用的仓库 commit SHA、实际读取路径、是否完整，以及 `FACT` / `CURRENT_IMPLEMENTATION` / `DESIGN_DECISION` / `PROPOSAL` / `OPINION` / `UNKNOWN` 分类。不得把整理者的话伪装为模型原文。缺失轮次要注明原因，不填造模型意见。

`05_SYNTHESIS.md` 必须按下列标题保留全部栏目，即使某栏为“无”或 `UNKNOWN`：

```markdown
# Consensus

# Remaining Disagreement

# Facts Confirmed

# Assumptions Challenged

# Risks Identified

# Proposed Changes

# Changes NOT Recommended

# Human Decisions Required

# Final Status
```

`Facts Confirmed` 要指向当前证据；`Consensus` 仅指模型讨论的一致意见，不代表事实或用户决定。`Human Decisions Required` 应逐项列可接受、拒绝或进一步核验的具体结论。`Final Status` **只能**填写 `OPEN`、`READY_FOR_HUMAN_DECISION`、`ACCEPTED`、`REJECTED`、`SUPERSEDED` 中的一个：

| 状态 | 使用条件 |
| --- | --- |
| `OPEN` | 讨论尚未完成默认轮次或证据核对 |
| `READY_FOR_HUMAN_DECISION` | 已形成综合结论，等待用户明确决定；这是未获确认时的默认终态 |
| `ACCEPTED` | 用户明确接受了已标定范围的结论，并记录确认依据与对应 DEC ID |
| `REJECTED` | 用户明确拒绝该结论，并记录依据 |
| `SUPERSEDED` | 后续已确认决定取代本讨论，记录新讨论/DEC ID |

只有用户明确 `ACCEPT` 后，工作窗口才可更新 [DECISIONS.md](../DECISIONS.md) 并在 [CHANGELOG.md](../CHANGELOG.md) 留痕。此前不得写入正式决策，也不得用模型多数票消除分歧。状态变化要追加日期与依据，不覆盖讨论原文。归档中不要放 API Key、私人音频或未经授权的媒体。

早期 ChatGPT 历史引用 `6ab15bc8-2d5c-83ec-a72e-b26e77e879c9` 目前未导入完整逐字记录；已有 Claude 云端聊天也不自动成为 Council 讨论。需要引用时，另行记录来源和完整性，不伪造 `D-XXX` 的正式轮次。
