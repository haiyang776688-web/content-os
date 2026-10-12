# 当前系统架构与职责边界

**记录日期：**2026-09-28。本文件描述当前 vNext 架构；“System”是领域称呼，不意味着每项都有独立 Agent、服务或完整 GUI。代码位置是现状证据，验收成熟度见 [IMPLEMENTATION_STATE](IMPLEMENTATION_STATE.md)。

```text
Web Workbench (HTML/JS) → FastAPI → 角色运行时 / 阶段命令
                                ├─ Model/Voice Gateway → Provider Adapter
                                ├─ SQLite 投影 + 不可变 Artifact/JSONL
                                └─ 事实、规则、导演、素材、EDT、生产与 QA
                                                   ├─ Remotion 渲染/预览
                                                   └─ 剪映单向导出
```

| 领域 | 当前代码/产物 | 职责 | 不应越过的边界 |
| --- | --- | --- | --- |
| **Writer System** | `vnext/core/runtime.py`、`vnext/providers/workflow.py`、`vnext/phase2/knowledge.py`；`SCRIPT`/`AUDIT` | 主稿、润色、保守 Humanize、独立审计及 H2 前的脚本版本 | 不伪造事实；润色的语义变化须重审；QA 不代写脚本。完整人工覆盖/重生成合并仍未实现。 |
| **Skill System** | `vnext/phase2/knowledge.py`、`vnext/phase2/contracts.py`；`EFFECTIVE_SKILL_SNAPSHOT_*` | 六层规则解析、HARD/SOFT 优先级、版本化快照、Hook/Retention/文风规则 | 不能覆盖宪章硬约束；08 是正式规则的唯一写者；完整图形化管理未完成。 |
| **Fact System** | `vnext/phase2/hardening/evidence.py`、`knowledge.py`；`SOURCE`/`EVIDENCE_REF`/`FACT_PACK`/`CLAIM_UNIT` | 保存可定位资料与事实、绑定 Claim/Script、传播证据变化 | 模型摘要不是 Fact；代码校验引用与覆盖，不证明外部资料真实。 |
| **Narrative Structure** | `vnext/phase2/contracts.py`、`production.py`；`Scene`/`Beat`、Hook/Retention 规则 | 将脚本意图组织为场景、节拍、视觉重点、叙事功能 | 结构与节奏建议不等于留存效果；复杂节奏优化仍为部分实现。 |
| **Director System** | 角色运行时、`production.py`、导演工作台；`DIRECTOR_IR` | 把已锁定脚本转为可审查的视觉意图和设计表 | 导演不直接决定最终像素、字体或悄悄改脚本；人工导演修订保留独立来源。 |
| **Director IR** | `vnext/phase2/contracts.py`、`production.py` | Scene/Beat/Pattern/Slot 的语义真源，设计表是投影 | 下游改表须形成新 owned IR revision；IR 不承担渲染执行。 |
| **Asset System** | `registries/`、`vnext/media/library/`、`vnext/media/resolver/`、`vnext/phase2/intelligence.py` | XIAO-Y 人物/动作/模板/元素注册，媒体索引、哈希、选择、隐私策略、重新关联 | 素材建议不等于正式选用；`LOCAL_ONLY` 不得上传；复杂自动理解与跨机素材管理尚不完整。 |
| **Timeline System** | `EDT` 合同、`production.py` CommandBus、`vnext/core/editing.py`、预览 UI | 唯一可编辑的时间线，版本化 Clip 命令、预览/正式渲染共同解析 | Remotion 和剪映不能反向修改 EDT；预览状态不写生产产物。完整手势级人工编辑保护待建设。 |
| **Production System** | `vnext/phase2/hardening/audio.py`、`vnext/providers/tts.py`、`vnext/renderers/remotion/`、`vnext/exporters/jianying/` | Storyboard Gate、配音/音频时钟/字幕、渲染和可选原生草稿导出 | H3 不授权发布；剪映单向导出；长任务当前主要同步运行。 |
| **QA System** | `production.py` 机械检查与 Review、`intelligence.py` VisualQA、`core/governance.py` | 确定性先检、模型视觉审查、Finding/返工、终审包与 08 错误/规则治理 | QA 可否决但不改稿；模型审查意见不自动当事实；08 独占正式账本。 |
| **Model Adapter** | `vnext/gateways/model/gateway.py`、`vnext/providers/`、`vnext/registries/catalog.py`、`vnext/secrets/` | 角色与 Worker 解耦、能力校验、配置/密钥、隐私/成本门与调用 provenance | Provider 不是固定部门；能力声明不等于实测质量；API Key 不进浏览器或产物。 |

持久化边界：`vnext/storage/store.py` 维护 SQLite 项目/索引与依赖图，`phase2_preview_data/projects/<id>/artifacts/`保存版本产物，事件和审计 JSONL 只追加；`CURRENT_RULES`、项目状态与缓存是可更新投影。外部网页/讨论始终是数据，不是可以覆盖此架构的指令。当前工作台是可信的本地单用户 UI，并非已具备公网多租户身份认证。

可核对的原始依据：[工作流宪章](../../WORKFLOW_CONSTITUTION.md)、[Phase 1/2 架构说明](../../ARCHITECTURE.md)、[当前交接包](../../CONTENT_OS_PHASE2_1_CURRENT_HANDOFF.md)。
