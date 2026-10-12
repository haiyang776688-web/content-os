# 尚未决定的问题

只放仍需要产品决定、技术取舍或外部信息的问题。讨论建议不自动升级为决策；已经明确的原则在 [DECISIONS](DECISIONS.md)，已经写好的代码现状在 [IMPLEMENTATION_STATE](IMPLEMENTATION_STATE.md)。`UNKNOWN` 是当前没有足够证据，不是默认答案。

| ID | 问题 | 已知约束 / 尚缺的证据 | 决定后影响 |
| --- | --- | --- | --- |
| Q-001 | P0 工作台保留原生 JS 逐步模块化，还是迁到轻量框架？ | 不改现有 Core；应以真实 GUI E2E、维护成本和迁移风险比较。当前没有冻结选择。 | Workbench 结构与交付节奏 |
| Q-002 | 用户修改与 AI 再生成怎样合并？ | 保留人工修改是已确认原则；`generated base + user override + resolved state` 等只是讨论方案，冲突提示/回滚/重基规则尚未定。 | Writer、Director、EDT、版本历史 |
| Q-003 | P0 演示题材、时长、哪些人工修改动作作为固定 GUI E2E 验收样例？ | 核心验收“普通用户不碰终端/JSON/API 完成视频”已定；可复现测试脚本和样本边界仍需定稿。 | E2E 测试、验收证据 |
| Q-004 | 如何落地 DeepSeek 的 Red Team 定位，又怎样处理当前 DeepSeek Research/Script、OpenAI 默认 Audit、实际 GLM Audit？ | [DEC-003](DECISIONS.md)是设计方向；现有配置不同。不要直接改老项目记录。 | Model Router、默认角色、迁移/回归 |
| Q-005 | H4 先支持哪个平台、何种授权与发布日志格式？ | H3≠H4 已定；当前无 `PUBLISH_LOG`，真实平台 API 未接。平台/账号/审核机制 `UNKNOWN`。 | Publish、权限、失败恢复 |
| Q-006 | 克隆声音的长期注册、同意记录、跨项目可用范围怎样统一？ | 旧 `YU_LOCAL_V1` 静态注册表与本次真实 VOICE 运行状态冲突；一次可用不等于普遍授权。 | Voice Registry、隐私门、GUI |
| Q-007 | 本地项目/素材的可移植备份和跨机恢复应采用什么最小合同？ | 有产物与剪映单向交接；完整备份/恢复验收证据 `UNKNOWN`。 | Storage、Asset、Export |
| Q-008 | Claude 云端讨论的原始链接/全文及哪些结论获用户确认？ | 当前窗口提供的是 ChatGPT 历史和当前请求；没有可独立核对的 Claude 原始逐字记录。 | `discussions/` 归档及决策追溯 |
| Q-009 | **Director 是否应从“文案后、配音前”移动到“配音与 AudioTimingMap 后”，把真实音频时间轴设为视频 Master Clock？** | 当前实现允许 Director 先用 `timing_intent` / `estimated_duration` 预估分镜，再在 VOICE/AUDIO_TIMING_MAP 产生后 retime；这会造成两类系统性返工：①真实配音时长与预估分镜不符；②即使总时长被 retime 对齐，画面切换点仍可能与真实语义时间点不一致，最终在 QA 暴露音画错位。用户已明确要求：**下次与 Claude 的 Council 讨论必须加入此问题，并在下一轮实际调整时优先修正流程顺序。** 待讨论目标方案：`H2 Script → Narration Units → Voice → AudioTimingMap → Director → Storyboard → Final EDT → Render/QA`；其中 Writer 负责 semantic truth，Voice/AudioTimingMap 负责 temporal truth，Director 负责 visual truth。尚需 Claude 复核现有依赖、Storyboard Gate、EDT 与返工路径后再决定正式合同。 | Production pipeline、Director IR、AudioTimingMap、Storyboard、EDT、QA、P0 GUI-Only E2E；可能形成新的 Council 议题 D-002 Audio-First Director Pipeline |

| Q-010 | **是否建立统一的 Role Prompt Pack + Model Adapter + Quality Rubric 系统，取代当前零散、过薄且分散在 registry / workflow / intelligence 等路径中的 system prompt？** | 当前已有 RoleContract、prompt_id/prompt_version、Skill Snapshot、response schema 和 Model Gateway，但多个核心角色的系统提示仍接近占位级，且运行路径中存在额外 hardcoded prompt，导致职责、Source of Truth、Must/Must Not、Hard Fail、返工规则和自检标准不统一。用户已明确要求：每个角色需要专属 Prompt 与严格审核标准，同时模型差异应通过 provider/model adapter 适配，而不是复制多套业务规则。D-003 已建立，需 Claude 进一步审查 Prompt Pack 分层、rubric、deterministic validator 边界、qualification suite 与模型适配策略。 | Prompt architecture、Role contracts、Writer/Audit/Director/Video QA、Model Adapter、Skill Snapshot、QA、provenance、P0 产出质量 |

关闭问题时记录结论、证据与日期；若形成正式决策，迁入 [DECISIONS](DECISIONS.md) 并在 [CHANGELOG](CHANGELOG.md) 留痕。不要把未答的问题反向写成已完成的实现。
