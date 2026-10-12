# Content OS 路线图

> **Open-source archive notice (2026-10-12):** Active development is paused and the public snapshot is based on the validated MDC baseline, not the later P0 GUI experiment branch described below. This file is retained as a dated historical state record. For the publishable current status, use the repository `README.md`, `LOCAL_PROJECT_INVENTORY.md`, and `docs/MAINTAINER_HANDOFF.md`. GUI-001 remains incomplete in the public snapshot.


**状态：**2026-09-28 维护版。只有 **P0 的 GUI-Only E2E 产品目标**由用户本轮明确指定为当前核心；其余优先级是基于 [实现缺口](IMPLEMENTATION_STATE.md)整理的工作排序，尚非冻结的功能/发布日期承诺。完成标准必须看真实代码、GUI 行为和产物，不以设计稿标 READY。

## P0 · 当前核心：GUI-Only E2E

**验收场景：**一位普通用户从浏览器进入本地 Content OS，完成一条 XIAO-Y 视频：新建/选题与资料 → 事实与脚本 → 人工方向确认 → 导演/分镜 → 人工分镜确认 → 素材与声音 → EDT/预览 → 正式渲染 → QA/返工 → H3 终片确认 → 下载可用成片，并可选择单向导出可编辑剪映草稿。全程不打开 Terminal、不修改 JSON、不直接调用内部 API。系统能显示当前 owner、下一步、风险、版本和失败后的回退点。

P0 完成还须有**真实浏览器操作记录或端到端自动化**，覆盖至少一次返工、保留人工修改、重新生成后核对、产物路径可找到；不能只用路由单测代替。H3 通过仍不等于 H4 发布；若测试延伸到发布，H4 必须单独授权。当前无此完整验收记录。

当前建议先后次序：

1. 把 H1/资料/事实/脚本/审计/导演/分镜/声音/时间线/QA 的断点连成清楚的工作台路径，取消完成任务时必须手填内部 JSON 的步骤。
2. 让人工镜头、文字、动作、时间线调整可修改、可比较、可撤销；定义 AI 重新生成与用户修改冲突时的处理方式，不能静默覆盖。
3. 给长时间模型/渲染任务可理解的进度、失败恢复与重复操作保护，并通过 GUI 真实走完一次。
4. 验证正式视频和可选剪映原生草稿的交付路径；明确草稿中无法保留的特性。

## P1 · 稳定创作与一致性

- 更细粒度的依赖失效和变更请求，避免一处小改动使整个作品无谓重做。
- 稳定的 XIAO-Y 动作/表情语义选择、镜头运动、标题与证据画面节奏；以实际观看质量而非素材数量验收。
- 声音、字幕时间线精度与人工校正；完善资产可用性、隐私状态和角色/声音元数据。
- 根据 [DEC-003](DECISIONS.md)调和 DeepSeek Red Team 设计定位与当前 Worker 分配；方法尚未决定。

## P2 · 审计、数据与多模型深化

- 07 Analytics 在 GUI 中生成 Observation/Hypothesis/Experiment，并与 08 的正式 Rule 审核隔离。
- 扩大模型能力实测、视觉 QA 的时间戳可复核性和审查来源呈现；在授权范围内评估视听合并 QA。
- 治理规则生命周期、错误复发与失效解释在工作台中的闭环。

## P3 · 发布与运营

- 在目标平台与授权方式明确后建设 H4、发布日志、平台适配与失败恢复。没有 H4 不进行对外发布。
- 多项目/多用户运营、权限与运行监控的产品化；具体范围待决定。

## Future · 仅作候选

更长时长稳定量产、跨设备素材/项目迁移、复杂人物动画或口型、多平台自动分发、完整商业化部署。它们不代表已经决定实施，也不能挤占 P0。相关选择放在 [开放问题](OPEN_QUESTIONS.md)。
