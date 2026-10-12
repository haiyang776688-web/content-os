# Content OS · Independent Gap Review 001 · WorkBuddy

**Review ID:** WB-001
**Reviewer seat:** WorkBuddy Council Reviewer / Diversity Reviewer
**Date:** 2026-09-29
**Baseline:** `main@7d06424` + `p0/gui-only-e2e-interim@323f7a2`，merge base `6749578`
**标记约定：** `FACT` / `CURRENT_IMPLEMENTATION` / `RISK` / `PROPOSAL` / `UNKNOWN`

> 本轮不修改业务代码、Prompt、模型岗位、Audio-first、DECISIONS.md 或任何 Discussion 的 Final Status。所有结论待用户裁定。

---

# Executive Summary

`FACT`：本轮最核心的判断是——**Track B 的 Creative FAIL 主要不是 Prompt 问题，而是渲染层表达能力天花板（renderer expressivity ceiling）**。当前的 `Composition.tsx` 没有任何连续运动能力：没有镜头、没有推拉/摇移、没有转场，每个 clip 只有一段约 0.27 秒的入场动画，然后整段 beat 完全静止。在这个前提下，任何 Director Role Prompt、任何新增的 Beat 语义字段、更多 XIAO-Y 动作素材，都不可能产出「不是 PPT」的成片。

`FACT`：**这个天花板同时被三层乘法式压缩**：

1. `motion_intent` 只有 `HOLD / FADE / SLIDE_UP` 三种（`vnext/providers/director_contract.py:19`）；
2. Director **不能选择 template 或 layout**（`template_id` 与 `semantic_pattern` 被 `const:None` 锁死），实际可达模板只有 6 个（共 12 个），且 layout 是 `vnext/phase2/hardening/visual.py:20` 里 12 组硬编码坐标；
3. XIAO-Y 动作由 `VisualResolver` **取第一个匹配项**（`visual.py:94`），同一 `character_intent` 永远产出同一个 pose，且 Mechanical QA **完全不检查动作重复**。

`FACT`：证据就在仓库里。`examples/phase2/DIRECTOR_IR.json` 六个 beat 全部是 `character_intent=EXPLAIN`、`character_action_id=None`、`timing_intent=10.0`；`examples/activation/AUDIO_TIMING_REVIEW.md` 明确写着 84.76 秒样片里「18 个节拍采用同一种动画方式」，且 18 个 beat 全部正好落在所属音频段落的**算术中点**。

`FACT`：据此，D-002 的问题前提需要修正。**当前实现已经把每个 beat 的外边界锚定到真实音频**（`AudioClock.retime` 用真实 segment 起止做分段），Director 只决定**段落内部**各 beat 的比例。真正残留的误差是「段内按比例均分」和「字幕按字数比例拆分」两处**同一个比例猜测缺陷**——两者都已在项目自己的复核文档中被承认，但没有被任何一方识别为「可不重排管线就能修」的最小解。同时，`BEAT_SCHEMA` 里本来就存在却零引用的 `phrase_id` 字段、脚本里本来就存在的「script segment ↔ 音频 entry」一一对应关系（样例 IR 为 1 段 1 beat，Track B 历史样片为 1 段 2 beat——粒度本身不受任何规则约束，这本身就是问题的一部分）、以及 TTS 返回后被存下来却没人使用的 `word_ranges`，都说明 **Narration Units 可能不需要成为独立 Artifact，而只需要一个显式的切分粒度策略 + 一个 anchor 机制**。

`FACT`：Visual QA 一侧也有同等量级的硬伤。MiniMax 拿到的 system prompt 只有两句话（`vnext/phase2/intelligence.py:168`），**没有任何 rubric**；同时视频以 `fps=1`（`vnext/gateways/model/gateway.py:84`）送入，模型物理上只能看到约每秒一帧，**不可能判断 rhythm / PPT feel / 动作重复**。项目自己的 `MINIMAX_QA_TRIAGE.md` 显示：6 条 finding 里 **5 条的时间定位或 beat 归属是错的**，即便它上下文里已经有正确的 EDT clips 时间范围。

`FACT`：**仓库内不存在任何 Platform Profile**，且画布被硬编码为横屏（`preview-720p`=1280×720，`preview-1080p`=1920×1080，无 9:16 选项）。同时 Mechanical QA 把字幕规则写成 BLOCKER：必须白色、必须无背景板、必须精确在 `y=.91`。对抖音/小红书/视频号这种底部 UI 密集的竖屏环境，这是一组朝错误方向用力的硬约束。另外，小红书 Title/Cover 相关策略目前**没有任何目标产物**（仓库内无 TITLE / COVER artifact 类型），所以 `emotion_hook_preferred` 这类策略暂时无处落地。

`FACT`：过程层面必须点名——**D-002 并没有 Claude 的 Review / Rebuttal / Final，Synthesis 也全是 PENDING**（三个文件各 5 行占位）。因此「GPT 和 Claude 对 D-002 的共同分析」在仓库记录里并不存在，D-002 目前只有 GPT 单方面的 Proposal。这不是假设，是可核对的文件事实。

**新发现 12 项，其中 BLOCKER 2 项、MAJOR 7 项、其余为 NOTE/MINOR。** 最高杠杆问题：**先给渲染器增加连续运动能力（哪怕只有「缓慢推近 + beat 间转场」两件事），再谈 Director Prompt 重构。** 否则 D-003 的投入会被渲染管线吞掉，产出「Prompt 已升级」的错觉，而用户看到的画面几乎不变。

---

# Facts Confirmed

优先级按用户规则：**真实代码 / commit / 测试 / 产物 > Project Brain > 历史交接 > 模型记忆**。

| # | FACT / CURRENT_IMPLEMENTATION | 证据位置 |
| --- | --- | --- |
| FC-1 | 双分支确认：`main@7d06424`、`p0@323f7a2`，merge base `6749578`，`main +25 / p0 +10` | `git branch -a`、`git rev-list --left-right --count` |
| FC-2 | **D-002 只有 GPT Proposal。** `02_CLAUDE_REVIEW.md` / `03_GPT_REBUTTAL.md` / `04_CLAUDE_FINAL.md` 均为 5 行占位（PENDING），`05_SYNTHESIS.md` 正文全为 `PENDING` | 文件实读 |
| FC-3 | D-003 缺 Rebuttal / Final，Synthesis 同为空壳 | 文件实读 |
| FC-4 | 渲染器仅有四类动效：reveal 透明度插值（8 帧）、SLIDE_UP 位移（8 帧）、MARKER/UNDERLINE SVG 描边绘制（12 帧）、treatment 缩放（10 帧）。**无 camera / zoom / pan / 转场** | `Composition.tsx:11–32` |
| FC-5 | `motion_intent` 枚举 = `['HOLD','FADE','SLIDE_UP']` | `director_contract.py:19` |
| FC-6 | Director 被禁止指定 `template_id` / `semantic_pattern`（`{'const':None}`），由 resolver 按 `pattern_id → SEMANTICS → TEMPLATES` 决定 | `director_contract.py:19`、`visual.py:13–18` |
| FC-7 | 12 个模板中，生产链路可达的只有 6 个；`CTA_END_CARD`、`CHARACTER_CENTER`、`INFO_LEFT_CHARACTER_RIGHT`、`CHARACTER_LOGO`、`EXTREME_CLOSEUP` 不可达（尽管 dynamic 分支为其中几个写了 layout 代码） | `visual.py:16–18` 与 `TEMPLATES` 映射对照 |
| FC-8 | layout 是 12 组硬编码 `[x,y,scale]` | `visual.py:20–32` |
| FC-9 | 角色动作选择为**首个匹配**：`next(a for a in actions if intent in a.semantic_intents)`，无轮转/去重/预算 | `visual.py:94` |
| FC-10 | 6-beat 样例 IR 中：6/6 `character_intent=EXPLAIN`、6/6 `character_action_id=None`、6/6 `timing_intent=10.0`、6 个 script segment 对应 6 个 beat（1:1） | `examples/phase2/DIRECTOR_IR.json` |
| FC-11 | 84.76s 样片：18 个 beat，每段 2 个 beat 且**均分**；官方自查承认「18 个节拍采用同一种动画方式」「超宽字幕在段落内部按字数比例拆分，不是逐词强制对齐」 | `examples/activation/AUDIO_TIMING_REVIEW.md` |
| FC-12 | `AudioClock.retime()` 已用真实音频 segment 起止重算 beat 外边界，段内按 `timing_intent` 比例分配 | `audio.py:90–102` |
| FC-13 | TTS 逐段返回并可能带 `word_timestamps`，已被写入 `entries[].word_ranges` 与 `provenance.raw_provider_timestamps`，但 `retime()` 与 `subtitles()` **都不读取** | `workflow.py:57–61`、`audio.py:98–131` |
| FC-14 | `BEAT_SCHEMA` / `DIRECTORIR_SCHEMA` 中存在 `phrase_id` 字段，全仓库从未被赋值或读取；`DirectorIR.transitions` 同样恒为空 | 全仓 Grep |
| FC-15 | MiniMax QA 的 system prompt 仅两句话，无任何 rubric | `intelligence.py:168` |
| FC-16 | 视频以 `{'fps':1}` 送入 MiniMax | `gateway.py:84` |
| FC-17 | QA 输入为整段视频 base64 inline，上限 45MB，**无降采样/重编码通道**（对比：图片 caption 路径会 scale 到 480px） | `intelligence.py:161`、`visual_review_copy()` |
| FC-18 | 任一 QA item 时间戳越界 → **整次 QA 抛异常**（`QA_TIMESTAMP_INVALID`），不降级、不剔除该条 | `intelligence.py:183` |
| FC-19 | 6 条 MiniMax finding 中 5 条时间定位或 beat 归属错误 | `MINIMAX_QA_TRIAGE.md` |
| FC-20 | `npx remotion render` / `storyboard_motion` 硬编码 `timeout=300`；`still` 为 `timeout=120`，且 **每 beat 生成 2 张 still，每张一个子进程** | `adapter.py:66,86`、`production.py:188–190` |
| FC-21 | Voice 逐 script segment 调用一次 TTS，再 concat；无逐段缓存复用 | `workflow.py:57–61` |
| FC-22 | Voice 当前被 `require_storyboard()` 强制排在 Storyboard Gate 之后（D-002 描述的属实） | `workflow.py:50` |
| FC-23 | 画布只有两种：1280×720 / 1920×1080，均为 16:9；无 9:16 分支 | `production.py:142,158,159`、`contracts.py:213` |
| FC-24 | 全仓无 Platform Profile / 抖音 / 小红书 / 视频号 概念代码（唯一 `PLATFORM-LOGO-SLOT` 是通用元素槽位）；无 TITLE / COVER artifact 类型 | 全仓 Grep + contracts 目录 |
| FC-25 | 字幕被 Mechanical QA 强制：必须无标点、单行、无背景、颜色必须为白、`y` 必须精确 0.91，任一违反为 BLOCKER | `production.py:381–389` |
| FC-26 | `purpose / visual_focus / visual_form / retention_function / density / tempo` 六个 Beat 字段被 contract 要求产出，但**无任何生产代码读取** | `contracts.py:301–307` + 全仓 Grep |
| FC-27 | `CURRENT_RULES.md` 全文被拼进每个角色的 system prompt，含最多 4 个 rule set 的 `indent=2` JSON 全文，**无任何长度预算或裁剪** | `runtime.py:158`、`governance.py:81–99` |
| FC-28 | `registries/skills/RESOLUTION_ORDER.json` 从未被代码加载；层序在 `knowledge.py:LAYERS` 重复实现；`hard_rules_override:false` 无对应实现 | Grep + `knowledge.py:13` |
| FC-29 | `VOICE_AUTHORIZATION` artifact 在音频已合成之后才创建 | `workflow.py:57–68` 顺序 |
| FC-30 | Audit 判 FAIL 时代码直接清除 `project.h2_script_artifact_id` | `runtime.py:218` |
| FC-31 | **p0 分支已有多项 D-002/GPT 提案的半成品实现**：`GENERATE_PRESERVING_AUDIO`、`human_edits_present()` 重生成护栏、Final EDT 显式绑定 voice+amap 依赖、后台 job 化 storyline/voice/videoqa | `git diff main p0` |
| FC-32 | 既有的成熟 mitigations（blind audit、`CLAIM_REVIEW_*` 强制、visible_review_copy 去音轨、`no_pixels()` 禁像素、剪映单向导出）在代码中确实存在且有效 | runtime.py / production.py / intelligence.py |

**Project Brain 与代码的冲突（按规则同时保留，不静默选边）：**

| 冲突 | 说明 |
| --- | --- |
| C-1 | `CURRENT_STATE.md` 记 "P0 相对 main: ahead 10 / behind 16"；本次实读为 `main +25 / p0 +10`。两者都不错，是计数基准不同，但文档容易被误读为 P0 落后更多。**不得据此改写任一侧代码状态。** |
| C-2 | `SKILL_ABSORPTION_MATRIX.md` 大量建议落在「Writer/Director 增加字段」，但 FC-26 证明这类字段目前是 write-only。**矩阵的建议不自动等价于有效实现。** |
| C-3 | `director_contract.py` 注释称 Scene duration 「等于 beat timing_intent 之和」，而 `audio.py` 在真实音频存在时会整体覆盖这些值。两者同时为真，取决于是否已有 AudioTimingMap——这正是 D-002 未决造成的语义漂移，建议在 resolving 前保持双标注。 |

---

# Shared Assumptions To Challenge

按用户要求逐条回应，并补 3 条。

| # | 共同假设 | WorkBuddy 结论 | 依据 |
| --- | --- | --- | --- |
| Q1 | Audio-first 一定比当前顺序好吗 | **不确定，且当前论证不足。** 外边界已音频驱动；真正痛点在段内比例分配。先做 Spike 区分「是否需要整条重排」vs「只需引入 word/phrase anchor」 | FC-12 / FC-11 |
| Q2 | Narration Units 一定需要独立 Artifact 吗 | **大概率不需要。** script segment ↔ 音频 entry 已一一对应，样例 IR 中又是 1 段 1 beat。所需的是**颗粒度策略**（Writer 产出更短 segment），而不是新产物类型 | FC-10 / FC-13 |
| Q3 | Prompt 写得越详细一定越好吗 | **否。** FC-26 证明已有 6 个语义字段是 write-only；FC-27 证明每层规则无预算约束地进入 system prompt。加厚 prompt 在 write-only 字段上纯粹是 token 成本 | FC-26 / FC-27 |
| Q4 | Visual Job 真能解决 PPT 感吗 | **只有在 resolver/renderer 消费它时才有意义。** 否则就是第 7 个 write-only 字段。PPT 感的物理定义是「画面在 beat 内不发生连续变化」，这是渲染器属性 | FC-4 / FC-26 |
| Q5 | MiniMax 适合长期担任 Visual QA 吗 | **当前配置下不适合做「时间维度」审查。** 它被要求判断 rhythm/重复/节奏，却只收到 1fps 输入且无 rubric。可以保留做静态构图/可读性审查，时间类应转 deterministic | FC-15 / FC-16 / FC-19 |
| Q6 | Track B Creative FAIL 主要真的是 Prompt 问题吗 | **不是。** 主要是渲染表达能力 + easy resolver 确定性坍缩 | FC-4 / FC-5 / FC-9 |
| Q7 | Renderer / Template / Asset Resolver 有没有可能才是主要瓶颈 | **是。** 这是本轮最重要的结论 | FC-4 / FC-7 / FC-8 / FC-9 |
| Q8 | Content OS 是否角色过多 | **当前 6 个核心角色数量合理**；真正冗余的是**字段**而非角色（FC-26），以及 MEDIA_RESOLVER 名不副实（Claude 已指出，本轮确认） | FC-26 |
| Q9 | 某些 Agent 是否应该直接合并 | **不建议此时合并。** 在 write-only 字段未清理前合并角色，会让「谁产出、谁消费」更难定位。建议先删 write-only 字段，再评估合并 | — |
| Q10 | Platform Profile 是否会让 Prompt 系统过度复杂 | **问题不成立——因为还没有 Platform Profile。** 真正的复杂度风险来自 FC-27（规则无预算注入），与 Platform Profile 无关 | FC-24 / FC-27 |
| E1（新增） | 「给模型更多上下文没有代价」 | 否：每加一层 prompt，Director 的可控性反而下降，因为 Director 最终只能输出 resolver 认识的东西 | FC-6 / FC-26 |
| E2（新增） | 「205 tests passed 说明链路健康」 | 否：测试覆盖的是 contract/geometry/typography，**没有任何测试断言「相邻 beat 的视觉状态不同」**，也没有 pose 多样性断言 | production.py:442–448 |
| E3（新增） | 「Storyboard Gate 是有效的创作关卡」 | 否：Gate 审的是每 beat 2 张静态图，而渲染器无连续运动 → **这个人类关卡结构上无法发现 PPT 感与节奏问题** | FC-4 / production.py:169–199 |

---

# New Gaps Found

> 只列本轮认为**双方共同遗漏**的新问题。Claude Round 02 已经准确指出的问题（多路径冲突、schema 双拼、`thinking:disabled`、MiniMax 单点依赖、数字溯源 validator 设计）不再重复，仅在结尾标注确认。

---

## FINDING-01 · 渲染层没有连续运动能力：Creative FAIL 的物理根因

```text
Finding ID:   WB-FC-001
Type:         FACT + RISK
Problem:      Remotion Composition 只支持四类一次性入场动画，没有任何 camera / zoom / pan / 转场。
              beat 内部在第 ~8 帧之后完全静止。这套渲染词汇无论 Prompt 怎么写都只能产出 PPT。
Evidence:     Composition.tsx:11–32（仅有 opacity/translate/scale 插值 + SVG clipPath 描边）；
              director_contract.py:19（motion_intent 枚举仅 3 项）；
              AUDIO_TIMING_REVIEW.md「18 个节拍采用同一种动画方式」；
              用户对 SPAbold 的实际判语：PPT 感、白底偏空、机械重复。
Why it matters: 它决定了 D-003 的天花板。如果先修 D-003，会得到「Prompt 已升级」的观感，
              而画面几乎不变，用户在下一轮会再次 FAIL，并损失一轮 Council 与一轮真实生产。
GPT/Claude current assumption:
              GPT: Track B Creative FAIL 是「Director 职责/质量标准不清」→ 走 Role Prompt Pack。
              Claude: 同意并指出 Director 收到的指令里完全没有 PPT/XIAO-Y 取向。
              双方都把「补指令」当成主要解法。
WorkBuddy challenge:
              补指令的前提是「模型有能力表达」。在渲染词汇为 3 个、且全部是 0.27s 入场动画时，
              Director 无论多懂电影语言都只能输出 PPT。缺的是词汇，不是理解。
Alternative explanation or solution:
              分层补词汇，成本由低到高：
              (a) Ken Burns：给 CHARACTER/MEDIA clip 增加 scale/position 的帧函数（~10 行 TSX）；
              (b) 层次转场：beat 之间的 crossfade / swipe（Composition 里加 8–12 帧交叠）；
              (c) Evidence POI zoom：让 SCREEN_DETAIL_ZOOM 名副其实（现在名不副实，见 F-07）；
              (d) 信息状态动画：进度、计数、对比条形随时间变化。
              建议先在单一现有 IR 上做 (a)+(b)，再让用户判定，验证后再写 Role Prompt。
Severity:     BLOCKER（对 creative acceptance 目标而言）
Confidence:  HIGH（代码事实）+ MEDIUM（「这就能让画面变好」是待验证命题）
What would prove or disprove this:
              取 Track B 同一份 IR，只改渲染器加 (a)+(b)，其余不变，产出第三条视频给用户盲评。
              若用户仍判 FAIL → 根因另有其人（很可能是 F-03 的模板坍缩）；若判明显改善 → 本条成立。
```

---

## FINDING-02 · XIAO-Y 动作重复是「首个匹配」确定性坍缩，不是素材库不足

```text
Finding ID:   WB-FC-002
Type:         FACT + RISK
Problem:      VisualResolver 用 next(...semantic_intents...) 取第一个匹配动作。
              同一 character_intent 在任何 beat、任何剧集里永远得到同一个 PNG。
              既没有轮转，也没有多样性预算，也没有上一次用过的记忆。
Evidence:     visual.py:92–96；examples/phase2/DIRECTOR_IR.json 6/6 beat 为 EXPLAIN 且 action_id=None；
              XIAO-Y_V1.json 里 EXPLAIN 意图只有 4 个动作、KEY_POINT 6 个、POSITIVE 9 个。
Why it matters: 用户已经在 prepare 新的 XIAO-Y HD 动作包（本项目路径下可见 v1.1_HD）。
              但增加素材**不会改变输出**——resolver 仍然返回第一个匹配项。
              这是典型的「加了资源但效果不变」陷阱。
GPT/Claude current assumption:
              GPT D-003 §7：Director 应「控制 pattern repetition」→ 靠 Must Do 约束模型。
              Claude §8：建议加 deterministic 计数（连续 3 个 beat 同 action 就拒绝）。
WorkBuddy challenge:
              两位都把「重复」当成 Director 的选择问题。实际上在 intent-only 输入路径上
              Director **没有选择权**：它没填 action_id，resolver 自己定了。
              Claude 的计数校验是必要的但仍不够——因为它是「拒绝」，不是「分配」。
Alternative explanation or solution:
              把动作选择从「模型责任」移回「程序责任」：
              (a) deterministic allocator：intent + 可用动作集 + 最近使用历史 → 轮转/加权选择；
              (b) 允许 Director 指定 action_id 时保留其权威，但 allocator 拒绝连续重复并给出次优替换；
              (c) Mechanical QA 增加 ACTION_REPETITION / INTENT_REPETITION 硬检查（现完全缺失，
                  目前只有 MOTION_REPETITION（全体同才触发）与 KEYWORD_PATTERN_REPETITION（全同 pattern 才触发））。
              注意1：题材足够时，也应该限制 character presence 比例——现在 evidence 类模板
              presence 是 ['NONE']，但角色回归后仍占 ~50% 宽度，人物出场比例并无保险人监管。
Severity:     MAJOR
Confidence:  HIGH（代码与产物双向证据）
What would prove or disprove this:
              用同一份 IR 跑 allocator 版本，统计 distinct action 数从 1 → 6 后，
              用户是否仍评价「动作重复」。
```

---

## FINDING-03 · Director 没有 layout / template 权限，可视组合上限极低

```text
Finding ID:   WB-FC-003
Type:         FACT + RISK
Problem:      director_contract 把 template_id / semantic_pattern 锁为 const:None。
              生产链路可达模板仅 6 个（注册表 12 个），layout 是 12 组硬编码坐标。
              理论状态空间 ≈ 6 模板 × 12 layout × 3 motion ≈ 数百个离散静态卡片。
Evidence:     director_contract.py:19；visual.py:16–18（TEMPLATES 映射）、20–32（LAYOUTS）；
              12 个模板中 EXTREME_CLOSEUP / CHARACTER_CENTER / INFO_LEFT_CHARACTER_RIGHT /
              CHARACTER_LOGO / CTA_END_CARD 均无可达路径；CTA_END_CARD 需要 'CTA' 语义，
              而 8 个 pattern 的 SEMANTICS 里没有 CTA。
Why it matters: 解释「每条视频看起来都差不多」的结构性上限，且它横跨剧集而非单条视频。
              同时它解释了为什么 dynamic/XIAOY_EXPLAINER 分支里给不可达模板写 layout 代码毫无意义。
GPT/Claude current assumption:
              D-003 讨论中的隐含前提：Director 是 layout 的决策者之一（只是被禁了像素坐标）。
WorkBuddy challenge:
              Director 实际上连「语义级布局」都不是决策者；它只能选 pattern_id，
              而 pattern 到 layout 的映射是 1:1 的确定性函数。所谓 visual truth owner 在这个维度上是空名。
Alternative explanation or solution:
              不必立即给 Director 像素权限（那违反 DEC），但可以：
              (a) 放开 template_id 让 Director 在「同一 semantic 的若干合规 template」里二维选择；
              (b) 或反过来：承认 layout 是 XIAO-Y brand 资产（品牌一致性要求），
                  那么 variational 的责任就落到 motion / pacing / 内容密度，
                  必须同时补 F-01 的运动词汇，否则「不放权 + 无运动」= 恒定 PPT。
Severity:     MAJOR
Confidence:  HIGH
What would prove or disprove this:
              统计 N 条已完成视频的 (template_id, layout, motion) 三元组去重数量。若长期个位数，本条成立。
```

---

## FINDING-04 · D-002 的前提需要收窄：段外边界已由真实音频决定，真正残留的只有「段内比例猜测」

```text
Finding ID:   WB-FC-004
Type:         FACT + PROPOSAL
Problem:      当前 retime() 已用 AudioTimingMap 的真实 segment 起止为每个 beat 定外边界，
              段内则按 timing_intent 比例均分。因此 Director 「猜 timing」的范围
              比 D-002 描述的要小得多——它猜的是「一个 8 秒段落内部怎么切两刀」，
              而不是「整段多长」。同理，字幕在段内按**字符数比例**再拆分。
Evidence:     audio.py:98–101（retime 公式）；audio.py:117–123（字幕按 len(c)/weights 比例分配）；
              AUDIO_TIMING_REVIEW.md 明示：18 个 beat 全部落在段落算术中点，
              「超宽字幕在段落内部按字数比例拆分，不是逐词强制对齐」。
Why it matters: 它把一个「重构整条管线」的命题，缩小为一个「引入锚点」的命题。
              若直接重排 Director/Voice 顺序，要改 require_storyboard 依赖、Storyboard Gate 语义、
              GUI 工作流顺序与多条测试；而收益可能只来自其中一个子问题。
GPT/Claude current assumption:
              D-002 00_TOPIC：Director 在真实音频前确定了 timed storyboard → 音画错位 → 返工。
              D-001 Claude Final 已警告「先做 Spike 区分局部 bug 与系统性顺序问题」。
WorkBuddy challenge:
              Spike 的设计本身有盲点：它比较的是「旧顺序 + retime」vs「完整 Audio-first」，
              但没有把「保留顺序 + 引入 phrase/word anchor」作为第三个臂。缺这个臂就无法判断
              完整重排是否必要。
Alternative explanation or solution:
              三条由小到大的候选，建议按此顺序验证：
              (S1) **Word/phrase anchor**：TTS 已返回 word_timestamps 并被存进 word_ranges（FC-13）。
                   让 retime() 把 beat 边界吸附到最近的词/短语边界，而不是按比例切。
                   字幕同样用真实词边界而非字符比例。零管线改动。
              (S2) **Narration Units 作为「切分粒度策略」而非新 Artifact**：
                   要求 Writer 产出的 segment 更短（例如 1 个单位想法 / ≤2 句），
                   使「每 segment 一个 beat」成为常态（样例 IR 已是 1:1），
                   让 segment 的真实起止直接等于 beat 的真实起止。
              (S3) **Placement of Director after Voice**（完整 Audio-first，需改 require_storyboard 与 Gate 语义）。
              另有两条明显更省的选项，此前无人提出：
              (S4) 已有但未用的 `phrase_id` 字段（BEAT_SCHEMA / DIRECTORIR_SCHEMA 中存在，全仓零引用）。
                   把它接上线即可完成 anchor 绑定，无需新增 Artifact 字段。
              (S5) `DirectorIR.transitions` 字段同样恒为空且渲染器不支持任何转场——
                   这说明「contract 承诺渲染器不实现的能力」不是孤例（见 F-07 vs SCREEN_DETAIL_ZOOM）。
Severity:     MAJOR（可能避免一次高成本低收益的重排）
Confidence:  HIGH（代码与文档一致）/ MEDIUM（S1 是否可行取决于 word_timestamps 实际是否非空）
What would prove or disprove this:
              检查 Track B 真实 VOICE payload 的 word_timestamps（仓库内 fixture 为空）。
              若非空：先做 S1，用量^(-1) 的切 ASEalignment 误差衡量是否需要 S3。
              若为空：需先引入本地强制对齐（whisper / aeneas 一类），成本仍低于重排整条管线。
```

---

## FINDING-05 · Visual QA 的失效是「输入 + rubric 双重不足」，不只是 Prompt 问题

```text
Finding ID:   WB-FC-005
Type:         FACT + RISK
Problem:      (1) MiniMax 收到的 system prompt 只有两句话，没有 rubric、没有 severity 定义、
              没有 XIAO-Y 一致性标准、没有「什么算 PPT 感」的可执行描述。
              (2) 视频以 fps=1 输入 → 模型每秒只看约一帧，物理上无法感知节奏/连续性/运动重复。
              (3) 0 issues → verdict = PASS，而不是「无信号」。
              (4) 任一 item 时间戳越界 → 整次 QA 抛异常，整段昂贵上传作废。
Evidence:     intelligence.py:168（prompt 全文）、gateway.py:84（fps:1）、intelligence.py:187（0 issue → PASS）、
              intelligence.py:183（越界即 raise）；
              MINIMAX_QA_TRIAGE.md：6 条 finding 中 5 条时间定位或 beat 归属错误，
              而 MiniMax 的 context 里**已经**提供了正确的 EDT clips 时间范围。
Why it matters: 承担 creative 部分把关的环节既看不见被测现象，也没有判断标准，
              还会在长视频里因单条幻觉而整体失败。它的 PASS_WITH_RISK 目前信息量接近零。
GPT/Claude current assumption:
              Claude §9：核心解法是让 QA 引用 clip_id 而非时间戳。
              GPT §8：让 MiniMax 审查 dimensions 列表（含 PPT feel、rhythm）。
WorkBuddy challenge:
              clip_id 方向是对的，但不足以解释 FC-19 的现象：MiniMax 在**持有正确 clip 范围**的情况下
              依然把现象归给了错误的 beat。这说明它的失败层在「时间→片段」映射，而非仅输出格式。
              同时，即便它格式完美，1fps 输入使 rhythm/motion 类判断**本质上不可执行**。
Alternative explanation or solution:
              把 MiniMax 的职责收窄到它真正能做的事，其余转 deterministic：
              (a) 输入：短视频随机/按 beat 采样若干关键帧 + 少量短 motion 片段（>8fps），
                  而不是整视频 1fps；顺带解决 45MB 上限（见 F-06）。
              (b) Rubric：写成结构化 checklist 放进 request.config / user message（不是 system prompt），
                 每一项要求「引用 clip_id + 一句话画面证据 + 观察/推断二分类」。
              (c) 0 finding 时输出 NO_FINDING_REPORTED 的显式 WARNING，避免静默 PASS。
              (d) 时间戳越界 → 剔除该条并加 WRONG_ITEM 计数，而不是终止整次 QA。
              (e) 所有可由程序算的维度（同 pose 连续出现、相邻 beat 构图签名相似度、
                  文字 Minimumfont size、对比度、初级主体占比、白底面积比）转 Mechanical QA。
Severity:     MAJOR
Confidence:  HIGH
What would prove or disprove this:
              用同一视频跑：① 当前配置 ② clip_id 要求 ③ 提高采样 fps + rubric checklist，
              对比 beat 归属正确率（当前基线 1/6 ≈ 17%）。
```

---

## FINDING-06 · 长视频的三个硬失败点：渲染 timeout、per-beat still 风暴、45MB QA 上限

```text
Finding ID:   WB-FC-006
Type:         FACT + RISK
Problem:      61s 通过不能外推到 3–5 分钟，有三个与倍数无关的**硬性**阻塞点：
              (1) `npx remotion render` 与 `storyboard_motion` 硬编码 timeout=300s，与时长无关；
              (2) storyboard 每 beat 生成 2 张 still，每张一个独立 npx 子进程（各含一次 headless browser 启动）。
                  3–5 分钟视频约 30–60 beat → 60–120 次浏览器冷启动；
              (3) MiniMax QA 输入为原视频重封装（不重编码）且上限 45MB，无降采样通道 →
                  长视频直接 `VIDEO_TOO_LARGE_FOR_INLINE_INPUT`，视觉 QA 不可用。
              另加成本项：Voice 是对每个 script segment 各调一次 TTS；N 段 = N 次调用，
              且任何 script 改动都会整体重录（无逐段复用）。
Evidence:     adapter.py:66,86（timeout=300）；adapter.py:48（still timeout=120）；
              production.py:184–192（逐 beat 逐帧子进程）；
              intelligence.py:161 与 visual_review_copy()（-c:v copy，无 scale）；
              workflow.py:57–61（逐 segment TTS）。
Why it matters: 这三项都会在 Track C（3–5 分钟）上直接报错，而不是「慢一点」。
              尤其 (3) 会让「物理 утратив inability to perform any form of visual QA」= 长视频完全没有视觉把关。
GPT/Claude current assumption:
              双方都把长视频风险列为「会被放大」，但没有定位到具体的硬编码阈值与操作数量级。
WorkBuddy challenge:
              61s → 300s 不是「放大」，是跨过三个不同性质的阈值。需要在 Track C 之前逐项处理，
              而不是等 Tree 成长视频返工时再诊断。
Alternative explanation or solution:
              (a) timeout 改为按 duration 计算的下限 + 可配置上限；
              (b) storyboard 改为一次 render 抽取多帧（或用 --frames 批量），或至少抽样而非全 beat；
              (c) QA 输入增加低码率/低分辨率/短片段三种 mode，并对 >90s 视频默认分段审查；
              (d) Voice 增加 segment 级内容哈希缓存（text+profile+segment_id → 音频），
                  script 小改时只重录受影响段落（这也正好是 D-002 提案里
                  「Script 修改后 Voice 重生成的最小边界」这一未答问题的工程答案）。
Severity:     BLOCKER（对 3–5 分钟目标）
Confidence:  HIGH（阈值与循环均為代码事实）/ MEDIUM（45MB 的确切断点取决于实际码率）
What would prove or disprove this:
              取 Track B 的 MP4，测其字节数并与 45MB 相比，按倍数推算穿着。
              同时用 120s 脚本跑一次 storyboard，统计子进程数与总耗时。
```

---

## FINDING-07 · 没有 Platform Profile，且画布被硬编码为横屏；字幕硬约束与竖屏平台反向

```text
Finding ID:   WB-FC-007
Type:         FACT + RISK
Problem:      (1) 全仓无任何 Platform Profile / 抖音 / 小红书 / 视频号 代码或配置。
              (2) 画布只有 1280×720 与 1920×1080 两个 16:9 选项，没有 9:16。
              (3) 字幕被 Mechanical QA 写成 BLOCKER：必须单行、无标点、无背景板、白色、精确 y=.91。
              (4) 小红书 Title / Cover 相关策略在当前架构里**没有目标产物**——
                  仓库内不存在 TITLE / COVER artifact 类型，`emotion_hook_preferred` 无处落地。
Evidence:     全仓 Grep（仅命中 PLATFORM-LOGO-SLOT 元素槽与 jianying 的 source_platform 字段）；
              production.py:142/158/159 与 contracts.py:213；production.py:381–389；contracts 目录清单。
Why it matters: 目标平台（抖音/小红书/视频号）以竖屏为主，底部 UI 区密集。
              当前组合 = 横屏画布 + 白底 + 白色无背景字幕 + 固定在 91% 高度，
              是竖屏平台上可读性最差的配置之一；而且 QA 把它锁成 BLOCKER，
              意味着「为了提升可读性而加字幕底衬」会直接 QA FAIL。
GPT/Claude current assumption:
              SKILL_ABSORPTION_MATRIX §9 已经规划 DOUYIN/XIAOHONGSHU/WECHAT_CHANNELS Profile，
              GPT D-003 §10 也在讨论 Platform Profile 会让 Prompt 变复杂。
              双方都在 Prompt 层讨论平台。
WorkBuddy challenge:
              平台差异在 Content OS 里**大部分不在 Prompt 层**，而在画布/安全区/字幕渲染/发布字段层。
              先把 Profile 做成 Prompt 注入层，会得到一个无法生效的层。
              另外「平台 Profile 会不会让 Prompt 太复杂」（挑战 Q10）目前是伪问题——
              真正的膨胀源是 FC-27 的规则无预算注入。
Alternative explanation or solution:
              按「能不能被渲染/校验」重新切分：
              · 进渲染配置（不是 Prompt）：aspect_ratio / safe_area_profile / subtitle_plate_policy；
              · 进 Episode Brief：目标平台、目标时长、语调、是否允许情绪钩子；
              · 进 Role Prompt：Hook 文案策略、信息密度偏好；
              · 新增产物类型 + 人工关卡：TITLE / COVER（否则小红书策略无处作用）；
              · 不进入任何 deterministic validator：所有 HEURISTIC（含首图 70%）。
Severity:     MAJOR
Confidence:  HIGH（代码事实）/ MEDIUM（「用户目标是竖屏」为推断，需用户确认）
What would prove or disprove this:
              向用户确认首选输出画幅。若为 9:16 → 本条升级为 BLOCKER。
```

---

## FINDING-08 · Storyboard Gate 结构上无法发现 PPT 感：唯一创作关卡是盲的

```text
Finding ID:   WB-FC-008
Type:         CURRENT_IMPLEMENTATION + RISK
Problem:      Storyboard Gate 审批的是「每 beat 2 张静态图」。
              由于渲染器没有连续运动（F-01），这两张图几乎等于该 beat 的全部信息。
              因此这个人类关卡**无法**观察到「节奏」「连续性」「是否在动」——
              而这正是用户反复 FAIL 的类别。
              项目里其实有一条 `storyboard_motion` 动效预览路径，但它不在 Gate 的必要条件里
              （require_storyboard 只校验 STORYBOARD_GATE）。
Evidence:     production.py:169–199（逐 beat 抽 2 帧）；production.py:224–231（require_storyboard 校验项）；
              adapter.py:76–92（storyboard_motion 存在但为非正式渲染）。
Why it matters: 这解释了一个反直觉现象：人已经过了 Storyboard Gate，正式渲染后仍然 FAIL。
              不是 Gate 的人不认真，是 Gate 的输入不包含被测现象。随之而来的是反复渲染费用。
GPT/Claude current assumption:
              双方都把 Storyboard Gate 当作既有的、有效的创作关卡，讨论集中在 Gate 「应该审什么」。
WorkBuddy challenge:
              先问 Gate 「能审到什么」。在输入信息不足时，改 Gate 的审批清单是形式主义。
Alternative explanation or solution:
              (a) 将 storyboard_motion 预览设为 Gate 的前置必做项（至少抽样若干连续 beat）；
              (b) Gate 输入增加「beat 序列一览（构图签名 / pattern / action / duration）」的
                  确定性摘要卡片，让重复与平均停留一眼可见（五行 XLSX 级信息量即可）；
              (c) 把 F-01 的运动词汇补上之后，动效预览才有内容可看——两条要一起做。
Severity:     MAJOR
Confidence:  HIGH
What would prove or disprove this:
              把 Track B 的 2 张/beat 静态板给用户，问是否能据此判断「这条有没有 PPT 感」。
              若不能，本条成立。
```

---

## FINDING-09 · Beat 有 6 个 write-only 字段：D-003 加语义字段前先看有没有人读

```text
Finding ID:   WB-FC-009
Type:         FACT + RISK
Problem:      Beat 的 purpose / visual_focus / visual_form / retention_function / density / tempo
              被 contract 要求、被模型产出、**但没有任何生产代码读取**。
              真正被消费的只有 pattern_id / slots / character_* / element_ids / motion_intent /
              reveal_order / timing_intent / script_segment_id / scene_id。
Evidence:     contracts.py:301–307 与全仓 Grep（唯一命中出现在 tests 与 mock 生成器里）。
Why it matters: (1) 纯 token 成本与 prompt 表面积；
              (2) 更重要的是：SKILL_ABSORPTION_MATRIX 提议新增 visual_job / viewer_should_notice /
                  evidence_carrier / cognitive_change / continuity_from_previous 五个字段，
                  若不先让 VisualResolver 消费它们，就是再加五个 write-only 字段。
GPT/Claude current assumption:
              D-003 §7 与矩阵 §7 都把「增加 Beat 语义字段」当作提升视觉质量的主要杠杆。
WorkBuddy challenge:
              字段只有在被映射成 layout/pixels 时才影响画面。当前映射函数是
              pattern_id → template → layout 的一一对应，没有任何语义字段参与。
              因此「加字段」与「提升画面多样性」在当前架构下没有因果通路。
Alternative explanation or solution:
              二选一，且必须显式选择：
              (A) 让 resolver 消费语义字段：例如 visual_form=EVIDENCE 时提升 media 权重、
                  visual_job=CONTRAST 时锁定 COMPARE_SPLIT + 双色 treatment —— 这是真杠杆；
              (B) 删除 write-only 字段，减少 prompt 表面积，明确「视觉决策只来自 pattern_id + slots」这一事实。
              建议先做一次「字段 → 消费点」盘点，再决定 D-003 加哪些字段。
Severity:     MAJOR（影响 D-003 投入产出比）
Confidence:  HIGH
What would prove or disprove this:
              在 VisualResolver 里对六个字段各加一个 print/断言，跑一次生产看是否命中。
```

---

## FINDING-10 · Prompt 膨胀的机制已可指认：规则层无预算注入 + 死配置

```text
Finding ID:   WB-F-010
Type:         FACT + RISK
Problem:      governance 把整个 CURRENT_RULES.md（含最多 4 个 rule set 的 indent=2 JSON 全文）
              拼进每个角色的 system prompt；没有任何字符预算、裁剪或摘要机制。
              另外 registries/skills/RESOLUTION_ORDER.json 从未被代码加载——
              层序在 knowledge.py:LAYERS 里重复实现，其 hard_rules_override 字段无对应实现。
Evidence:     runtime.py:158、governance.py:81–99、governance.py:133–135；
              knowledge.py:13（LAYERS）、全仓 Grep（RESOLUTION_ORDER 零引用）。
Why it matters: 这是 Claude Round 02 标为 UNKNOWN 的一项，本轮给出了具体机制与代码位置。
              同时它说明：真正的 Prompt 爆炸风险源不是 Platform Profile（挑战 Q10），
              而是规则层的无预算注入 + 一个已经漂移的死配置。
GPT/Claude current assumption:
              Claude §4：「必须补测 '实测一次真实调用的完整 system_prompt 字符数'」，结论 UNKNOWN。
WorkBuddy challenge:
              不需要等实测也能先做结构性防御——因为这个注入机制本身就是无上限的。
Alternative explanation or solution:
              (a) 给 active_rules 注入加预算上限，超出部分改为摘要 + 引用 ARTIFACT_ID；
              (b) rule set 用 compact JSON（无 indent）或仅注入与当前 role 相关的 subset；
              (c) 把 RESOLUTION_ORDER.json 接上（或删掉），并把 hard_rules_override 语义实现或移除——
                  目前「CREATIVE_POLICY 高于短期指标」是写出来的 HARD 规则，但没有执行机制。
Severity:     MINOR（当前体积小）→ NOTE（长期必爆）
Confidence:  HIGH（机制）/ MEDIUM（是否已到问题的量级）
What would prove or disprove this:
              导出一次 Track B 的真实 system prompt 字符数（这是 Claude 已经要求的 Slice 0 项，本轮支持）。
```

---

## FINDING-11 · 过程事实：D-002 目前只有 GPT 单方面意见

```text
Finding ID:   WB-F-011
Type:         FACT
Problem:      02_CLAUDE_REVIEW / 03_GPT_REBUTTAL / 04_CLAUDE_FINAL 均为 5 行占位，
              05_SYNTHESIS 正文全为 PENDING。按 COUNCIL_PROTOCOL，五步流程尚未跑完。
Evidence:     文件逐行实读。
Why it matters: 用户本轮的问题是「GPT 和 Claude 共同遗漏了什么」。
              对 D-002 而言，仓库里不存在 Claude 的分析，因此「共同遗漏」在 D-002 上
              只能退化为「GPT 单方面遗漏」。
GPT/Claude current assumption: 隐含双方都已分析 D-002。
WorkBuddy challenge: 该前提不成立。建议下一步优先级：先补齐 D-002 的 Claude Review 轮，
              再决定是否 Spike，而不是基于「双方共识」推进。
Alternative explanation or solution: 维持 D-002 Final Status = OPEN；在推进前补 Round 02–04。
Severity:     NOTE（过程项）
Confidence:  HIGH
What would prove or disprove this: 若 Claude 在其他窗口产出过 review 但未归档 → 应归档；否则本条成立。
```

---

## FINDING-12 · p0 分支已经包含 D-002 部分答案，而 main 的知识层不知道

```text
Finding ID:   WB-F-012
Type:         FACT + RISK
Problem:      p0 分支已实现：GENERATE_PRESERVING_AUDIO（纯视觉再生保留音频边）、
              Final EDT 显式绑定 voice + amap 依赖、human_edits_present() 重生成护栏、
              storyboard / voice / videoqa 后台 job 化、expected_revision 冲突校验。
              这些正好对应 GPT D-002 提案里的「Invalidation」第 3–4 条。
Evidence:     git diff main p0（production.py / api.py / workflow.py）。
Why it matters: Council 在 main 的知识状态上讨论，而答案的一部分已经在另一个分支上实现了。
              若不 diff，容易把已实现项当成待决项，或在 main 上重复实现。
GPT/Claude current assumption: 隐含「main 的知识 = 当前能力边界」。
WorkBuddy challenge: 至少一个方向（纯视觉再生不触发重录）已经在代码里跑通。
              剩下的是把它 reconcile 到 main 并写进决策，而不是重新讨论。
Alternative explanation or solution: 在讨论 D-002 Invalidation 时，以 `git diff main p0` 作为输入之一。
Severity:     NOTE
Confidence:  HIGH
What would prove or disprove this: 在 p0 上实跑「改一个 beat → 重新生成 EDT → 看 VOICE 是否复用」。
```

---

# Architecture Risks

| 风险 | 相关 Finding | 说明 |
| --- | --- | --- |
| 语义字段 → 像素没有通路 | F-09 + F-01 | 所有 Beat 语义最终被丢弃，`pattern_id → template → layout` 是一一对应 |
| contract 承诺渲染器不实现的能力 | F-04(S5) + F-07 | `transitions`、`SCREEN_DETAIL_ZOOM`、`CTA_END_CARD` 均属此类 |
| 三层缓存各自键不同 | 观察 | StageCache / Runtime job key / Gateway cache / VisualResolver hash / visual_revision，五个去重层无统一失效契约 |
| 规则真源分散 | FC-28 | `RESOLUTION_ORDER.json`（死） vs `knowledge.py:LAYERS`（活） vs `WRITING_DEFAULT.json` |
| 双分支鸿沟持续扩大 | F-12 | main 25 / p0 10，两条线各自推进会增加 reconcile 成本 |
| `Scene` 组件实为「卡片序列渲染器」 | F-01 | Remotion 只渲染 `Sequence` + 静态 `Img`/`div`，没有 scene graph 概念 |

---

# Prompt / Role Risks

- **并不存在角色层面的重复劳动（Role Overlap）**，但存在**字段重复**：`purpose` / `visual_focus` / `visual_form` / `keyword` / `retention_function` 五个字段语义高度重叠，样例 IR 里填的内容互相复述。（→ F-09）
- **真正的 Role Gap（没人负责）**：没有人负责「跨邻居 beat 的视觉多样性预算」。Audit 审事实，Visual QA 看不见 1fps，Mechanical QA 不检查 pose/pattern 连续重复，Director 没有 layout 权限。这个空缺正好落在用户最在意的维度上。（→ F-02 / F-05）
- **模型 vs 程序分工错位**（用户 F 类）：应当改为程序判断、当前却交给模型或根本无人负责的有：pose 多样性分配、相邻 beat 构图差异、第一屏视觉钩子是否存在、evidence 是否成为主体、面部/人物出场占比、白底面积比、停顿/静帧时长。以上全部可由 EDT/DirectorIR 直接算。（→ F-02 / F-05 / F-08）
- **`VOICE_AUTHORIZATION` 是事后记录**（FC-29），名字暗示一个前置关卡，实际在合成之后创建；这与 H 门/idempotency 的可审核性预期不符，建议改名或前置。
- **Audit FAIL 自动清除 H2**（FC-30）：机器可以撤销一个人类 gate 状态（即使通常此时 H2 尚未授予）。这是 user O 类「自动化侵蚀人工权限」的一处具体实例，建议改为显式记录 `H2_INVALIDATED_BY_AUDIT` 事件而非静默置空。

---

# Creative Pipeline Risks

用户 G 类「为什么 Engineering PASS 但 Creative FAIL」的最短回答：

> 因为 Engineering 检查的是**约束是否被满足**（schema、bbox、字体、时长、依赖），
> 而 Creative 检查的是**画面是否值得看**。当前系统里没有任何一处——无论人还是机器——
> 拥有观察「画面是否值得看」所需要的输入：Director 没有 layout 与运动词汇，
> Storyboard Gate 只有静态图，MiniMax 只有 1fps 且没有 rubric，Mechanical QA 不看多样性。
> 所以 Creative FAIL 不是某个环节失手，而是**这条链上没有任何环节具备该能力**。

已确认的已知根因（PPT 感、白底偏空、pose 重复、pattern 重复、evidence 不足、rhythm 不足）**并不构成全部**。经代码核对，至少还有三条未被任何一方列出的结构性原因：

1. **渲染词汇缺失**（F-01）——这是「PPT 感」的物理定义来源；
2. **reveal 语法被锁死**（观察）：`reveal_order` 被改写成必须以 `PRIMARY` 打头（`director_contract.py:25`），并且 `reveal.delay` 在 `visual.py:201` 被 clamp 到 `duration*0.4/0.65`，也就是说「信息如何逐步出现」这件事既被约束了起点也被约束了上限，Director 无法做真正的 reveal 编排；
3. **` treatment` 只存在于 dynamic 模式**（`visual.py:190–198`）：只有当 TypographyProfile 的 `presentation == 'XIAOY_EXPLAINER'` 时才有 MARKER/CHECKLIST/COMPARE/NUMBERED/UNDERLINE 装饰与强调色。若项目未采用该 presentation（样例中就未启用），那么输出就是纯黑字贴白底——这正是「白底偏空 / 稀疏」的直接技术原因，**而不是 Director 或 Prompt 的选择**。这一条值得单独 Spike：确认 Track B 是否运行在 `XIAOY_EXPLAINER` 下。

---

# Audio / Timing Risks

除 F-04 外：

| 风险 | 说明 |
| --- | --- |
| 字幕比例拆分的系统性漂移 | 段内按字符数分配时长；中文字符发音时长差异大，长句尾部字幕会明显抢拍/拖拍。这是抖音观众最敏感的维度之一（F-04 / FC-11） |
| 逐段 TTS concat 造成的韵律断层 | 每段单独合成再 concat，段边界无自然停顿/连贯语调；长视频段落越多，断层越多 |
| 无逐段缓存 | 任何 script 改动 → N 次完整重录，成本随段数线性增长（F-06） |
| `PROVIDER_TIMESTAMPS` 路径与 `MEASURED_SEGMENT_BOUNDARIES` 路径并存 | `AudioClock.create` 支持五种 method，而 GUI 只用其中一种；`from_voice()` 走 PROVIDER_TIMESTAMPS 且要求完整覆盖，这条路径缺少 GUI 实践证据（UNKNOWN） |
| VOICE 后置于 Storyboard Gate | 已确认属实（FC-22）。任何 Voice 前置方案必须同时修改 `require_storyboard` 语义，否则会出现「声音已录但分镜未批」的状态（这也是 D-002 需要的最小改动清单里的一项） |

---

# Platform Risks

见 F-07。补充对用户第 16 节三问的直接回答：

**小红书「首图 ≈ 70% 点开率」处理为 HEURISTIC 是否合理？**
合理，且 matrix 的处理方式（HEURISTIC_LABEL + 禁止进入 Fact System / QA 阈值）是本轮看到最规范的一处。唯一补充：**它目前没有承载对象**——Content OS 没有 TITLE / COVER 产物与审核步骤（F-07(4)）。因此这条策略要真正生效，需要新增产物类型与一道人工关卡，而不是只加一层 Prompt。

**`emotion_hook_preferred = true` 作为默认值是否合理？**
作为默认值合理（它保留了「严肃/证据型主题可不使用」的出口，也禁止为情绪造事实）。两点提醒：(a) 它必须与 fact-binding 硬约束同在实现，否则容易滑向标题党——而 matrix 已经写了这条禁律，属于已经自洽；(b) 同样缺少目标字段。

**抖音哪些是真规则、哪些是爆款套路？**

| 主张 | WorkBuddy 判断 | 理由 |
| --- | --- | --- |
| 文案 Hook × 视觉 Hook 需要联动 | **真高价值** | 它定义了 Content OS 目前缺失的一个 deterministic 校验点：第一视觉状态是否与第一句 Hook 指向同一冲突。可程序化为「前 2 秒 beat 的 pattern/evidence 是否被标记为 hook carrier」 |
| 第一视觉状态重要 | **真，且当前实现无对应概念** | 仓库内没有 first-frame / first-visual-state 的任何校验；这也解释了 why 视觉钩子问题反复出现 |
| 冲突/结果尽快出现 | **结构策略，非平台铁律** | 属于 Episode Brief 层的编排选择 |
| Evidence 尽快出现 | **真，且当前 evidence 优先权只在 dynamic（XIAOY_EXPLAINER）treatment 里隐含存在** | F-07 相关；建议做成 Bridge deterministic：前 15 秒内是否至少有一个 beat 含 media/evidence |
| 节奏更紧 | **不可执行** | 「紧」是相对量，且当前渲染器无连续运动，谈不上节奏（F-01） |
| 「黄金 3 秒」「固定字数/语速」「算法权重排序」 | **爆款套路 / HEURISTIC** | matrix 已正确降级，本轮同意 |

**视频号当前五条（信任/完整表达/真实声音/真实经历/关系链）是否够完整？**
方向正确，缺两条：(a) **「可被转述」**——视频号的传播单位是熟人对话，因此需要一个「一句话能被复述的判断句」，这属于 Script 层的 pay-off 校核，不是文案技巧；(b) **封面/标题在会话流中的可读性**——视频号在聊天会话里以小卡片呈现，构图需要在极小尺寸下仍可辨认，这同样是没有人负责的校验点。

---

# Cost / Efficiency Risks

| 环节 | 成本问题 | Finding |
| --- | --- | --- |
| Director | 产出 6 个 write-only 字段；system prompt 里 schema 被发两遍（Claude 已指出，本轮确认） | F-09 / FC-27 |
| Voice | N 段 N 次调用；无逐段缓存；script 小改 → 全部重录 | F-06 |
| Storyboard | 每 beat 2 次 `npx remotion still` 冷启动；O(beats) | F-06 |
| Render | 固定 300s timeout；失败即整段重渲染 | F-06 |
| Visual QA | 整段视频 base64 重复上传；单条时间戳越界即整次失败；0 finding 静默判 PASS | F-05 / F-06 |
| QA 重复 | 同一问题被 Mechanical / Visual / 人三层以不同口径检查，且缺失的维度（多样性 / 画面能量状态）三层都不检查 | F-05 / F-08 |
| Storyboard 白做 | Gate 无法发现 PPT 感 → 渲染后 FAIL → storyboard+render 全部作废 | F-08 |

---

# Long-video Risks

用户 L 类七项，逐项给结论（「会被放大」都不是重点，重点是**跨界**）：

| 项 | 判断 | 依据 |
| --- | --- | --- |
| Pattern exhaustion | **必然**，可达模板只有 6 个（F-07） | 30–60 beat 时，pattern 必然循环 4–8 轮 |
| XIAO-Y repetition | **确定性必然**，同一 intent 永远同一 pose（F-02） | 比-pattern exhaustion 更硬，因为是「同一」而非「重复出现」 |
| Prompt drift | 中等风险；`CURRENT_RULES` 无预算注入会加剧（F-10） | 长项目规则会累积 |
| QA overload | **会失败而非变慢**：45MB 上限直接抛错（F-06） | — |
| audio alignment | **漂移随段长线性增长**：比例拆分误差随句子长度放大（F-04） | 每 beat >5s 时明显 |
| render time | **硬阻塞**：timeout=300 固定（F-06） | — |
| state recovery | p0 已有单点 recovery（orphan→SERVER_RESTARTED、retry、refresh），本轮未发现新问题；但 `StageCache.states()` 的 14 个 stage 中任一 RUNNING 卡住会标 BLOCKED 要求人工重跑，**长视频 IqinbingSelect 会让部分完成的重跑成本很高** | 观察 |
| human edit complexity | **显著放大**：per-beat SET_BEAT 手工修正量随 beat 数线性增长；`visual.py` 的 p0 版已加计数 clamp 防溢出（progress steps 超出框体），说明已出现过同类问题 | p0 diff |

---

# Track B Creative Failure Mapping

> 格式：`Track B 问题 → 根因 → Owner → Skill 原则 → 实现方式`。刻意区分「Prompt 能解决」与「必须改代码」两列，因为这是本轮的核心分歧点。

| Track B 问题 | 真实根因（本轮核对后） | Owner | Skill 原则来源 | 实现方式（关键：Prompt 是否够） |
| --- | --- | --- | --- | --- |
| PPT 感 | 渲染器无连续运动；beat 内 8 帧后静止；入场动画只有 3 种且均是 8 帧一次性 | Renderer（现无人显式拥有） | cinematic-director「Slideshow Repair：不要靠 zoom/fade 假装动态」 | **必须改代码**：加 Ken Burns + beat 间转场；再让 Director 指定 motion vocabulary。Prompt 单独无效 |
| 白底过空 | ① 未启用 `XIAOY_EXPLAINER` presentation 时无任何 treatment/强调色；② 布局是 12 组静态坐标，无图层/纹理/衬底概念；③ 无 ratio 校验 | VisualResolver / Typography Profile 配置 | video-talkcraft「主体让位」、xiaohongshu Title/Cover 视觉预算 | **两者都需**：先程序化加 treatment + 底衬 + 背景层；再让 Director 在 Rubric 里选层级 |
| XIAO-Y pose 重复 | `next(first match)` 确定性选择 + Director 默认只给 intent + QA 无检查 | VisualResolver（当前无人拥有多样性） | video-maker「cognitive change」 | **主要改代码**：deterministic allocator + QA ACTION_REPETITION；Director Prompt 作为次要约束（要求显式 action_id） |
| Pattern 重复 | 8 patterns → 6 templates 1:1 映射；无 SIMULTANEOUS 上下文记忆 | Director + VisualResolver | Seedance Skill「Final Assembly QA 检查跨 Beat 重复」 | **改代码为主**：跨 beat 构图签名差异的 deterministic 校验 + pattern 预算；Prompt 辅助 |
| Evidence 不足 | ① evidence 需要 media_asset_id，而 Director 只有在确有可用 media 时才能用它；② 模板 `allowed_character_presence=['NONE']` 与 `LAYOUTS` 使 evidence 主角化受限；③ 无「前 N 秒必须有 evidence」校验 | Writer/Research（供给）+ Director（使用） | video-maker Evidence Map / Overclaim Boundary | **两者都需**：先保证 Episode Brief 有 evidence carrier；再加 deterministic：前 15 秒内是否存在含 media 的 beat |
| visual rhythm 不足 | 无转场、无 exit 动画、reveal delay 被 clamp 到 0.4×duration；所有人/机器都看不见运动 | Renderer + Storyboard Gate | cinematic-director Continuity、Seedance Final Assembly QA | **必须改代码 + 改 Gate 输入**：运动词汇 + 动效预览进 Gate 前置 + beat 序列摘要卡片 |
| audio/visual timing 偏差 | 段外边界正确，段内按比例猜测（beat 切点）+ 字幕按字数比例拆分 | AudioClock + Writer（颗粒度） | video-talkcraft「语义拍 / 时间真源」 | **改代码为主，无需重排管线**：吸附到已有 word_ranges / phrase_id；或收紧 Writer 切分粒度（S1/S2/S4） |
| Evidence OCR/截图可读性（观察到但未列入用户清单） | 无截图可读性 deterministic 检查；依赖 MiniMax 在 1fps 上判断 | Deterministic QA + Visual QA | Seedance Post-render checklist | **改代码**：程序化检查截图区域占比、最小字号、对比度 |

---

# Skill Absorption Corrections

对 `SKILL_ABSORPTION_MATRIX.md` 的分类修正。**核心原则：凡是描述「画面怎么变」的原则，都不能只进 Role Prompt。**

| Skill / 原则 | Matrix 当前归类 | WorkBuddy 修正 | 理由 |
| --- | --- | --- | --- |
| researcher_agent · Source Qualification | Research Role | **Deterministic Validator + Source Schema** | `source_type/credibility/freshness/conflict_group` 是字段，不是 Prompt 文本 |
| fact-check · All-Claim Coverage | Red Team Role | **Deterministic（已部分实现）+ Role Rubric** | `CLAIM_REVIEW_INCOMPLETE` 已在代码中强制 |
| fact-check · 六种 fabrication 类型 | Red Team Must | **Prompt Qualification Suite 用例**（不是每次调用都发） | 六个类型作为测试用例比作为 system prompt 更有效 |
| video-maker · Content Contract | Writer 上游输入 | **同意，落到 Episode Brief** | 且需新增 Brief artifact，否则无处存放 |
| video-maker · Evidence Map / Overclaim Boundary | Writer | **Episode Brief + Fact Pack 字段** | 「这份证据最多允许说到哪里」是个可判定的上限字段，应 programmaticalize |
| video-maker · Cognitive Change | Director Beat 字段 | **先决定 resolver 是否消费**（F-09） | 否则是第 7 个 write-only 字段 |
| youtube-script-writer · Promise/Beat/Payoff | Writer 自检 | **同意 Role Prompt + Qualification** | 保持 Heuristic，不进 Hard Gate（matrix 已正确处理） |
| youtube-script-writer · read-aloud pass | Writer 自检 | **Qualification Suite（人工/朗读），不是 rubric 分数** | 口播自然度主观且依赖受众；且 fuller Retention 自评无预测效力（Claude 已指出，本轮同意） |
| huashu-douyin · 文案 Hook × 视觉 Hook | Writer + Director | **拆三处**：文案 Hook→Writer Rubric；视觉 Hook→Director Role Prompt；Hook 一致性→**deterministic 首屏校验** | 只有第三项是新的且当前完全缺失 |
| huashu-douyin · Observed Pattern 库 | Heuristic | **同意，但需要「不能被 Hard Gate 引用」的存储层** | matrix 已警惕，建议落成 `observed_pattern` artifact 而非 Skill Snapshot 的一部分 |
| rainwell · 不虚构后台数据 | Analytics | **Role Prompt Hard Fail + deterministic 禁词** | 「不得写出完播率/CTR 数值」可以作为 Writer/Audit 的 deterministic 数字来源检查的一部分 |
| xiaohongshu-ops · 账号战略层 | 未来 Strategy | **同意延后**；但注意 Strategy→Episode Brief 边界未定义，别过早开放 | — |
| xiaohongshu-writer · Title/Cover 联动 | Platform Profile | **需要新增 TITLE/COVER 产物 + 人工关卡**（F-07(4)） | Prompt 层无法承载，因为它没有输出目标 |
| xiaohongshu-writer · 首图 70% | HEURISTIC | **同意，且建议加一条**：永不复制到 Renderer/QA 的任何数值阈值 | matrix 已写明，本轮只是强调「hav auto-execute 通道不存在时更安全」 |
| xiaohongshu-writer · emotion_hook_preferred | DEFAULT_PLATFORM_TACTIC | **同意**，但绑定到「必须存在且有 fact 支撑」；并依赖 TITLE 产物落地 | — |
| humanize · Minimum Effective Edit | Script Editor Role | **同意 Role Prompt** | 已有 `SEMANTIC_CHANGE_REQUIRED` 通路且代码已支持（Claude 已确认） |
| de-ai-flavor · 中文 AI 腔 | Script Editor | **Deterministic lint（命中不 FAIL）+ Role Prompt** | 词表（首先/其次/值得注意的是）完全是机器可判的 |
| cavekit · Refutation | Red Team Role | **同意 Role Prompt + Qualification** | — |
| adaptico · Falsifiability / Attack Your Own PASS | Red Team Role | **同意；但建议「Would change my mind」做成 Audit 输出的必填字段 + deterministic 存在性校验** | 比放 system prompt 更可执行 |
| cinematic-director · Beat Visual Function | Director Beat 字段 | **Role Prompt + resolver 消费（缺一不可）** | 见 F-09 |
| cinematic-director · Continuity | Director Beat 字段 | **Deterministic**（相邻 beat 构图签名/主体变化的差分检查） | 「上一 beat 的结束状态帮助下一 beat 展开」是可计算的 |
| cinematic-director · Slideshow Repair | Director Must Not | **Renderer 能力**（最重要的一条） | 「不要靠 zoom/fade 假装动态」当前状态是：连 zoom/fade 都没有，只有 8 帧 fade |
| video-talkcraft · Voice-first / 语义拍 | D-002 方向 | **同意方向；但「语义拍」可以在**不移动 Voice** 的前提下通过 word/phrase anchor 实现**（F-04 S1/S4） | 这是本轮对 D-002 最实质的修正 |
| video-talkcraft · 主体让位（Evidence 主角） | Director | **Renderer + Resolver**（模板 presence 与 layout 需支持「证据全幅」） | Director 说「这个 beat 证据是主角」，但模板把它放成右栏配图 |
| Seedance · Beat QA / Final Assembly 分离 | Visual QA | **强烈同意，并建议：Beat QA 做 deterministic 预筛，Final Assembly QA 才交给模型** | 直接降低 MiniMax 的输入负担与幻觉窗口 |
| Seedance · Fresh Reviewer | Visual QA | **同意，且建议与 MiniMax 单点依赖问题合并处理** | Claude 已指出单点风险 |

**明确应拒绝（补充 matrix 第十一节）：**
- 任何要求 Director 输出「更细的画面 / 版式控制」的外部模板（违反 DEC 与 `no_pixels()`）；
- 任何把 Platform 经验数字（70%、3 秒、完播率排序）写进 deterministic validator 的提议；
- 任何在系统性问题上仅仅通过「再加一层 prompt」来解决的方案——本轮已经看到这条路径的成本（F-09）。

---

# Highest-Leverage Issues

最多五项，按投入产出比排序：

1. **给渲染器加连续运动**（F-01）：最小可行版本是「每个 media/character clip 加缓慢 Ken Burns + beat 间 8–12 帧交叉转场」。这是所有 Creative 失败项的物理前提，其余投资在它之前都会打折。**判断标准：同一份 IR，只改渲染，用户盲评。**
2. **把 pose 选择从「模型责任」移回「程序责任」**（F-02）：写一个 deterministic allocator + 一个 ACTION_REPETITION 的 Mechanical QA 规则。改动集中在 `visual.py:92–96` 与 `production.py:442–448`，风险低、见效直接，且能让已经准备好的新 HD 动作包真正生效。
3. **先把 word_ranges / phrase_id 用起来，再决定是否 Audio-first**（F-04）：TTS 已返回并已存储词级时间戳，合约里已有 `phrase_id` 字段却无人使用。这是本轮看到的「被浪费的最高价值资产」。同时建议在 D-002 Spike 中加入第三臂，避免在尚未验证的前提下先把整条管线重排一遍。
4. **修 Long-video 三处硬阈值**（F-06）：timeout 按时间计算、storyboard 批量取帧、QA 输入降采样/分段。不修则 Track C 无法开始。
5. **给 human gate 装上能看到问题的眼睛**（F-08 + F-05）：动效预览前置 + beat 序列摘要卡片 + 把有用的 on-screen-everything-dimensions 转 deterministic。这决定了返工成本是发生在 Storyboard Gate 之前，还是要等到渲染与 QA 之后才暴露。

**明确建议暂缓**：在 1–2 完成前，不要把 D-003 的重点放在「加厚 Director Prompt / 新增 Beat 语义字段」上（F-09）。

---

# Things GPT / Claude Probably Got Right

本轮独立核对后**确认**的既有结论（不重复论证，只标注已核实）：

1. **Director 收到的指令里完全没有 PPT/XIAO-Y/一致性取向**（Claude §1）：已核实，`director_contract.py:28` 的 instructions 全文只谈 ID/schema/timing 估算。
2. **同一角色存在多条互相不知道的 prompt 路径**（Claude §1）：已核实，`RESEARCH_V1` / `VIDEO_QA_V1` / `MEDIA_RESOLVER_V1` 在 GUI 实际路径上均不生效。
3. **schema 被发送两遍**（Claude §4）：已核实，`runtime.py:158` 的 `str(schema)` 与 `gateway.py:94` 的 `json.dumps(schema)`。
4. **`thinking:disabled` 被按 provider 名硬编码**（Claude §2）：已核实，`gateway.py:88–92`；这确实是 Q-004 迁移的技术前提。
5. **MiniMax-M3 是多模态单点依赖**（Claude §2）：已核实，`gateway.py:72–73` 是唯一允许 `content_blocks` 的分支。
6. **数字溯源应转 deterministic**（Claude §7）：Strongly agree；并且同一套「程序预筛 + 模型复核」思路应扩展到「数字 vs 批准 segment」之外的「evidence vs approved media」。
7. **Blind audit 与 `CLAIM_REVIEW_*` 强制已实现**（Claude §6）：已核实，属于本项目里做得最对的部分之一。
8. **Qualification Suite 不应由另一个模型判定是否通过**（Claude §11）：同意，并且这条原则应同样适用于 Track B 的创作质量验收——不应把 Vidéo QA 的结论当成验收本身。
9. **`PASS_WITH_RISK` 需要收紧**（Claude §6）：同意，但补充——当前更大的问题是 MiniMax 在 0 finding 时静默判 PASS（F-05）；仅收紧措辞解决不了这一条。

---

# Things WorkBuddy Disagrees With

| # | 对方观点 | WorkBuddy 立场 | 依据 |
| --- | --- | --- | --- |
| 1 | GPT D-003：Creative FAIL 主要是 Prompt/Role 质量问题 | 主要是渲染表达 ceiling；Prompt 是必要不充分条件 | F-01 / F-09 |
| 2 | GPT D-002：需要 Narration Units 作为独立 Artifact | 粒度单位已存在（segment ↔ audio entry ↔ beat 1:1）；需要的是粒度策略与 anchor，不是新产物 | F-04 / FC-10 证据 |
| 3 | GPT D-002：Director 在真实音频之前先猜 timing | 已部分不成立：外边界已音频驱动；残留误差仅在段内比例 | FC-12 + FC-11 证据 |
| 4 | Claude：MiniMax 时间戳幻觉的核心缓解手段是「引用 clip_id」 | 方向对但不够：1fps 输入 + 零 rubric + 已发生的 beat 归属错误三者中，输入是根 | F-05 / FC-19 |
| 5 | Claude：12 个 section 的 Role Pack 只需分层即可控制膨胀 | 真正的膨胀源在规则无预算注入（FC-27）与 write-only 字段（FC-26），分层不解决这两个 | F-09 / F-10 |
| 6 | Claude：`NUMBER_NOT_IN_APPROVED_SOURCE` 建议升级为 deterministic | 同意，但要注意 `production.py:71` 的 `numbers()` 已经 deterministic 且 **Director 段已经在跑**——该检查对 Director 已在位，真正缺失的是 **Script Editor 的非 claim 文本**（Claude 已指出，本轮只是确认其存在以免重复实现） | production.py:71 |
| 7 | 双方：把新增 Beat 语义字段作为主要杠杆 | 在没有消费点前，那是第 7–11 个 write-only 字段 | F-09 |
| 8 | Matrix：Platform Profile 作为注入 Writer/Director 的一层 | 平台差异主要不在 Prompt 层，且在多数 promises **no target artifact** | F-07 |

---

# UNKNOWN / Needs Evidence

1. Track B 真实 `VOICE` payload 的 `word_timestamps` 是否非空 → 决定 F-04 的 S1 是否立即可行。
2. Track B 最终 MP4 字节数 / 码率 → 决定 45MB 失效的确切时长阈值。
3. Track B 是否运行在 `presentation == 'XIAOY_EXPLAINER'`（dynamic）模式 → 决定「白底偏空」是否主要由 mode 未启用导致（本轮推测但未证实；若证实，这是一个配置级而非架构级修复）。
4. 一次真实 system prompt 的完整字符数（Claude 已要求；本轮支持，作为 Slice 0 项）。
5. Track B 真实 artifact 树中 SCRIPT 的 segment 数量与 beat 数量之比 → 验证 F-04 的 1:1 结构假设（样例 IR 是 6:6，但 Track B 是 9 段 18 beat，**并非 1:1，而是 1:2**——这一点需要在真实项目上复核，因为它会改变 S2 的表述：粒度应当「每段不多于 1 个语义单位」，而不是「每段一个 beat」）。

> 更正：`AUDIO_TIMING_REVIEW.md` 显示 Track B 历史样片是 **9 段 / 18 beat（1:2）**，而 `examples/phase2/DIRECTOR_IR.json` 是 6 段 / 6 beat（1:1）。两者都真实，说明颗粒度**没有被任何规则约束**，进一步支持 F-04 的 S2：需要的是显式的粒度策略，而不是新 Artifact。

6. Claude 是否在其它窗口产出过 D-002 的 Review 但未归档（Q-008 同款问题）。
7. 用户首选输出画幅意向（横屏 / 竖屏 / 两者）。

---

# Human Decisions Required

1. **是否认可「Creative FAIL 的根因在渲染器而非 Prompt」这一判断的优先级？** 若是，建议把 F-01 的最小 Spike 排在 D-003 实施之前。（最高优先）
2. **是否批准在 D-002 的 Spike 中加入「不重排管线 + word/phrase anchor」这一第三臂？** 这决定是否值得承担整条管线重排的迁移成本。（次高）
3. **目标画幅**：是否必须为抖音/小红书/视频号提供 9:16？若是，F-07 升级为 BLOCKER，且需要先于 Platform Profile 讨论。
4. **是否新增 TITLE / COVER 产物与审核关卡？** 这是小红书策略能否落地的前置，当前无任何承载物。
5. **是否允许 Mechanical QA 放宽字幕硬约束**（允许背景衬板、允许白色以外的颜色、允许非 0.91 基线），以便适配竖屏平台底部 UI？当前这些是 BLOCKER。
6. **是否把 pose 多样性明确划归 VisualResolver（程序）而非 Director（模型）？** 这会改变一条权责边界：Director 不再决定「用第几个动作」，而是决定「需要哪种情绪/语义」，由程序在保证多样性约束下分配具体动作。
7. **是否要求动效预览作为 Storyboard Gate 的前置条件？**（F-08）
8. **本轮 Review 应停在 main 还是需要独立分支？** 本轮按用户默认流程 push 到 `main`；若希望第三席 review 一律走独立分支，请告知，下轮改走 `council/workbuddy-review-00X`。

---

*本轮未修改业务代码、Prompt、模型岗位、Audio-first、DECISIONS.md、D-002/D-003 Final Status；未 merge、未发布、未做 H4、未创建 PR。*
