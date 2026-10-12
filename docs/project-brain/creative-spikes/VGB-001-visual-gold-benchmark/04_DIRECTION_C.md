# Direction C — Kinetic Editorial Explainer

Status: REVIEW_SAMPLE / awaiting human choice. This document is an experimental visual treatment, not a design decision.

## Intent

深墨底、黄色引文标记、原始界面裁片与可读的关系动画。主角是一条引文从来源到脚本引用的关系；它不会因为旁白进入下一句就被另一张页面替换。XIAO-Y 仅在人类确认关口出现约 1.5 秒，不承担持续站台。

固定源区间：CS-001 5.56–24.68 秒，源内容 19.12 秒；视频轨 574 frames / 30 fps = 19.133333 秒，最终容器 19.178667 秒，与 A/B 相同。同原脚本、同已生成配音、同事实及 research/script 原截图，字幕与 A/B 共用。无新配音、无字词级时间精度声明。

## Evidence boundary

- research.png 只能证明存在本地文件导入入口。画面未显示已选文件、模型候选或成功确认；本方向不会伪造这些 UI 状态。
- script.png 的方向文本包含保留 Fact ID 的要求。它不证明某一声明已经匹配或核验成功。
- 所有候选、人工关口、Fact Pack 双向关系都是标明“流程示意”的讲解图形。最终回到“原始界面 · 脚本要求”。
- 保留同一真实截图的不同裁片，不通过重新绘制模拟证据。

## Shot list

时间为样片相对时间。动作均由帧号驱动、可随机定位；字幕由共享层呈现，以下屏幕词只承担关键词和关系标记。

| Start–end | Narration | Protagonist | Primitive | Evidence | Camera / motion | Screen text | XIAO-Y role | Why / 新增视觉信息 |
|---|---|---|---|---|---|---|---|---|
| 0.00–2.91 | 研究页允许从本地文件导入资料 | 真实导入入口 | 宽幅 UI 细节 + 边角定位 | research 原像素 | 入口轻推近，黄色边角沿实际导入区描出；末尾证据向上退出 | 入口，在这里 | 无 | 指出导入发生在哪里，保留 No file chosen 的真实状态 |
| 2.91–6.24 | 模型提取的原文候选需要操作者确认 | 黄色引文标记 | 引文移动 / 关系图 | 流程示意（非捕获候选） | 引文由左移向关系边界；连接线向 Fact 延伸，尚未建立事实状态 | 确认之前 / 候选引文 | 无 | 把“来源文字”和“事实”分成两个不同对象 |
| 6.24–9.87 | 候选引文不会自动成为已核实 Fact | 被截断的关系 | 否定捷径 / 因果剪切 | 流程示意 | 连接后半段消失，红色斜线切断自动升级；引文仍留在候选侧 | ≠ | 无 | 明确排除自动成为事实的错误理解；动作改变关系 |
| 9.87–11.88 | 这一步必须由人来把关 | 人工关口 | 全高边界 / 字体尺度变化 | 流程示意 | 候选与 FACT 的关系退场，黄色门槛竖起；门保持关闭 | 确认权 | serious 在 10.20–11.70 短暂标点 | 展示确认权归属，没有制造“已批准”的状态 |
| 11.88–15.42 | Fact Pack 把选中的事实与来源绑定 | 来源与事实的双向连接 | 关系构造 / 原 UI 裁片 | research 真实裁片 + 显式示意 | 上行连接画出，再反向画出回溯路径；引文回到来源一侧 | 溯源 / 来源 / FACT | 无 | 两条有方向的线分别表达选入与可回溯，不只是框体位移 |
| 15.42–19.12 | 脚本里的事实性主张要引用已有 Fact ID | 原要求中的 Fact ID | 匹配转场 / 放大证据 | script 原始方向字段裁片 | FACT 成为 FACT ID，原始字段进入占据中部，边角括住整段要求 | FACT ID / 引用要求 / 脚本方向·原始截图 | 无 | 将抽象关系落回真实界面文字；画面称作“要求”，不显示核验成功 |

## Why this is distinct

相比 A 的证据浏览和 B 的白底角色主持，C 把一段内容变为一条关系的建立、否定、人工边界、来源回溯、文字落点。截图不是全段背景；它分别作为起点与落点的凭据。中段的视觉对象和动作承担解释。

## Risks before human review

- 抽象关系图的比例高于 A/B；用户可能仍感到解释图形而不是实录，须由实际观看判断。
- 没有成功导入或候选确认的真实状态截图，无法用证据证明完整操作发生。
- 深色画面强化证据和黄色标记，但与用户白底 XIAO-Y 原图存在明显风格距离；这是有意测试的不同方向，未经选定不得成为生产规范。
- 原截图中文栅格文字被放大会显得不如矢量标题锐利，不应伪造重排来掩饰来源。
- XIAO-Y 只在确认关口短暂出现；品牌存在感是否足够必须由用户判断。

## Implementation boundary

Only `src/vgb001/DirectionC.tsx` implements this direction. It imports shared fixed assets/caption infrastructure; no Director IR, resolver, production template, audit, publish or DECISIONS change is required. It is not an automated generator or accepted architecture.
