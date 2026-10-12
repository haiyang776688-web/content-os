# P0 GUI-Only E2E · Interim Implementation

**Date:** 2026-09-28
**Baseline:** `674957813b5efea39e8cc3e61621245808ccacc7` (`main` 与 `origin/main` 同步后)
**Working branch:** `p0/gui-only-e2e-interim`
**Source discussion:** [D-001](discussions/D-001-p0-gui-only-e2e/00_TOPIC.md) 中的 GPT Proposal、Claude Review、GPT Rebuttal。Claude Final 尚未完成；[Synthesis](discussions/D-001-p0-gui-only-e2e/05_SYNTHESIS.md) 保持 `OPEN`/`PENDING`。

这是临时实施范围，不是 D-001 的最终决策，不修改 `DECISIONS.md`。Claude Final 到达后逐项核对，可能保留、修改或回滚本轮调整。已确认决策与当前代码实现仍分别核验。

## 当前验收定义

普通用户从新建空项目开始，不开 Terminal、不改 JSON、不调用内部 API，通过 GUI 完成 Source/Fact → Script/Audit/H2 → Director/Storyboard → Fresh Voice/Audio Timing → Final Editable EDT → Render/QA/H3 → MP4 下载；剪映导出可选，H3 不等于 H4。Track A 使用受控 Fake Provider 做 10–15 秒浏览器回归和真实短渲染；Track B 用新题材、真实 Provider、本地声音、MiniMax 视觉审查做 60–90 秒全新项目验收；3–5 分钟稳定性放在 P0 后。已有 `PRJ-bba515713057` 只作回归样本。

## 执行顺序与边界

1. **Slice 0 — 基线与四项 Spike。** 记录真实通过/失败/未知和证据；见 [p0-spikes](p0-spikes/)。开始前 189 passed、0 failed、1 条 Starlette 弃用警告，Workbench HTTP 200 且浏览器可打开。
2. **Slice 1 — Project → Source/Media → Fact → Script → Audit → H2。** 新项目表单补 Topic、Content Type；文件选择/拖放导入项目受控目录。脚本以普通文本和逐段最小 Claim/Fact/Evidence 修正为主，保存正式新版本并审计。所有写入携带当前 revision；每完成一段立刻用浏览器回归。
3. **Slice 2 — Director → Storyboard → 快速 Preview → Gate。** 从现有 StageCache、Artifacts、Gate、Revision 投影单一流程状态；只开放真实 `SET_BEAT` 可编辑字段。普通编辑不生成整套 Remotion still；Gate 前再生成正式 still。完成后做前端架构检查点，有证据才提出框架迁移。
4. **Slice 3 — Fresh Voice → Audio Timing → Final EDT → 窄 Timeline。** 分镜预览 EDT 是 provisional；本地正式配音和时间图建立后才开放 Final Editable EDT。字幕正文从已批准脚本派生，视觉样式可调；VOICE/SUBTITLE 时间不自由移动。
5. **Slice 4 — 最小持久 Job → Render → QA → H3 → Deliver。** Voice、Storyboard Still、Render、MiniMax QA 快速返回 job ID；同项目/种类/目标版本 single-flight，启动时将遗留 RUNNING 标为 `SERVER_RESTARTED`，刷新可见、失败可重试、显示阶段和已用时间。Render 绑定 EDT revision，过期结果标 STALE。H3 显示审查范围、Provider 和逐条风险确认；MP4/剪映包可实际下载。
6. **Slice 5 — Track A，然后 Track B。** 浏览器执行所有用户动作；测试 harness 只控制环境，Fake 位于 provider boundary。通过后停止，不进入 H4、Analytics 或 Phase 3。

每个 Slice 独立测试、独立 commit。P0 不迁移前端框架、不重写 Core、不建完整 NLE/队列/字段级智能合并/单 Beat AI regenerate；所有模型和来源文本统一安全渲染。AI 重建人工修订产物前，先拒绝并要求明确选择保留或丢弃。DeepSeek 当前实际 Provider/Model/Role 如实展示，Q-004 另议。

## Slice 0 已发现的直接阻塞

- 严格项目的主界面“保存新版本”调用旧文本脚本 API，只产生 `SCRIPT_REFERENCE`，不形成绑定的正式 `SCRIPT`；见 [SPIKE-001](p0-spikes/SPIKE-001-STRICT-SCRIPT-EDIT.md)。Slice 1 需要最小逐段修订/绑定入口，不能用纯文本绕过严格合同。
- 全新项目可以选本地克隆音色并试听，但正式 Voice 前的分镜、H2 等 GUI 链路尚未贯通；见 [SPIKE-002](p0-spikes/SPIKE-002-FRESH-VOICE.md)。
- 纯视觉 Beat 变更保留 Voice 和 AudioTimingMap；当前不需要重设计依赖图；见 [SPIKE-003](p0-spikes/SPIKE-003-DEPENDENCY-INVALIDATION.md)。
- 长任务没有可恢复的后台合同；见 [SPIKE-004](p0-spikes/SPIKE-004-LONG-JOBS.md)。

## 实施记录

- [Slice 1 · Project → H2](p0-slices/SLICE-001-PROJECT-TO-H2.md)：在隔离数据副本中，浏览器从新建项目走到真实独立审计和 H2；严格脚本修订另以既有回归项目验证。P0 全链路、Track A/B 仍未完成。
- [Slice 2 · Director → Storyboard Gate](p0-slices/SLICE-002-DIRECTOR-STORYBOARD.md)：同一隔离测试项目通过浏览器完成真实导演结构、人工 Beat 修改、快速预览、42 张正式分镜图及测试身份的 Gate；字体缺失与全角冒号预检阻塞已做针对性修复。前端架构检查点认为当前无需迁移框架。
- [Slice 3 · Fresh Voice → Final Timeline](p0-slices/SLICE-003-VOICE-TIMELINE.md)：同一隔离测试项目经浏览器生成正式本地配音和音频时间映射，再生成最终可编辑 EDT；视觉修改和撤销后音频依赖与分镜关卡保持有效。92.96 秒合成样本不是 Track B 验收。
- [Slice 4a · Background Jobs](p0-slices/SLICE-004A-BACKGROUND-JOBS.md)：正式配音、分镜图、渲染和视频视觉审查接入本地持久任务合同。隔离测试项目通过浏览器生成真实 MP4；QA、H3 与可下载交付仍属下一段工作。
- [Slice 4b · QA → H3 → Deliver](p0-slices/SLICE-004B-QA-H3-DELIVERY.md)：同一隔离合成项目通过普通 GUI 生成机械 QA、明确标记为 MOCK 的视觉 QA、终审包与测试身份的带风险 H3；MP4 和剪映 ZIP 均已实际下载并校验。真实 MiniMax 审查与 Track A/B 仍未完成。
