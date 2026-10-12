# Content OS

> **PROJECT STATUS: PAUSED — SEEKING MAINTAINER**
>
> 主动功能开发已经停止。欢迎 Fork、Issue、Pull Request、社区维护与独立演进。原作者不承诺持续维护；本仓库保存的是一套经过真实实验的研究型工程基线，不是已经可日常使用的商业 v1 产品。

**Content OS** 是一个面向知识型自媒体和长视频的 **AI-assisted video production system**。它把 Research、Evidence、Script、Voice、Director、ShotPlan、Storyboard Review、Motion Design、Visual Compiler、Timeline、Remotion、Review 和 Export 拆成可追溯、可审查、可失效、可回退的工程链路。

English: *Content OS is an evidence-first, human-gated AI video production system with semantic shot planning, audio-aware timing, deterministic visual compilation, renderer-neutral artifacts, and explicit review gates.*

## 为什么开发这个项目

把提示词接到视频模型或渲染器上很容易；稳定地生产一条可核验、可修改、具有导演感的长视频很难。项目针对这些反复出现的问题：

- 研究材料、模型总结、事实和脚本主张混在一起；
- 多模型协作增加调用次数，却没有增加事实可靠性或成片质量；
- Director、Compiler 与 Renderer 都在暗中决定画面，责任互相覆盖；
- 镜头像页面模板轮播，角色机械进出，成片呈现 PPT 感；
- 真实 Evidence 被裁坏或非等比拉伸；
- TTS 停顿、ASR 时间戳、语义断句和镜头切点被当成同一个问题；
- 上游产物修改后，下游审批和渲染仍被错误地当成有效；
- 后端脚本可以跑通，但普通用户仍需 Terminal、JSON 和内部 API。

Content OS 的回答是：**AI 负责理解和提出结构化意图；确定性系统负责数值执行；人保留关键审批和发布权。**

## 核心生产链

```text
Research
  → Registered Evidence / Facts / Claims
  → Approved Script
  → Voice
  → DirectorIR
  → ShotPlan
  → Storyboard Review + Human Gate
  → Motion Design Contract (experimental opt-in)
  → Visual Compiler
  → renderer-neutral EDT / Timeline
  → Remotion
  → Final Human Review
  → Export
```

这条链不是一条不可见的自动化管道。重要产物有版本、来源、依赖关系和审批状态；上游变化会使依赖它的下游产物 stale。

## 核心设计思想

### Evidence-first

来源只是来源，模型摘要也只是模型输出。系统显式区分 Source、EvidenceRef、Fact、Claim 与 Approved Script，并要求事实引用可回溯。Evidence 的职责是证明，而不是装饰画面。

### Human-gated

模型自检不等于独立审查，终片确认也不等于发布授权。Storyboard、H3 终片和 H4 发布是不同关卡。自动 QA 可以阻止机械错误或提出风险，不能替人做最终发布决定。

### Deterministic Compiler

Director 选择 **WHAT**：Visual Job、Visual Mode、PRIMARY、Evidence Treatment、Character Role 与 Motion Semantic。Visual Compiler 选择 **HOW**：几何、字号、裁切策略和运动数值。Renderer 执行像素，不重新发明视觉政策。

### Renderer-neutral artifacts

生产事实尽量保存在 schema 化的 DirectorIR、ShotPlan、EDT 与 Motion Contract 中，而不是隐藏在一段由模型即时生成的 Remotion/CSS 代码里。这样才能审查、复现、比较 renderer，并使人工修改有明确落点。

### Audio-first timing

最终音频决定时间事实，但不会自动决定语义结构：

```text
Semantic system decides WHAT.
Alignment decides WHEN.
Compiler decides HOW.
Renderer executes pixels.
```

TTS prosody、ASR/alignment 和镜头/字幕边界属于三个不同问题。Raw Whisper segment 不能直接作为切镜规则。

### Motion Design Contract

“元素支持动画”不等于“镜头具有导演感”。Motion Design 用 FOCUS、EXPLAIN、IMPACT_WARN、CONNECT 等 phrase 表达主次、错相、响应与收束；Compiler 再把定性结构编译成帧和曲线。

### XIAO-Y Evidence Editorial

项目冻结的视觉原则是：

```text
Evidence proves.
XIAO-Y explains.
Typography emphasizes.
Motion guides attention.
```

一个时刻只有一个 PRIMARY。PROVE / DEMONSTRATE 让证据主导；REACT / WARN / TRANSITION / SUMMARIZE 中角色出现必须有明确职责。默认模式是 `BRAND_BALANCED`，保留 `EVIDENCE_HEAVY` 子模式。

## 为什么没有让视频大模型一次生成整片

端到端视频生成适合短片段和开放式视觉探索，但信息型长视频还要求：固定角色身份、真实截图和来源、精确文字、可定位修改、稳定时长、可复现渲染和低成本返工。Content OS 选择固定 XIAO-Y 资产、真实 Evidence、Typography、结构化 ShotPlan 与 Remotion 组合。

这条路线的优点是可追溯、可局部修改、可自动回归；代价是需要设计 contract、素材治理、Compiler 和渲染适配器，也无法自动获得视频生成模型的摄影真实感。本项目保留 creative generation 的研究空间，但没有把 raw generated code/video 直接放进生产主链。

## 架构边界及其原因

| 层 | 负责 | 不负责 | 原因 |
|---|---|---|---|
| Research / Fact | 来源、证据、事实、主张可追溯 | 自动把模型输出升级为事实 | 抵御来源污染与幻觉 |
| Writer | 基于批准事实组织叙事 | 像素和时间线数值 | 保持文字可审查 |
| Director / ShotPlan | 视觉职责与语义意图 | x/y、宽高、CSS、像素裁切 | 防止提示词变成脆弱布局代码 |
| Alignment | 已批准锚点在最终音频中的时间 | 决定是否切镜 | 精度不能替代语义判断 |
| Motion Design | 主次、阶段、错相与收束 | raw frame/easing/scale 数值 | 让运动意图可审查且 renderer-neutral |
| Visual Compiler | 几何、裁切、字号、运动数值 | 改写叙事意图 | 同一输入应得到确定结果 |
| EDT / Timeline | 唯一可编辑时间线事实 | 重新导演内容 | 避免多个时间线互相漂移 |
| Remotion | 确定性像素执行 | 隐藏视觉政策 | Renderer 行为必须与 artifact 一致 |
| QA / Human Gate | 检查、拒绝、批准 | 偷偷修上游内容 | 保持责任与变更历史清晰 |

详见 [Open Source Architecture](docs/OPEN_SOURCE_ARCHITECTURE.md)。

## 当前真实进度

这些状态是不同层级，不能互相替代。

### PRODUCTION IMPLEMENTED

- FastAPI 本地 Workbench、SQLite/文件产物存储与基础状态/权限约束；
- 模型 Adapter / Router、Mock 模式、Keychain/环境变量 secret 边界；
- Source → Fact → Claim → Script 的结构化产物与基础验证；
- EDT、Remotion adapter、preview/render 使用同一 resolved composition；
- XIAO-Y 资产注册、模板/排版/visual pattern registry；
- 基础 QA、artifact provenance、stale/invalidation、Error/Rule 治理骨架；
- 剪映单向导出器的代码路径（这不代表当前样片已经完成剪映交接）。

### EXPERIMENTALLY VALIDATED

- VLA-001 Director → ShotPlan Adapter 与 pre-render Storyboard Gate；
- 注册媒体的等比 contain / cover-crop invariant；
- ATS-001 Sample A post-TTS alignment accuracy；
- TCU-001 timing consumer 验证；
- FAI-001 opt-in alignment runtime 与 fallback；
- MPH-001 Motion Primitive Contract；
- MDC-001 Motion Design Contract；
- `XIAO-Y Evidence Editorial` 的受控视觉实验。

这些实验通过不表示它们已经全部进入默认 Production GUI。

### PARTIALLY INTEGRATED

- 最新 Director / ShotPlan / Storyboard Review 与原 Production Workbench 的完整连接；
- Timeline GUI 和人工覆盖后的依赖失效体验；
- ALIGNED timing（默认仍为 CURRENT，ALIGNED 是 opt-in）；
- Motion Design（默认 disabled / experimental）；
- 视频 QA 与真实多模态 Provider 激活；
- 导出后的真实剪映交接验证。

### PLANNED

- GUI-001：普通用户只通过 GUI 完成整条生产链；
- 长任务后台执行、取消、恢复和可理解的进度；
- 稳定的真实 3–5 分钟连续生产验证；
- 根据真实 expressive gap 决定是否需要受控 Creative Composer。

### NOT STARTED / OUT OF SCOPE AT PAUSE

- 稳定日更能力；
- 自动平台发布和 H4 发布授权闭环；
- 完整 Analytics 学习闭环；
- 无人值守的多租户 SaaS；
- 让大模型直接生成和执行任意 production renderer code。

发布前的净化快照重新验证为 **270 passed, 0 failed, 1 dependency deprecation warning**。这是当前公开快照的实际结果；历史 MDC checkpoint 也曾记录 270 passed，但两者不是同一次运行。详见 [Security Audit](OPEN_SOURCE_SECURITY_AUDIT.md)。

## 已解决的重要问题

- 用严格 producer/consumer contract 消除了“schema 声称支持、Renderer 没有消费”的能力幻觉；
- 发现并修复真实 Evidence 非等比拉伸，新增机械 BLOCKER；
- 将 timing truth、semantic boundary、TTS prosody 拆开；
- 证明更准 timing 只有在下游 consumer 实际使用时才有价值；
- 把 Motion Primitive 与 Motion Design 分层，引入主次、错相和 settle；
- Storyboard Gate 绑定 exact ShotPlan/hash，避免批准旧版本；
- 通过 integration baseline 处理并行分支重新引入旧缺陷的问题；
- 将私有声音、模型、字体、真实 Provider 快照与公开源代码分离。

## 仍未解决的问题

最大的未完成项是 **GUI-001 / GUI-only E2E**。当前代码和实验并不等于普通用户能在一个工作台内稳定完成：

```text
Create Project → Research → Script → Voice → Director → ShotPlan
→ Storyboard → Render → Review → Export
```

如果过程仍需要 Terminal、手改 JSON、内部 API、数据库 patch 或 Remotion CLI，就不能宣称产品闭环完成。详细接手顺序见 [Maintainer Handoff](docs/MAINTAINER_HANDOFF.md) 与 [Roadmap](docs/OPEN_SOURCE_ROADMAP.md)。

## 工程错误与教训

[Lessons Learned](docs/LESSONS_LEARNED.md) 记录了 17 类真实问题，包括多模型失效、PPT 感、职责漂移、asset distortion、Whisper 误切、timing 无消费、motion 声明与实现不一致、静态 Storyboard 的盲区、分支回退、GUI 验收缺口和范围失控。实验二进制证据因隐私或授权没有公开；结构化结论、测试与必要 contract 保留在仓库中。

## 为什么项目暂停

核心架构没有被证伪，多个实验反而证明了边界设计的价值。暂停来自工程现实：链路太长、单人维护成本高、工具生态快速变化、继续扩展的边际收益下降，而产品最关键的 GUI-only 闭环仍需要集中投入。继续堆模型或功能会扩大维护面，不能替代产品收口。

## 本地安装

要求：Python 3.12+、Node.js 20+、npm、可选的 Chrome/Chromium 与 ffmpeg。真实 Provider、真实 TTS、Whisper 模型、第三方字体、用户媒体均未随仓库分发。

```bash
git clone https://github.com/haiyang776688-web/content-os.git
cd content-os

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd vnext/renderers/remotion/project
npm ci
npx tsc --noEmit
npm run build:monitor
cd ../../../..

CONTENT_OS_TEST_NO_KEYCHAIN=1 python -m pytest vnext/tests tests -q
CONTENT_OS_DATA="$PWD/data" uvicorn vnext.apps.workbench.server:app --host 127.0.0.1 --port 8766
```

打开 `http://127.0.0.1:8766/`。没有 API key 时可使用 Mock 路径验证系统 contract。真实 Provider 请复制 `.env.example` 的字段到本机环境或使用系统 Keychain；不要提交 `.env`。

### 可选能力

- Remotion 正式渲染可能需要已安装的浏览器；可用 `REMOTION_BROWSER_EXECUTABLE` 指定。
- Alignment 需要外部 ASR runtime/model；模型权重不会自动随仓库分发。
- 本地 TTS 需要实现 JSON argv bridge，并通过 `CONTENT_OS_LOCAL_TTS_COMMAND` 配置；公开仓库不含克隆声音参考。
- Jianying 只支持单向导出，且需要用户本机合法安装和草稿目录。

## 仓库导航

- `vnext/`：核心代码、Workbench、Provider、Compiler、Timeline、QA、Renderer adapter；
- `contracts/`：跨层 schema；
- `registries/`：模型、prompt、skill、style、asset、voice 示例注册表；
- `assets/`：项目所有者确认可公开的 XIAO-Y 原创资产；
- `fixtures/`：合成或脱敏测试输入；
- `docs/project-brain/`：项目事实、决策与历史讨论；
- `docs/project-brain/creative-spikes/`：实验范围、方法、结构化结果；
- `docs/`：架构、经验、路线与维护交接；
- `examples/`：脱敏结构化历史输出；不含原私有音视频和多数截图。

本机研发分支、遗漏与发布快照选择记录见 [Local Project Inventory](LOCAL_PROJECT_INVENTORY.md)。

## 许可证与资产

源码和项目自有文档使用 [MIT License](LICENSE)。第三方依赖保留各自许可证。XIAO-Y 素材由项目所有者确认为项目原创并随本仓库按 MIT 提供；其他外部素材、模型、声音、字体、平台软件不因本仓库的 MIT 自动获得重新授权。完整边界见 [Asset Notice](ASSET_NOTICE.md)。

## 贡献

欢迎接手，但请先阅读 [Contributing](CONTRIBUTING.md)、[Architecture](docs/OPEN_SOURCE_ARCHITECTURE.md)、[Lessons](docs/LESSONS_LEARNED.md) 与 [Maintainer Handoff](docs/MAINTAINER_HANDOFF.md)。

第一优先级是 GUI-001，不是增加新模型。涉及视觉、Timing 或 Renderer contract 的修改应附机械测试、人工审查说明、输入版本/hash 和回归结果。

安全问题请遵循 [Security Policy](SECURITY.md)，不要把真实凭据或私人媒体放进公开 Issue。
