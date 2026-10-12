# VGB-001 · Visual Gold Benchmark

Date: 2026-09-29
Status: EXPERIMENT / AWAITING_HUMAN_VISUAL_CHOICE
Repository: `haiyang776688-web/content-os-vnext-phase1`
Branch: `p0/visual-gold-benchmark-1`
Implementation baseline: `p0/visual-progression-spike-1@e5f72dabe784ed5bed276b86e49a78df5d97a8b4`

## 本轮要证明什么

先制作三条可以直接观看、彼此明显不同的短片，让用户选择 `A / B / C / NONE`。这是寻找视觉目标的实验，不是对现有架构的证明，也不是正式 Gold Master 已经成立的声明。通过渲染、测试或代理自评，均不能替代用户选择。

用户已经明确否定 Track B、CS-001、VPS-001 A 与 B 的观看效果。VPS B 虽然更可读，仍被认为是“更容易看清的 PPT”。旧 VPS `04_RESULTS.md` 的 `Human visual-model verdict: PASS (BETTER)` 是前轮代理给出的相对评价，**不是用户视觉批准**；该历史记录保留，本轮不把它作为合格基准，也不继续称它为 Human PASS。

三方向仅改变视觉语言：

- **A — Evidence-first Product Documentary：**真实 Workbench 像素为主，镜头按解说聚焦证据区域，人物缺席或极少出现。
- **B — XIAO-Y Editorial Hybrid：**白、黑、红、黄品牌语言；人物承担引入、反应或转折，证据出现时让出主角位置。
- **C — Kinetic Editorial Explainer：**把同一证据拆成局部、关系与引用标记，用空间关系及连续运动解释逻辑，避免整张网页长期停留。

方向名称是创作假设，不是完成后的质量结论。三版的逐镜理由、像素检查及定性比较另见 `02_DIRECTION_A.md` 至 `06_RECOMMENDATION.md`。

## 冻结输入与时间

| 项目 | 本轮固定值 |
| --- | --- |
| 原项目 | CS-001 `PRJ-951fb6b86911` |
| 原视频 | `RUN-dda8992671.mp4`，88.896 秒，1920×1080 / 30 fps |
| 连续源区间 | **5.56–24.68 秒，19.12 秒** |
| Script | `ART-278087e926034f3b`，`SEG-02`、`SEG-03`、`SEG-04`；不改旁白文字 |
| Voice | `ART-7ef0a1a38f894364`，同一现有本地克隆声音的 5.56–24.68 秒区间；不重新调用 TTS、不拉伸、不换声音 |
| Audio clock | `ART-661d1f96d1054fe8`；已测量 segment 边界，无 word timestamps；镜头与短字幕切点是手工语义锚点，不声称逐字强制对齐 |
| 事实 | 原 CS-001 已确认事实及该脚本的既有主张；不新增事实，不改变支持范围 |
| Source screenshots | `fixtures/creative-spike-1-evidence/research.png`、`script.png`；与 CS-001 / VPS-001 同源 |
| 视频格式 | 三版均为 1920×1080、30 fps、574 frames |
| 可改变 | 构图、镜头尺度、证据裁切、标注、信息层级、人物角色、转场和叙事运动 |

574 frames 对应视频轨 19.133333 秒；19.12 秒是冻结的源内容区间，两者不可混写。最终三个 MP4 的容器探测时长均为 19.178667 秒，解码音轨一致。技术检查范围、观看限制及未达 Gold Master 的评价见 `05_COMPARISON.md`；技术通过不代表视觉批准。

选择这一段，是因为它连续包含本地资料导入、候选与已核实事实的区别、人工把关、事实与来源绑定、脚本引用要求；两个真实截图均有关联，同时旧版 PPT 感十分明显。它允许比较视觉处理，而不需要更换题材、重写文本或新增证据。

## 已阅读与实际观察

本轮阅读 `PRODUCT_TASTE.md`、`CURRENT_STATE.md`、`IMPLEMENTATION_STATE.md`、`COUNCIL_SYNTHESIS_2026-09-29.md`、整个 `C-2026-09-29-claude-synthesis-review/`、`SKILL_ABSORPTION_MATRIX.md` 及 CS-001 / VPS-001 的全部实验文档。旧文档的实现描述须对照其基线，不能默认仍是当前代码状态。

实际视频检查覆盖：

- CS-001 88.896 秒 master：全片每 0.5 秒连续取样，共 178 帧。
- VPS A、B、motion-off：各全片每 0.5 秒连续取样，各 38 帧。
- 查看原尺寸重点帧，包括 CS-001 的 9.8 秒、24.3 秒，VPS B 的 8 秒和 motion-off 的 16 秒；结合完整 timeline、脚本和字幕切点检查。CS-001 24.3 秒附近的 `t ID` 碎片是实际像素问题。
- 独立审阅另查看两张源截图、VPS B 全段 contact view 及导入区域、Fact ID 区域的 1080p 关键帧。

**观看限制：**本轮基线复核没有完成实时、连续的声画播放。密集连续抽帧、原尺寸关键帧和完整 timeline 可以支持对构图、可读性、静态停留及字幕碎片的判断，不能冒充对全部亚秒转场、声音感受和连续观看体验的完整验证。用户最终观看三条 MP4 并选择仍是必需步骤。

## 证据表达边界

`research.png` 显示的是空的本地文件导入控件，仍写着 `No file chosen`；不能据此编造上传完成或候选确认前后的真实 UI 状态。`script.png` 中“保留真实 Fact ID”位于可编辑的脚本方向输入框；它证明这次创作指令可见，不单独证明程序已执行引用校验，也不是 Fact Pack 内部页面。

可以保留原像素作裁切、聚焦、标注，也可以用明确的解释图示表达原旁白中的关系。解释图示不得伪装为已经发生的软件操作、真实确认结果或不存在的 before/after 截图。更具体的限制见 `01_CURRENT_FAILURES.md`。

## 实施边界

本轮允许专用、手工设计的 Remotion composition，暂时绕开 DirectorIR、模板分配器、VisualResolver 和 VisualProgression 编译器。代码仅服务这三条实验片，不接入生产入口，不写入原生产项目状态或修改既有产物。

只吸收与本次画面有关的研究原则：证据优先、解说驱动画面、语义拍、单一视觉主角、证明/演示/比较、镜头连续性、信息递进、XIAO-Y 身份一致性和人工创作判断。不把整套 Skill 或平台运营规则塞入 Prompt。

以下明确不做：全长 88 秒重做、Track C、Full Audio-first、Narration Units、HyperFrames 迁移、完整 PromptComposer、Platform Profile、9:16、Analytics、Publish、D-002 / D-003 Final、`DECISIONS.md` 修改。`main` 不变，不 force push。

用户选择前不为 DirectorIR、Beat、Resolver、模板系统、VisualProgression、Remotion Composition、动作分配器、各 QA 或 Storyboard Gate作 KEEP / MODIFY / REPLACE / DELETE 决定。三条手工片即使获得偏好，也不自动证明 AI 能复现、GUI 能编辑或已具备稳定日更能力。

## 交付与裁决

交付三条 MP4（A/B/C）、三份逐镜 shot list、同源/时长/音频/字幕检查和十个维度的 `STRONG / GOOD / WEAK / FAIL` 定性比较。shot list 必须解释每镜新增的视觉信息及运动目的，不能只写“把配音变成大字”。

最终代理可以推荐 `A / B / C / NONE`，必须给具体理由，不能把推荐写成批准。**只有用户明确选择后，才进入所选视觉语言的反向拆解；本轮停在 Awaiting human visual choice。**
