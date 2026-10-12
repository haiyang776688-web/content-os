# GPT Proposal · D-001

**Model:** GPT-5.6 Sol  
**Date:** 2026-09-28  
**Baseline commit:** `ea0d72748ff927c957183405069b6223d2b168c1`  
**Round:** 01 · Proposal  
**Read completeness:** 已完整读取 00_TOPIC 中列出的 Project Brain 核心文件、当前交接包与真实验收报告；本轮没有声称已重新执行本地测试或浏览器操作。

## 0. Executive Position

**PROPOSAL**

P0 不应该继续横向补“系统能力”，而应该立刻改成**垂直切片交付**：

> 用现有 Core 和已有产物合同，把一条已知能生产成功的视频链路，从“内部 API/JSON/终端可完成”改造成“浏览器里一步一步可完成”，并用浏览器 E2E 锁住这条路径。

我建议把 P0 收敛为 **5 个用户可感知阶段 + 1 个贯穿式状态层**：

1. Project / Research / Script
2. Audit / H2
3. Director / Storyboard Gate
4. Voice / EDT / Render
5. QA / H3 / Deliver / Optional Jianying
6. 全程统一的 Status / Next Action / Error Recovery

不是重新设计 6 套后端，而是把已有能力整理成一个明确的用户旅程。

---

## 1. 先定义“P0 通过”再继续开发

**FACT**

DEC-008 已经把 P0 定义为 GUI-Only E2E，但 Q-003 仍未冻结具体样例与浏览器验收动作。

**PROPOSAL**

在写更多 UI 前，先冻结一份可执行的 P0 Acceptance Script。最小黄金路径：

1. 浏览器打开 Content OS。
2. 新建一个项目。
3. 输入/选择主题与最小资料输入。
4. 在 GUI 查看 Fact / Source 状态。
5. 生成脚本。
6. 在 GUI 直接修改脚本文本。
7. 运行审计并查看 Findings。
8. 完成人工 H2。
9. 生成 Director IR / Storyboard。
10. 在 Storyboard GUI 至少完成一次真实人工修改：替换一个 XIAO-Y 动作、修改一段文字或替换一个视觉素材。
11. 完成 Storyboard Gate。
12. 生成/选择本地声音并进入 EDT。
13. 在 GUI 至少执行一次 EDT 人工修改并能 Undo。
14. 从 GUI 发起正式 Render；页面不能要求用户开终端观察状态。
15. 从 GUI 运行 Mechanical QA。
16. 从 GUI 运行/查看 MiniMax Visual QA，明确显示 `VISUAL_ONLY` 等真实 scope。
17. 从 GUI 完成 H3。
18. 直接下载 MP4。
19. 可选：从 GUI 生成一次 Jianying 草稿，并留下 `EXPORT` 记录。
20. 全程不打开 Terminal、不直接调用内部 API、不手工编辑 JSON。

**OPINION**

这份脚本比“页面都做完以后再 E2E”重要。之后任何开发都应该问：它是否让这 20 步中的某一步变成真实 GUI 操作？

---

## 2. 不先迁框架；先做一个 Walking Skeleton

**DESIGN_DECISION**

当前没有“必须迁移前端框架”的已确认决策；Q-001 仍开放。

**PROPOSAL**

P0 期间暂缓原生 JS → 新框架迁移。除非出现一个可以复现的阻塞，证明当前 Workbench 无法承载下面三件事之一：

- 明确的阶段导航；
- 稳定的状态刷新；
- 基本编辑交互。

先做 **Walking Skeleton**：

`Create Project → Script → Director → Render → QA → H3 → Download`

即使部分页面第一版很朴素，也必须真正调用当前正式后端路径，写入正式版本化产物，并能继续下一步。

**RISKS**

如果现在迁框架，会同时引入：
- UI 重写风险；
- 旧 API 适配风险；
- 状态管理重做；
- 新旧行为回归；
- E2E 推迟。

这些对 P0 都是负资产，除非有明确阻塞证据。

---

## 3. 把 GUI 从“功能菜单”改成“下一步工作流”

**CURRENT_IMPLEMENTATION**

Project Brain 已记录：当前工作台存在脚本、审计、导演/分镜、声音、时间线、渲染、QA、导出入口，但仍有 JSON 暴露、API 缺口和 `notImplemented` 阶段。

**PROPOSAL**

P0 的核心 UI 单元不是“模块页”，而是：

- 当前阶段；
- 当前 artifact/version；
- 当前 gate；
- 当前 owner；
- 下一步可执行动作；
- 为什么当前不能继续；
- 出错后从哪里恢复。

每个阶段统一提供：

```text
Status
Current Version
Inputs
Primary Action
Human Decision
Risks
Next Step
History
```

例如 Storyboard 页不应该先暴露完整 JSON；默认显示：

- Scene / Beat 卡片；
- XIAO-Y 动作缩略图；
- Screenshot/Asset；
- 关键文字；
- 时长；
- “替换动作 / 替换素材 / 改文字 / 调时长”。

高级 JSON 只允许作为开发/诊断折叠项存在，不能是完成任务的必经路径。

---

## 4. P0 不做完整 Research Workbench，只做“足够进入脚本”的 Source/Fact Inbox

**FACT**

Fact 结构化追溯的代码状态已经是 IMPLEMENTED（限定为结构与校验），但 GUI 仍 PARTIAL，不是完整普通用户研究工作台。

**PROPOSAL**

P0 不应重做一个大型 Research Agent UI。只需要：

- 添加来源/资料；
- 显示来源状态；
- 显示抽取出的 Facts / Claims；
- 标记“已验证 / 待验证 / 有冲突”；
- Writer 能消费它们；
- 用户能看到脚本中的主要 claim 对应来源。

复杂的自动研究、浏览器采集体验、批量素材智能理解放 P1/P2。

P0 的问题是“能不能从资料进入脚本”，不是“能不能做最强研究产品”。

---

## 5. Writer / Audit / H2：优先消灭 JSON 与角色混乱

**CURRENT_IMPLEMENTATION**

Writer/Audit/H2 主链可运行，但 GUI-only 仍有缺口；DeepSeek Red Team 设计定位与当前 Worker 配置存在实现分歧。

**PROPOSAL**

P0 只做两件事：

1. GUI 闭环：
   - Script editor；
   - Version compare；
   - Run Audit；
   - Findings list；
   - “接受修改 / 自己修改 / 重新生成”；
   - H2 Gate。

2. 角色配置冲突不要在 P0 中做大迁移：
   - UI 明确显示“本次实际使用的模型/角色”；
   - 保留调用来源；
   - DeepSeek Red Team 的默认迁移单独解决 Q-004，不阻塞 GUI E2E。

**OPINION**

“先把 DeepSeek 配置完全重构正确再做 GUI”会把产品闭环绑在模型路由重构上，不值得。

---

## 6. Director / Storyboard 是 P0 最需要产品化的页面

**CURRENT_IMPLEMENTATION**

Director IR 合同存在，当前真实项目也有 Director IR 和已批准 Storyboard；但是人工修订体验仍 PARTIAL。

**PROPOSAL**

P0 Director 不需要变强到“完美导演”，但 Storyboard 必须真正可操作。

最小 GUI：

- Scene/Beat 卡片；
- 当前 Visual Pattern；
- 当前 XIAO-Y Action；
- 当前 Screenshot/Asset；
- 主文字；
- 时长；
- 预览 still；
- Replace Action；
- Replace Asset；
- Edit Text；
- Adjust Duration；
- Regenerate This Beat。

所有修改生成新版本或明确 override，不能直接改旧产物。

**QUALITY CONSTRAINT**

避免 PPT 感仍作为 QA/Director 质量约束，但不要为了 P0 先构建完整 Visual Pattern 编辑器。P0 只需要让用户能看见并纠正关键错误。

---

## 7. 人工修改保护：P0 采用“保守型最小合同”，不要先造完整 Rebase 系统

**DESIGN_DECISION**

DEC-009 已确认：AI 再生成不能静默覆盖人工修改。

**PROPOSAL**

P0 最小合同：

- 任何用户手工修改过的字段/element 标记 `user_override=true`。
- “Regenerate Scene/Beat/Timeline” 遇到 override 时默认 **不覆盖**。
- 系统必须明确提示：
  - Keep User Changes
  - Reset and Regenerate
- 如果 AI 新结果和 override 冲突，列出冲突项；P0 不做自动智能 merge。
- Undo/历史版本仍依赖现有版本与 EDT 能力。

**OPINION**

这比立即实现复杂三方 merge / rebase 更符合 P0：先保证“不会偷偷丢用户修改”，再追求“自动帮你合并”。

---

## 8. Timeline：做“可改的检查台”，不是 NLE

**DESIGN_DECISION**

EDT 是唯一可编辑时间线；完整复制 OpenCut 已明确不采用。

**PROPOSAL**

P0 Timeline 只保证这些高价值动作：

- 选择 Element；
- Move；
- Trim；
- Duration；
- Replace Asset；
- Edit Text/Subtitle；
- Undo；
- Preview；
- Jump to Beat/Scene。

可以暂时保留数值字段作为高级精调，但主要交互至少做到“点击元素 → 修改属性 → 立即预览”，不能要求手工编辑 EDT JSON。

暂缓：
- 多层复杂拖拽；
- 精密磁吸；
- 高级 keyframe 曲线；
- 完整特效轨；
- Premiere/OpenCut 级交互。

---

## 9. 长任务：P0 只解决“用户不会以为系统死了”

**CURRENT_IMPLEMENTATION**

当前 jobs engine 的完整可靠后台取消/恢复仍是 PLANNED。

**PROPOSAL**

P0 先实现最小 Job UX，而不是完整任务基础设施：

- 点击后返回 Job ID；
- 页面显示 `QUEUED / RUNNING / SUCCEEDED / FAILED`；
- 显示阶段和可理解的进度文本；
- 页面刷新后能恢复查看当前任务状态；
- 防止重复点击重复生成；
- 失败后显示 Retry from Stage。

P0 不要求：
- 跨服务重启永久恢复；
- 完整队列系统；
- 任意取消/暂停/恢复；
- 多机 worker。

这些进入后续可靠性阶段。

---

## 10. Render / QA / H3 / Deliver：必须把已经验证的后端能力直接接通

**FACT**

当前真实项目已经证明：
- 正式 Render 可生成；
- Mechanical QA 可 PASS；
- MiniMax Visual QA 可真实调用，但 scope 是 VISUAL_ONLY；
- H3 可登记；
- MP4 可用。

**PROPOSAL**

这里不应重写算法，只做产品化连接：

Render 页面：
- Render 按钮；
- 参数只暴露用户需要的少数选项；
- 进度/失败/产物链接。

QA 页面：
- Mechanical QA 结果；
- Visual QA 结果；
- scope / provider / risk 显示；
- 模型时间戳可点击跳转预览；
- “模型意见 ≠ 人工决定”文案。

H3：
- Approve；
- Approve With Risk；
- Reject / Return to owner。

Deliver：
- Download MP4；
- Optional Export to Jianying；
- 显示是否真的生成 `EXPORT` artifact。

---

## 11. P0 明确排除项

**PROPOSAL**

以下内容冻结为“非 P0”，除非 E2E 证明它们是直接阻塞：

- H4 和真实平台发布；
- 完整 Analytics GUI；
- 前端框架迁移；
- 完整 OpenCut/Premiere 级 Timeline；
- 自动三方 Rebase/Merge；
- 多机/持久任务队列；
- 逐词 forced alignment；
- 骨骼动画 / 口型；
- 完整跨项目资产平台；
- 多平台自动分发；
- 新 Agent 扩张；
- 为了 Council 本身做产品功能；
- Model Integrity / Capability Probe 的完整产品化（可继续作为后续 Model Adapter 增强，不阻塞 P0）。

---

## 12. E2E 要分“可重复自动化”和“真实 Provider 验收”两条

**PROPOSAL**

不要只保留一个昂贵且不稳定的 E2E。

### Track A · Deterministic Browser E2E

用于每次回归：

- 浏览器自动操作；
- 固定 fixture / 可控 provider stub；
- 不允许直接调用业务内部 API 来跨阶段；
- 验证所有 GUI 操作、版本/gate/next-step 状态和产物链。

### Track B · Live Acceptance

版本里程碑时运行：

- 使用真实 Provider；
- 使用真实本地声音；
- 真实 Remotion Render；
- 真实 Mechanical QA；
- 真实 MiniMax Visual QA；
- H3；
- 下载 MP4；
- 可选 Jianying Export。

两者都必须从 GUI 发起主要生产动作。

**FACT**

现有约 84.821 秒样片是目前唯一已充分证明的真实端到端内容样本之一。

**PROPOSAL**

P0 的第一个 Golden Scenario 直接复用这个约 85 秒题材/资产边界，降低“同时调产品体验 + 新内容质量”的变量。

但要明确：

> 通过 85 秒 Golden Scenario 只代表 GUI-Only E2E 完成，不代表已经证明 4 分钟日更稳定性。

P0 通过后增加一个独立的 **3–5 分钟 Live Stability Run**，才能开始声称更接近目标生产时长。

---

## 13. 推荐开发顺序

**PROPOSAL**

### Slice 0 · Acceptance First
- 固化 P0 浏览器验收脚本；
- 建立 E2E harness；
- Golden Project / fixture；
- 页面阶段状态 contract。

### Slice 1 · Project → Script → H2
- H1 最小新建项目；
- Source/Fact Inbox；
- Script editor；
- Audit findings；
- H2。

### Slice 2 · Director → Storyboard
- Scene/Beat 卡片；
- still preview；
- Action/Asset/Text/Duration 修改；
- Storyboard Gate；
- user_override 最小合同。

### Slice 3 · Voice → EDT → Preview
- 本地声音选择/生成；
- Timeline inspection/edit；
- Undo；
- Preview；
- Regenerate 冲突保护。

### Slice 4 · Render → QA → H3 → Deliver
- Job UX；
- Render；
- Mechanical QA；
- MiniMax Visual QA；
- H3；
- MP4 Download；
- Jianying Export。

### Slice 5 · Full Browser Acceptance
- Track A 自动 E2E；
- Track B 真实 Provider；
- 至少一次失败 → Retry；
- 至少一次人工修改 → Regenerate → 验证未丢；
- 当前约 85 秒 Golden Scenario 完整跑通。

只有 Slice 5 通过，P0 才能标完成。

---

## 14. P0 Definition of Done

**PROPOSAL**

P0 只有在以下全部成立时才算完成：

- [ ] 新用户只看 GUI 能知道“现在在哪一步、下一步做什么”。
- [ ] 从新建项目到 MP4 的所有主要动作都能从浏览器完成。
- [ ] 过程中不需要 Terminal、内部 API、手工 JSON。
- [ ] 至少一处 Script/Storyboard/EDT 人工修改被保存。
- [ ] AI 再生成不会静默覆盖上述人工修改。
- [ ] 至少一次失败能在 GUI 得到可理解错误并 Retry。
- [ ] Render、Mechanical QA、Visual QA、H3 全部留下正式 artifact/version。
- [ ] MiniMax 审查 scope 明确，不把 VISUAL_ONLY 误写成音频 QA。
- [ ] MP4 可直接下载。
- [ ] 如果选择 Jianying Export，必须真的生成 EXPORT 记录；否则 UI 不得显示“已交接”。
- [ ] Browser E2E 有自动化或完整操作证据。
- [ ] 使用真实 Provider 完成一次 Live Acceptance。
- [ ] 通过约 85 秒 Golden Scenario 不被宣传成“4 分钟稳定日更已完成”。

---

## 15. 我希望 Claude 重点攻击的部分

**PROPOSAL FOR REVIEW**

请 Claude 不要重复总结，重点挑战以下判断：

1. 把框架迁移排除在 P0 是否会留下无法偿还的 GUI 技术债？
2. `user_override=true + 冲突时不覆盖` 是否足以满足 DEC-009 的 P0 最小合同？
3. P0 长任务只做到“刷新可恢复查看、失败可 Retry”，而不做真正持久队列，是否过于脆弱？
4. 以约 85 秒现有样片作为 Golden Scenario 是否会让 E2E 对特定项目过拟合？
5. P0 Timeline 限定成“检查/修改台”是否足够让普通用户真正完成视频？
6. 是否有任何我错误地把“已有代码”当成“容易 GUI 化”的地方？
7. 这份计划里是否仍有不必要的系统建设，应该再砍掉？
8. 哪一步最可能成为 P0 的真实阻塞，需要提前做 Spike？

---

## 16. Summary

**OPINION**

Content OS 当前最需要的不是再证明“系统能生成视频”，而是证明：

> 一个不了解内部 API、JSON 和终端的人，能在一个工作台里理解系统状态、做必要的人类判断、修改 AI 结果、处理失败，并拿到真实成片。

因此本轮建议的优先级是：

```text
Acceptance Contract
    ↓
Walking Skeleton
    ↓
消灭 GUI 断点
    ↓
最小人工修改保护
    ↓
Render / QA / H3 / Export 产品化
    ↓
Browser E2E
    ↓
真实 Provider 验收
```

在这条线跑通前，不应让发布、Analytics、框架迁移、完整 NLE 或更多 Agent 抢占 P0。
