# WB-001 · WorkBuddy Independent Gap Review · Scope

**Review ID:** WB-001
**Reviewer seat:** WorkBuddy Council Reviewer / Diversity Reviewer（第三方独立审查席）
**Date:** 2026-09-29
**Repository:** `haiyang776688-web/content-os-vnext-phase1`（PRIVATE）
**Role boundary:** 本轮为 Council Review 起草，**不改业务代码、不改 Prompt、不改音频链路、不 merge、不改 DECISIONS.md、不改 D-002/D-003 Final Status、不发布、不做 H4、不创建 PR**。

---

## 一、本轮任务

回答一个问题：

> GPT 和 Claude 当前对 Content OS 的分析，还有哪些可能共同遗漏的重要问题？

检查方向覆盖用户指定的 A–O 共 15 个方向，并额外挑战 10 条 GPT/Claude 共同假设。目标是找**新问题**，不是把已知问题换说法重写。

---

## 二、接入方式

| 项 | 事实 |
| --- | --- |
| 通道 | 本机 `gh` CLI（已登录账号 `haiyang776688-web`），未使用其 API Key / Token 内容，未读取 Keychain |
| 克隆方式 | `git clone https://github.com/haiyang776688-web/content-os-vnext-phase1.git` |
| 本地路径 | `${EXTERNAL_VOLUME}/workbuddy/content-os-vnext-phase1` |
| 触及仓库范围 | **仅该仓库**，未扩大到其他 GitHub 仓库 |
| `git fetch origin` | 首次执行因本机代理返回 `CONNECT tunnel failed, response 502` 失败；克隆本身是最新的（remote `pushedAt` = 2026-09-29T04:47:50Z），因此对 `origin/*` 的认识等同于抓取后的状态。已复核 `origin/main` 与 `origin/p0/gui-only-e2e-interim` 两个 ref 指向的 commit 与 Project Brain 记录一致 |

Git 连接结论：**PASS**（有一处网络告警，未影响事实准确性）。

---

## 三、读取的分支与 commit

| Ref | Commit | 说明 |
| --- | --- | --- |
| `main`（知识主分支） | `7d06424` | `docs: add skill absorption matrix` |
| `p0/gui-only-e2e-interim`（活动实现分支） | `323f7a2` | `test: record fresh live gui e2e track B`，与 Project Brain 记录一致 |
| merge base | `6749578` | 与 `CURRENT_STATE.md` 记录一致 |
| 分歧 | main +25 / p0 +10 | 与 Project Brain 记录的 "ahead 10 / behind 16" **口径不同**（该记录是站在 p0 视角再含后续 push）；本次以 `git rev-list --left-right --count` 实读为准，两条路径都真实，只是计数基准不同 |

---

## 四、读取的关键文件

### Project Brain（main）

- `PROJECT_CONTEXT_MASTER.md`
- `PRODUCT_TASTE.md`
- `CURRENT_STATE.md`
- `IMPLEMENTATION_STATE.md`
- `DECISIONS.md`
- `REJECTED_IDEAS.md`
- `OPEN_QUESTIONS.md`（含 Q-009 / Q-010）
- `CHANGELOG.md`、`COUNCIL_PROTOCOL.md`、`ARCHITECTURE.md`、`ROADMAP.md`
- `HANDOFF_2026-09-29_P0_GUI_E2E.md`

### Council（main）

- `D-001-p0-gui-only-e2e/`（目录级核对）
- `D-002-audio-first-director-pipeline/00_TOPIC.md`、`01_GPT_PROPOSAL.md`、`02～05`（**仅占位**）
- `D-003-role-prompt-quality-contract/00_TOPIC.md`、`01_GPT_PROPOSAL.md`、`02_CLAUDE_REVIEW.md`、`03～05`（**仅占位**）
- `research/SKILL_ABSORPTION_MATRIX.md`

### 真实代码（main 为主，逐-file diff 到 p0）

`vnext/core/runtime.py`、`vnext/core/governance.py`、`vnext/core/editing.py`、
`vnext/phase2/production.py`、`vnext/phase2/contracts.py`、`vnext/phase2/visual_state.py`、
`vnext/phase2/stages.py`、`vnext/phase2/intelligence.py`、`vnext/phase2/api.py`、
`vnext/phase2/hardening/visual.py`、`vnext/phase2/hardening/audio.py`、`vnext/phase2/hardening/geometry.py`、`vnext/phase2/hardening/voices.py`、
`vnext/providers/director_contract.py`、`vnext/providers/workflow.py`、`vnext/providers/script_contract.py`（引用处）、
`vnext/gateways/model/gateway.py`、`vnext/registries/catalog.py`、
`vnext/renderers/remotion/adapter.py`、`vnext/renderers/remotion/project/src/Composition.tsx`、`vnext/renderers/remotion/resolver.py`、
`registries/characters/XIAO-Y_V1.json`、`registries/styles/XIAO-Y_TEMPLATES_V1.json`、`registries/skills/WRITING_DEFAULT.json`、`registries/skills/RESOLUTION_ORDER.json`、
`contracts/DIRECTORIR_SCHEMA.json`、`contracts/BEAT_SCHEMA.json`

### 真实产物证据

`examples/phase2/DIRECTOR_IR.json`、`examples/hardening/RESOLVED_VISUAL_COMPOSITION.json`、
`examples/activation/AUDIO_TIMING_REVIEW.md`、`examples/activation/style_review/MINIMAX_QA_TRIAGE.md`、
`examples/activation/style_review/FORMAL_REVIEW.md`（目录）

---

## 五、多模型 / 多视角说明

本席由单一 WorkBuddy 会话执行，**未使用多个独立模型跑流水线**；本轮采用「按评审角色切换分析框架」替代多模型并行：

| 视角 | 主要负责发现 |
| --- | --- |
| Architecture Reviewer | FINDING-03 / F-10 / F-12 |
| Product Reviewer | FINDING-07 / FINDING-08 |
| Prompt / Agent Reviewer | FINDING-09 / F-10 |
| Video Production Reviewer | FINDING-01 / FINDING-02 / FINDING-04 |
| QA Reviewer | FINDING-05 / FINDING-08 |
| Cost / Efficiency Reviewer | FINDING-06 / FINDING-09 |

已按用户要求去重，未列出六份原始输出。

---

## 六、未验证内容（明确 UNKNOWN）

1. Track B 真正 VOICE artifact 里 `word_timestamps` 是否非空（仓库内 fixture 的 `word_ranges` 为空，真实运行时数据不在仓库）。
2. Track B 最终 MP4 的实际文件大小 / 码率（用于判定 45MB MiniMax 上限的确切断点）。
3. `Governance.current_rules()` 在实际项目里生成的 `CURRENT_RULES.md` 真实字符数。
4. Claude 云端讨论的原始链接与逐字记录（`OPEN_QUESTIONS.md` Q-008 已记录同一缺口）。
5. 本机 `~/.content-os/settings/providers.json` 与 Keychain（**按用户指令不读**）。
6. 运行态数据库中 Track B 项目的真实 artifact 树（只有 part / delta，即 examples 快照）。

---

## 七、禁止修改范围（本轮坚守）

未修改：`vnext/**`、`registries/**`、`contracts/**`、`scripts/**`、`docs/project-brain/**` 下除 `discussions/WB-001-independent-gap-review/` 之外的任何文件、`DECISIONS.md`、D-002/D-003 的 Final Status、任何 prompt、任何模型岗位、任何分支 ref。

本轮唯一新增：

```text
docs/project-brain/discussions/WB-001-independent-gap-review/
├── 00_SCOPE.md
└── 01_WORKBUDDY_REVIEW.md
```
