# Model Comparison · GLM 5.3 vs WorkBuddy/Hunyuan4 + Council Cross-check

**Date:** 2026-09-29
**诚实前提：** WB-001（Hunyuan4 轮）与 WB-002（GLM 5.3 轮）在同一延续会话中产出，GLM 无法做到物理盲评（见 00_SCOPE 偏差声明）。本文件按任务书第十三、十四条输出，比较目的不是分高下，是为用户提供可用的证据质量校准。

---

# Part 1 · GLM 5.3 vs WB-001 (Hunyuan4)

## GLM found but WB missed

| # | 发现 | 证据 | 价值 |
| --- | --- | --- | --- |
| 1 | **p0 渲染器已无条件给字幕加深色衬底（rgba(13,19,24,0.88)），QA 的 SUBTITLE_BACKGROUND/SUBTITLE_COLOR BLOCKER 规则原样保留——规则与实现脱节**（G-05） | p0 Composition.tsx diff + p0 production.py:407–411 | WB 的 F-07 断言「加衬底会 QA FAIL」在 p0 上不成立；且暴露「症状补丁不回改规则」的模式 |
| 2 | **D-001 Claude Final 已预警 Q-009 顺序冲突并给出三选项；p0 实现走了「方式 1」但该选择从未被记录为决策**（G-06） | D-001/04 §2 + 05 PENDING + p0 提交序列 | D-002 讨论的隐性成本输入；COUNCIL_PROTOCOL 执行缺口的实例 |
| 3 | **Track B 是 7 段 × 7 beat 的 1:1 结构——beat 级音画对齐实际是精确的；「段内比例猜测」只存在于字幕层与 1:N 项目**（G-07） | SLICE-006 + audio.py retime 单 beat 分支 | 直接修正 D-002 的问题定位与 Spike 设计对象 |
| 4 | **D-002 三方案的真实区别：A/B 修「切在哪」，C 修「切几刀」；Track B 的 8.8s/beat 静态卡只有 C 能修**（G-08） | SLICE-006 时长数据 + 决策链分析 | WB 倾向「S1 做完可能不需要 S3」低估了 C 的独有收益 |
| 5 | **MiniMax QA 的精确能力边界：静态布局维度有效（Track B 两次实测报出真实问题）、动态维度盲区**（G-10） | SLICE-006 两次 QA finding 清单 | 修正 WB「信息量接近零」；给 Visual QA 一个可执行的重新定位 |
| 6 | **长视频实测外推：45MB≈10 分钟容量非 3–5 分钟 blocker；storyboard 慢而非阻塞；render timeout 是唯一真实候选**（G-11） | SLICE-006/004A/002 实测数字 | 推翻 WB F-06 的两个「硬失败点」，把 Track C 准备清单缩为一项 |
| 7 | **Track B Creative FAIL 含「题材因子」：纯方法论教程、无 media import，media 类 pattern 被 schema 剔除——选材本身决定了无法展示 evidence 表现力**（G-03） | fixtures 源材料 + director_contract.py:16 + MiniMax "missing platform demos" | 三方 Council 都没讨论的必要条件；直接产生 Track C 选材标准 |
| 8 | **人工抽帧是当前唯一有效的 creative 质量信号（Track B 白底白字由它而非 MiniMax 发现），但未制度化**（G-15） | SLICE-006 "found a defect the model review missed" | 成本最低的立即落地项 |

## WB found but GLM missed（Phase A 盲评未覆盖，Phase B 阅读 WB 后确认代码依据成立）

| # | WB 发现 | GLM 确认状态 |
| --- | --- | --- |
| 1 | treatment 装饰系统（MARKER/CHECKLIST/COMPARE/NUMBERED/UNDERLINE + 强调色）只在 `presentation == 'XIAOY_EXPLAINER'` dynamic 模式存在；未启用时输出是纯黑字白底（WB Creative Pipeline Risks 第 3 条） | 代码依据成立（visual.py:65,190–198）。Track B 是否启用该模式仍 UNKNOWN——若未启用，这是「白底偏空」的配置级候选解释，优先级应高于渲染器改造 |
| 2 | reveal delay 被 clamp 至 duration*0.4/0.65（visual.py:201），reveal 编排上限被锁 | 代码依据成立。GLM Phase A 未查 |
| 3 | VOICE_AUTHORIZATION 在音频合成之后创建（名不副实的事后记录） | 代码依据成立（workflow.py:57–68 顺序）。GLM Phase A 未查 |
| 4 | Audit FAIL 时静默清除 h2_script_artifact_id（runtime.py:218）——机器撤销人类 gate 状态 | 代码依据成立。GLM Phase A 未查 |
| 5 | AudioClock 五种 provenance method 并存、GUI 只用其一，from_voice() 路径无 GUI 实践证据 | 代码依据成立。GLM Phase A 未细查 |
| 6 | 对 GPT/Claude 既有结论的逐项核实表（Things Got Right 部分）——WB 系统性地复核了 Claude R02 的十个论点 | GLM Phase A 没做这个对账（本轮在 02 文件中部分弥补） |

## Same finding, different reasoning

| 主题 | WB-001 (Hunyuan4) | GLM 5.3 |
| --- | --- | --- |
| Creative FAIL 根因 | 单因论：renderer expressivity ceiling 是主要根因，Prompt 是必要不充分条件 | 乘积论：无 media 题材 × Director 权限 × 渲染词汇 × 多样性无人负责，四因子缺一画面即不同；Track B 无法区分因子权重 |
| MiniMax QA | 双重不足 → 「信息量接近零」 | 同样识别双重不足 → 「静态有效/动态盲区」，Track B 实测支持后者 |
| D-002 方案 | S1(anchor) 优先，S3(重排) 可能不必要 | S1 修切点、S3 修刀数，两者互补不互替；B+C 组合才完整 |

## WB overclaimed

1. F-06 的「三个硬失败点 / BLOCKER」——两项被实测数字推翻（45MB、storyboard），一项待实测（render timeout）。
2. F-05 的「信息量接近零」——Track B 两次 QA 实测推翻。
3. F-01 的「物理根因 / BLOCKER」——单因归因超出 Track B 证据能支持的范围（无 media 题材构成未控制的混淆变量）。
4. F-07 的「竖屏可读性最差配置 / MAJOR」——Current/Future 未分层；「加衬底会 QA FAIL」已被 p0 架空。
5. FC-19（84s 复核表）与 F-04（18 beat 均分）引用历史样片证据时未标 HISTORICAL，违反证据分层。

## WB underclaimed

1. S3/Audio-first 的独有收益（beat 密度决策）——WB 的「切在哪」框架漏了「切几刀」维度。
2. D-001 Claude Final 对 Q-009 的三选项分析——WB 只看到「D-002 缺 Claude 轮」，没发现 D-001 已有预警且被实现绕过。
3. Track B 的 MiniMax 真实输出（repeated text / white space / platform demos）没有作为改进线索被使用——这些 finding 恰好逐条对应四因子的证据。
4. SLICE-003 对 F-12 的浏览器验收背书（视觉编辑后 VOICE 保持可用）——WB 只说「代码跑通」。

## GLM uncertain

1. Track B word_timestamps 是否非空（决定 anchor 方案成本）。
2. Track B Director 是否显式填了 action_id。
3. Track B 是否运行于 XIAOY_EXPLAINER dynamic 模式（若否，白底稀疏有配置级解释，会再次改变根因权重）。
4. render timeout 线性外推的准确性（无 3 分钟实测）。
5. 锚定偏差对本轮的影响幅度——尽管采取了重新采集证据的措施，GLM 无法自证免疫（这也是为什么 01 文件保留冻结态供用户检验）。

---

# Part 2 · Council Cross-check（GPT / Claude / WB / GLM 四视角）

## GPT likely right

- D-003 的核心判断：多路径 prompt 冲突（RESEARCH/VIDEO_QA 死 prompt、Director 被覆盖式替换）——三方（Claude R02、WB、GLM）独立验证一致。
- Audio-first 的职责三分概念（semantic/temporal/visual truth）——即使 GLM 修正了 D-002 的证据链，这个概念框架仍然有效。
- D-001 的六点撤回与 Track A/B 分轨设计——被 Track B 实际运行验证。

## Claude likely right

- schema 双拼、thinking:disabled 硬编码、MiniMax 单点依赖、数字溯源应转 deterministic——全部经 GLM 复核成立。
- D-001 Final 的三选项框架——GLM 进一步发现它被实现绕过，说明该框架当时就切中了要害。
- 「先 Spike 区分局部 bug 与系统性顺序问题」——GLM 的 G-08 在这个方向上给出了更细的切分（切点 vs 刀数）。

## WB likely right

- F-02（first-match）、F-03（权限锁死）、F-08（Gate 盲）、F-09（write-only 字段）、F-12（p0 答案）——全部经 GLM 独立验证接受。
- 「评审必须对照 p0 分支」的方法论（虽然 WB 自己没读 SLICE 文件，但方向正确）。
- D-002 前提需要收窄的方向（尽管收窄本身也需要再收窄）。

## All three may share wrong assumption（三方或四方共同盲区）

1. **「Track B 的 Creative FAIL 存在一个主导根因」**。GPT/Claude 押 Prompt，WB 押 Renderer，GLM 认为这是四因子乘积且 Track B（无 media 题材）在实验设计上就无法分离变量。**三方都在单因框架内竞争，没有人质疑框架本身**。
2. **评审证据基线不包含运行记录**。GPT/Claude（D-003 讨论）基于 main 分支代码，WB 读了 p0 diff 却没读 SLICE 记录，GLM（WB-001 轮同样如此）。Track B 的实测数字（4.3MB、2m08s、MiniMax 两次清单、7:7 结构）推翻或修正了三方各自的部分结论——**仓库里明明有验收文档，但三份评审都没把它当证据源**。 Council Protocol 的「共同事实源」清单应加入 p0-slices 运行记录。
3. **默认现有关卡结构值得修补**。三方都在讨论「Storyboard Gate 应该审什么 / MiniMax 应该怎么改」，没有人提出「当前唯一被证明有效的 creative 信号是人工抽帧」（G-15）——它不在任何 Gate 里，纯属 Track B 执行者的一次自觉动作。若它不被制度化，下一次运行可能就没有这次运气。
4. **没有人质疑 Track B 的选材适当性**。用一份纯文字方法论教程去验收一个「evidence-first 视觉系统」——验收题材与产品核心卖点错配。这不是谁的失误，而是 D-001/Track B 规划期三方都没有提出「验收题材应覆盖 evidence 媒体路径」的要求（Claude D-001 Final 第 4.5 条曾建议 Track B 加数字强调 beat，被采纳了一半——数字有了，evidence 媒体没有）。

## Still unresolved（四视角之后仍开放）

- D-002 的最终顺序决策（现被 G-08 的「切在哪/切几刀」框架重新组织，待用户裁定）；
- Q-004 DeepSeek Red Team 定位与 thinking:disabled 的解耦；
- Q-002 人工修改与 AI 再生成的字段级 merge 合同；
- H4/平台发布（含画幅 Current/Future 分层决策）；
- Track C 的选材标准（GLM 建议明确要求含 evidence 媒体）；
- 三条 UNKNOWN 实测项：word_timestamps、XIAOY_EXPLAINER 模式、3 分钟渲染时长——都是一次实验即可关闭的低成本项。

---

# 给用户的合并建议（仅供参考，非决策）

若只允许保留一份行动清单，GLM 建议的优先级（与 WB-001 的 Highest-Leverage 差异处以 ★ 标出）：

1. **三个低成本实测**（一次各关闭一条 UNKNOWN）：Track B VOICE 的 word_timestamps；Track B 是否 XIAOY_EXPLAINER 模式；3 分钟测试渲染时长。★ 新增，替代 WB 的直接上渲染器改造。
2. **人工抽帧制度化**（G-15）：≥5 指定帧强制人工过目，H3 前置。★ 新增。
3. **Ken Burns + 转场最小改造 + 带素材题材对照运行**（WB F-01 修正版：两臂实验分离题材因子与渲染因子）。
4. **Pose allocator + ACTION_REPETITION QA**（WB F-02，三方共识）。
5. **D-002 按「切在哪/切几刀」双维度重新立项**（★ 替代 WB 的 S1 单线推进建议；p0 既成事实作为显式成本输入）。
