# Claude Review · D-001

**Model:** Claude Sonnet 5 (Anthropic)
**Date:** 2026-09-28
**Round:** 02 · Review
**Baseline commit（00_TOPIC 固定）:** `ea0d72748ff927c957183405069b6223d2b168c1`
**main HEAD at read time:** `5be67bbc0716f23154d67e5a4127e7d3b26805ed`。核对方法：`docs/project-brain/` 下 11 个核心文件的 blob SHA 与基线读取时逐一相同，仅 `discussions/` 新增了文件；代码文件均按基线 commit 读取。**未**逐目录 diff 其他路径。
**Session link/ID:** UNKNOWN（本会话没有可取得的链接或 ID）
**Read completeness:**

- 已完整读取：`docs/project-brain/COUNCIL_PROTOCOL.md`、`discussions/README.md`、`D-001-p0-gui-only-e2e/00_TOPIC.md`、`01_GPT_PROPOSAL.md`、`PROJECT_CONTEXT_MASTER.md`、`PRODUCT_TASTE.md`、`CURRENT_STATE.md`、`IMPLEMENTATION_STATE.md`、`DECISIONS.md`、`REJECTED_IDEAS.md`、`OPEN_QUESTIONS.md`、`ROADMAP.md`。
- 为核对 GPT 的“容易 GUI 化”假设，另读代码与证据（基线 commit）：`vnext/apps/workbench/server.py`、`vnext/phase2/api.py`、`vnext/phase2/production.py`、`vnext/core/jobs/engine.py`、`vnext/registries/catalog.py`、`REAL_WORKFLOW_ACCEPTANCE_REPORT.md`、`CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md`，以及 `vnext/apps/workbench/` 的文件清单与大小。
- **有意未读：** `03_`、`04_`、`05_`（协议规定每轮只基于共同事实源与已归档的上一轮）。
- **未读，相关结论标为 UNKNOWN：** `workbench.js` / `phase2.js` 内部结构、`vnext/phase2/knowledge.py`、`vnext/core/editing.py`、`vnext/phase2/stages.py`、`vnext/storage/store.py` 的依赖失效逻辑、`vnext/providers/api.py`、`vnext/phase2/hardening/*`、Remotion 适配器。
- **未执行：** 测试、浏览器操作、本地服务。本文所有 CURRENT_IMPLEMENTATION 结论来自静态阅读，不代表运行验证。

标记沿用协议：`FACT` / `CURRENT_IMPLEMENTATION` / `DESIGN_DECISION` / `PROPOSAL` / `OPINION` / `UNKNOWN`。

---

## 0. 总体判断

**OPINION**

我不反对 GPT 的三条主线：验收优先、垂直切片、P0 期间不把框架迁移作为前提。**但提案把若干需要新后端行为或新合同的工作，当作“接入 GUI”来估价。** 这些是估价错误，不是方向错误。最严重的 5 处：

1. 人工修改保护合同（`user_override=true`）内部自相矛盾，且现有 EDT 的 clip 标识不稳定，按提案写法无法落地（见 Q2）。
2. “Job UX”并非纯 GUI 工作。当前渲染与配音在 HTTP 请求内同步执行，且存在重复点击会并发重复渲染的缺陷（见 Q3）。
3. “Regenerate This Beat”“Adjust Duration”在当前后端没有对应能力（见 Q6）。
4. 提案的 20 步验收缺少三个真实必经步骤：素材/来源导入、配音时间对齐、交付物取回（见第 2 节）。
5. “复用 85 秒样片”作为黄金样例，会验证夹具而不是线性 GUI 路径，因为样片本身是非线性、含人工 API 操作产生的（见 Q4）。

---

## 1. 逐条回应 GPT 提出的 8 个问题

### Q1 · 排除框架迁移是否留下无法偿还的 GUI 技术债？

**结论：部分同意。排除“作为前提”合理；“不会留下无法偿还的债”缺乏证据。**

- **FACT**：`vnext/apps/workbench/` 中除预构建包外的前端 JS 合计约 97.5 KB（`workbench.js` 30,057 B、`phase2.js` 21,293 B、`settings.js` 20,444 B、`production-ux.js` 9,245 B、`hardening.js` 6,616 B、`preview.js` 5,647 B、`i18n.js` 4,201 B）；另有 `monitor.bundle.js` 515,171 B（预构建产物）。
- **OPINION**：这个体量对两个方向都有影响。它说明“迁移是巨大重写”的论据比提案暗示的弱，因为现有 GUI 很小；同时也说明 P0 要新增的 Storyboard 面板、Timeline Inspector、Job 状态、Source Inbox 会让代码量成倍增长，债的增速取决于这些交互怎么写。
- **UNKNOWN**：`workbench.js` 内部是否用字符串拼接 `innerHTML`、有无共享状态层，我没有读，无法判断实际债务。`monitor.bundle.js` 的构建脚本位置也未确认。
- **PROPOSAL**：不迁移，但在 Q-001 上设**预先声明的止损检查点**，而不是“出现阻塞再说”。建议在 Slice 2（Storyboard）完成后做一次 1–2 天的证据评估：E2E 是否因前端状态同步不稳定而反复失败、同一类 UI 缺陷是否需要跨多个 JS 文件修补。在此之前立三条约束：任何渲染不可信文本（来源摘录、模型输出）的位置必须走统一转义函数；新面板不得直接读写全局变量而要经一个小型状态入口；每个 slice 的 E2E 是硬性退出条件。

### Q2 · `user_override=true` + 冲突时不覆盖，是否满足 DEC-009 的 P0 最小合同？

**结论：不足，且当前写法有三处缺陷。**

1. **内部矛盾。** 提案写“P0 不做自动智能 merge”，又提供 `Keep User Changes` 与冲突项列表。若“Keep”表示“重新生成但保留用户字段”，就必须做字段级合并；若表示“取消这次重新生成”，那它只是“不重新生成”，不该叫 Keep User Changes。合同必须先写清楚二选一。
2. **标识不稳定。** **CURRENT_IMPLEMENTATION**：`vnext/phase2/production.py` 的 `generate_edt` 中，字幕 clip 的 ID 是 `'CLP-'+digest([resolved['output_hash'], beat_id, 'subtitle', i])[:16]`，配音 clip 的 ID 是 `digest([amap['output_hash'],'VOICE'])`。ID 随 resolved composition 或音频时钟哈希变化，一次重生成就全部改变。因此按 `clip_id` 标记 override 不能跨重生成存活；override 必须挂在语义地址上（如 `beat_id + track + role`）。视觉 clip 的 ID 由 `VisualResolver.clips` 生成，我没有读，标 UNKNOWN。
3. **现有 EDT 重生成会丢掉全部人工 clip 编辑，且没有任何提示。** **CURRENT_IMPLEMENTATION**：`CommandBus.execute` 的 EDT 分支中，`GENERATE` 直接调用 `Production.generate_edt`，从 IR、resolver、音频时钟重建全部 clip；`GENERATE_PRESERVING_AUDIO` 只保留 `VOICE/BGM/SFX` 三种轨道。也就是说，用户只要重新生成配音（例如修一个读错的词），新的 `AUDIO_TIMING_MAP` 就会触发 EDT 重建，之前所有拖动、裁剪、文字修改都会消失。这与 `CURRENT_STATE.md` 中“Override/Rebase 合约尚未交付”一致。

**PROPOSAL（更小、更稳的 P0 合同）——修订级保护，不做字段级标记：**

- 现有 `EDIT_COMMAND` 产物已记录 `actor_type`、`before_revision`、`after_revision`，`CommandBus.execute` 也支持 `expected_revision` 乐观并发。
- 合同：当某目标（EDT、DIRECTOR_IR、SCRIPT）的当前 head 修订是由 HUMAN 命令产生的，且发生在最近一次 AGENT/SYSTEM 生成之后，则任何 AGENT/SYSTEM 的重生成**默认拒绝**（返回 `HUMAN_EDITS_PRESENT`），除非调用方显式传入丢弃标志。
- GUI 在拒绝时列出将被丢弃的人工命令清单（来自 `EDIT_COMMAND`），提供“保留当前版本 / 丢弃我的修改并重新生成”两个动作。
- 代价：颗粒度粗，只能全留或全丢。收益：能立刻满足“不静默覆盖”，不需要稳定 ID、不需要三方合并；字段级保留与自动重放留给 Q-002。
- 兜底：`CommandBus` 的撤销栈在 GENERATE 前会压入 `before`，理论上“丢弃后可撤销”。但 EDT 的 UNDO 在 head 过期时会抛 `TIMELINE_STALE`，所以“丢弃后能撤销”**必须进入 E2E 验证，不能假设成立**。
- **UNKNOWN**：`Editing.edit_timeline` 是否会给人工编辑的 clip 写 `edit_source`（EDTClip 已有 `origin` / `edit_source` 字段）。若会，“修订级”之外也许可以直接复用它做粗粒度标记，请在实现前核对。

### Q3 · 长任务只做到“刷新可查看、失败可 Retry”，是否过于脆弱？

**结论：有条件同意，但提案低估了工作量，并漏掉一个已存在的缺陷。**

- **CURRENT_IMPLEMENTATION**：`vnext/core/jobs/engine.py` 的 `JobEngine.execute` 在调用线程内同步执行，状态仅 `RUNNING/COMPLETED/FAILED`，没有 `QUEUED`。`server.py` 的 `render_video`、`render_still` 甚至不经 `JobEngine`，而是手工构造 `Job` 后在请求内同步调用 `RemotionAdapter`。配音 `synthesize` 也是在请求内同步执行。提案里“点击后返回 Job ID、QUEUED/RUNNING/SUCCEEDED、阶段进度”**需要改变执行模型**，不是纯 GUI。
- **CURRENT_IMPLEMENTATION（缺陷）**：`render_video` 仅当 `previous.state == "COMPLETED"` 才复用结果。若上一次仍是 `RUNNING`，第二次点击会用同一个 `job_id`（键为 `RENDER_VIDEO:<timeline_id>`）再启动一次渲染，即并发重复渲染。提案的“防止重复点击重复生成”因此不是 GUI 防抖能解决的，服务端必须做 single-flight。
- **UNKNOWN**：没有找到清理孤儿 `RUNNING` 任务的逻辑（未读全仓）；服务重启后任务是否永远停在 `RUNNING` 未确认。`IMPLEMENTATION_STATE.md` 也把可靠后台执行标为 PLANNED。
- **UNKNOWN**：正式渲染、分镜静帧、克隆配音、MiniMax QA 的实际耗时，Brain 与验收报告都没有记录。等待体验的设计取决于这些数字。
- **PROPOSAL（P0 最小版，不做持久队列）**：
  1. 长操作改为进程内后台线程，接口返回 202 与 `job_id`，GUI 通过现有 `GET /api/projects/{id}`（已含 `jobs`）轮询。
  2. 按 `(project, kind, 目标产物)` 做 single-flight，运行中拒绝重复提交。
  3. 服务启动时把遗留的 `RUNNING` 标记为 `FAILED(SERVER_RESTARTED)`，让 Retry 可用。
  4. 进度只显示“阶段 + 已用时间”，不做百分比，避免从 Remotion 子进程解析进度。
  5. 渲染进行时，GUI 显示“正在渲染 EDT 修订 N”，期间的编辑需明示会使该结果过期。
- 满足这五点，则“不做持久队列”可以接受；缺任一点则脆弱。

### Q4 · 以约 85 秒样片作为黄金样例，是否会过拟合？

**结论：部分同意（复用降低变量，但会产生假阳性）。**

- **FACT**（`CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md`）：该样片使用的是“人工导演视觉修订 v2”的 Director IR，本地克隆配音“没有重做”，H3 是用户在对话中回复“通过”后再登记的（`REAL_WORKFLOW_ACCEPTANCE_REPORT.md`）。
- **CURRENT_IMPLEMENTATION**（`server.py`）：`/voice` 要求分镜 Gate 已批准，且配音文本必须与已批准脚本一致。线性顺序是“IR → EDT（用于分镜）→ 分镜 → Gate → 配音 → EDT 用音频时钟重建”。样片是非线性构建出来的（配音先存在、分镜后批准），所以**线性的 GUI 首次路径从未被样片证明过**。
- **OPINION**：因此“复用 85 秒题材与资产”只能验证夹具与既有产物，验证不了：AI 导演在无人工修订时能否给出可接受方案、全新项目首次走线性顺序会不会撞上过期/顺序约束。
- **PROPOSAL**：
  - 黄金场景 A：空项目起步，线性走完，使用**受控的假 Provider（Provider 边界处的本地假服务，而不是在应用内选 MOCK worker）**，脚本取自样片以降低变量，短夹具（约 10–15 秒、3 个 Beat）用于每次回归。
  - 场景 B（Live Acceptance）：一个**未用过的**新题材（含数字强调类 Beat，以覆盖事实绑定与 `DIRECTOR_NUMBER_MISMATCH` 校验），真实 Provider、真实克隆配音。
  - 提案“通过 85 秒不等于 4 分钟稳定”的声明保留，同时补一句：“通过样片复用不等于 AI 导演可用”。
  - **假 Provider 输出必须满足严格合同**（`Production.ir` 的校验、事实绑定、时间戳），这个夹具成本要计入 Slice 0。

### Q5 · Timeline 限定为“检查/修改台”，是否足够让普通用户完成视频？

**结论：方向同意，但轨道范围和重点要调整。**

- **CURRENT_IMPLEMENTATION**：配音与字幕 clip 由 `AUDIO_TIMING_MAP` 主时钟生成（`origin='AUDIO_TIMING_MAP'`），机械 QA 对其有 `VOICE_DURATION_MISMATCH`、`VOICE_TIMELINE_GAP`、`SUBTITLE_*` 等规则。让用户直接拖动、裁剪这些 clip，会与主时钟冲突并被机械 QA 否决。`ROADMAP.md` 也把“声音、字幕时间线精度与人工校正”放在 P1。
- **CURRENT_IMPLEMENTATION**：真正可撬动画面质量的杠杆是 `DIRECTOR_IR.SET_BEAT`（可改 `template_id`、`character_action_id`、`element_ids`、`keyword`、`media_need`、`slots` 等）。若 AI 首稿有 PPT 感，普通用户能靠 Storyboard 的模板/动作/元素替换来救，而不是靠 Timeline 的拖动。
- **PROPOSAL**：P0 的 Timeline 必需项收窄为：预览与跳转、视觉/文字轨道的选择与属性修改、素材替换、撤销。**Move/Trim/Duration 对 `VOICE`/`SUBTITLE` 轨道不进 P0**；把工程量转到 Storyboard 的替换操作与预览回路上。
- **需要用户决定（见第 4 节）**：字幕文字是否允许与已批准脚本不同。

### Q6 · 是否有把“已有代码”误当成“容易 GUI 化”的地方？

**结论：是，至少 6 处。**

1. **Regenerate This Beat**：**CURRENT_IMPLEMENTATION**：`/run/DIRECTOR` 重跑整个 IR；`Production.storyboard` 遍历全部 Beat；`phase2/api.py` 没有单 Beat 重生成路径。提案把它列入 P0 最小 GUI，但它需要新的单 Beat 模型调用、局部失效与人工修改保护，不是接入。
2. **Adjust Duration**：**CURRENT_IMPLEMENTATION**：`SET_BEAT` 允许的字段集不含 `timing_intent`；`Production.ir` 还要求场景内 Beat 时长之和等于 `estimated_duration`（`SCENE_DURATION_MISMATCH`）；配音后时长由音频时钟决定。
3. **“改一段文字”的含义**：Storyboard 上能改的是 `keyword` / `slots`，且受 `DIRECTOR_NUMBER_MISMATCH` 约束（数字必须出现在对应脚本片段中）。口播文本属于 SCRIPT owner；`Production.ir` 要求 IR 引用的脚本等于 `h2_script_artifact_id`，所以改口播会产生新脚本、需要重新过 H2、并使 IR 及下游失效。GUI 需要把这条“回到文案会使分镜/配音失效”的后果讲清楚。
4. **“立即预览 still”**：**CURRENT_IMPLEMENTATION**：`Production.storyboard` 对每个 Beat 依次用 `npx remotion still` 渲染 2 帧，每帧超时 120 秒。任何 `SET_BEAT` 都会改变 IR 哈希，使已批准的 Gate 变为 `STORYBOARD_APPROVAL_STALE`，需要整板重渲染并重新批准。快速预览应走已有的 `/api/projects/{id}/preview`（`CompositionResolver.frame`），Storyboard 静帧只在提交 Gate 前生成一次。
5. **脚本编辑与事实绑定**：**CURRENT_IMPLEMENTATION**：`mechanical()` 会对“有 claim 却没有 `fact_ids`”的片段报 `UNBOUND_CLAIM`（BLOCKER）；`/phase2/script` 接收的是含 segments 的结构化 payload，`/phase2/source`、`/phase2/facts` 接收的是自由格式 `payload: dict`。GUI 里的“直接修改脚本文本”若要通过严格模式，需要把用户文本还原成带 segment 与 fact 绑定的结构。`knowledge.py` / `editing.py` 我没读，能否无 JSON 完成属 UNKNOWN，见 Spike 1。
6. **Source/Fact 的表单必须与内部 schema 同步**：上述接口的 payload 是开放字典，GUI 表单一旦与合同不一致就会在运行时才失败。需要契约测试，而不是只靠 E2E 发现。

### Q7 · 是否仍有不必要的系统建设应该砍掉？

**结论：是。**

- **砍：Slice 0 的“页面阶段状态 contract”。** **CURRENT_IMPLEMENTATION**：`/api/projects/{pid}/phase2` 已返回 `StageCache.states(pid)`。Status/Next Action 应是对现有阶段状态与 Gate 产物的**纯函数投影**，配表驱动测试，不要新增一层合同或第二套状态来源。
- **砍：`Regenerate This Beat` 与 `Adjust Duration`**（理由见 Q6 第 1、2 点）。用 `SET_BEAT` 手动替换加“整段重跑 Director（受 Q2 的保护合同约束）”代替。
- **砍：Timeline 对 `VOICE/SUBTITLE` 的 Move/Trim/Duration**（见 Q5）。
- **砍：进度百分比**，改为阶段 + 已用时间（见 Q3）。
- **收窄：H1。** 提案的 Slice 1 写有“H1 最小新建项目”，但 `IMPLEMENTATION_STATE.md` 与 `DECISIONS.md` 都把 H1 标为未开始。P0 应明确只做“新建项目”，**不实现 H1 关卡**，否则是范围蔓延。
- **收窄：Version compare。** `Review.build` 已用 `difflib` 生成 `script_diff`。P0 只需要只读并排 diff，不做逐段接受/合并。
- **收窄：Track A 的渲染。** 每次回归不应跑 85 秒真实渲染，用短夹具（见 Q4）。

### Q8 · 哪一步最可能成为 P0 的真实阻塞，需要提前 Spike？

**Spike 顺序（各 0.5–1 天，时间盒；产出是 PASS/FAIL 记录与证据，不是实现）：**

1. **严格模式下的纯文本脚本编辑。** 问题：GUI 里改几句口播并保存，能否不碰 JSON 就得到通过 `bound_script` 与 `UNBOUND_CLAIM` 检查的新 SCRIPT？通过标准：只用浏览器完成一次“改一句 + 重新绑定 claim + 通过 H2”。失败则 P0 需要 Claim/Evidence 的最小编辑 UI，体量显著增加。
2. **全新项目的配音路径。** `synthesize` 在响应中没有 phrase/word 时间戳时会返回 `alignment_required: VOICE_TIMING_ALIGNMENT_REQUIRED` 且不产生 `AUDIO_TIMING_MAP`，随后机械 QA 会因 `AUDIO_MASTER_CLOCK_REQUIRED` 阻断。另外 `CURRENT_STATE.md` 记录了旧声音注册表 `consent: PENDING / UNAVAILABLE` 与真实运行的冲突（Q-006）。通过标准：一个新建项目在 GUI 里选声音、生成、得到有效时间轴。
3. **配音之后改一个 Beat 的失效级联。** 问题：在 `VOICE` 已生成后执行 `SET_BEAT`，是否会使已生成的配音失效并强制重录（`VOICE` 的依赖包含 Storyboard Gate 或 `VOICE_AUTHORIZATION`）。我没有读 `store.is_usable_input` 与依赖失效实现，属 UNKNOWN。若会强制重录，则“返工”的代价极高，而 `ROADMAP.md` 把“更细粒度的依赖失效”放在 P1，**P0 与 P1 边界存在冲突**，需要决定 P0 是否包含该最小子集。
4. **后台执行 + single-flight + 孤儿任务清理**，验证 Q3 的五点方案能否在不引入队列的前提下成立，同时**测量**正式渲染、分镜静帧、克隆配音、MiniMax QA 的实际耗时。

---

## 2. 提案 20 步验收与开发顺序中遗漏的真实步骤

1. **素材与来源如何进入项目。**
   - **CURRENT_IMPLEMENTATION**：`POST /media/folder` 接收路径字符串（`FolderIn.path`）；`/phase2/source` 接收自由格式 payload。提案在 `SCREEN_DETAIL`、`CHARACTER_REACTION_MEDIA` 等需要 `media_asset_id` 的 Pattern（缺失则 `ASSET_GAP`）上要求“替换素材”，却没有说明素材如何导入。
   - 这不违反 DEC-008 的字面（路径输入不是终端/JSON/内部 API），但它决定了普通用户能否完成，见第 4 节的人工决定项。
2. **隐藏的中间步骤。** `Production.storyboard` 需要已有的 EDT 与 `VISUAL_EDT`，因此“生成分镜”在 GUI 中必须隐式先生成一次（估算计时的）EDT；配音后 EDT 会被音频时钟重建一次。GUI 不应把这两次 EDT 当作用户可见步骤，但**第二次重建会覆盖第一次之后的人工编辑**（回到 Q2）。此外，Storyboard Gate 的新鲜度只比较 `ir_hash`（`require_storyboard`），不含最终计时，所以“已批准分镜”与“配音后的最终 EDT”可能不一致。
3. **交付物取回。** MP4 由 `render_file` 以 `FileResponse` 返回，可直接下载。剪映导出走 `export_transfer_bundle`，我没有读出口的具体形态，很可能是磁盘目录；GUI 需要提供打包下载或明确的取回方式。“显示 EXPORT 记录”不等于用户拿到了草稿。
4. **乐观并发。** `CommandBus.execute` 已支持 `expected_revision` 并会抛 `EDIT_REVISION_CONFLICT`。GUI 每次编辑都应传入它，否则多标签页、刷新、后台重生成会静默覆盖。
5. **H3 的 GUI 化。** 现有 H3 是用户在对话里表态后由 API 登记；提案已包含 H3 GUI，但需注意 `Review.build` 要求 13 类产物齐备，且“带风险通过”需逐条确认风险代码（`RISK_ACKNOWLEDGMENT_REQUIRED`），GUI 必须渲染这份风险清单，而不是一个“通过”按钮。
6. **安全核对（不是 P0 阻塞）。** **UNKNOWN**：本基线的 `server.py` 中我没有看到 Host/Origin/CSRF 校验，`vnext/providers/api.py` 未读。我此前在 Council 之外审查过一个**不同快照**的压缩包，看到相关校验只覆盖设置类接口；该结论**不能直接套用到本基线**。P0 会新增更多由浏览器触发的写操作，建议在 Slice 0 加一项“核对所有 mutating 路由的来源校验”的检查，结果另行记录。

---

## 3. 我未提出异议的部分（基于何种依据）

- 验收脚本先行、Golden 与 Live 分轨（除 Q4 所述的样例选择）：与 `ROADMAP.md` 的 P0 定义一致。
- Director/Storyboard 用缩略图与选择器替代 JSON：`SET_BEAT` 已支持 `template_id`、`character_action_id`、`element_ids`，后端有基础。
- Render/QA/H3 只做产品化连接：`Review.gate` 与 `mechanical()` 已有结构化校验与风险确认。
- 明确排除 H4、Analytics、完整 NLE、更多 Agent：与 `REJECTED_IDEAS.md` 与 DEC 一致。
- MiniMax `VISUAL_ONLY` 范围显式展示：与 DEC-004 一致。

---

## 4. 待用户决定（本轮 Review 不代为决定）

1. **人工修改保护采用哪一档？** A：修订级保护（本文 Q2 建议，粗粒度，可立即实现）；B：字段级保留（需稳定语义地址，属 Q-002 范围）。
2. **字幕文字是否允许与已批准脚本不同？** 允许则需规定它是否只是显示层覆盖、是否仍受事实绑定约束；不允许则字幕文字只能通过改脚本获得。
3. **P0 是否接受“粘贴本机路径”作为素材导入方式？** 若不接受，需要新增选择器类接口，属于“GUI 必需的后端补充”，应单独立项并附带来源校验。
4. **P0 与 P1 的边界：** 若 Spike 3 证明“配音后改 Beat 会强制重录”，是否把最小的细粒度失效纳入 P0。
5. **Track A 是否包含真实渲染？** 建议只用短夹具，完整 85 秒与新题材放在 Live Acceptance。

---

## 5. 结论标记

- 本文是 Round 02 Review，**不是 Decision**；未修改 `DECISIONS.md`、未实现代码、未创建 PR。
- 对 GPT Proposal 的整体评价：**方向成立，估价与合同不足**。需要在 Round 03 回应的实质异议为 Q2（override 合同）、Q3（Job 需要后台执行与 single-flight）、Q6（Beat 重生成与时长调整无后端）、Q4（黄金样例的线性路径缺口）、第 2 节遗漏步骤，以及 Q8 的四个 Spike。
