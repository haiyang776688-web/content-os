# Content OS Council 综合复核 · 2026-09-29

**Status:** PROVISIONAL_SYNTHESIS_FOR_CLAUDE_REVIEW  
**性质:** Project Brain / Council 证据整合，不是正式 Decision，不修改 `DECISIONS.md`。  
**知识基线:** `main@504ecc4da97d1b6adabbb09cebf29facda844d27`  
**实现基线:** `p0/gui-only-e2e-interim@323f7a2376efcfcfd1643a3e9d15333e084c1739`  
**merge base:** `674957813b5efea39e8cc3e61621245808ccacc7`

本文件把 D-001 / D-002 / D-003、Track B、WB-001、WB-002 以及 2026-09-29 的代码复核合并为一份可供 Claude 再审的当前结论。凡未被代码、运行记录或真实产物直接支持的因果判断均标为 HYPOTHESIS / PROPOSAL。

---

## 1. 证据优先级

本轮采用：

`当前代码 / commit / test / artifact / p0-slices 运行记录 > 当前 Project Brain > 历史样片/历史讨论 > 模型结论 > 模型推测`

特别要求：

- Track B 与 84–85 秒历史 regression sample 必须分开；
- `main` 知识层与 `p0/gui-only-e2e-interim` 实现层必须分开；
- Framework limitation 与 Content OS current implementation limitation 必须分开；
- `FACT` 不得直接升级成 root-cause conclusion。

---

## 2. Reviewer 身份更正

### FACT

`WB-002-glm53-independent-review` **不是由真实 GLM 5.3 执行的独立模型评审**。

WB-002 的 `00_SCOPE.md` 已主动更正：

- WB-001 与 WB-002 为同一个 WorkBuddy 延续会话；
- 底层模型未实际切换为 GLM 5.3；
- 严格 Blind Review 因上一轮上下文可见而不能物理成立；
- WB-002 的价值应解释为「同一模型在更严格证据方法下的第二次复核」，而不是 Hunyuan4 vs GLM 5.3 模型能力比较。

因此：

- WB-001 / WB-002 的代码证据仍可使用；
- `03_MODEL_COMPARISON.md` 不应作为模型族性能比较证据；
- 真正的模型多样性目前仍主要来自 GPT / Claude 与 WorkBuddy 这一第三席，而非 WB-001 / WB-002 两个席位互相独立。

---

## 3. Track B 当前事实

### FACT

Track B fresh GUI run：

- 7 script segments；
- 7 Director beats；
- Voice 61.400s；
- final MP4 61.461333s；
- 1920×1080 / 30fps；
- 约 4.3 MB；
- real DeepSeek Research / Script；
- real GLM Audit / Director；
- local cloned voice；
- Remotion render；
- real MiniMax-M3 VISUAL_ONLY QA；
- Engineering PASS；
- Creative FAIL / pending redesign；
- H3 为 `P0_TEST_HARNESS` 测试记录，非用户创作批准；
- H4 未授权。

Track B Creative FAIL 的已观察现象：

- slide/PPT-like 稀疏感；
- 大面积白底 + 少量文字；
- XIAO-Y pose 重复；
- platform overlay / occlusion demonstration 不足；
- text-only reveal 偏快；
- rhythm / balance 不足。

Track B 的题材是纯方法论教程，运行记录未显示实际导入平台截图或视频 media。代码中当项目没有 media asset 时，需要 `media_asset_id` 的 Director patterns 会从允许集合中移除。

---

## 4. Creative FAIL：当前最佳解释

### FACT：已确认的结构性限制

#### 4.1 Director 实际控制权较窄

`director_contract.py` 当前：

- `template_id = null`；
- `semantic_pattern = null`；
- `motion_intent` 仅 `HOLD / FADE / SLIDE_UP`；
- layout 最终由 Resolver 决定；
- Director 可决定 pattern、slots、character intent/action（若显式给）、element、timing intent 等，但不能直接决定 geometry。

所以「Director = visual truth owner」目前是设计意图，实际控制面尚不完整。

#### 4.2 VisualResolver 存在 deterministic collapse

当 Director 未显式给 `character_action_id` 时：

`VisualResolver -> next(first semantic_intent match)`

同一 intent 会稳定回到首个匹配动作。当前没有 deterministic allocator / rotation / diversity budget。

Mechanical QA 只在所有 beat 使用同一 motion 或所有 beat 都是同一 keyword pattern 时告警，没有「部分 pose 连续重复」检查。

#### 4.3 当前 Remotion Composition 的运动词汇很少

当前 `Composition.tsx` 主要实现：

- reveal opacity；
- SLIDE_UP；
- 小幅 scale-in；
- marker / underline draw；
- video/image/text/character 基础显示。

没有实现完整的：

- beat 内持续 pan/zoom；
- camera state；
- beat-to-beat transition；
- 丰富 temporal visual grammar。

**这属于 Content OS 当前 renderer implementation limitation，不是 Remotion framework limitation。** Remotion 本身能实现更复杂的逐帧动画。

#### 4.4 多个语义字段没有进入 pixels

已确认 Beat / Scene 中存在多个生产代码不消费或消费不足的字段，例如：

- purpose；
- visual_focus；
- visual_form；
- retention_function；
- density；
- tempo；
- scene narrative / retention related fields。

因此 D-003 若继续增加 `visual_job / cognitive_change / viewer_should_notice` 等字段，必须同时定义 Resolver / QA / Renderer 的消费点，否则会成为新的 write-only fields。

#### 4.5 Storyboard Gate 对 temporal quality 输入不足

当前正式 Storyboard Gate 主要审核每 beat 的静态 stills；虽然有 motion preview 路径，但并非正式 Gate 必要输入。

所以它适合发现 geometry / composition 问题，却不能可靠提前发现：

- rhythm；
- transition；
- continuous motion；
- 长时间静态停留；
- 整片 PPT 感。

### HYPOTHESIS：根因不是单一 Prompt 或单一 Renderer

当前最合理的 root-cause model 是多因子：

`题材/证据供给 × Director 控制权 × Resolver 映射 × motion/pattern vocabulary × QA/Gate 可观察性`

因此当前不支持以下任何单因结论：

- 「主要就是 Prompt」；
- 「主要就是 Remotion」；
- 「主要就是 Renderer」；
- 「只要多加 XIAO-Y 动作就会解决」。

下一轮实验应主动分离变量。

---

## 5. D-002 Audio-first：问题重新定义

### FACT

当前 Voice 在 Director / Storyboard 后生成，但 `AudioTimingMap` 已经把 script segment 的真实起止时间绑定到最终 EDT。

Track B 是：

`7 segments : 7 beats = 1:1`

所以 Track B 的 beat 外边界已经等于真实 segment audio boundary；它本次不存在 1:N beat 的段内比例切分误差。

### FACT

在 1:N 情况下，当前 `AudioClock.retime()` 会按各 beat 的 `timing_intent` 比例分配同一 segment 内的真实音频时长。

字幕在 aligned phrase 内仍存在按字符比例拆分的路径。

`phrase_id`、`word_ranges` 等结构存在，但其是否在 Track B 真实 Voice 中可用仍需运行数据确认。

### 当前应比较的三个方案

#### A. Current retime

解决：

- segment 真实外边界；
- 当前 Track B 1:1 beat 边界。

不解决：

- 1:N 段内真实语义切点；
- Director 在听到/知道真实时长前决定 beat 密度的问题。

#### B. Phrase / word anchor

主要解决：

- 「切在哪里」。

需要先确认：

- Track B / 当前本地 TTS 是否实际返回可用 word timestamps；
- 若没有，是否采用 forced alignment。

#### C. Full Audio-first / Voice-before-Director

额外可能解决：

- 「切几刀」；
- Director 基于真实语速、停顿、duration 决定 beat 数与 visual pacing。

### PROPOSAL

D-002 Spike 不应只比较「旧顺序 vs Audio-first」，而应比较：

`A current retime vs B anchor-based vs C full audio-first`

并分别测：

- beat boundary accuracy；
- beat density；
- storyboard返工；
- Director visual quality；
- implementation / invalidation cost。

Narration Units 是否需要独立 Artifact 仍未证明；优先测试现有 Script segments + phrase/word binding 是否足够。

---

## 6. MiniMax Visual QA：重新定位

### FACT

当前 GUI Visual QA：

- MiniMax-M3 单点多模态路径；
- silent video；
- `fps=1`；
- system prompt 很薄；
- 0 issue => PASS；
- 任一返回 timestamp 越界可使整次 QA 失败；
- context 包含 Script / DirectorIR / 简化 EDT。

### 运行证据

Track B 两轮 MiniMax QA 实际能发现：

- text crowding / truncation；
- repeated text；
- white-space balance；
- missing concrete platform demonstration；
- tight reveal 等。

84 秒历史 regression sample 则存在多条时间定位/beat 归属错误；这是 **HISTORICAL REGRESSION EVIDENCE**，不能直接当成 Track B 的事实。

### 当前定位

MiniMax @ 1fps 可以继续承担：

- static composition；
- text density；
- whitespace / visual balance；
- semantic mismatch / missing evidence 的部分判断。

不应依赖其可靠判断：

- sub-second reveal；
- transition smoothness；
- micro motion；
- temporal rhythm。

### PROPOSAL

- deterministic QA 负责能程序判断的 temporal / repetition / geometry；
- MiniMax 负责语义与静态视觉质量；
- Human 负责最终观看体验；
- 后续再 A/B 测更高 fps / segmented motion sampling 是否值得成本。

---

## 7. 长视频 Track C 风险校正

### FACT

WB-001 的「3–5 分钟三个硬 blocker」需要修正。

#### 45MB MiniMax inline limit

Track B：

`4,309,544 bytes / 61.461s ≈ 70 KB/s`

另一个约 93 秒样片约 74 KB/s。

按现有码率粗略外推：

- 3 分钟约 13 MB；
- 5 分钟约 21–22 MB。

所以 **45MB 当前不是 3–5 分钟已证明 blocker**。

#### Storyboard stills

14 stills / 28s、42 stills / 67s 的运行记录表明它会线性变慢，但目前没有证据证明 3–5 分钟会直接失败。

#### Render timeout

当前 renderer timeout 为 300s。

Track B 61s 视频约 124–128s render。若近似线性，3 分钟可能触碰/超过 300s，但这只是 HYPOTHESIS。

### 必做实验

在宣称 Track C 稳定或 blocker 前，直接跑一条约 3 分钟测试 render，记录：

- wall time；
- peak memory；
- file size；
- storyboard time；
- QA input size。

---

## 8. Subtitle / Renderer 真源漂移

### FACT

P0 为修复白底白字幕，`Composition.tsx` 已无条件给 subtitle 文本绘制深色背景衬底。

但 Mechanical QA 仍检查 EDT metadata 中：

- `SUBTITLE_BACKGROUND`；
- `SUBTITLE_COLOR`；
- `SUBTITLE_BASELINE`。

渲染器添加的衬底没有进入 EDT metadata，所以 QA 看不到这个视觉决定。

### 风险

这形成：

`EDT / QA 规则 != 最终 pixels`

并与「EDT 是唯一可编辑时间线」的方向产生张力。

### PROPOSAL

最终视觉政策（subtitle plate / background / opacity / style）应进入可追踪的 renderer-neutral config / EDT projection，而不是长期硬编码在 `Composition.tsx`。

---

## 9. Prompt Governance 的修正原则

D-003 仍然成立，但实施顺序需要调整：

1. 先统一 Prompt invocation path；
2. PromptComposer 成为唯一组装点；
3. schema 只发送一次；
4. Role Prompt 只承担真正需要 LLM 判断的岗位标准；
5. deterministic 的事情不要继续塞 Prompt；
6. 新语义字段必须先有消费点；
7. 给 CURRENT_RULES / Skill Snapshot 设置 budget / relevance selection；
8. qualification suite 用来验证 Prompt，而不是持续增加 production prompt 长度。

所以：

**D-003 不是取消，而是从「写更厚 Prompt」升级为「Prompt + deterministic + resolver consumption 的职责闭环」。**

---

## 10. 当前确认的高价值问题

优先级不代表正式 Decision，只代表信息增益 / 风险收益比。

### P0 / Creative

1. XIAO-Y first-match allocator；
2. partial action/pattern repetition QA；
3. Director semantic -> Resolver -> pixels 消费链；
4. motion vocabulary；
5. motion-aware Storyboard Gate；
6. evidence/media-bearing test topic；
7. subtitle renderer/QA truth drift。

### D-002

8. Track B word timestamps 是否真实存在；
9. anchor vs audio-first 的「切在哪 / 切几刀」实验。

### Track C

10. 3-minute real render timeout test；
11. segment-level Voice cache / invalidation economics。

### D-003

12. Prompt invocation unification；
13. write-only fields audit；
14. prompt size / rules budget；
15. Visual QA rubric + clip binding + graceful invalid timestamp handling。

---

## 11. 当前不应做的事

- 不因 PPT 感直接更换 Remotion；
- 不因为 HyperFrames 更 Agent-friendly 就立即迁移 renderer；
- 不直接把 WB-001 的 Renderer root-cause 写成 Decision；
- 不把 WB-002 当真实 GLM 5.3 独立评审；
- 不把历史 84 秒 MiniMax 错误率当 Track B 错误率；
- 不把 45MB 当 3–5 分钟 blocker；
- 不因未来抖音/小红书/视频号而把 9:16 当当前 P0 bug；
- 不继续添加没有消费点的 DirectorIR 字段；
- 不在 Claude Review 前修改 `DECISIONS.md` 或关闭 D-002 / D-003。

---

## 12. 给 Claude 的复核问题

Claude 下一轮请重点攻击以下结论，而不是重新泛读全部项目：

1. 多因子 Creative FAIL 模型是否遗漏关键因子？Track B 无 media 是否被高估或低估？
2. Director 控制权应扩大到什么层级？是否应该让 LLM 选择 template，还是保持 semantic-only 后由 deterministic Resolver 选 variant？
3. `visual_job / cognitive_change` 等字段是否值得存在？每个字段的明确消费点是什么？
4. first-match pose 的 owner 应归 Director、Resolver 还是二者共同？最佳 deterministic allocator 合同是什么？
5. D-002 的「切在哪里 vs 切几刀」框架是否成立？Full Audio-first 的独有收益是否被正确描述？
6. Track B 7:7 是否足以说明本次 beat alignment 精确？还有没有别的 timing mismatch 被忽略？
7. MiniMax 的「static useful / temporal weak」定位是否合理？1fps 下哪些 temporal dimensions 仍然能可靠判断？
8. 3–5 分钟风险校正是否正确？300s render timeout 是否真应是 Track C 第一实测项？
9. subtitle background 的 renderer-only 决策是否真的违反 EDT truth，还是可以合法属于 Renderer policy？
10. Prompt Governance 下一步应先修 invocation architecture、semantic consumption，还是 Role Pack 内容？
11. 当前有哪些 WorkBuddy finding 虽然代码事实正确，但 severity / causality 仍被高估？
12. 是否应该在 Council Protocol 中强制纳入 `p0-slices` / acceptance records，并验证 reviewer/model identity？

---

## 13. 状态

- D-001: OPEN / synthesis 未正式完成；
- D-002: OPEN；
- D-003: OPEN；
- WB-001: Review evidence；
- WB-002: same-model second-pass review evidence，**not real GLM 5.3 comparison**；
- 本文件: **等待 Claude Review**；
- `DECISIONS.md`: 未修改；
- business code: 未修改。
