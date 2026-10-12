# GPT Rebuttal · D-001

**Model:** GPT-5.6 Sol  
**Date:** 2026-09-28  
**Round:** 03 · Rebuttal  
**Baseline commit:** `ea0d72748ff927c957183405069b6223d2b168c1`  
**Claude Review commit:** `70f0849f0ddb5b6c581f7572552be1a72a8a8444`  
**Read completeness:** 已完整读取 `02_CLAUDE_REVIEW.md`，并重新核对 D-001 Topic、Proposal、Council Protocol、CURRENT_STATE、IMPLEMENTATION_STATE、DECISIONS、OPEN_QUESTIONS。没有重新执行本地测试或浏览器操作。

---

## 0. 总体回应

**OPINION**

Claude 的主要批评成立。它没有推翻“验收优先、垂直切片、P0 不以框架迁移为前提”的方向，而是指出我第一轮把若干**新后端合同**错误估价成“GUI 接入”。

我接受并修订以下六点：

1. `user_override=true` 不是足够稳的 P0 合同，尤其在 clip ID 会随重生成变化时。
2. Job UX 不是纯前端工作；P0 至少要补异步返回、single-flight、孤儿 RUNNING 清理与 Retry。
3. `Regenerate This Beat` 与自由 `Adjust Duration` 不应进入 P0，因为当前后端没有对应稳定合同。
4. 85 秒既有样片不能作为唯一 Golden Scenario；它只能作为回归参考，不能证明“全新项目线性 GUI 路径”。
5. Timeline 不应允许直接破坏 AUDIO_TIMING_MAP 主时钟的 VOICE/SUBTITLE Move/Trim/Duration。
6. P0 在真正开发前需要 4 个时间盒 Spike，把“未知阻塞”变成证据。

同时保留三条主张：

- P0 仍应以 **GUI-Only E2E** 为唯一主线。
- 前端框架迁移仍不应成为 P0 前提，但应设置显式止损检查点。
- H4 / Publish / 完整 Analytics / 完整 NLE / 更多 Agent 仍应排除在 P0 之外。

---

## 1. Q1 · 框架迁移：接受“止损检查点”，不接受现在迁移

**FACT**

Q-001 仍开放，没有已确认的框架迁移决策。

**REBUTTAL / PROPOSAL**

接受 Claude 的修订：

- P0 **不迁框架作为前提**。
- 但不是“永远不迁”，而是在 **Slice 2（Storyboard 可用）后设置一次固定 Architecture Checkpoint**。
- Checkpoint 只看证据：
  - E2E 是否频繁因前端状态同步失败；
  - 同一状态/交互是否在多个 JS 文件重复修；
  - 新面板是否已经需要不可控的全局状态；
  - 安全转义与事件绑定是否开始产生重复缺陷。

P0 期间新增三条前端卫生约束：

1. 不可信文本统一转义，不在各页面自行拼接未转义 HTML。
2. 新 GUI 状态经一个小型统一状态入口，不允许继续扩散隐式全局变量。
3. 每个 Slice 的 Browser E2E 是退出条件，不允许“页面都写完最后再测”。

**OPINION**

这比现在迁移更可控，也比“遇到阻塞再说”更有纪律。

---

## 2. Q2 · 人工修改保护：接受“修订级保护”作为 P0 合同

**DESIGN_DECISION**

DEC-009 只要求：人工修改不能被 AI 再生成静默覆盖；它没有要求 P0 必须做到字段级智能 merge。

**REBUTTAL**

我撤回第一轮的 `user_override=true + 字段级 Keep User Changes` 作为 P0 默认实现。

Claude 指出的两个问题成立：

- clip ID 可能随 composition/audio hash 变化，不能把跨重生成保护建立在不稳定 clip_id 上；
- “不做 merge”却又承诺“重生成并保留字段”在语义上自相矛盾。

**REVISED PROPOSAL**

P0 采用**修订级保护（revision guard）**：

> 当目标产物在最近一次 AGENT/SYSTEM 生成后存在 HUMAN 修改时，任何可能重建该产物的 AGENT/SYSTEM 操作默认拒绝，并返回 `HUMAN_EDITS_PRESENT`（或等价状态）。

GUI 只提供两个明确动作：

- **保留当前人工版本**：取消本次重生成；
- **丢弃我的修改并重新生成**：用户明确确认后才允许重建。

P0 **不承诺自动字段合并**，也不显示一个容易误导的“Keep User Changes while Regenerating”。

**SPIKE REQUIREMENT**

Claude 已证明 EDT 有 revision / actor / EDIT_COMMAND 基础，但 SCRIPT 与 DIRECTOR_IR 是否已有等价的人工修订来源链，需要在实现前核对。若现有记录不统一，P0 可在 server/service 层实现等价的“head 之后是否存在 HUMAN revision”检查，但不能假装已有。

字段级 stable semantic address、重放人工命令、三方 merge 继续留在 Q-002。

---

## 3. Q3 · Job：接受“最小后台执行”是 P0 后端工作

**CURRENT_IMPLEMENTATION**

根据 Claude 的静态核对，当前 render/voice 等长操作存在同步请求路径，且重复点击可能并发重复渲染。

**REBUTTAL**

我撤回“Job UX 主要是 GUI 接入”的估价。P0 必须补一个**最小异步执行合同**。

但我不冻结具体实现为“线程”；机制可以是 FastAPI background task、受控线程或本地 worker。P0 冻结的是行为：

1. 长操作快速返回 `202 + job_id`。
2. 至少有 `RUNNING / SUCCEEDED / FAILED`（是否需要 QUEUED 由实现决定，不为 UI 好看强加状态）。
3. 同一 `(project, kind, target revision)` 必须 single-flight。
4. 服务启动时遗留 RUNNING 必须变为明确失败态，如 `SERVER_RESTARTED`，而不是永久悬挂。
5. GUI 刷新后能重新读取 Job 状态。
6. 失败后能从安全阶段 Retry。
7. 不展示伪造百分比；只显示阶段 + 已用时间。
8. Render 必须绑定 EDT revision；完成时若 head 已变化，结果标 stale，不冒充最新。

**P0 EXCLUSION**

仍不做：
- 多机 worker；
- durable distributed queue；
- 任意暂停/恢复；
- 跨进程精确续跑。

---

## 4. Q4 · Golden Scenario：接受“三层验收”，不再把 85 秒旧项目当唯一 Golden

Claude 的关键判断成立：

> 既有 85 秒项目包含非线性和人工 API 操作，复用它只能验证已有资产/产物，不足以证明“全新项目 GUI 线性路径”。

**REVISED PROPOSAL**

### Track A · Deterministic Browser Regression

从**空项目**开始：

- 10–15 秒；
- 约 3 个 Beat；
- Provider 边界使用受控假服务；
- 真实浏览器点击；
- 不调用内部业务 API 跨阶段；
- 仍执行真实短 Remotion render，以验证 Render/Download 路径；
- 不消耗真实云模型费用。

### Track B · Fresh Live Acceptance

从**从未使用过的新题材**开始：

- 真实 Provider；
- 真实 Fact/Script/Director；
- 真实本地克隆声音；
- 真实 Render；
- Mechanical QA；
- MiniMax Visual QA；
- H3；
- MP4 取回；
- 可选 Jianying Export。

建议时长先控制在约 60–90 秒，目的是证明新项目线性路径，而不是同时挑战 4 分钟稳定性。

### Track C · Long-form Stability（P0 通过后）

再跑 3–5 分钟真实内容，才评估目标生产时长的稳定性。

**85 秒现有项目的新定位**

保留为 **Known Regression Case**，用于验证旧能力没有被 P0 GUI 改造破坏；不再把它称为 P0 唯一 Golden Scenario。

---

## 5. Q5 · Timeline：接受进一步收窄

**DESIGN_DECISION**

EDT 仍是唯一可编辑时间线（DEC-005）。

**REVISED PROPOSAL**

P0 Timeline 只面向**视觉与展示层**：

- Preview / Playhead；
- Jump to Scene / Beat；
- 选择视觉/文字 element；
- Replace Asset；
- 修改视觉属性；
- Undo；
- 查看 revision / stale 状态。

P0 不允许用户直接对以下 AUDIO_TIMING_MAP 派生轨做 Move/Trim/Duration：

- VOICE；
- SUBTITLE。

否则会破坏主时钟并与 Mechanical QA 冲突。

### 字幕文字

**PROPOSAL**

P0 中字幕文本默认**只读派生自已批准脚本**。要修正字幕内容，用户回到 Script 修改，并明确提示下游会失效/需要重建。

原因：允许字幕独立于已批准脚本，会立刻引入“事实绑定、口播、字幕三者谁是真源”的新合同，不适合作为 P0 默认能力。

这项仍应由用户最终确认。

---

## 6. Q6 · 接受删除两个“伪轻量”功能

### 6.1 Regenerate This Beat

**ACCEPT**

从 P0 删除自动 `Regenerate This Beat`。

当前 P0 只允许：

- 用已有 `SET_BEAT` 能力修改后端已经支持的字段；
- 或整段/整个 Director 重新生成，但受“修订级保护”约束。

单 Beat 模型重生成、局部依赖失效和局部人工修改 merge 留到 P1。

### 6.2 Adjust Duration

**ACCEPT**

从 P0 Storyboard 的自由编辑项删除。

时长在配音前后受 Scene contract 与 AUDIO_TIMING_MAP 约束，不能把一个看似简单的 Duration 输入框当成局部 UI 属性。

### 6.3 Preview

**ACCEPT**

人工 `SET_BEAT` 后的快速反馈优先使用已有 preview/composition frame 路径，而不是每次都调用完整 Remotion still 生成整板。

正式 Storyboard still 只在 Gate 前生成。

### 6.4 Script 编辑不是纯文本框问题

**ACCEPT**

严格模式下的 claim/fact binding 可能让“直接改一句脚本”需要额外 UI。

因此这不是默认已解决能力，进入 Spike 1。

---

## 7. Q7 · 再砍一轮范围

接受 Claude 的以下收缩：

- 不新增第二套“页面阶段状态合同”；Next Action/Status 应优先由现有 stage/gate/artifact 状态做纯函数投影。
- P0 不实现完整 H1 Gate；只实现**新建项目与开始生产**。
- Version compare 只做只读 side-by-side diff，不做逐段 merge。
- Track A 不跑 85 秒真实云流程；使用短夹具。
- 不做 VOICE/SUBTITLE Move/Trim/Duration。
- 不做进度百分比。
- 不做单 Beat AI regenerate。
- 不做自由 Beat duration 编辑。

---

## 8. Q8 · 接受 4 个 Spike，并将它们前置到 Slice 0

**REVISED SLICE 0**

在大规模 GUI 改造前，先做 4 个 0.5–1 天时间盒 Spike。产物只允许是：

- PASS / FAIL；
- 证据；
- 阻塞说明；
- 对 P0 scope 的影响。

不得借 Spike 顺手做大重构。

### Spike 1 · Strict Script Edit

验证：

> 浏览器里改一句口播 → claim/fact 重新绑定 → strict mechanical 检查通过 → H2 可继续。

如果 FAIL，P0 必须加入最小 Claim/Evidence 编辑 UI。

### Spike 2 · Fresh Project Voice

验证：

> 全新项目通过 GUI 选择/生成本地克隆声音，得到有效 AUDIO_TIMING_MAP，而不是依赖旧项目已有产物。

同时核对声音 consent/registry 冲突。

### Spike 3 · Dependency Invalidation

验证：

> VOICE 已存在后，仅修改视觉 Beat，会不会错误地强制重录/重建无关上游。

**PROPOSAL**

如果证据显示“纯视觉改动会使 VOICE 无条件失效”，我赞成把**最小细粒度依赖修正**提入 P0。因为这会直接破坏普通用户返工体验，不能用“P1 再优化”掩盖。

但只修导致 GUI E2E 不可用的依赖边，不扩成完整增量构建系统。

### Spike 4 · Long Job

验证：

- 异步返回；
- single-flight；
- orphan RUNNING → FAILED；
- refresh 后可查看；
- Retry；
- 记录 Render / Storyboard / Voice / MiniMax QA 实际耗时。

---

## 9. Claude 指出的遗漏步骤：逐项吸收

### 9.1 素材 / 来源导入

**ACCEPT**

这是 P0 必经路径，不能继续隐藏在“Asset Resolver 已有”后面。

**PROPOSAL**

P0 不把“粘贴本机绝对路径”作为普通用户默认流程。

优先做浏览器可理解的本地导入：

- File input / drag-and-drop；
- 上传/复制到项目受控 media workspace；
- 返回 media asset；
- 对图片/视频显示缩略图和可用状态。

文件夹批量导入可使用浏览器 folder selection（能力允许时）或后续补充；不让用户手工输入内部路径作为主流程。

这确实是一个**GUI 必需的最小后端补充**，不是纯 UI。

### 9.2 两次 EDT 与“何时允许人工 Timeline 编辑”

Claude 指出的覆盖风险非常重要。

**REVISED PROPOSAL**

- Storyboard 阶段的 provisional EDT 视为**内部预览产物**，不开放给用户做最终 Timeline 编辑。
- 用户的视觉调整在 Storyboard 阶段落在 Director IR / SET_BEAT 层。
- 配音完成、AUDIO_TIMING_MAP 生成后，再构建 **final editable EDT**。
- Timeline 人工编辑从这一步之后才开放。

这样避免“用户先改 EDT → 生成声音 → EDT 被重建 → 人工修改消失”的必然坑。

如果当前代码强制暴露 provisional EDT，也只显示 preview，不承诺它是可编辑 head。

### 9.3 交付物取回

**ACCEPT**

“有 EXPORT artifact”不等于用户拿到文件。

P0 Deliver 必须提供：

- MP4 直接 Download；
- Jianying 导出若成功：提供可下载 bundle（优先 ZIP）或明确可操作的本地取回入口；
- UI 显示路径/包内容/导出损失说明；
- 没有 EXPORT artifact 就不能显示“已完成剪映交接”。

具体 bundle 形态在实现前核对现有 exporter。

### 9.4 Optimistic Concurrency

**ACCEPT**

所有 GUI 写操作都必须携带当前 `expected_revision`（或等价版本条件）。冲突返回明确 UI，不允许刷新/后台更新后静默覆盖。

这不是高级功能，而是 DEC-009 的基础保障之一。

### 9.5 H3 风险确认

**ACCEPT**

H3 GUI 不是一个“通过”按钮。

当存在 risk 时必须：

- 显示风险代码与来源；
- 逐条确认必要风险；
- 提供 APPROVE / APPROVE_WITH_RISK / REJECT；
- 保留 `publish_authorized=false`，不把 H3 混成 H4。

### 9.6 Mutating Route 安全核对

**ACCEPT AS CHECK**

Slice 0 增加一次当前基线的 mutating route Origin/CSRF/localhost exposure 核对。

这不是要求 P0 建完整安全平台，但不能在 GUI 扩大写操作面时忽略基础来源校验。

---

## 10. 修订后的 P0 开发顺序

### Slice 0 · Acceptance + Spikes

- 冻结 Browser Acceptance Script；
- 建短夹具 + Provider boundary fake；
- Spike 1 Strict Script Edit；
- Spike 2 Fresh Voice；
- Spike 3 Dependency Invalidation；
- Spike 4 Long Job；
- Mutating route security check；
- 根据证据更新 P0 scope。

### Slice 1 · Project → Source/Fact → Script → H2

- New Project（不实现完整 H1 Gate）；
- 浏览器本地素材/来源导入；
- Source/Fact Inbox；
- Script editor；
- Claim/Evidence 最小编辑能力（仅在 Spike 1 证明需要时）；
- Audit findings；
- read-only version diff；
- H2。

### Slice 2 · Director → Storyboard

- Scene/Beat 卡片；
- quick preview；
- Action/Asset/Text/Pattern 等**现有 SET_BEAT 支持范围**内的修改；
- Storyboard still；
- Gate；
- revision guard；
- 完成后执行前端架构止损 Checkpoint。

### Slice 3 · Voice → Final EDT → Preview

- Fresh voice path；
- AUDIO_TIMING_MAP；
- final editable EDT；
- 视觉/文字层有限编辑；
- optimistic concurrency；
- Undo；
- revision guard；
- VOICE/SUBTITLE 不提供自由 Move/Trim/Duration。

### Slice 4 · Jobs → Render → QA → H3 → Deliver

- 最小后台 Job 行为；
- single-flight；
- stale result 标记；
- Render；
- Mechanical QA；
- MiniMax Visual QA；
- H3 risk acknowledgment；
- MP4 download；
- optional Jianying bundle retrieval。

### Slice 5 · Acceptance

Track A：
- fresh empty project；
- short deterministic fixture；
- browser only；
- fake provider；
- real short Remotion render。

Track B：
- fresh unseen topic；
- real provider；
- real voice / render / QA / H3。

Track C（P0 后）：
- 3–5 分钟稳定性。

---

## 11. 修订后的 P0 Definition of Done

**PROPOSAL**

P0 通过必须同时满足：

- [ ] 全新项目可从 GUI 创建并进入生产。
- [ ] Source / Media 能从 GUI 导入，不要求手填内部 JSON/API；默认流程不要求粘贴内部绝对路径。
- [ ] Script 人工修改可以通过 strict fact/claim 校验并继续 H2。
- [ ] Director/Storyboard 可用卡片/选择器完成至少一次真实视觉修订。
- [ ] Storyboard 阶段的 provisional EDT 不被误当成最终人工编辑真源。
- [ ] Fresh project 可以从 GUI 生成有效本地 Voice/AUDIO_TIMING_MAP。
- [ ] Final editable EDT 在声音主时钟确定后产生。
- [ ] 用户至少完成一次视觉/文字 Timeline 修改并 Undo。
- [ ] 人工修订存在时，Agent/System 重生成默认被 revision guard 阻止，不会静默覆盖。
- [ ] 所有写操作使用 revision 条件，冲突不静默覆盖。
- [ ] 长操作异步返回、single-flight、刷新可恢复查看、孤儿任务可失败恢复、Retry 可用。
- [ ] Render 绑定 EDT revision，过期结果不冒充最新。
- [ ] Mechanical QA、Visual QA、H3 都从 GUI 可操作并留下正式产物。
- [ ] Visual QA scope 明确，VISUAL_ONLY 不冒充声音 QA。
- [ ] H3 风险需明确确认，且仍不授权 H4。
- [ ] MP4 可以直接取回。
- [ ] 可选 Jianying 成功时，用户能实际取回草稿 bundle，不只是看到 EXPORT 标记。
- [ ] Track A fresh-project deterministic browser E2E 通过。
- [ ] Track B fresh-topic live acceptance 通过。
- [ ] 旧 85 秒项目作为 regression case 未被 P0 改造破坏。
- [ ] 不把上述结果宣传成 3–5 分钟稳定量产已完成。

---

## 12. 仍需 Claude Final 重点判断的分歧/建议

在 Claude Final 中，我希望它重点判断以下收敛是否足够：

1. **修订级 revision guard** 是否可作为 P0 对 DEC-009 的正式最小合同；字段级 merge 继续放 Q-002。
2. **字幕文本只读派生自 Script** 是否是 P0 最稳边界。
3. **素材默认走 browser import/drag-drop**，而不是粘贴本机路径，是否值得纳入 P0 必需后端补充。
4. 若 Spike 3 证明视觉 Beat 修改会使 Voice 失效，是否同意把**最小依赖边修正**提升到 P0。
5. Track A 使用**短夹具 + 假 Provider + 真实短 Remotion render**，Track B 使用 fresh unseen topic + real provider，是否足够避免过拟合。
6. “provisional EDT 只预览、final EDT 在 voice timing 后才开放人工编辑”的边界是否符合现有事实源和 DEC-005，还是会引入新的概念债。
7. 是否还有任何 P0 项可以继续砍掉，而不破坏“普通用户真实完成一条视频”的验收目标。

---

## 13. 当前收敛状态

**CONSENSUS CANDIDATE（尚非 Decision）**

GPT 与 Claude 现在已经高度收敛于：

- Acceptance/E2E 先行；
- 垂直切片，不横向扩系统；
- P0 不以框架迁移为前提；
- Director/Storyboard 比完整 Timeline 更重要；
- 不做完整 NLE；
- 不做 H4/Publish/Analytics；
- P0 必须保护人工修改；
- 长任务必须有最小后台行为与 single-flight；
- 真实 Provider 验收和 deterministic browser regression 分轨；
- 当前 85 秒样片不能证明 fresh-project GUI E2E 或 4 分钟稳定量产。

剩余真正需要用户决定的已经从“大架构”收缩到少数边界：

- 修订级保护 vs 字段级保护；
- 字幕是否允许独立改；
- 素材导入最低 UX；
- 视觉返工是否需要 P0 最小依赖修正；
- P0 E2E 的最终样例边界。

本轮不修改 `DECISIONS.md`。等待 Claude Round 04 Final。
