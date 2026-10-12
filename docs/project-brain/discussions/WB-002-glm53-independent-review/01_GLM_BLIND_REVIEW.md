# GLM Blind Review · Phase A（冻结版）

**Model:** GLM 5.3
**Date:** 2026-09-29
**状态说明：** 本文件为 Phase A 独立盲评结论，**Phase B 结束后不回改**。标记约定按任务书：`FACT` 仅限代码直接支持的内容；因果判断一律降级为 `HYPOTHESIS`。凡标注「独立重验证」的条目，为本轮重新读取代码后独立得出（可能与 WB-001 重合，可能相反）。

---

# 主问题回答：为什么 Engineering PASS 但 Creative FAIL？

**结论（OPINION，基于下列 G-01～G-04、G-07 的代码事实综合）：**

Engineering 检查的是**约束合规**（schema、哈希、依赖、几何、时长），Creative 检查的是**观看体验**。Track B 的 Creative FAIL 不是单一根因，而是**四个因子的乘积**，缺任何一个因子，画面都会明显不同：

1. **题材因子（本轮新识别）**：Track B 题材是纯方法论教程（"字幕安全区检查法"），全程没有导入任何 media asset。`director_contract.py:16` 在无 media 时直接把需要 `media_asset_id` 的 pattern（CHARACTER_REACTION_MEDIA / SCREEN_DETAIL）从 enum 中剔除。Director 的可选视觉词汇从 8 个 pattern 收窄到 6 个纯文本型 pattern。MiniMax 的 INFO findings（"missing concrete platform/occlusion demonstrations"）正是这个因子的直接体现。
2. **Director 权限因子**（G-01）：Director 无法选择 template/layout/motion 词汇，reveal 编排被 clamp。
3. **渲染词汇因子**（G-02）：beat 内 8 帧入场动画后完全静止，beat 间无转场。
4. **多样性无人负责因子**（G-04）：pose 分配是首匹配、QA 不查连续重复、Director prompt 无多样性要求。

**关键推论（HYPOTHESIS）**：如果 Track B 题材自带 evidence 截图（平台 UI 演示），因子 1 消失，画面至少会有 media 主体和 SCREEN_DETAIL 类模板出现——**Track B 的 FAIL 无法证明「换成有素材的题材也会 FAIL」**。选材本身决定了这次验收无法展示系统的 evidence 表现能力。反之，即便题材带素材，因子 2/3/4 仍在。因此：**任何单因子修复（只改 prompt、只改 renderer、只加素材）都不足以必然翻转为 Creative PASS**；同样，Track B 的 FAIL 也不能把责任单独归给任何一方。

---

# Findings

## G-01 · Director 的实际控制权远小于「visual truth owner」的名义

```text
Finding ID: G-01
Type: FACT
Claim: Director 在 schema 层被剥夺了 template / layout / semantic_pattern 的选择权，
      motion_intent 枚举只有 HOLD/FADE/SLIDE_UP 三种，reveal_order 首位被强制为 PRIMARY，
      slots 数字必须逐字来自 segment。它真正能决定的只有：pattern_id（6–8 选 1）、
      keyword/slots 文本、character_intent、element_ids、timing_intent（之后被 retime 覆盖）。
Evidence: director_contract.py:19（'template_id':{'const':None}、'semantic_pattern':{'const':None}、
          motion_intent enum、reveal_order prefixItems={'const':'PRIMARY'}）；
          director_contract.py:28（instructions 明确 "Leave semantic_pattern and template_id null"）；
          visual.py:13–18（pattern→semantic→template 一一映射）。
Branch: both（director_contract.py 不在 p0 diff 中，两分支相同）
Applies to: Track B / Architecture
Why it matters: 「Director 负责 visual truth」的职责表述与其实际自由度不匹配，
              是评估任何 Director Prompt 改进收益时的先决事实。
Confidence: HIGH
What would falsify this: 指出 director_contract.py 中允许 Director 选择 template/layout 的代码路径（不存在）。
```

## G-02 · 渲染器的完整运动能力清单：4 类一次性入场动画，无 beat 内持续运动与 beat 间转场

```text
Finding ID: G-02
Type: FACT
Claim: 当前 Composition.tsx 的全部动画能力：
      (1) reveal 透明度插值：interpolate(frame,[reveal,reveal+8],[0,1])，约 0.27s @30fps；
      (2) SLIDE_UP 位移：同样 8 帧内 20px→0；
      (3) MARKER/UNDERLINE SVG 描边：clipPath inset 随 frame 推进（12 帧量级）；
      (4) treatment 缩放：interpolate([reveal+10],[.96,1])。
      不存在：beat 内持续 zoom/pan（Ken Burns）、beat 间转场（crossfade/swipe）、
      camera 概念、按时间的连续数据动画。CHARACTER/MEDIA 是静态 <Img>（或整段 OffthreadVideo）。
Evidence: Composition.tsx:16,20,24–32（全部 interpolate 调用点）；p0 diff 仅新增字幕深色衬底，未新增运动。
Branch: both
Applies to: Track B / Architecture
Why it matters: 这份清单是后续任何「PPT 感」归因讨论的公共事实基础。
Confidence: HIGH
What would falsify this: 在 Composition.tsx 找到第 5 类动画或任何帧函数驱动的持续运动（不存在）。
```

## G-03 · Track B Creative FAIL 是四因子乘积，题材因子（无 media）被所有讨论忽略

```text
Finding ID: G-03
Type: HYPOTHESIS（因子构成中每一项是 FACT，因果组合是 HYPOTHESIS）
Claim: Track B 的稀疏画面 = 无 media 题材 × Director 权限窄 × 渲染词汇少 × 多样性无人负责。
      题材因子是本轮新识别：fixtures 源是纯文本方法论教程，Track B 无 media import 记录，
      media 依赖 pattern 被 schema 剔除，MiniMax 报 missing platform/occlusion demonstrations。
Evidence: SLICE-006-TRACK-B.md（题材、无 media 记录、MiniMax findings）；
          fixtures/track-b-subtitle-source.txt（源材料全文为文字步骤）；
          director_contract.py:16（无 media 时剔除 media pattern）。
Branch: both
Applies to: Track B
Why it matters: (1) 单因归因（"主要是 Renderer"或"主要是 Prompt"）都会导致错误的投资顺序；
              (2) Track C 选材标准应明确要求「含 evidence 媒体的题材」，否则下一轮还会得到同样稀疏的画面；
              (3) 对用户最重要的含义：**Track B 不能证明系统在有素材题材上的表现**。
Confidence: MEDIUM（组合因果无法从单次运行证明；四个因子各自的存在是 HIGH）
What would falsify this: 用同一管线跑一个带真实截图的题材，若画面依然 PPT 感不变，
              则题材因子权重被高估；若画面显著改善，则单靠 renderer/prompt 修复论被削弱。
```

## G-04 · Pose 多样性在三个环节都无人负责（独立重验证）

```text
Finding ID: G-04
Type: FACT + RISK
Claim: (1) VisualResolver 的动作选择是 next(first intent match)（visual.py:94），无去重/轮转/预算；
      (2) Mechanical QA 无 pose/action 连续重复检查——MOTION_REPETITION 仅在全部 beat 同一 motion 时触发，
          KEYWORD_PATTERN_REPETITION 仅在全部 beat 同一 pattern 时触发（production.py:442–445），
          即 7 个 beat 中 5 个重复同一 pose 不会触发任何告警；
      (3) Director schema 允许填 character_action_id（enum 含全部 48 动作），但 instructions
          没有任何多样性要求。
Evidence: visual.py:92–96；production.py:442–445；director_contract.py:19,28；
          SLICE-006 记录 "several scenes reuse the same XIAO-Y pose" + 两次 MOTION_REPETITION warning。
Branch: both
Applies to: Track B / Architecture
Why it matters: 归因是「Resolver 机制 + QA 盲区 + Prompt 缺要求」三方组合，修复也必须三方同时；
              只改任何一处（例如只加 QA 检查）只会把问题推到另一处。
Confidence: HIGH（代码事实）/ Track B 实际 beat 是否填了 action_id 为 UNKNOWN，
            但 SLICE-006 确认重复现象存在。
What would falsify this: 展示 Director prompt 中存在多样性要求、或 QA 存在部分重复告警（均不存在）。
```

## G-05 · p0 渲染器已无条件给字幕加深色衬底，但 QA 的「无背景/白字」BLOCKER 规则原样保留——规则与实现脱节（本轮新发现）

```text
Finding ID: G-05
Type: FACT + RISK
Claim: p0 分支 Composition.tsx 给 SUBTITLE 无条件加 background:'rgba(13,19,24,0.88)' 深色衬底
      （c0ed169，Track B 白底白字缺陷的修复）。但 p0 的 mechanical QA 仍然保留：
      SUBTITLE_BACKGROUND（metadata.background 存在即 BLOCKER）、SUBTITLE_COLOR（非白即 BLOCKER）、
      SUBTITLE_BASELINE（y 必须精确 .91）。
      QA 检查的是 clip metadata 数据字段，渲染器根本不读这些字段而是无条件画衬底——
      「字幕必须白字无底」这条产品规则在 p0 上事实上已被架空，但 QA 语义、i18n 文案与
      规则文档都没有更新。
Evidence: p0 Composition.tsx diff（衬底样式）；p0 production.py:407–411（QA 规则原样）；
          SLICE-006 记录该修复的来龙去脉（人工抽帧发现 → 渲染器补丁）。
Branch: p0
Applies to: Track B / Architecture
Why it matters: (1) 这是「逐个症状打补丁、规则不回头改」模式的实例：渲染行为变了，
              验证它的 QA 规则没变，未来任何人读 QA 规则会得出错误的系统行为认知；
              (2) 衬底颜色/透明度硬编码在渲染器里，TypographyProfile 无对应字段，风格不可配置；
              (3) 与 DEC-005「EDT 是唯一可编辑时间线」的精神张力：视觉决策（衬底）绕过了 IR/EDT 链。
Confidence: HIGH
What would falsify this: 找到 p0 中 QA 规则或 typography profile 对应更新的提交（不存在）。
```

## G-06 · D-001 Claude Final 已明确预警 Q-009 顺序冲突并给出三个选项；p0 实现走了「方式 1」，但这一选择从未被记录为决策（本轮新发现）

```text
Finding ID: G-06
Type: FACT（过程事实）
Claim: D-001 04_CLAUDE_FINAL.md 第 2 节明确指出 Q-009（Audio-first）与 GPT Slice 2→3 顺序冲突，
      给出三个处理方式：1) 按旧顺序打通、Q-009 留给 D-002；2) 对调 Slice 顺序；3) 先跑 Spike 3 再定。
      Claude 倾向方式 3 并警告「窗口很短」。p0 分支实际按旧顺序（Director 在 Voice 前）完成
      Slice 2→3→4→Track A/B 并通过验收——即走了方式 1。但：
      - D-001 的 05_SYNTHESIS.md 仍是 PENDING（三选项从未被 Synthesis 收敛）；
      - Q-009 在 OPEN_QUESTIONS 中仍为 open；
      - 没有任何 commit / 文档记录「用户选择了方式 1」。
      实现以既成事实的方式替三个合法选项中的一个做了选择。
Evidence: D-001/04_CLAUDE_FINAL.md §2；D-001/05_SYNTHESIS.md（PENDING）；
          p0 分支提交序列（5095878→…→323f7a2 按 Slice 2/3 旧顺序）；
          OPEN_QUESTIONS.md Q-009 状态。
Branch: main（文档）+ p0（实现）
Applies to: Architecture / Process
Why it matters: (1) D-002 现在讨论的「是否重排」，其机会成本已经被 p0 的既成实现抬高——
              这一点应作为 D-002 讨论的显式输入；
              (2) 这是 COUNCIL_PROTOCOL「Proposal≠Decision」约束的执行缺口：
              不是模型越权写 DECISIONS，而是实现越权消解了 OPEN 的 Question。
Confidence: HIGH（全部为文件与 commit 可核对事实；「未记录用户选择」基于仓库内无该记录）
What would falsify this: 找到仓库外（对话记录）用户明确批准方式 1 的证据——若存在，本条降级为
              「决策未归档」的流程瑕疵。
```

## G-07 · Track B 的 beat 级音画对齐实际是精确的；D-002 描述的错位只存在于字幕层与 1:N 段内（独立重验证 + 本轮精确化）

```text
Finding ID: G-07
Type: FACT
Claim: Track B 是 7 段 script × 7 beats 的 **1:1** 结构。retime() 对单 beat segment 的处理是
      start=e['start']、end=e['end']（audio.py:98–101，单元素 selected 时 i==len-1 分支）——
      **每个 beat 的起止就是该段真实音频的起止**，beat 层不存在「段内比例猜测」。
      D-002 描述的音画错位在 Track B 上只表现为：
      (1) 字幕层：production voice 把整段文本作为一个 phrase_range（workflow.py:59），
          subtitles() 在段内按字符数比例拆分 chunk（audio.py:117–123）——字幕切点是猜的；
      (2) 历史样片（84.76s，9 段 18 beat，1:2 结构）才有 beat 层段内比例分配问题
          ——属 HISTORICAL REGRESSION EVIDENCE，不是 Track B 事实。
Evidence: audio.py:90–102（retime 逻辑）；workflow.py:57–61（每段单 phrase）；
          audio.py:117–123（字符比例拆分）；SLICE-006（7 段 7 beat）；
          AUDIO_TIMING_REVIEW.md（84s 样片 9 段 18 beat，HISTORICAL）。
Branch: both
Applies to: Track B（beat 层精确）；Historical（1:N 段内比例问题）；Architecture
Why it matters: D-002 的「Why Now」证据链需要重新对准：真正的普适缺陷是字幕字数比例拆分；
              beat 层缺陷只在 1 段多 beat 的项目出现。若 D-002 讨论不区分这两层，
              Spike 设计会测错对象。
Confidence: HIGH
What would falsify this: 展示 Track B 实际 beat 边界与音频段边界偏离的数据（运行态数据不可得，
              但 retime 代码逻辑与 1:1 结构都是仓库事实）。
```

## G-08 · D-002 三方案的真实区别：A/B 修「切在哪」，C 修「切几刀」——C 有不可替代收益，此前讨论未区分

```text
Finding ID: G-08
Type: PROPOSAL（分析框架）+ HYPOTHESIS
Claim: 对三个候选方案的精确切分：
      A（现状 retime）：修不了切点也修不了刀数。Track B（1:1）beat 精确但字幕仍字数比例；
          1:N 项目 beat 切点为比例猜测。
      B（word/phrase anchor）：把切点吸附到真实词/短语边界。前提：word_timestamps 非空
          （Track B UNKNOWN；segment-concat 模式下 TTS 若不返回词级时间戳，需引入本地强制对齐）。
          修「切在哪」，不修「切几刀」。
      C（full Audio-first）：唯一能修「切几刀」的方案——Director 拿到真实时长后再决定
          beat 密度。Track B 的 61.4s/7 beat ≈ 8.8s 一张静态卡：如果 Director 知道每段真实
          只有 8.8 秒且渲染词汇只有静态卡片，合理的决策是切 2–3 个 beat 分摊信息——
          这个「按真实时长决定视觉密度」的决策链只有 C 能提供。
      成本：A=0；B=改 audio.py 两个函数+对齐数据源；C=改 require_storyboard、
          Storyboard Gate 语义、GUI 流程、invalidation 测试，且与已完成的 p0 实现冲突（见 G-06）。
      结论：B+C 组合才同时覆盖两层；只做 B 会让 8.8s 静态卡问题原样保留。
Evidence: audio.py（retime/subtitles 现状）；SLICE-006（8.8s/beat 实测）；
          workflow.py:50（require_storyboard 现状）。
Branch: both
Applies to: Architecture / D-002
Why it matters: 把「切在哪/切几刀」混为一谈会让 D-002 用错成本买到错的收益。
Confidence: MEDIUM（框架本身 HIGH；C 的实际收益依赖 Director 会不会用好真实时长，未验证）
What would falsify this: 让 Director 在拿到真实时长后依然按 1 段 1 beat 输出（即信息不被利用）；
              或证明 8.8s 静态卡与 PPT 感评分无相关性。
```

## G-09 · Storyboard Gate 只看静态图，动效预览通道存在但不在 Gate 前置（独立重验证）

```text
Finding ID: G-09
Type: CURRENT_IMPLEMENTATION + RISK
Claim: Gate 的输入是每 beat 2 张 still（首帧+尾帧附近）；storyboard_motion（动画预览渲染）在
      adapter.py:76–92 存在，但 require_storyboard() 只校验 STORYBOARD_GATE 本身，
      动效预览不是 Gate 的必要输入。人类关卡观察不到运动/节奏维度——而这正是
      Creative FAIL 的核心维度。Slice 2 记录（21 beats 只产 stills）证实实际流程不产动效预览。
Evidence: production.py:169–199（storyboard still 逻辑）、224–231（require_storyboard）；
          adapter.py:76–92（storyboard_motion，"never a formal render"）；
          SLICE-002 记录（42 stills 流程）。
Branch: both
Applies to: Track B / Architecture
Why it matters: 成本核算错位——最贵的人工注意力花在了信息最少的输入上。
Confidence: HIGH
What would falsify this: 找到 Gate 强制动效预览的代码（不存在）。
```

## G-10 · MiniMax QA 的能力边界：静态布局维度有效、动态维度盲区——Track B 两次实测证明它并非「零信息量」

```text
Finding ID: G-10
Type: FACT + 修正性结论
Claim: 输入层：视频以 fps=1 抽帧送入（gateway.py:84 'fps':1）；system prompt 仅两句话无 rubric
      （intelligence.py:168）；0 findings → PASS；单条时间戳越界 → 整次 QA 抛异常（:183）。
      但 Track B 两次真实 QA **有效报出了静态维度问题**：v1 报 SUBTITLE_OVERLAP_ARTIFACT /
      TEXT_TRUNCATION_RIGHT / TIMING_DENSITY_HIGH / BEAT_SAFETY_DISCLAIMER_PRESENT；
      v2 报 1 条 subtitle/text crowding WARNING + 6 条 INFO（repeated text、missing platform demos、
      tight list reveals、unbalanced white space）。
      边界划分：fps=1 下**仍可判断**——布局拥挤、白空间失衡、文本重复、可读性、构图；
      **不能判断**——亚秒级 reveal 节奏、转场平滑、运动重复（Track B 的 MOTION_REPETITION
      恰恰是本地机械 QA 报的，不是 MiniMax）。
      注意证据分层：84s 历史样片的「6 条 finding 5 条时间归属错误」复核表属
      HISTORICAL REGRESSION EVIDENCE；Track B 两次输出无逐条复核记录，时间戳准确率 UNKNOWN。
Evidence: gateway.py:84；intelligence.py:168,183,187；SLICE-006（两次 QA 的 finding 清单与耗时）；
          MINIMAX_QA_TRIAGE.md（HISTORICAL，PRJ-bba515713057）。
Branch: both
Applies to: Track B / Architecture
Why it matters: 「MiniMax 视觉 QA 接近零信息量」与「MiniMax 可以继续当全能视觉 QA」都是错的。
              正确定位：静态布局审查者 + 需要补 rubric 与 clip 绑定；动态维度应转 deterministic。
Confidence: HIGH（能力清单与 Track B 输出均为记录事实；「不能判断动态」由 fps=1 推出，置信 HIGH）
What would falsify this: MiniMax 在 fps=1 输入下准确报告 sub-second motion 问题（与抽帧机制矛盾，
              不太可能）；或 Track B 逐条复核证明其静态判断大量错误。
```

## G-11 · 长视频风险的实测外推：45MB 与 storyboard 仍 safely 非阻塞，render timeout 是唯一真实候选（本轮用真实数字重算）

```text
Finding ID: G-11
Type: FACT（测量）+ HYPOTHESIS（外推）
Claim: 基于真实测量外推 3–5 分钟视频：
      (1) 码率：Track B 4,309,544 B / 61.46s = 70.1 KB/s；synthetic 93s 片 6,901,444 B / 93.01s
          = 74.2 KB/s。两样本一致 ≈ 70–75 KB/s。45 MB 上限 ≈ 606–656 秒 ≈ **10 分钟以上**。
          3 分钟 ≈ 12.7 MB、5 分钟 ≈ 21 MB，均远低于 45 MB → **45MB 不是 3–5 分钟 blocker**
          （只在 >8–10 分钟时才可能触发，且届时还有降采样选项）。
      (2) storyboard stills：实测 14 stills/28s 与 42 stills/67.1s → 1.6–2.0 s/still。
          3–5 分钟 ≈ 30–60 beats → 60–120 stills → 96–240 秒总耗时。慢，但每个子进程
          独立 timeout=120s，不构成失败条件 → **非阻塞，只是耗时线性增长**。
      (3) render timeout：Track B 61.46s 视频渲染 124s/128s（≈2.05× 实时，两次一致）。
          线性外推：180s 视频 ≈ 370s > 300s timeout；300s 视频 ≈ 620s。
          subprocess timeout=300 硬编码 → **3 分钟以上视频大概率渲染超时失败**
          （HYPOTHESIS：渲染时间对时长大致线性，但每帧成本会随 beat 数/DOM 复杂度上升，
          实际可能更糟；无 3 分钟实测）。
      (4) voice：Track B 7 段 299s ≈ 42.7 s/段，无逐段缓存。60 段 ≈ 43 分钟 TTS——
          成本与时长问题，非失败。
Evidence: SLICE-006（4,309,544 B、2m08s/2m04s、7 段 4m59s、14 stills/28s）；
          SLICE-004A（6,901,444 B、93.013s）；SLICE-002（42 stills/67.1s）；
          adapter.py:66（timeout=300）、:48（still timeout=120）；intelligence.py:161（45MB）。
Branch: both
Applies to: Future（Track C 3–5 分钟）
Why it matters: 长视频准备清单应只有一项 P0：把 render timeout 改为按时长计算或可配置。
              其余三项是优化项不是阻塞项。
Confidence: HIGH（测量与外推算术）；(3) 的「大概率超时」为 MEDIUM（无 3 分钟实测）
What would falsify this: 实测一条 3 分钟视频在 300s 内完成渲染（Remotion 并发收益超线性时可能）。
```

## G-12 · Platform Profile 不存在是事实，但当前产品定义是横屏 16:9——「无 9:16」不是当前 bug

```text
Finding ID: G-12
Type: FACT + 分类修正
Claim: (1) FACT：全仓无 Platform Profile / 抖音 / 小红书 / 视频号 概念代码；画布仅
          1280×720 / 1920×1080 两种横屏 profile。
      (2) 分类：PROJECT_CONTEXT_MASTER / IMPLEMENTATION_STATE / DECISIONS 均未将竖屏或
          平台原生格式列为当前产品需求；SKILL_ABSORPTION_MATRIX 中的平台 Profile 全部处于
          RESEARCH/PROPOSAL 状态。→ 9:16 属于 Future Platform-native Requirement，
          不是 Current Product Requirement 的缺口。
      (3) 当前真正成立的问题：字幕 QA 规则集（单行/无标点/白字/y=.91）是一套**平台意图
          不可追溯**的通用规则——不知道它为哪种观看环境优化；且 p0 衬底补丁后规则已脱节（G-05）。
Evidence: contracts.py:213（render_profile 两值）；全仓 grep（无平台概念代码）；
          SKILL_ABSORPTION_MATRIX.md 状态行；DECISIONS.md（无画幅决策）。
Branch: both
Applies to: Architecture / Future
Why it matters: 防止把 research 层的未来方向当成当前 bug 修复，浪费 P0 窗口；
              同时把「规则意图不可追溯」这个当前真问题从「没有 9:16」中剥离出来。
Confidence: HIGH
What would falsify this: 找到用户已确认的竖屏需求记录（仓库内不存在）。
```

## G-13 · write-only 语义字段清单（独立重验证 + 补充）

```text
Finding ID: G-13
Type: FACT
Claim: 被合同要求产出、被模型填充、但无任何生产代码消费的 Beat/Scene 字段：
      Beat: purpose、visual_focus、visual_form、retention_function、（renderers 层的 density/tempo
      仅存在于 DirectorPlan 旧模型）；Scene: density、tempo、retention_goal、narrative_function
      （scenes 的 purpose 进入 storyboard 展示但渲染链不消费）。
      另外 DirectorIR.phrase_id 与 transitions：schema 存在、全仓零赋值零消费。
      视觉决策实际只来自：pattern_id + slots + character_* + element_ids + motion_intent +
      reveal_order + timing_intent。
Evidence: contracts.py（phase2）字段定义；全仓 grep（消费点仅 tests 与 mock 生成器）；
          visual.py:70–132（resolve 消费的字段集合）。
Branch: both
Applies to: Track B / Architecture
Why it matters: 新增任何 Beat 语义字段（visual_job/evidence_carrier 等）之前必须先决定
              VisualResolver 如何消费它，否则只是第 7–12 个 write-only 字段。
Confidence: HIGH
What would falsify this: 找到 production/visual/renderer 路径读取这些字段的代码（不存在）。
```

## G-14 · 规则层无预算注入 + 死配置（独立重验证）

```text
Finding ID: G-14
Type: FACT
Claim: Governance.current_rules() 把 CURRENT_RULES.md 全文（含最多 4 个 rule set 的
      indent=2 JSON 全文）拼进每个角色 system prompt，无长度预算或裁剪；
      registries/skills/RESOLUTION_ORDER.json 从未被代码加载（层序在 knowledge.py:LAYERS
      重复实现；hard_rules_override 字段无对应实现，尽管 HARD_RULES_OVERRIDE 权限检查
      在 snapshot() 里存在——两者是不同机制，配置文件仍是死的）。
Evidence: governance.py:81–99,133–135；runtime.py:158；knowledge.py:13,73–80；全仓 grep。
Branch: both
Applies to: Architecture
Why it matters: Prompt 膨胀的结构性机制；以及「CREATIVE_POLICY 高于指标」这条 HARD 规则
              只有注入没有执行语义。
Confidence: HIGH
What would falsify this: 找到 RESOLUTION_ORDER.json 的加载点或注入的长度上限（不存在）。
```

## G-15 · 当前唯一有效的 creative 质量信号来自「人工抽帧」，而这一步没有被制度化

```text
Finding ID: G-15
Type: FACT + PROPOSAL
Claim: Track B 全程唯一按用户标准发现真实创作缺陷（白底白字对比度不足）的环节，
      是 SLICE-006 记录的 "Manual MP4 frame inspection"——MiniMax 漏掉了它。
      该人工抽帧步骤：不在任何 Gate 的必要条件里、没有 checklist、没有记录格式、
      属于一次性的人工动作。Mechanical QA 检查约束、MiniMax 检查静态布局、
      Storyboard Gate 看静态图、H3 由 P0_TEST_HARNESS 代打——四个关卡没有一个
      能按用户标准评估观看体验。
      PROPOSAL：把「N 帧强制人工过目」制度化为 creative gate 的最小版本
      （例如：正式渲染后、H3 前，强制人工查看 ≥5 个指定帧并逐帧记录 PASS/FAIL），
      成本极低（Track B 已证明其检出能力高于 MiniMax），且在渲染器改造完成前是
      唯一能拦住 creative 缺陷的手段。
Evidence: SLICE-006（manual frame inspection 段落——"found a defect the model review missed"）；
          production.py Review.build()（H3 前无人工帧检查要求）。
Branch: p0
Applies to: Track B / Architecture
Why it matters: 在等待 renderer/prompt 改造收益验证的期间，这是唯一可立即落地的
              creative 质量防线；也解释了为什么缺陷总是「上线后才被用户看到」。
Confidence: HIGH（事实层）/ MEDIUM（proposal 效果）
What would falsify this: 证明 MiniMax 在等效输入下能稳定检出低对比度字幕这类缺陷
              （Track B 已给出反例）。
```

---

# Phase A 小结（供 Phase B 对照）

- 15 条 Finding：FACT 8、FACT+RISK/修正 4、HYPOTHESIS/PROPOSAL 3；
- 与因果最相关的是 G-03（四因子乘积）——它同时约束了「Renderer 是第一根因」与「Prompt 是第一根因」两种单因论；
- 本轮独有的新事实：G-05（衬底/QA 脱节）、G-06（D-001 方式 1 未决策先实现）、G-07（Track B beat 层 1:1 精确）、G-10（MiniMax 静态有效/动态盲区的精确边界）、G-11（实测外推推翻 45MB/storyboard 阻塞论）、G-15（人工抽帧未制度化）。
