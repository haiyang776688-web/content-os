# 已确认项目决策

本表只收用户已确认的方向或现行 [工作流宪章](../../WORKFLOW_CONSTITUTION.md)的约束。**Status** 标的是设计决策状态，不代表代码已实现或 GUI 已可用；实现程度以 [IMPLEMENTATION_STATE](IMPLEMENTATION_STATE.md) 为准。以下条目的原始决策日未全部留下可核对记录，所以 Date 使用本次登记日并明确原日 `UNKNOWN`，不伪造历史时间。若某项实现与决策冲突，保留冲突，不改写决策为现状。

| ID | Date | Decision | Reason | Status | Affected Components |
| --- | --- | --- | --- | --- | --- |
| DEC-001 | 2026-09-28 登记；原日 UNKNOWN | **Remotion 只作为执行/渲染引擎，不承担 AI Director。**创作意图先在 Director IR/EDT 中形成。 | 避免渲染代码悄悄变成语义真源。 | CONFIRMED；当前架构已遵循，GUI 成熟度另见实现表。 | Director、Director IR、Timeline、Remotion |
| DEC-002 | 2026-09-28 登记；原日 UNKNOWN | **剪映只接单向导出的原生草稿**，不把剪映内修改自动回灌 Content OS。 | EDT 保持唯一可编辑真源，同时给用户精修出口。 | CONFIRMED；导出器有历史验收，当前样片无 EXPORT。 | EDT、Jianying Export、项目历史 |
| DEC-003 | 2026-09-28 登记；原日 UNKNOWN | **DeepSeek 定位为独立 Red Team/反例审查方向。** | 用异构模型挑战主生产结论，不把多模型多数票当事实。 | CONFIRMED_DESIGN；**IMPLEMENTATION_DIVERGED**：代码默认 DeepSeek 负责 Research/Script，Audit 默认 OpenAI，当前项目 Audit 由 GLM 执行。具体配置迁移未决。 | Model Adapter、角色目录、Audit、Worker 配置 |
| DEC-004 | 2026-09-28 登记；原日 UNKNOWN | **MiniMax 定位为视觉 QA**；审查范围必须与实际发送媒体一致。 | 视觉问题需要看画面；没有音频输入就不能宣称音频质检。 | CONFIRMED；本条真实调用为 `VISUAL_ONLY`，其结果需人工复核。 | Video QA、隐私门、Review Pack |
| DEC-005 | 2026-09-28 登记；原日 UNKNOWN | **EDT 是唯一可编辑时间线；分镜/设计表是上游意图，Remotion 与剪映是消费者。** | 降低多个时间线并行修改造成的漂移。 | CONFIRMED；命令与产物已落地，完整 GUI 编辑保护仍部分完成。 | Director IR、Timeline、Render、Export |
| DEC-006 | 2026-09-28 登记；原日 UNKNOWN | **H3 终片确认与 H4 发布授权分离。**H3 不能隐含允许发平台。 | 人工最终权必须在对外发布前再次生效。 | CONFIRMED；本条 H3 已通过且 `publish_authorized=false`；H4 功能尚未完成。 | Review、Publish、GUI |
| DEC-007 | 2026-09-28 登记；原日 UNKNOWN | **08 独占正式 Error/Rule Ledger 写入；07 只能形成观察/假设/实验，不能直接升级规则。**`CREATIVE_POLICY` 高于短期指标。 | 防止偶然数据与执行部门自评直接变成硬规则。 | CONFIRMED；基础治理代码存在，完整 GUI 流程待验收。 | Audit/Evolution、Analytics、Skill、Creative Policy |
| DEC-008 | 2026-09-28 用户本轮确认 | **P0 是 GUI-Only E2E：普通用户不打开终端、不改 JSON、不调用内部 API，完成一条视频。** | 当前最大缺口是可用生产工作台，而不是更多独立 Agent。 | CONFIRMED_PRODUCT_PRIORITY；尚未通过 E2E 验收。 | Workbench、全部生产阶段、验收测试 |
| DEC-009 | 2026-09-28 用户本轮确认 | **AI 自动化后保留人的修改权**，不能靠重新生成悄悄覆盖人工内容；最终可进入剪映精修。 | 创作者对风格、镜头和发布保有最终判断。 | CONFIRMED_DESIGN；覆盖层/重生成合并合约仍未定。 | Writer、Director、EDT、GUI、Export |
| DEC-010 | 2026-09-28 用户本轮确认 | **保持 XIAO-Y 角色与视觉一致性；拒绝 PPT 感、机械动作和通用白板动画。** | 成片要有辨识度、节奏和可复用的品牌身份。 | CONFIRMED_PRODUCT_TASTE；逐片质量仍需人工验收。 | Asset、Director、Production、QA |
| DEC-011 | 2026-09-29 用户明确确认 | **采用 `XIAO-Y Evidence Editorial` 作为正式视觉语言原则：默认使用 VGB-002 F2 / `BRAND_BALANCED`，同时保留 F1 / `EVIDENCE_HEAVY` 子模式。**Evidence 负责证明；XIAO-Y 负责解释、人格、反应、责任、转场和收束；Typography 负责短信息强调；Motion 负责引导注意力和表现信息变化。 | VGB-002 的同源受控比较中，F2 同时保留了可读证据、XIAO-Y 品牌人格与因果连续性；F1 的证据表达仍有效，只是不作为默认模式。 | CONFIRMED_PRODUCT_DECISION；冻结视觉语言原则，不冻结 VGB-002 的 19 秒镜头清单、坐标或时间点。来源：`VGB-002`；用户原文：`ACCEPT F2，F1 保留为 Evidence-heavy mode。` | Visual Language、Director、Visual Compiler、Storyboard、Remotion、Visual QA |

上述决策的来源是当前用户请求、已有 [宪章](../../WORKFLOW_CONSTITUTION.md)、[产品取向](PRODUCT_TASTE.md)与 [当前交接包](../../CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md)。其中 DEC-003/004 按用户本轮要求登记为**目标定位**，不是对当前 Worker 配置的描述。讨论模型提出的方案不自动进入本表。
