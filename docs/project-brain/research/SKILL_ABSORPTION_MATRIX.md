# Content OS · Skill Absorption Matrix v0.1

**日期：** 2026-09-29  
**状态：** RESEARCH / PROPOSAL  
**用途：** 汇总当前已调研的中英文公开 Skill，明确哪些原则可吸收进 Content OS，哪些只能改写后吸收，哪些明确拒绝。  
**注意：** 本文件不是 `DECISIONS.md`，不得把这里的建议自动视为正式产品决策或 Prompt 已上线。

---

## 一、总原则

Content OS 不安装、不整体复制这些外部 Skill。只吸收经过项目约束筛选后的：

- 角色职责；
- Prompt 结构；
- Quality Rubric；
- Hard Fail / Return-to-owner 规则；
- 平台表达策略；
- QA 方法；
- 可确定性验证的规则设计。

外部 Skill 中的固定时长、固定算法权重、万能爆款数字、平台“铁律”、特定技术栈和供应商 API，不自动进入 Content OS。

所有外部经验分为四级：

1. **DIRECT_ABSORB**：原则可直接转成 Content OS 规则。
2. **ADAPT_ABSORB**：方向有价值，但必须按 Content OS 架构重写。
3. **HEURISTIC**：作为经验策略/候选，不得描述成已证实事实。
4. **REJECT**：明确不采用。

---

# 二、Research / Fact System

## 1. `drader/researcher_agent` · Source Verifier

**吸收等级：DIRECT_ABSORB + ADAPT_ABSORB**

### 借什么

- “来源资格”与“事实真假”分开判断。
- 先验证来源真实存在，再允许进入 Evidence Pool。
- Primary / Secondary / Commentary 分层。
- 检查 freshness、作者/机构、原始出处、利益关系、来源冲突。
- 找不到可靠原始来源时明确 `UNKNOWN` / `REJECT`，不能补写。

### 改造成 Content OS

建议 Source 至少记录：

- `source_type`: PRIMARY / SECONDARY / COMMENTARY / UNKNOWN
- `credibility`: HIGH / MEDIUM / LOW / REJECT
- `published_at`
- `retrieved_at`
- `freshness_status`
- `conflict_group_id`
- `source_owner`

Research 不因为来源“权威”就自动证明其中所有 Claim；Source Qualification 只回答“它是否有资格作为证据”。

### 不借什么

**REJECT / CONDITIONAL ONLY**：

- 默认 PRISMA 流程；
- 期刊等级；
- 引用次数；
- 同行评审；
- 学术撤稿数据库检查。

仅在科学/医学/正式学术内容中按需启用。

---

## 2. `jwynia/agent-skills` · fact-check

**吸收等级：DIRECT_ABSORB**

### 借什么

- 生成和验证必须分开。
- Writer 完成 Candidate 后，由 Fresh Audit Context 独立核验。
- 必须覆盖全部可验证 Claim，不能只抽查几个“重要 Claim”。
- Claim 类型区分：Hard Fact / Soft Fact / Attribution / Inference / Opinion-as-Fact。
- Verification status：Confirmed / Partially Supported / Not Found / Contradicted / Outdated。
- 特别检查：
  - Plausible Fabrication
  - Confident Extrapolation
  - Temporal Confusion
  - Attribution Drift
  - Amalgamation
  - Precision Inflation

### 改造成 Content OS

与现有 `claim_units` 对接：每一个 factual claim 必须有 Audit 状态，遗漏触发 `CLAIM_REVIEW_INCOMPLETE`。

最终仍使用 Content OS 自己的：

- PASS
- PASS_WITH_RISK
- FAIL

不并行建立第二套最终 Gate。

---

# 三、Writer / Script

## 3. `BraveCowNoFear/video-maker`

**吸收等级：DIRECT_ABSORB + ADAPT_ABSORB**

### 借什么

#### Content Contract

正式写稿前明确：

- root question
- audience
- current confusion
- core judgment
- answer shape
- evidence carrier
- overclaim boundary
- transfer rule

#### Evidence Map

核心 Claim 不仅记录“有什么证据”，还记录：

> 这份证据最多允许我们说到哪里。

避免来源只支持“可能相关”，Writer 却升级成“已经证明”。

#### Visual Responsibility

视觉不是装饰。每一段重要信息都应该明确：

- Evidence Carrier
- Viewer Should Notice
- Cognitive Change

### 改造成 Content OS

增加 `EPISODE_BRIEF / CONTENT_CONTRACT`，作为 Writer 的上游输入，不直接写进 Base Prompt。

### 不借什么

- 禁止 Remotion：**REJECT**。Content OS 继续遵守 DEC-001，Remotion 是执行/渲染引擎。
- 它自己的 Bilibili / Manim / FFmpeg 特定生产栈：不吸收。

---

## 4. `SkillMedev/skills` · youtube-script-writer

**吸收等级：ADAPT_ABSORB + HEURISTIC**

### 借什么

- Hook → Body Beat → Payoff。
- 每个 Beat 必须产生新信息或推动问题。
- 开头必须兑现用户点击前的 Promise。
- `read-aloud pass`：最终稿必须适合真实口播，不只是“看起来顺”。
- 长内容需要注意力重置，但不机械按秒数执行。

### 改造成 Content OS

建议 Writer 自检增加：

- `viewer_promise`
- `beat_question`
- `new_information`
- `transition_reason`
- `payoff_matches_promise`
- `read_aloud_risk`

### 不借什么

以下全部只允许作为 `HEURISTIC`：

- 固定 30 秒 Hook；
- 150 WPM；
- 每 90–120 秒 Pattern Interrupt；
- 固定 3–5 Beats。

不能成为 Hard Gate。

---

# 四、中文平台 Writer / Platform Profile

## 5. `yanhua1010/self-media-content-workflow`

**适用：抖音 / 小红书视频 / 视频号**  
**吸收等级：DIRECT_ABSORB + ADAPT_ABSORB**

### 借什么

#### 平台原生化

同一母题多平台适配时，共享：

- Fact
- Claim
- Evidence
- Boundary

但必须重写：

- 标题
- 第一屏 / 第一段
- Evidence 顺序
- 信息密度
- 视觉结构
- CTA
- 发布字段

如果多平台稿件只有长短差异，视为适配失败。

#### 视频共同规则

- 一条视频一个核心判断；
- 前段快速给冲突 / 结果 / 利益 / 具体场景；
- 口播必须说得出口；
- 画面承担证明、演示、对比、情绪任务，不能重复字幕；
- 优先真实证据和真实录屏。

#### 平台 Profile 候选

**抖音：**
- 停留优先；
- 前段冲突/结果更快；
- 视觉 Hook 强；
- 广泛可懂；
- 节奏更紧。

**小红书视频：**
- 搜索标题；
- 身份/场景；
- 过程证据；
- 可收藏信息；
- Title / Cover 联动。

**视频号：**
- 真实声音；
- 微信关系链传播；
- 完整可信表达；
- 更适合“转给熟人”的内容逻辑。

### 不借什么

“前 3 秒”等不能进入 Core Writer Hard Rule，只进入短视频 Platform Profile。

---

## 6. `huashu-douyin-script`

**适用：抖音**  
**吸收等级：ADAPT_ABSORB + HEURISTIC**

### 借什么

#### 文案 Hook × 视觉 Hook

Hook 不只是 Writer 说什么，还要检查：

- semantic_hook
- visual_hook
- evidence_hook
- audio_hook
- hook_alignment

前段视觉需要分析：

- 第一帧
- 构图
- 主体
- 动作
- 特效
- 信息密度
- 文案和画面是否共同强化同一个认知冲突

#### 竞品拆解 → Observed Pattern

流程：

`竞品视频 → 结构拆解 → 共性 → 用户确认 → Pattern Library`

Content OS 不称其为“爆款公式”，而记录为：

- Observed Hook Pattern
- Observed Visual Pattern
- Observed Pacing Pattern
- Observed Evidence Pattern

这些只能影响创作建议，不能升级为 Hard Rule。

#### AI 味审校

短句、口语、朗读检查、避免机械连接词等可并入 Script Editor。

### 不借什么

以下属于带货/千川场景，默认不进入 Content OS Core：

- 15 秒 / 30 秒固定脚本；
- 强硬 CTA；
- 价格锚定；
- 千川投放套路；
- “短句必须 ≤15 字”等绝对规则。

---

## 7. `rainwell-douyin-viral-analyzer`

**适用：抖音竞品 / 爆款分析**  
**吸收等级：DIRECT_ABSORB + HEURISTIC**

### 借什么

- 公开数据拿不到就不编。
- 不虚构完播率、每秒留存、CTR 等后台数据。
- 明确区分：观察事实 vs 模型推断。
- 用评论区反向验证“真正被用户感知的爆点”。
- 作者认为精彩 ≠ 用户真正觉得精彩。

### 改造成 Content OS

未来 Analytics / Pattern Mining 可以记录：

- observed_pattern
- audience_comment_evidence
- hypothesis
- confidence

不能从“爆款视频采用某结构”直接写成“该结构导致爆款”。

---

## 8. `xiaohongshu-ops`

**适用：小红书运营策略**  
**吸收等级：ADAPT_ABSORB + HEURISTIC**

### 借什么

- “账号战略层”与“单篇内容生产层”分离。
- Strategy 负责：定位、选题、内容矩阵、复盘、账号目标。
- 单篇生产交给 Episode Brief → Content OS。
- 小红书重点考虑搜索意图与长期长尾价值。
- 内容类型矩阵避免账号只有一种内容。

### 改造成 Content OS

未来增加 Strategy → Episode Brief 边界，但不并入当前 Writer 主 Prompt。

### 不借什么

曝光池、点击率、收藏权重等具体阈值暂归 `HEURISTIC`，不可直接写成平台算法事实。

---

## 9. `xiaohongshu-writer`

**适用：小红书标题 / 首图 / 开头 / 正文结构**  
**吸收等级：ADAPT_ABSORB + HEURISTIC**

### 借什么

#### Title + Cover 联动

小红书必须把“标题承诺”和“首图承诺”当作同一个点击合同设计。

建议 Platform Profile 增加：

- `title_promise`
- `cover_promise`
- `title_cover_alignment`
- `search_intent`
- `identity_context`
- `save_value`

#### 首图优先级

**用户确认需要保留的国内运营经验：**

> “首图决定约 70% 点开率”作为中文自媒体圈常用经验表述纳入策略层。

Content OS 中的正式表达应是：

- **HEURISTIC：首图是小红书点击决策中最高优先级资产之一，应投入高于普通内页的设计与审核预算。**
- “70%”只作为经验性标签 / 来源备注保留，**不得被描述成已被平台官方验证的固定比例**。
- Prompt 可以要求：在小红书 Profile 下，Title / Cover 未通过时，不应把主要精力先花在正文精修。

#### 情绪词策略

**用户确认需要加入：**

> 标题默认优先考虑一个与内容真实情绪相符的情绪钩子词，这是当前国内自媒体常见点击策略。

Content OS 中建议写成：

- `emotion_hook_preferred = true`
- 情绪词必须与真实内容一致；
- 不允许为了“钩人”制造不存在的震惊、焦虑、收益或冲突；
- 如果主题本身是严肃、技术、证据型内容，可以不用情绪词；
- 情绪词是默认策略，不是每条标题的强制语法。

可使用的策略维度包括：

- 惊讶 / 反差
- 避坑 / 风险
- 真香 / 后悔
- 身份共鸣
- 紧迫 / 建议
- 好奇 / 偷窥感

禁止：

- 虚假夸张；
- 与正文不兑现的标题党；
- 无 Fact 支持的具体收益；
- 把观点写成事实。

#### 内容类型差异

- 种草测评
- 教程攻略
- 故事分享
- 盘点榜单

不同类型使用不同结构，不要所有内容都用同一模板。

### 不借什么 / 降级为 Heuristic

- “所有标题必须有数字”：只做候选策略；
- “所有标题必须有 emoji”：不采用；
- “标题必须某固定字数”：需要实时平台验证，不能成为永久规则；
- “首图 70%”不能进入事实系统或 QA 确定性校验。

---

## 10. `wechat-video-trending-content-script`

**适用：视频号**  
**吸收等级：LIMITED ADAPT_ABSORB**

### 借什么

- 视频号应有独立 Platform Profile；
- 关系链传播意识；
- 搜索词意识；
- 口播 + Storyboard + 发布字段联动。

### 更推荐采用的 Content OS 视频号原则

- 信任 > 夸张；
- 完整表达 > 极端压缩；
- 真实声音 / 真实经历 / 真实证据；
- 内容应具备“适合转给朋友、同事、家人”的传播语境；
- 不照搬抖音式高刺激话术。

### 不借什么

- 固定“完播率 > 点赞率 > 评论率”算法排序；
- 固定黄金发布时间；
- 固定 30–60 秒。

除非有当前官方/真实数据证据，否则只作为参考。

---

# 五、Script Editor / 中文去 AI 味

## 11. `ryanmaule/humanize`

**吸收等级：DIRECT_ABSORB**

### 借什么

- `minimum effective edit`：能改 10% 解决问题，不重写 80%。
- Detect 与 Edit 分离。
- 保留原作者 voice。
- 不新增事实、数字、观点或例子。
- 如果需要改变语义，返回 `SEMANTIC_CHANGE_REQUIRED`。

### 不借什么

英文固定禁词表不直接迁移到中文。

---

## 12. `de-ai-flavor`

**适用：中文 Script Editor**  
**吸收等级：DIRECT_ABSORB + HEURISTIC**

### 借什么

检测中文 AI 腔：

- 框架词过密；
- “首先/其次/最后/综上所述”；
- AI 高频空话；
- 排比/对仗机械；
- 句长同构；
- 情绪/个人质感缺失；
- 具体细节缺失；
- 书面腔；
- 冗余总结。

流程必须是：

`Detect → 定位具体句子 → Minimum Effective Edit`

### 改造成 Content OS

可以建立中文 `STYLE_SIGNAL` lint，但命中不直接 FAIL。

Script Editor 决定是否需要修改，同时遵守：

- semantic truth 不变；
- Fact / number / attribution 不变。

---

# 六、Audit / Red Team

## 13. `JuliusBrussee/cavekit` · review

**吸收等级：DIRECT_ABSORB**

### 借什么

Red Team 的任务是“尝试推翻”，不是“帮 Writer 看看有没有明显问题”。

强制攻击：

- Goal vs Reality
- Missing Invariant
- Interface Drift
- Constraint Conflict
- Unowned Edge
- Altitude / 可执行性

Finding 必须有证据，无证据降级并标记 `[unverified]`。

Severity 可映射为 Content OS：

- BLOCK → BLOCKER
- HARDEN → WARNING / rule candidate
- NOTE → INFO

---

## 14. `adaptico/adaptico-os` · gtm-critic

**吸收等级：DIRECT_ABSORB**

### 借什么

Finding 结构：

- Location
- Exact Claim / 原文
- Problem
- Principle
- Why it matters
- Fix direction
- Would change my mind

尤其吸收：

### Falsifiability

每个判断必须说明“什么证据会让我改变结论”。

### Don’t Inflate

不能为了显得审查严格，把所有问题升级成 BLOCKER。

### Attack Your Own PASS

每一个 PASS 在最终提交前，强制做一次最强反驳；反驳成立就翻转 verdict。

### 不借什么

营销领域 4U、Value Equation、SaaS stage 等具体评分体系全部拒绝。

---

# 七、Director / Visual Storytelling

## 15. `cajias/agentic-video-skills` · cinematic-director

**吸收等级：ADAPT_ABSORB**

### 借什么

- Beat before Shot。
- Every Shot must have a story function → Content OS 改成 **Every Beat must have a Visual Function**。
- Visual Thesis 必须可视觉化，不能是抽象情绪口号。
- Blocking / staging 可改写成 Composition Blocking。
- Continuity：上一 Beat 的结束状态应帮助下一 Beat 展开。
- Slideshow Repair：不要靠 zoom / fade 假装动态，真正动态应来自信息状态变化。

### 改造成 Content OS Beat

建议 Director Beat 增加：

- `visual_job`
- `viewer_should_notice`
- `evidence_carrier`
- `cognitive_change`
- `continuity_from_previous`

### 不借什么

- 导演风格模仿；
- 复杂电影运镜；
- 灯光/焦段体系；
- 固定 shot 时长。

XIAO-Y 是解释型内容，不是短电影。

---

## 16. `video-talkcraft`

**适用：中文口播 + Remotion**  
**吸收等级：S+ / HIGH PRIORITY ADAPT_ABSORB**

### 借什么

这份 Skill 直接支持 D-002 的核心方向：

`Script → Voice → 字/句级 Timing → 语义拍 → 分镜 → Remotion → QA`

关键思想：

- 解说词驱动画面；
- 时间真源来自真实音频；
- 按“语义拍”切镜，不机械“一句一个新元素”；
- 一个 Beat 一个视觉主角；
- 新元素只在语义边界进场；
- 反 PPT 不等于“所有东西不停动”；
- 主体可以让位：Evidence / Data 成为主角时，人物退场或弱化。

### 改造成 Content OS

直接支持候选：

- Narration Units
- AudioTimingMap temporal truth
- Semantic Beat
- Director consumes real timing
- XIAO-Y / Evidence / Data 主体让位规则

### 不借什么

- 固定 Apple 视觉语言；
- 108 张动效卡整套复制；
- 它的项目级依赖管理方式；
- 具体 ASR/TTS 供应商实现。

这些只能参考技术方法。

---

# 八、Visual QA

## 17. `a86582751/doubao-seedance-video-skill`

**吸收等级：DIRECT_ABSORB FOR QA ONLY**

### 借什么

- 生成者与审查者分离；
- 每轮使用 Fresh Reviewer；
- QA 上下文保持瘦，只给必要 Evidence；
- Segment / Beat QA 与 Final Assembly QA 分离；
- Final QA 检查跨 Beat 重复、节奏、视觉连续性和整体 balance。

### 改造成 Content OS

#### Pre-render Beat QA

检查：
- semantic match
- visual job
- evidence selection
- XIAO-Y action
- pattern repetition

#### Post-render Visual QA

检查：
- composition
- crop
- blocking
- typography
- screenshot readability
- PPT feel
- rhythm
- repeated / empty / broken frames

### 不借什么

- Seedance / AI Video 主路线；
- Token / generation workflow；
- last-frame continuation 等生成式视频特定方法。

---

# 九、中文平台的 Platform Profile 建议

## DOUYIN_PROFILE

### 默认策略

- 前段必须迅速形成停留理由；
- Hook 同时考虑文案与视觉；
- 第一视觉状态重要；
- 语言广泛可懂；
- 节奏较紧；
- Evidence 尽快出现；
- 允许冲突、反差、结果前置等表达。

### Heuristic，不是 Hard Rule

- “黄金 3 秒”；
- 固定脚本时间比例；
- 固定字数/语速；
- 算法指标权重排序。

---

## XIAOHONGSHU_PROFILE

### 默认策略

- Title / Cover 为第一点击合同；
- 搜索意图强；
- 身份处境和具体场景强；
- 过程证据；
- 可收藏信息；
- 标题与首图必须共同兑现正文；
- **首图获得高于普通内页的设计与 QA 优先级**；
- **标题默认优先加入与真实内容相符的情绪钩子词**；
- 情绪钩子不等于虚假夸张。

### 用户确认纳入的行业经验

#### 首图“约 70% 点开率”

保留为 `HEURISTIC_LABEL`：

> “首图决定约 70% 点开率”是当前中文自媒体圈常见运营经验表达，用于提醒系统把首图视为小红书点击链路的极高优先级资产。

限制：

- 不进入 Fact System；
- 不作为官方平台算法结论；
- 不作为确定性 QA 数值阈值；
- 后续如获得真实账号 Analytics，应以用户自己的点击数据替代行业经验。

#### 标题情绪词

保留为 `DEFAULT_PLATFORM_TACTIC`：

- 默认尝试一个真实、克制、有内容依据的情绪钩子；
- 支持惊讶、反差、避坑、真香、后悔、身份共鸣、紧迫、好奇等；
- 若主题严肃、技术、证据导向，可不使用；
- 不允许“为情绪而造事实”。

---

## WECHAT_CHANNELS_PROFILE

### 默认策略

- 信任优先；
- 完整可信表达；
- 真实声音 / 真实经历 / 真实证据；
- 关系链传播语境；
- 内容应具备“值得转给熟人”的信息价值；
- 少用纯刺激型网感喊话。

### Heuristic，不是 Hard Rule

- 固定黄金发布时间；
- 固定互动权重排序；
- 固定短时长模板。

---

# 十、最终建议的吸收架构

```text
RESEARCH
├─ researcher_agent → Source Qualification
├─ fact-check → Claim Verification
└─ video-maker → Evidence Map / Overclaim Boundary

STRATEGY / EPISODE BRIEF
├─ xiaohongshu-ops → 账号/选题/搜索意图
└─ self-media-content-workflow → Platform Routing

WRITER
├─ video-maker → Content Contract
├─ youtube-script-writer → Promise / Beat / Read-aloud
├─ huashu-douyin-script → 文案Hook×视觉Hook
└─ Platform Profile → 抖音 / 小红书 / 视频号差异化

SCRIPT EDITOR
├─ humanize → Minimum Effective Edit
└─ de-ai-flavor → 中文 AI 味检测

RED TEAM
├─ fact-check → All-Claim Coverage
├─ cavekit → Refutation
└─ adaptico → Evidence Finding / Falsifiability / Attack PASS

AUDIO / TIMING
└─ video-talkcraft → Voice-first / Semantic Beat / Timing Anchor

DIRECTOR
├─ video-maker → Cognitive Change / Evidence Carrier
├─ cinematic-director → Beat Visual Function / Continuity
└─ video-talkcraft → 反 PPT / 主体让位 / 语义拍

VISUAL QA
├─ video-maker → Review Real Pixels
└─ Seedance Skill → Fresh Reviewer / Beat QA / Final Assembly QA
```

---

# 十一、明确不做的事情

- 不整包安装外部 Skill；
- 不把平台“爆款公式”写成事实；
- 不把行业经验数字写进确定性 validator；
- 不建立多个互相冲突的 Prompt 真源；
- 不让 Platform Profile 改变 Fact / Claim 真源；
- 不用短视频平台规则绑死所有 3–5 分钟横屏内容；
- 不为了“网感”牺牲事实准确性；
- 不把 XIAO-Y 变成通用白板人物；
- 不改变 Remotion 的执行器定位。

---

# 十二、下一步

1. Claude 基于本矩阵做一次 D-003 补充 Review；
2. 对每条规则标记最终：ACCEPT / MODIFY / REJECT；
3. D-002 决定 Audio-first 后冻结 Director timing contract；
4. 再生成六个核心 Role Prompt Pack；
5. Platform Profile 作为独立层注入 Writer / Director，而不是复制三套 Role Prompt；
6. 建 Prompt Qualification Suite；
7. 用同题 Track B 做 A/B 创作质量对比。

本文件在用户明确 ACCEPT 前保持 Research / Proposal 状态。
