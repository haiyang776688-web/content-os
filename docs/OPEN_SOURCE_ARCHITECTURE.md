# Open Source Architecture

本文记录 Content OS 在暂停开发时最重要的架构结论。它不是“理想蓝图”，而是经过多轮真实实验后仍然保留下来的边界。

## 1. Evidence pipeline

```text
Source
  ↓
EvidenceRef
  ↓
Fact
  ↓
Claim
  ↓
Approved Script
```

核心原则：外部来源是数据，不是指令；模型总结不能自动升级成事实。

## 2. Semantic planning

```text
Approved Script
  ↓
DirectorIR
  ↓
ShotPlan
```

Director 负责：
- Visual Job（证明、演示、解释、比较、反应、警告、转场、总结）；
- Visual Mode；
- semantic focus；
- Evidence / XIAO-Y 的责任关系；
- motion semantic。

Director 不负责：
- x/y；
- width/height；
- crop px；
- font size；
- CSS；
- scale；
- easing；
- spring 参数；
- raw animation code。

## 3. Storyboard as a real gate

Storyboard Review 不是一个缩略图列表，而是对 ShotPlan 的人工审查层。

审批必须绑定 exact ShotPlan SHA。修改 ShotPlan 后审批失效。DRAFT / REJECT / hash mismatch 都应阻止最终 Render。

## 4. Visual Compiler owns geometry

Visual Compiler 是几何与数值实现的唯一 owner。

同一个语义输入应该得到确定性的 layout / motion artifact。Renderer 不重新决定构图。

## 5. Asset aspect-ratio invariant

真实媒体（截图、图片、视频、角色 PNG、logo、B-roll、imported SVG）只能：

- contain；
- uniform cover + crop；
- uniform focus zoom / pan。

禁止独立 scaleX / scaleY。

Procedural geometry（线、箭头、矩形、生成 SVG path）可以按需要形变。

这个 invariant 来自一次真实事故：早期 CropImage 分别使用 source region width / height 反向缩放，导致截图被非等比拉伸。后来加入机械 BLOCKER：`ASSET_ASPECT_RATIO_DISTORTED`。

## 6. Audio timing architecture

Content OS 最终把三个经常混淆的问题拆开：

### Timing truth
“某个已批准文本锚点在最终音频的什么时候发生？”

使用 post-TTS ASR timing + transcript alignment 可以提供更精确的 WHEN。

### Semantic policy
“这里到底该不该形成 Beat / Shot / subtitle boundary？”

这不能由 raw ASR segment 决定。

### Prosody
“voice.wav 本身为什么在这里错误停顿？”

这是 TTS / prosody 问题，不是 timing consumer 能修复的。

最终原则：

```text
Semantic system decides WHAT.
Alignment decides WHEN.
```

## 7. Motion Primitive Contract

早期系统存在“schema 声称支持，但 Renderer 实际没消费”的能力幻觉。

MPH-001 后建立权威 contract：每个 declared primitive 都必须有真实 Renderer consumer，且 primitive/layer 组合必须明确允许。

最终验证过的 primitive 包括：

- NONE
- PUSH_IN
- FADE_IN
- FOLLOW_PATH
- MATCHED_WIPE
- POP_CUT
- RETURN_TO_ANCHOR
- DRAW_CONNECTION
- SETTLE_HOLD
- DRAW_UNDERLINE
- LABEL_REVEAL

未知 primitive 或不支持的 layer 组合必须 fail-fast，不能静默退化成 NONE。

## 8. Motion Design Contract

“primitive 会动”不等于“镜头有导演感”。

MDC-001 增加 renderer-neutral Motion Design：

```text
Director / ShotPlan
  ↓
Motion Design Contract
  ↓
Visual Compiler
  ↓
Motion Primitive Contract
  ↓
Renderer
```

最小 phrase：
- FOCUS
- EXPLAIN
- IMPACT_WARN
- CONNECT

动态阶段：
- ANTICIPATION
- PRIMARY_ACTION
- IMPACT
- SECONDARY_RESPONSE
- SETTLE
- HOLD

Motion Design 只描述定性结构、主次责任、相位顺序、强度；frame、offset、curve、scale 数值仍由 Compiler 决定。

## 9. ONE PRIMARY

一个镜头可以有多个元素，但只能有一个主要视觉责任。

Evidence proves. XIAO-Y explains. Text emphasizes. Motion guides attention.

“所有元素一起动”是最常见的 AI PPT 来源之一。

## 10. Human gate hierarchy

系统的自动 QA 只能发现机械问题或给建议，不应该自己给自己最终批准。

关键 artifact 修改后必须使下游审批 stale。

## 11. Renderer-neutral artifacts

系统尽量让生产事实落在结构化 artifact，而不是大模型生成的 Remotion / Canvas / SVG 源代码。

Creative code generation 未来可以存在于 sandbox，但进入生产路径前应转换成可审查、hash-pinned、renderer-neutral 的 data/artifact。

## 12. Production defaults at pause point

项目暂停时：
- timing default = CURRENT；
- ALIGNED = opt-in；
- Motion Design = experimental opt-in / default disabled；
- Production GUI integration of latest vNext path = not finished；
- GUI-only E2E = not finished。

这几个事实不要在 fork 中被 README 的旧历史描述覆盖。
