# Content OS · 2026-09-29 P0 GUI-Only E2E 纠错交接

**核对日期：** 2026-09-29  
**知识主分支：** `main`  
**当前 P0 实现分支：** `p0/gui-only-e2e-interim`  
**实现分支核对 commit：** `323f7a2376efcfcfd1643a3e9d15333e084c1739` (`test: record fresh live gui e2e track B`)  
**状态：** P0 GUI-Only E2E 的**工程路径已取得真实 Track B 通过证据**，但创作质量仍 FAIL / pending redesign；D-001 仍未由用户正式 ACCEPT，D-002 / D-003 仍 OPEN。

## 1. 本文件为什么存在

2026-09-29 上传的交接 ZIP 同时包含多个历史阶段文档。它们内部存在明显时间差：

- `CONTENT_OS_当前状态交接包.md` 仍停在 2026-09-27 / 126 tests / 真实模型 0 次；
- `DELIVERY_README.md` 仍以 84.821 秒 Phase 2.1 样片和 189 tests 为主要状态；
- `CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md` / `REAL_WORKFLOW_ACCEPTANCE_REPORT.md` 仍描述旧 84 秒生产样片；
- 但同一交接包的 `DELIVERY_MANIFEST.json` 明确来自 `p0/gui-only-e2e-interim` commit `323f7a2`，且分支上的 `SLICE-006-TRACK-B.md` 已记录新的 61 秒 fresh-project GUI 验收。

因此旧顶层交接文档保留为历史快照，**不能继续作为“当前状态”覆盖更晚的 branch/test/run 证据**。

## 2. 已核实的最新 P0 实现事实

### 2.1 Track B fresh live GUI path

分支 `p0/gui-only-e2e-interim` 的 `SLICE-006-TRACK-B.md` 记录：

- 从空项目 `PRJ-ce790ce1fcc8` 开始；
- 通过普通 Workbench GUI 导入新题材资料；
- 真实 DeepSeek Research；
- GUI 人工确认 7 个 source-bound Facts；
- 真实 DeepSeek Script（第一次长度合同失败，第二次得到 317 字 / 7 segment 正式 Script）；
- 独立 GLM Audit PASS；
- 测试身份 H2；
- 真实 GLM Director 生成 7 Beats；
- 正式 Storyboard still job；
- 本地克隆声音 `YU_LOCAL_V1`；
- `AUDIO_TIMING_MAP`；
- Final Editable EDT；
- Remotion 1080p / 30fps 正式 MP4；
- Mechanical QA；
- 真实 MiniMax-M3 **VISUAL_ONLY** QA；
- Review Pack；
- 测试身份 H3 `APPROVE_WITH_RISK`；
- MP4 浏览器下载；
- 可选 Jianying transfer ZIP 浏览器下载。

这些生产动作由普通 GUI 发起；诊断和测试数据检查没有通过内部 API 偷生成生产 artifact。

### 2.2 Track B 媒体结果

最终修正版：

- RENDER：`ART-1d0f5aab9283447d`
- 时长：61.461333 秒
- H.264 / AAC
- 1920×1080
- 30 fps
- 4,309,544 bytes

Voice：

- 61.400 秒
- 正式本地克隆声音
- 本地声音未发送给 MiniMax

MiniMax：

- `ART-36c5967ba89e466f`
- provider=`minimax`
- model=`MiniMax-M3`
- `audio_transmitted=false`
- `review_scope=VISUAL_ONLY`
- verdict=`PASS_WITH_RISK`

### 2.3 当前测试证据

分支验收记录声明：

- `pytest -q vnext/tests`：**205 passed**
- 1 条既有 Starlette/httpx deprecation warning

本次外部纠错复核对上传快照做了额外检查：

- `pytest --collect-only`：**205 tests collected**
- 新增 P0 / XIAO-Y 重点测试：
  - `test_p0_delivery.py`
  - `test_p0_jobs.py`
  - `test_p0_provider_boundary.py`
  - `test_p0_workflow.py`
  - `test_xiaoy_presentation.py`
- 本次复核：**23 passed in 7.03s**

本次沙箱未在 90 秒窗口内完成全量 205 项重新执行，因此不要把“本次外部复核重新跑了 205 passed”写成事实；205 passed 的完整结果来自实现分支自身的最新验收记录。

## 3. 工程验收通过 ≠ 创作质量通过

Track B 的正确状态必须写成：

> **Engineering GUI path PASS; creative acceptance FAIL / pending redesign.**

人工检查与 MiniMax 都发现：

- 画面偏稀疏；
- 部分镜头大面积白底只有一行文字；
- XIAO-Y pose 重复；
- 实际平台 overlay / occlusion 示范不足；
- 部分 text-only reveal 过快；
- visual rhythm / balance 仍有问题。

用户已明确拒绝 PPT 感，因此：

- Mechanical QA `PASS_WITH_RISK`
- MiniMax `PASS_WITH_RISK`
- 测试 H3 `APPROVE_WITH_RISK`

**都不能覆盖“创作质量仍未通过”的产品判断。**

这也直接支持 D-003（Role Prompt & Quality Contract）：模型能按合同生成结构化结果，不代表 Writer / Director / QA 的角色标准已经足够严格。

## 4. H3 / H4 边界

Track B 的 H3：

- reviewer=`P0_TEST_HARNESS`
- 是 GUI E2E 测试确认；
- **不是用户对成片的最终创作批准**；
- `publish_authorized=false`；
- 没有 H4；
- 没有真实平台发布。

不得把这个测试 Gate 写成“用户已经批准视频”。

## 5. Jianying 状态

Track B：

- 生成 `EXPORT` artifact `ART-31fc96ae936a4486`；
- GUI 下载 Jianying ZIP 成功；
- `unzip -t` 通过。

这证明：

> 可下载 transfer bundle 已成功生成。

它**不证明**：

- 此 ZIP 已在剪映真实打开；
- 所有 crop / motion / reveal / font 映射完全一致；
- 剪映内编辑已经验收。

所以状态仍是：

**export bundle generated + archive validated; real Jianying-open verification pending.**

## 6. 当前 P0 已证实的 Slice

当前实现分支已有下列记录：

- Slice 1：Project → Source/Media → Fact → Script → Audit → H2
- Slice 2：Director → Storyboard → Preview → Gate
- Slice 3：Fresh Voice → Audio Timing → Final Editable EDT
- Slice 4a：Local Background Jobs
- Slice 4b：QA → H3 → Deliver
- Slice 5：Track A deterministic provider-boundary browser regression
- Slice 6：Track B fresh live GUI acceptance

Track A / B 均是**人工浏览器验收**，尚不是 unattended browser automation suite。

## 7. P0 已修正的工程问题

分支记录的已实现变化包括：

- 新建项目的 Topic / Content Type；
- browser file picker / drag-drop Source/Media import；
- strict Script 正式 revision + Claim/Fact binding；
- read-only workflow projection；
- Storyboard Beat card 编辑；
- `expected_revision` / revision conflict；
- human-edit protection；
- Preview 与正式 Storyboard still 分离；
- Voice 后才开放 Final Editable EDT；
- 本地后台 job + job_id；
- single-flight；
- orphan RUNNING → `SERVER_RESTARTED`；
- refresh 后恢复 job 状态；
- Render revision stale protection；
- H3 risk acknowledgment；
- MP4 / Jianying bundle 下载；
- subtitle contrast fix；
- process/action list 避让 subtitle band。

这些事实当前属于 `p0/gui-only-e2e-interim` 分支，不能假装已经全部合入 main。

## 8. Main 与 P0 分支目前仍分叉

在本次核对时：

- `p0/gui-only-e2e-interim` 相对 `main`：ahead 10 / behind 16
- merge base：`674957813b5efea39e8cc3e61621245808ccacc7`

原因是：

- P0 分支继续实现 GUI E2E；
- main 同时新增了 Model Council、Claude Final、Q-009、D-002、D-003、Q-010 等知识/讨论更新。

因此下一步不能强制把 main 指到 P0 commit，也不能把 P0 分支称作“main 当前代码”。

需要正常 reconcile / merge，并保留 main 上的新 Council 文档。

## 9. 两个仍未解决的架构问题

### D-002 · Audio-First Director Pipeline

Track B 仍沿用：

`Director → Storyboard → Voice → AudioTimingMap → Final EDT`

它证明旧顺序可以完成工程 GUI E2E，**没有证明这个顺序是正确的长期生产架构**。

Q-009 的问题仍成立：

- Director 先猜 timing；
- Voice 后建立真实 temporal truth；
- retime 可修总时长，但未必修正语义切换点；
- 可能导致无谓 Storyboard / Render / QA 返工。

因此 Audio-first 仍需单独 Council / Spike / 实现评估。

### D-003 · Role Prompt & Quality Contract

Track B 创作质量 FAIL 进一步证明：

- 模型能返回合法 JSON；
- Provider 能真实调用；
- GUI 能走完；
- QA 能给 verdict；

仍不等于：

- Writer 质量足够；
- Director 视觉语言足够；
- Red Team 足够严格；
- MiniMax Visual QA 足够可靠。

当前 Prompt / Role Contract 必须继续按 D-003 加固。

## 10. 上传交接 ZIP 中需要纠正的旧文档

以下应视为**历史阶段说明**，不是当前总状态：

- `CONTENT_OS_当前状态交接包.md`：2026-09-27 / 126 tests / real model 0 次，已过期；
- `CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md`：旧 84 秒项目状态；
- `REAL_WORKFLOW_ACCEPTANCE_REPORT.md`：旧 84 秒生产闭环；
- `DELIVERY_README.md`：189 tests / 84 秒主样片，已落后于 Track B；
- `HARDENING_WORK_STATE.md`：Phase 2 Hardening 历史 checkpoint。

另外，上传 ZIP 的 `DELIVERY_README.md` 声称包中包含运行数据库/项目目录，但 `DELIVERY_NOTES.md` 与 `DELIVERY_MANIFEST.json` 明确说不包含 runtime SQLite databases / private local state；实际 ZIP 文件清单也未见 `phase2_preview_data`。因此该处属于交付说明错误，后续重新打包时应统一为：

> 交付包包含 tracked source / tests / Project Brain / registries / selected delivery samples；不包含本地 runtime DB、Keychain secrets、私有声音模型权重、venv/node_modules/cache。

## 11. 下一步建议（不是 Decision）

1. 先 reconcile `p0/gui-only-e2e-interim` 与 main，保留双方新事实。
2. D-001 依据 Claude Final + Track A/B 新证据完成 Synthesis，再由用户决定是否 ACCEPT P0 工程路径。
3. 优先 D-002：判断是否迁移到 Audio-first。
4. 优先 D-003：重建 Role Prompt / Quality Contract，解决当前创作质量 FAIL。
5. 再做 Track C 3–5 分钟稳定性；不能用 61 秒 Track B 推断长视频日更稳定。
6. 补真实 Jianying-open 验收。
7. H4 / platform publication 继续保持未授权。

---

本文件只纠正状态与证据，不修改 `DECISIONS.md`。
