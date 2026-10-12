# GLM 5.3 Review of WB-001 · Phase B

**Date:** 2026-09-29
**前提：** Phase A（01_GLM_BLIND_REVIEW.md）已冻结，本文件不回改 Phase A。任务书要求的字段（Facts confirmed / Inference accepted / Inference rejected / Missing evidence / Corrected formulation / Recommended test）逐条给出。

**总判决统计：** ACCEPT 7 · MODIFY 4 · REJECT 1 · NEEDS_EXPERIMENT 0（部分 MODIFY 内含必做实验项，已在各条标出）。

**先说一个总体观察（影响多条判决）：** WB-001 的 `00_SCOPE.md` 读取清单中**没有 p0 分支的 `p0-slices/` 目录**——Track B 官方记录（SLICE-006）含关键实测数字（4,309,544 bytes、渲染 2m08s、MiniMax 两次真实 finding 清单、7 段 7 beat 结构）。WB 的多数代码事实正确，但**运行记录证据缺失**导致三条 Finding（F-05 / F-06 / F-07 的一部分）出现可被实测数据推翻的过度断言。这不是推理错误，是证据基线缺口。

---

## FINDING-01 · 「渲染层没有连续运动能力：Creative FAIL 的物理根因」

```text
Verdict: MODIFY
Facts confirmed:
  全部代码事实独立重验证成立（GLM G-02）：4 类一次性入场动画清单、无 beat 内持续运动、
  无 beat 间转场、motion_intent 3 值、beat 8 帧后静止。修复方向 (a) Ken Burns + (b) 转场
  与验证实验设计（同 IR 只改渲染盲评）均合理。
Inference accepted:
  「在这套渲染词汇下，无论 Prompt 怎么写，输出形态上限是卡片序列」——成立。
  「先修 D-003 会产生 Prompt 已升级的错觉」——风险真实。
Inference rejected:
  1. 「主要不是 Prompt 问题，而是 renderer expressivity ceiling」——这是单因归因，
     被标为 Type: FACT + RISK 且 Severity: BLOCKER，实际上「第一根因」判断是 HYPOTHESIS：
     Track B 的 Creative FAIL 是至少四个因子的乘积（GLM G-03）：无 media 题材 ×
     Director 权限窄（F-03/WB 自己也发现了）× 渲染词汇少 × 多样性无人负责。
     Track B 从未导入任何 media asset——renderer 的 media/evidence 表现路径
     （OffthreadVideo/SCREEN_DETAIL 模板）从未被这次验收触发。渲染器在「有素材」
     题材上的表现是 UNKNOWN，不能由 Track B 推出。
  2. 标题「物理根因」一词把机制（渲染词汇少=FACT）与归因（它是第一因=HYPOTHESIS）
     合并表述，正是任务书第十二条 A 警告的 FACT/ROOT-CAUSE 混写。
Missing evidence:
  (a) Remotion 框架能力 vs Content OS 实现能力的区分——WB 未回答任务书明确要求的问题。
      GLM 补上：Remotion 框架本身完全支持 zoom/pan/转场/任意帧函数动画/spring/Lottie/
      视频剪辑——本条全部是 **Content OS implementation limitation，不是 framework
      limitation**。这个区分很重要：它意味着修复不需要换框架，只改 Composition.tsx。
  (b) 带 media 题材的对照运行（WB 的盲评实验没控制「题材因子」变量）。
Corrected formulation:
  「当前渲染实现只有 4 类入场动画、无持续运动与转场（FACT）；这构成 Creative FAIL
  的必要条件之一，但 Track B（无 media 题材）不足以证明它是第一根因（HYPOTHESIS，
  与题材因子、Director 权限、多样性缺口共存）。Remotion 框架本身不构成限制。」
  Severity: MAJOR（从 BLOCKER 下调，待实验升级）。
Recommended test:
  WB 原盲评实验保留，但改为两臂：(1) 同 IR + Ken Burns/转场；(2) 同管线 + 带截图题材
  （不动渲染器）。两臂分离才能定位题材因子与渲染因子的各自权重。
```

---

## FINDING-02 · 「XIAO-Y 动作重复是首个匹配确定性坍缩」

```text
Verdict: ACCEPT
Facts confirmed:
  独立重验证全部成立（GLM G-04）：next(first intent match)（visual.py:92–96）、
  无去重/轮转/预算、Mechanical QA 无部分重复检查（MOTION_REPETITION 与
  KEYWORD_PATTERN_REPETITION 都是「全部相同才触发」）、XIAO-Y registry 的
  intent 分布数字一致。Track B 官方记录 "several scenes reuse the same XIAO-Y pose"
  确认现象在真实运行中存在。
Inference accepted:
  「加素材不会改变输出」（首匹配与新 pack 无关）——成立且重要。
  「拒绝式校验不够，需要分配机制」——成立。
Inference rejected:
  「Director 没有选择权：它没填 action_id，resolver 自己定了」——表述过强。
  schema 允许 Director 填 character_action_id（enum 含全部动作），Track B 的
  real GLM Director 是否填了 action_id 为 UNKNOWN。且 WB 引用的证据
  （examples/phase2/DIRECTOR_IR.json 6/6 action_id=None）是 main 分支的历史样例，
  不是 Track B 产物——用非 Track B 样例断言 Track B 行为是证据链滑动。
Missing evidence:
  Track B 真实 DirectorIR 的 action_id 填充情况（运行态数据不在仓库）。
Corrected formulation:
  「resolver 首匹配机制 + QA 部分重复盲区 + Director prompt 无多样性要求，
  三者共同造成 pose 重复；无论 Track B 走的是 intent-only 路径还是 Director
  主动选了重复动作，三个环节都没有任何机制阻止重复。」（归因从 Resolver 单方
  改为三方组合，与 GLM G-04 一致；WB 的 (a)(b)(c) 修复方案仍全部适用。）
Recommended test:
  WB 原实验保留：allocator 版本跑同 IR，统计 distinct action 数与用户评价。
```

---

## FINDING-03 · 「Director 没有 layout / template 权限」

```text
Verdict: ACCEPT
Facts confirmed:
  独立重验证全部成立（GLM G-01）：template_id/semantic_pattern 被 const:None 锁死、
  生产链路可达模板 6/12、LAYOUTS 为 12 组硬编码坐标、CTA_END_CARD 因无 CTA 语义
  pattern 而不可达、pattern→layout 为 1:1 确定性映射。
Inference accepted:
  「visual truth owner 在布局维度上是空名」——由代码结构直接支持。
  动态分支给不可达模板写 layout 代码确属死代码。
Inference rejected: 无。
Missing evidence: 无（纯代码事实）。
Corrected formulation: 无需修正。本条是 WB-001 中证据链最扎实的 Finding 之一。
Recommended test:
  WB 原建议（统计多视频 (template,layout,motion) 三元组去重数）可行；
  补充：Track B 已有一条数据点——7 beats、MOTION_REPETITION 触发即
  (template,layout,motion) 多样性低于 3。
```

---

## FINDING-04 · 「D-002 前提收窄：只剩段内比例猜测」

```text
Verdict: MODIFY
Facts confirmed:
  独立重验证成立（GLM G-07）：retime() 用真实 segment 起止定 beat 外边界、
  段内按 timing_intent 比例、字幕按字符数比例拆分（audio.py:117–123）、
  phrase_id/transitions 存在但零引用。S1–S5 方案清单与「Spike 缺第三臂」的
  方法论批评均有效。
Inference accepted:
  「D-002 的 Why Now 需要收窄」——方向正确。
Inference rejected:
  1. 「真正残留的只有段内比例猜测」——对 Track B 不成立。Track B 是 7 段 × 7 beat
     的 **1:1** 结构（SLICE-006），retime 对单 beat segment 直接赋真实段起止——
     **Track B 的 beat 层不存在任何比例猜测，beat 级音画对齐是精确的**。
     WB 引用的「18 beat 均分中点」证据来自 84 秒历史样片（9 段 18 beat，1:2），
     属 HISTORICAL REGRESSION EVIDENCE，被 WB 当作现行缺陷的通用证据使用——
     这正是任务书第六条禁止的混淆。段内比例问题只影响 1:N 结构的项目。
  2. S1「零管线改动」——不准确：word_timestamps 在 Track B 上是否非空为 UNKNOWN
     （WB 自己在 Confidence 里承认了，但 solution 描述仍写「零管线改动」）；
     且 subtitles() 的拆分逻辑本身需要重写。
  3. 隐含的「S1 做完可能就不需要 S3」——低估了 S3 的不可替代收益。GLM G-08 的
     区分：S1/S2 修「切在哪」，S3 修「切几刀」。Track B 的 61.4s/7 beat ≈ 8.8 秒
     一张静态卡——Director 在不知道真实时长的情况下决定 beat 密度，这个决策缺口
     只有 S3 能修。8.8s 静态卡正是 PPT 感的直接来源之一。
Missing evidence:
  Track B word_timestamps 是否非空；「Director 拿到真实时长会切更多 beat」的行为假设。
Corrected formulation:
  「retime 已锚定 beat 外边界（FACT）。剩余缺陷分两层：字幕字符比例拆分（普适）与
  1:N 段内 beat 切点（仅多 beat 段项目；Track B 1:1 不受影响）。方案 A/B 修切点，
  方案 C 额外修 beat 密度决策——B+C 组合才同时覆盖两层，只做 B 会保留 8.8s 静态卡
  问题。三方案应按『切在哪 vs 切几刀』两个维度分别评估，而非单一由小到大阶梯。」
Recommended test:
  (1) 核 Track B VOICE payload 的 word_timestamps（决定 B 的成本）；
  (2) 用 84s 样片的 1:2 结构做 B 方案 A/B 对比（那里才有段内切点问题）；
  (3) 让 Director 在拿到真实时长提示下重新规划同一脚本的 beat 数（验证 C 的独有收益）。
```

---

## FINDING-05 · 「Visual QA 失效：输入 + rubric 双重不足」

```text
Verdict: MODIFY
Facts confirmed:
  独立重验证全部成立（GLM G-10）：两句话 system prompt、fps=1、0 findings→PASS、
  单条时间戳越界→整次异常。(a)–(e) 修复方向（采样输入、rubric checklist、
  NO_FINDING 显式化、降级而非终止、静态维度转 deterministic）均合理。
Inference accepted:
  「fps=1 下无法感知节奏/连续性/亚秒级 reveal」——由输入机制直接推出，成立。
  「clip_id 方向对但不充分」——成立。
Inference rejected:
  1. 「它的 PASS_WITH_RISK 目前信息量接近零」——被 Track B 实测推翻。
     SLICE-006 记录两次真实 QA 均有效报出静态布局问题：v1 的
     SUBTITLE_OVERLAP_ARTIFACT / TEXT_TRUNCATION_RIGHT / TIMING_DENSITY_HIGH /
     BEAT_SAFETY_DISCLAIMER_PRESENT，v2 的 subtitle/text crowding WARNING +
     6 条 INFO（repeated text / missing platform demos / tight list reveals /
     unbalanced white space）。其中 v1 的发现还推动了真实修复（白底白字）。
     fps=1 的正确结论是「**静态布局维度有效、动态维度盲区**」，不是「接近零信息量」。
  2. 证据分层违规：FC-19「6 条 finding 5 条时间归属错误」来自 84 秒历史样片
     （PRJ-bba515713057）的 MINIMAX_QA_TRIAGE.md，WB 未标注 HISTORICAL，
     把单次历史复核当作 MiniMax 的一般行为证据。Track B 两次输出的时间戳
     准确率是 UNKNOWN（无复核记录）。
Missing evidence:
  Track B MiniMax 输出的逐条时间戳复核表；提高采样 fps 后的对比实验。
Corrected formulation:
  「MiniMax QA 缺 rubric、fps=1 限制动态维度、0-finding 静默 PASS、越界即整体失败
  （全部 FACT）。但其静态布局审查能力被 Track B 实测证明有效——正确定位是
  『静态布局审查者』+ 需补 rubric/clip 绑定/降级机制；动态维度（节奏/运动/亚秒 reveal）
  应转 deterministic。84 秒样片的高错误率是历史证据，不能外推到 Track B。」
  Severity 维持 MAJOR（机制问题真实，但『接近零信息量』表述删除）。
Recommended test:
  WB 原三臂实验保留；增加一臂：仅加 rubric checklist（不动 fps），验证静态维度
  检出率是否进一步提升——这是成本最低的增量验证。
```

---

## FINDING-06 · 「长视频三个硬失败点」

```text
Verdict: REJECT（三个『硬失败点』中两个被实测数据推翻；保留的 render timeout
        降级为待实验验证的单点风险）
Facts confirmed:
  硬编码值存在：render/storyboard_motion timeout=300（adapter.py:66,86）、
  still 子进程 timeout=120、QA 45MB 上限无降采样、voice 逐段调用无缓存。
  Track B 渲染时长（2m08s/2m04s）与 61s 的比例 ≈ 2.05×。
Inference rejected（本条判决核心）:
  1. 「45MB 上限让 3–5 分钟视频 VIDEO_TOO_LARGE——视觉 QA 不可用」——
     **被实测码率推翻**：Track B 4,309,544 B / 61.461s = 70.1 KB/s；
     synthetic 93s 片 6,901,444 B / 93.01s = 74.2 KB/s。两独立样本一致。
     45 MB ÷ ~72 KB/s ≈ **10 分钟以上**的容量。3 分钟 ≈ 12.7 MB、
     5 分钟 ≈ 21 MB——均不到上限的一半。45MB 是 8–10 分钟以上时点的风险，
     **不是 3–5 分钟 blocker**。WB 在 Confidence 里写了「确切断点取决于实际码率」、
     在 falsify 条目里写了「测 Track B MP4 字节数」——这个数字（4,309,544）
     就记录在 WB 未读取的 SLICE-006 里：验证方法正确，证据近在仓库却未取。
  2. 「storyboard still 子进程风暴是硬阻塞」——实测 14 stills/28s、42 stills/67.1s
     （≈1.6–2.0 s/still）。3–5 分钟 ≈ 30–60 beats → 60–120 stills → 96–240 秒
     总耗时。慢且线性增长，但每个子进程独立 timeout=120s，**不构成失败条件**。
     「60–120 次浏览器冷启动」的表述暗示失败，实际只是耗时。
  3. 「三项都会直接报错，而不是慢一点」——1 与 2 错，只有 3（render timeout）
     可能成立：61.46s→124–128s 线性外推，180s 视频 ≈ 370s > 300s。
     但这是外推（HYPOTHESIS），渲染时间对时长/beat 数的缩放未实测。
Inference accepted:
  voice 无逐段缓存是真实的成本问题（42.7s/段实测，60 段 ≈ 43 分钟）；
  (d) 段级哈希缓存方案有效且同时回答了 D-002 的 invalidation 问题——本条最有
  价值的部分，保留。
Missing evidence:
  3 分钟视频的实际渲染时长（唯一能救活或坐实 timeout 风险的数据）。
Corrected formulation:
  「Track C（3–5 分钟）前唯一必须处理的硬阈值是 render timeout=300s
  （线性外推 3 分钟 ≈ 370s，大概率超时，需实测确认）；45MB QA 上限在实测码率
  （~72 KB/s）下 ≈ 10 分钟容量，3–5 分钟不触发；storyboard stills 耗时线性
  增长至 1.5–4 分钟，可优化但非阻塞；voice 无逐段缓存是成本问题。」
  Severity: 从 BLOCKER 降为 MAJOR（单点，待实验）。
Recommended test:
  直接渲染一条 3 分钟测试视频（可用 Track B 素材复制拼接），记录耗时——
  一次实验即可关闭本条全部不确定性。
```

---

## FINDING-07 · 「没有 Platform Profile / 9:16」

```text
Verdict: MODIFY
Facts confirmed:
  独立重验证成立（GLM G-12）：全仓无平台概念代码、画布仅两种横屏 profile、
  TITLE/COVER 无产物类型、字幕规则集平台意图不可追溯。
Inference accepted:
  「平台差异大部分不在 Prompt 层，而在画布/安全区/字幕渲染/发布字段层」——
  有价值且成立。「按能否被渲染/校验切分」的归置方案合理。
  TITLE/COVER 需要新产物类型与人工关卡才能承载小红书策略——成立。
Inference rejected:
  1. 「目标平台以竖屏为主……当前组合是竖屏平台上可读性最差的配置之一」——
     把 Future requirement 当成了 Current 缺陷。当前产品定义（PROJECT_CONTEXT_MASTER、
     DECISIONS、IMPLEMENTATION_STATE）没有任何竖屏需求；SKILL_ABSORPTION_MATRIX
     中平台内容全部是 RESEARCH/PROPOSAL 状态。WB 自己在 Confidence 里写了
     「用户目标是竖屏为推断，需用户确认」，但 Severity 仍按竖屏成立给到 MAJOR、
     Why it matters 按竖屏展开。应分类为：Current 问题 = 字幕规则意图不可追溯 +
     规则已与渲染脱节（见 GLM G-05）；Future 问题 = 9:16 / 平台 Profile / TITLE-COVER。
  2. 「为了提升可读性而加字幕底衬会直接 QA FAIL」——在 main 分支读到的规则
     （metadata.background → BLOCKER）是对的，但 p0 分支渲染器已**无条件**给字幕加
     rgba(13,19,24,0.88) 衬底（c0ed169），且衬底画在渲染层、不进 clip metadata——
     Track B v2 渲染带着衬底通过了 Mechanical QA。此断言在 p0 上已被实现架空。
     WB 评审时读了 p0 的 diff（00_SCOPE 声称 diff 过 main..p0），但漏掉了
     Composition.tsx 的这处改动。
Missing evidence:
  用户对竖屏/平台优先级的明确表态（仓库内不存在）。
Corrected formulation:
  「平台层缺失是事实，但须分层：Current Product Requirement（横屏 16:9）下，
  真问题是字幕规则集的平台意图不可追溯且已与 p0 渲染行为脱节；9:16、平台 Profile、
  TITLE/COVER 产物全部属于 Future Platform-native Requirement，需用户在 H4/发布
  议题中决策，不应占用 P0 窗口。」
Recommended test:
  在 H4/Q-005 议题中向用户确认首个目标平台与画幅；在此之前不动 render_profile。
```

---

## FINDING-08 · 「Storyboard Gate 结构上无法发现 PPT 感」

```text
Verdict: ACCEPT
Facts confirmed:
  独立重验证全部成立（GLM G-09）：每 beat 2 张 still、storyboard_motion 存在但
  不在 require_storyboard 必要条件中。补充佐证：SLICE-002 记录 21 beats 的实际
  流程只产 stills、无动效预览。
Inference accepted:
  「不是 Gate 的人不认真，是 Gate 的输入不包含被测现象」——成立。
  「人已过 Gate、渲染后仍 FAIL」的反直觉现象解释成立。
Inference rejected: 无。
Missing evidence: 无。
Corrected formulation: 无需修正。(a)(b)(c) 方案均有效；与 GLM G-15（人工抽帧制度化）互补。
Recommended test:
  WB 原验证（静态板能否判断 PPT 感）可行。
```

---

## FINDING-09 · 「Beat 有 6 个 write-only 字段」

```text
Verdict: ACCEPT
Facts confirmed:
  独立重验证成立（GLM G-13）：purpose / visual_focus / visual_form /
  retention_function / density / tempo 无生产消费点（仅 tests 与 mock 命中）；
  实际消费字段清单一致。GLM 补充：Scene 层的 density / tempo / retention_goal /
  narrative_function 同样 write-only——清单比 WB 略保守。
Inference accepted:
  「先让 resolver 消费再加字段，否则是第 7–11 个 write-only 字段」——
  对 D-003 和 Skill Absorption Matrix 的实施顺序约束有效。
Inference rejected: 无。
Missing evidence: 无。
Corrected formulation: 仅补充 Scene 层字段。
Recommended test: WB 原建议（消费点断言）可行。
```

---

## FINDING-10 · 「Prompt 膨胀机制：规则层无预算注入 + 死配置」

```text
Verdict: ACCEPT
Facts confirmed:
  独立重验证成立（GLM G-14）：CURRENT_RULES.md 全文（含 indent=2 JSON）无预算注入、
  RESOLUTION_ORDER.json 零加载、层序在 knowledge.py:LAYERS 重复实现。
  GLM 补充一个精确化：hard_rules_override 配置字段无实现，但 snapshot() 内存在
  HARD_RULES_OVERRIDE 权限异常（knowledge.py:73–80）——两者是不同机制，
  「配置文件是死的」结论不变。
Inference accepted / rejected: 无异议。Severity（MINOR→NOTE）定级恰当。
Corrected formulation: 无需修正。
Recommended test: 导出真实 system prompt 字符数（维持）。
```

---

## FINDING-11 · 「D-002 目前只有 GPT 单方面意见」

```text
Verdict: ACCEPT（附扩展）
Facts confirmed:
  文件事实成立：D-002 的 02/03/04 为占位、05 全 PENDING。
  GLM 补充核实：D-001 的 05_SYNTHESIS 同样是 PENDING——三个讨论全部未收敛。
Inference accepted: 全部成立。
Missing evidence: 无。
Corrected formulation（扩展，非修正）:
  过程缺口比 WB 描述的深一层：D-001 的 04_CLAUDE_FINAL.md 第 2 节已明确预警
  Q-009 与 Slice 2/3 顺序冲突，并给出三个处理方式（旧顺序打通 / 对调顺序 /
  先 Spike）；Claude 倾向方式 3。p0 实现实际走了方式 1（旧顺序完成 Track B），
  但该选择未记录在任何 Synthesis / DECISION / commit message 中（GLM G-06）。
  即：不仅是「D-002 缺 Claude 轮」，而是「D-001 已识别的三选项被实现以既成
  事实的方式单方面选定」。D-002 讨论应把这个既成事实及其抬高的重排成本
  作为显式输入。
Recommended test: 无需实验；建议 D-002 Round 02 开场先确认方式 1 是否为用户默认接受。
```

---

## FINDING-12 · 「p0 分支已包含 D-002 部分答案」

```text
Verdict: ACCEPT
Facts confirmed:
  独立重验证成立：GENERATE_PRESERVING_AUDIO、Final EDT 绑定 voice+amap、
  human_edits_present() 护栏、后台 job 化、expected_revision 校验均在 p0 diff 中。
  SLICE-003 补充实测佐证：视觉编辑/undo 后 VOICE 与 AUDIO_TIMING_MAP 保持可用
  （EDT v5 直接依赖两个音频产物）——「纯视觉再生不触发重录」不仅实现了，
  还被浏览器验收记录背书。
Inference accepted: 全部成立。
Corrected formulation: 无需修正。可升格：从「代码里跑通」到「有浏览器验收记录」。
Recommended test: WB 原验证（改 beat → 看 VOICE 复用）已可由 SLICE-003 记录部分替代。
```

---

# 判决汇总

| WB Finding | Verdict | 核心理由 |
| --- | --- | --- |
| F-01 Renderer 无连续运动 | **MODIFY** | 代码事实全部成立；「第一根因」是 HYPOTHESIS 非 FACT；缺 framework/implementation 区分；Track B 无 media，渲染器的 media 路径未被测试 |
| F-02 first-match pose | **ACCEPT** | 全部成立；归因从 Resolver 单方细化为三方组合；样例 IR≠Track B 证据的小滑动不影响结论 |
| F-03 Director 无 layout 权限 | **ACCEPT** | 全部成立，证据链最扎实条目之一 |
| F-04 D-002 前提收窄 | **MODIFY** | 外边界锚定成立；但 Track B 是 1:1——beat 层无段内问题，84s 证据未标 HISTORICAL；S3 修「切几刀」的独有收益被低估 |
| F-05 MiniMax QA 双重不足 | **MODIFY** | 代码机制成立；「信息量接近零」被 Track B 两次实测推翻（静态维度有效）；84s 复核表未标 HISTORICAL |
| F-06 长视频三硬失败点 | **REJECT** | 实测码率 ~72KB/s → 45MB≈10 分钟容量，3–5 分钟不触发；storyboard 慢而不失败；唯一候选是 render timeout（需实测） |
| F-07 无 Platform Profile / 9:16 | **MODIFY** | FACT 成立；Current/Future 未分层致严重性夸大；「加衬底会 QA FAIL」已被 p0 实现架空 |
| F-08 Storyboard Gate 盲 | **ACCEPT** | 全部成立，SLICE-002 实际流程佐证 |
| F-09 write-only 字段 | **ACCEPT** | 成立，GLM 补充 Scene 层字段 |
| F-10 Prompt 膨胀机制 | **ACCEPT** | 成立，含一处无害的机制精确化 |
| F-11 D-002 单方面意见 | **ACCEPT+扩展** | 成立；扩展为 D-001 三选项被实现绕过的更深过程缺口 |
| F-12 p0 含 D-002 答案 | **ACCEPT** | 成立，SLICE-003 浏览器记录可升格其证据强度 |

**对 WB-001 方法论的两条总评（供后续 Review 轮引用）：**

1. **代码事实可靠、运行证据缺失**：WB-001 的代码引用经本轮全部独立重验证基本无误，但它没有读 p0-slices 运行记录，导致三个方向性断言（45MB、storyboard 阻塞、MiniMax 零信息）被仓库内已有的实测数字推翻。教训：**评审证据基线必须包含运行记录（SLICE/验收文档），不能只有代码**。
2. **Severity 纪律**：多处出现「Confidence 里承认推断需确认，Severity 却按推断成立给满」的模式（F-01 BLOCKER、F-06 BLOCKER、F-07 MAJOR）。FACT/HYPOTHESIS 分层在 Finding 正文执行得不错，但严重性定级没有跟随分层。
