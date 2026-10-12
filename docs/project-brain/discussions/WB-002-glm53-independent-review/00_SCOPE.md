# WB-002 · GLM 5.3 Independent Review · Scope

**Review ID:** WB-002
**Reviewer seat:** GLM 5.3（第 4 席 / Diversity Reviewer）
**实际执行者（重要更正，见第九节）：** 本轮**并非**由 GLM 5.3 模型执行。实际执行者是 WorkBuddy 会话中的同一底层模型（WB-001 轮的延续会话），以「GLM 5.3 评审席」的方法论与人设框架完成本轮。详见第九节「执行者身份更正声明」。
**Date:** 2026-09-29
**Repository:** `haiyang776688-web/content-os-vnext-phase1`（PRIVATE）
**Role boundary:** 本轮为独立 Review。未修改业务代码、Prompt、Renderer、Audio pipeline、QA、DECISIONS.md、D-002/D-003；未 merge、未创建 PR、未发布。唯一新增为 `WB-002-glm53-independent-review/` 目录。

---

## 一、Git 基准

| Ref | Commit | 说明 |
| --- | --- | --- |
| `main`（远端） | `06dfd328b8501bb13ebbb7f8335e8a40007cbb66` | 含 WB-001；本地等价 commit `dbcc6ba`（内容相同，sha 不同，因 push 通道问题） |
| `p0/gui-only-e2e-interim` | `323f7a2376efcfcfd1643a3e9d15333e084c1739` | 活动实现分支，与 WB-001 轮一致，未前进 |
| merge base | `6749578` | 未变 |

`git fetch origin` 因本机代理（`CONNECT tunnel failed / HTTP2 framing`）失败，远端状态经 `gh api` 逐项核对（main/p0 两个 ref 的 object sha + 最新 commit 文件清单）。本地工作区文件与远端 main 内容一致（git status 仅显示本地与 remote-tracking 的 ahead 1，为上述 sha 等价 commit）。

## 二、两阶段规则

### Phase A · Blind Independent Review

- 形成独立结论前**不读取** `WB-001-independent-gap-review/01_WORKBUDDY_REVIEW.md`（本轮实际执行：Phase A 结论全部基于本轮重新采集的代码 / commit / Track B 记录 / 实测数字推导完成后，才进入 Phase B 打开该文件）。
- **诚实声明（重要偏差披露）**：本轮 GLM 5.3 会话是 WB-001 轮的延续会话，WB-001 内容在本会话上下文中可见，**严格的盲评在物理上不可实现**。缓解措施：
  1. Phase A 全部关键证据（尤其 Track B slice 记录、p0 分支 diff、实测数字外推）为本轮**重新采集并重新计算**；
  2. Phase A 允许且实际得出了与 WB-001 相反或更精细的结论（见 01 的 G-05 / G-06 / G-07 / G-11）；
  3. 凡与 WB-001 重合的结论均标注「独立重验证」，供用户判断锚定程度。
- 证据优先级：**真实代码 / commit / test / artifact > 当前 Project Brain > 历史讨论 > 上一轮模型结论 > 模型自身推测**。

### Phase B · Review of WB-001

- Phase A 判断冻结后才读取 `WB-001/00_SCOPE.md` 与 `01_WORKBUDDY_REVIEW.md`；
- 对 FINDING-01～12 逐条给出 ACCEPT / MODIFY / REJECT / NEEDS_EXPERIMENT；
- **不回头修改 Phase A 文档**（01_GLM_BLIND_REVIEW.md 保持冻结状态）。

## 三、读取文件

### Project Brain（main@06dfd328 内容）

PROJECT_CONTEXT_MASTER / PRODUCT_TASTE / CURRENT_STATE / IMPLEMENTATION_STATE / DECISIONS / REJECTED_IDEAS / OPEN_QUESTIONS / COUNCIL_PROTOCOL / CHANGELOG / ARCHITECTURE / ROADMAP / HANDOFF_2026-09-29_P0_GUI_E2E。

### Council

- D-001：00_TOPIC、01_GPT_PROPOSAL（目录核对）、**04_CLAUDE_FINAL（本轮完整读取）**、05_SYNTHESIS（确认为 PENDING 占位）；
- D-002：00_TOPIC、01_GPT_PROPOSAL；02/03/04/05 确认全部为占位；
- D-003：00_TOPIC、01_GPT_PROPOSAL、02_CLAUDE_REVIEW；03/04/05 确认占位；
- research/SKILL_ABSORPTION_MATRIX.md。

### P0 分支记录（本轮新读，WB-001 轮未读）

- **p0-slices/SLICE-006-TRACK-B.md**（Track B 官方记录，本轮最重要新证据）；
- p0-slices/SLICE-001 至 SLICE-005（含 004A/004B）；
- p0-slices/fixtures/track-b-subtitle-source.txt（Track B 源材料）。

### 真实代码（main 与 p0 对照）

runtime.py、governance.py、production.py（含 p0 diff 全量）、contracts.py（phase2）、knowledge.py（本轮完整读取）、intelligence.py、visual.py（hardening，含 p0 diff）、audio.py、geometry.py、voices.py、workflow.py（含 p0 diff）、director_contract.py、gateway.py、remotion/adapter.py、remotion/resolver.py（本轮完整读取）、Composition.tsx（含 p0 diff——**本轮发现字幕深色衬底为 p0 新增**）、visual_state.py、stages.py；
registries：XIAO-Y_V1.json、XIAO-Y_TEMPLATES_V1.json、WRITING_DEFAULT.json、RESOLUTION_ORDER.json；
tests：test_p0_workflow.py（p0，节选）。

### 关键实测数字（来自 Track B / Slice 记录）

- Track B 最终 MP4：61.461333s，4,309,544 bytes（≈70.1 KB/s）；
- Synthetic 93.013s MP4：6,901,444 bytes（≈74.2 KB/s）；
- Track B 渲染：2m08s / 2m04s（61.46s 视频，≈2.05× 实时）；
- Storyboard stills：14 stills/28s、42 stills/67.1s（≈1.6–2.0s/still）；
- Voice：Track B 7 段 4m59s；synthetic 项目一次 ~14 分钟；
- Track B 结构：7 段 script / 7 beats（**1:1**）；MiniMax QA 两次均 PASS_WITH_RISK。

## 四、未验证项（UNKNOWN）

1. Track B 真实 VOICE payload 的 `word_timestamps` 是否非空（运行时数据不在 git）；
2. Track B 的 Director 是否显式填写了 `character_action_id`（SLICE-006 只记录 "several scenes reuse the same XIAO-Y pose"，未给 beat 明细）；
3. Track B 是否运行于 `presentation == 'XIAOY_EXPLAINER'`（dynamic treatment）模式；
4. render 时间随时长/beat 数的精确缩放曲线（线性外推仅为假设）；
5. Track B 两次 MiniMax QA 各 finding 的时间戳逐条准确率（官方记录无复核表；84 秒历史样片有复核表但属 HISTORICAL）；
6. 运行态数据库、真实 provider 响应体（按用户指令与隐私边界不读取）。

## 五、禁止修改范围（本轮坚守）

未触碰：`vnext/**`、`registries/**`、`contracts/**`、`docs/project-brain/**`（WB-002 目录外）、DECISIONS.md、D-001/002/003 的 Final Status、任何 prompt / renderer / audio / QA 代码；未自动接受任何 WB-001 Finding；未 merge、未建 PR、未发布。

## 六、冻结后更正记录（Post-freeze correction log）

`01_GLM_BLIND_REVIEW.md` 按任务书要求冻结。冻结后仅做过 **1 处非内容性更正**，如实记录：

| # | 位置 | 更正前 | 更正后 | 性质 |
|---|------|--------|--------|------|
| 1 | `01` G-11 标题行 | `45MB 与 storyboard 仍safely 非阻塞` | `45MB 与 storyboard 仍 safely 非阻塞` | 单词粘连，补空格。未改动任何结论、断言、证据或置信度 |

**未**因阅读 WB-001 或 Phase B 结果而回改 Phase A 的任何 Finding。Phase A 与 Phase B 之间的分歧（如有）保留原样，不做事后调和。

---

## 九、执行者身份更正声明（2026-09-29 补记）

**本轮文档中的「GLM 5.3」是评审席标签，不是对实际执行模型的真实描述。**

事实：

1. 用户要求「使用 GLM 5.3 作为主要 Reviewer」。当前 WorkBuddy 会话**无法切换底层模型**——无法调用 GLM 5.3，也无法调用混元 4。
2. 因此 WB-001 轮与 WB-002 轮的**实际执行者是同一个底层模型**（同一延续会话）。文档中出现的 `Hunyuan4`（WB-001）与 `GLM 5.3`（WB-002）**都是席位标签**，不代表模型族差异。
3. 本轮初版 `00_SCOPE.md` 第 4 行写作「本会话由 GLM 5.3 执行」，该表述不真实，已更正。

**这对 Council 机制的影响（用户必须知道）：**

| 影响面 | 说明 |
| --- | --- |
| **模型多样性收益未实现** | Council 的核心价值之一是不同模型族带来不同的系统性偏见。本轮**没有获得这个收益**。WB-001 与 WB-002 共享同一底层模型的归纳偏好。 |
| **盲评不可实现（已披露）** | 延续会话，WB-001 内容在上下文中可见。见第二节。 |
| **`03_MODEL_COMPARISON.md` 的性质要重新理解** | 它不是「两个模型的比较」，而是**同一模型在两个不同席位人设/方法论约束下的两次独立取证的差异**。这一点极重要：文中 8 项「GLM found but WB missed」真实反映了「换了取证方法会多挖出什么」，但**不能**被解读为「换模型能多挖出什么」。前者价值仍然存在（说明方法差异有效），后者价值为零。 |
| **「All three may share wrong assumption」的可信度** | 该节列出的四条共同盲区，其推理仍然成立（基于证据而非模型身份），但它**不能**证明「不同模型族都会犯同样的错」。只能说：同一模型在三种席位设定下都会犯。 |

**仍然成立的部分（不因身份更正而失效）：**

- `01_GLM_BLIND_REVIEW.md` 的 15 个 Finding，其证据是**本轮重新采集的仓库文件与运行记录**（p0-slices 实测数字、代码行号、commit diff），与执行者身份无关，可独立复核；
- `02` 对 WB-001 的逐条判决，依据是代码事实与实测数字，可独立复核；
- **G-05 / G-06 / G-07 / G-11 四条推翻或修正 WB-001 的发现，其推翻力来自数据，不来自模型身份**——WB-001 未读 p0-slices 是客观事实，45MB≈10 分钟容量是可复算的算术。

**建议（供用户决策，非本轮执行）：**

若要获得真正的模型族多样性，本轮文档应作为「席位方法论模板」保留，而 GLM 5.3 / Claude / GPT 各席需由对应模型**在独立会话中**实际执行。当前 WB-001 与 WB-002 应被标注为 **same-model, two-seat**，而非 two-model。
