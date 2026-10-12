# Project Brain 变更记录

此日志只记录 `docs/project-brain/` 知识层的变化，不代替代码版本、视频生产日志或产品发布说明。

## 2026-10-12 · Open-source archive transition

- Marked active development as paused and the project as seeking a maintainer.
- Added archive notices to the master context, current state, implementation state and roadmap so dated P0 GUI experiment claims are not mistaken for the sanitized public baseline.
- The public snapshot uses the validated MDC baseline and excludes the incomplete, uncommitted GUI-001 worktree.
- Current public status is defined by the root README, local inventory, security audit and maintainer handoff; historical Project Brain decisions remain preserved.


## 2026-09-29 · Council / WorkBuddy 综合复核收敛

- 新增 [COUNCIL_SYNTHESIS_2026-09-29](discussions/COUNCIL_SYNTHESIS_2026-09-29.md)，把 Track B、D-002、D-003、WB-001、WB-002 与代码复核整理为 Claude 可直接再审的统一证据包。
- 明确更正 WB-002 身份：该轮并非真实 GLM 5.3 独立模型评审，而是同一 WorkBuddy 底层模型在延续会话中的第二套评审方法；技术证据可引用，但不得作为 Hunyuan4 vs GLM 5.3 能力比较。
- Creative FAIL 从单因归因改为多因子假设：题材/媒体证据供给、Director 控制权、VisualResolver 映射、motion/pattern vocabulary、Storyboard/QA 可观察性共同作用；未把任何模型的 root-cause 判断升级为 Decision。
- D-002 问题收窄：Track B 为 7 segments / 7 beats，segment/beat 外边界已由真实 AudioTimingMap 锚定；下一步比较 current retime、phrase/word anchor、full Audio-first，分别验证「切在哪里」与「切几刀」。
- 校正 WB-001 的长视频风险：45MB 按 Track B 当前码率不是 3–5 分钟已证明 blocker，Storyboard stills 是耗时风险；300s render timeout 是优先实测候选。
- 记录 P0 subtitle 深色衬底与 Mechanical QA metadata 规则脱节、XIAO-Y first-match fallback、write-only semantic fields、MiniMax 1fps temporal limitation 等已复核问题。
- 更新 [CURRENT_STATE](CURRENT_STATE.md) 与 [IMPLEMENTATION_STATE](IMPLEMENTATION_STATE.md)；分支计数改为记录本轮写入前基线（`main@504ecc4` 时 P0 ahead 10 / behind 28），并明确后续 main 文档提交会使该计数继续变化，合并前必须重新 compare。
- 未修改业务代码、`DECISIONS.md`、D-001/D-002/D-003 Final Status，也未把 Council 结论自动升级为正式产品决策。

## 2026-09-29 · P0 GUI-Only E2E 交接纠错

- 核对上传交接 ZIP 的 `DELIVERY_MANIFEST.json` 与 GitHub 活动分支 `p0/gui-only-e2e-interim@323f7a2`；确认该包代表比旧 Phase 2.1 文档更新的 P0 实现快照。
- 新增 [HANDOFF_2026-09-29_P0_GUI_E2E](HANDOFF_2026-09-29_P0_GUI_E2E.md)，纠正 126/189 tests、旧 84 秒主样片、数据库是否随包交付、Jianying 是否真实打开验收、H3 是否用户批准等过期或冲突表述。
- 更新 [CURRENT_STATE](CURRENT_STATE.md)、[IMPLEMENTATION_STATE](IMPLEMENTATION_STATE.md)、[PROJECT_CONTEXT_MASTER](PROJECT_CONTEXT_MASTER.md)：记录 Track A/B、205 passed 分支证据、61.46 秒 Track B、Engineering PASS / Creative FAIL、P0 branch 与 main 分叉、D-002/D-003 未决。
- 上传快照外部复核：205 tests collected；新 P0/XIAO-Y 重点测试 23 passed in 7.03s。外部沙箱未在 90 秒窗口完成全量 205 项，因此未伪称再次独立验证 205 passed。
- 未修改 `DECISIONS.md`，未把 D-001/D-002/D-003 自动升级为正式决策，未把 P0 branch 业务代码直接强推到 main。

## 2026-09-29 · D-002 / D-003 Council 议题

- 新建 `D-002-audio-first-director-pipeline/`：把 Q-009 的 Audio-first 流程问题升级为正式 Council 议题；同时纳入 D-001 Claude Final 的既有意见——先用 Spike 区分局部依赖失效与 Director-before-Voice 的系统性顺序问题，再决定是否正式重排主链。
- 新建 `D-003-role-prompt-quality-contract/`：记录当前角色 Prompt 过薄、职责/审核标准不完整、hardcoded system prompt 分散等问题；GPT Proposal 提出 Role Prompt Pack + Model Adapter + Quality Rubric + Qualification Suite 的候选架构，等待 Claude Round 02 完善。
- `OPEN_QUESTIONS.md` 新增 Q-010，登记 Prompt Governance / Role Prompt System 为待决问题。
- 未修改 `DECISIONS.md`，未把 D-002/D-003 的模型建议升级为正式产品决策，也未修改业务代码。

## 2026-09-28 · Model Council v0 协议

- 新增 [COUNCIL_PROTOCOL](COUNCIL_PROTOCOL.md)：两个模型各自读取共同事实源、标记发言性质、最多五步讨论，并把正式决策权留给用户。
- 更新 [讨论归档约定](discussions/README.md)：每个正式议题使用 `D-XXX-topic/` 六文件结构；综合结论在用户明确接受前维持 `READY_FOR_HUMAN_DECISION`。
- 本次只调整 Project Brain 文档，没有创建第一场讨论，也没有修改 `DECISIONS.md` 或业务代码。依据为用户本轮明确提出的 Model Council 研发协作要求。

## 2026-09-28 · 初版

- 创建入口、产品取向、架构、当前状态、严格实现核验、已确认决策、弃用方案、路线图、开放问题与讨论归档约定。
- 按“当前仓库代码/产物/测试 → 项目已有文档 → 本窗口 Content OS 历史”整理；无法独立核对的原始决策日期、Claude 逐字讨论等标为 `UNKNOWN`。
- 记录四项现状冲突：旧能力路线图落后于 MiniMax QA/H3；DeepSeek Red Team 目标与现有 Worker 分配不符；旧声音注册表与本次本地克隆声音产物不同步；发布/Analytics 导航入口与实际 `notImplemented` 阶段视图不同。
- 本次只新增项目知识文件，没有改动现有生产代码、现有项目文档或运行数据。此仓库目录没有 Git 元数据，未创建 commit。

后续更新必须写明日期、改了哪些知识条目、依据是什么；若仅是模型意见，先存 [讨论记录](discussions/README.md)，不要直接改已确认决策。
