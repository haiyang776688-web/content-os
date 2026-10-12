# VGB-001 · Comparison

Date: 2026-09-29
Status: TECHNICAL_PASS / CREATIVE_TARGET_NOT_ESTABLISHED / AWAITING_HUMAN_VISUAL_CHOICE

三条实验片已经输出。代理建议为 **NONE**：它们可以用于比较三种视觉语言，尚没有一条足以推荐为正式 Gold Master。此结论不是用户的最终审美选择，也不覆盖旧的人工 Gate。

## 控制变量与真实产物

| 项目 | A / B / C 共用值 |
| --- | --- |
| Source | CS-001 5.56–24.68 s；SEG-02/03/04，源内容 19.12 s |
| Script / Voice | ART-278087e926034f3b / ART-7ef0a1a38f894364；不重写、不重配、不变速 |
| Facts | F-dc561e10da、F-71b1b7f9d0 |
| Evidence | 同一 research.png、script.png 的原始像素 |
| Resolution / rate | 1920×1080 / 30 fps |
| Frames / video track | 574 / 19.133333 s |
| MP4 container duration | 三版均为 19.178667 s；音频封装边界与源区间不同 |
| Subtitles | 同一 6 条完整语义字幕；文字与原脚本一致（省略句间标点），无切碎 Fact ID |
| Human visual choice | PENDING |

产物在工作区 `outputs/vgb-001/`（仓库目录的 `../../outputs/vgb-001/`），不进入 Git：

| Render | Bytes | SHA-256 |
| --- | ---: | --- |
| VGB-001-A.mp4 | 3997757 | 6921c108d66f2bb49f6169920605055dd8d502156da8945a3004cf99034e0a63 |
| VGB-001-B.mp4 | 1662936 | f90a6ffb91fd9bc3e1cb03485f111bb6a3102e29dcef76015786ef0eb7349f74 |
| VGB-001-C.mp4 | 2127180 | 8a09aeaa480656f226549440ca30d99b10c0a5d933f8d88b0bb718fa1bfb5fdf |

输入与探测证据在本目录 `evidence/input-manifest.json`、`evidence/verification.json`。`compare.html` 是输出目录中的只读本地看片页，不接入 Content OS，不记录选择。

## 检查方法与限制

- 最终三个 MP4 各以每秒 4 帧连续抽样，共 77 帧，覆盖全段；检查全部连续图和多处 1920×1080 原尺寸关键帧。制作期间另检查 A/B/C 各语义切点、字幕区和原始截图。
- A 最终 8.5 s 的标线位于原文下方，18 s 的 Fact ID 与字幕完整；C 最终 18 s 的 FACT ID 已有明确间距。抽样未见黑场、字幕遮挡或字幕碎片。
- `tsc --noEmit` 通过。`scripts/vgb001.py verify` 检查三版格式、帧数、时长、解码音轨一致，字幕串与源脚本匹配、时间连续；预备配音、图像、字体哈希未变。它不做 OCR，也不等于逐帧视觉缺陷自动证明。
- 三版音轨解码哈希相同：`a4b438037280fe1abeaf0f78ef11737cbf1ce54e759e32bbd038098373c4995b`。同源配音另由公共 `Film` 音频入口、冻结输入和渲染执行记录支持；AAC 成品没有与源 WAV 做逐样本相等检查，不宣称完整端到端密码学来源证明。
- 主线程完成全段密集抽帧和关键帧复核；独立代理另审查最终 composition 时间结构与制作关键帧。代理之间的相同结论不是模型多数投票或人工批准。
- **没有完成实时连续声画观看。** 下述节奏和吸引力评价基于完整时序、密集帧序列和原尺寸静帧，仍需用户直接播放。不能据此宣布“愿意继续看”已验证。
- 本次未修改生产逻辑，未重跑整个业务测试套件，不新增或声称新的业务通过数量。

## 十个维度

等级只有 STRONG / GOOD / WEAK / FAIL，不计算总分。`PPT feeling` 评价控制 PPT 感的程度，STRONG 才表示更少 PPT 感；`Text overload` 同样评价对过载的控制。

| Dimension | A | B | C |
| --- | --- | --- | --- |
| Watchability | **WEAK**：沿软件说明文字巡读，吸引力主要仍靠配音。 | **WEAK**：大脸反应形成转折，随后又进入完整流程页。 | **WEAK**：连续引文有理由，但仍像抽象逻辑讲义。 |
| Information clarity | **GOOD**：入口、人工审查区、引用要求来历可见。 | **GOOD**：候选与事实的区别、人工决定权容易理解。 | **GOOD**：断路明确；确认权归谁仍依靠配音补全。 |
| Evidence credibility | **GOOD**：原 UI 像素为主，明确是静态证据。 | **GOOD**：截图与示意分开，未伪造通过状态。 | **GOOD**：裁片保留原字，关系图不冒充实录。 |
| Visual rhythm | **WEAK**：按语义运镜有用途，但本质仍是读页面。 | **GOOD**：引路、让位、大脸、对比有尺度变化；实时感受待用户检验。 | **GOOD**：同一引文、断线、关口、回溯提供时序因果；实时感受待用户检验。 |
| Brand identity | **WEAK**：暗色产品 UI 为主，XIAO-Y 身份弱。 | **STRONG**：白黑黄红、原始人物与近景反应最接近参考。 | **GOOD**：黄黑与 IP 标点一致，但偏离白底参考。 |
| PPT feeling | **WEAK**：更像帮助文档导览，尚未成为有力的视频叙事。 | **WEAK**：3–6、7–10、12–15 s 的盒子、箭头、标签仍按页重置。 | **WEAK**：深色大字、关系图与尾部证明卡仍有讲义感。 |
| Text overload | **GOOD**：新增字少，但原 UI 无关文字仍占空间。 | **GOOD**：以短标为主，没有完整句重复配音。 | **WEAK**：字标、说明、标题、关系标签、截图与字幕层级仍多。 |
| Visual protagonist clarity | **GOOD**：当前被聚焦的原生区域明确。 | **GOOD**：人物、证据和关系按段接替。 | **GOOD**：引文关系是主角；尾部大字与实际证据仍竞争注意。 |
| Screenshot readability | **GOOD**：放大目标可读，受原始栅格分辨率限制。 | **GOOD**：尾部直接给出 Fact ID 原句局部。 | **WEAK**：尾部 textarea 保留太多非目标指令，大标题比原证据更抢眼。 |
| XIAO-Y usefulness | **GOOD**：证据段缺席合理；品牌不足在另一维度计。 | **GOOD**：指引、惊讶、严肃有分工；把关一镜仍接近人物配标题。 | **WEAK**：严肃姿态没有实质改变关系，接近可有可无的品牌贴纸。 |

## 三个方向仍缺什么

A 有可定位的真实控件，没有真实动作与结果；静态截图不能提供当前素材里不存在的 before/after。B 有最清楚的品牌感，但人物反应只解决局部节奏，中段完整构图仍是旧的页面语法。C 的关系对象能连续，却没有一个具体候选被判断的过程，仍用抽象名词解释抽象名词。

因此，“更容易读”“品牌更接近”“运动有因果”都不足以推出 Gold Master 成立。本轮保留全部三片供选择，停止继续零散补动画。

## 复现边界

独立入口 `vnext/renderers/remotion/project/src/vgb001-index.tsx`，不是生产入口。脚本只准备实验媒体、渲染与验证；无模型调用、生产项目状态变更或发布。

复现需要现有 Remotion 依赖、ffmpeg/ffprobe、Pillow、Chrome，以及 CS-001 源 props、SCRIPT artifact 和 props 对应的原配音/字体公共缓存。**单独 Git checkout 不包含私有配音与所有生成缓存，不能承诺凭仓库即可独立复现。** 缺失输入应恢复原文件并核对 manifest，不能换声音或截图后沿用本报告。

从仓库根目录执行（`/path/to` 换成保留的本地输入与输出目录）：

```sh
python3 scripts/vgb001.py prepare --source-props /path/to/RUN-dda8992671-props.json --output /path/to/vgb-001
python3 scripts/vgb001.py render --output /path/to/vgb-001
python3 scripts/vgb001.py verify --output /path/to/vgb-001
cd vnext/renderers/remotion/project
./node_modules/.bin/tsc --noEmit
```

`prepare` 预期 SCRIPT 位于源项目 `artifacts/SCRIPT/v0003-ART-278087e926034f3b.json`。预备媒体只写 `public/PREVIEW-VGB001/`（已被忽略），源媒体不改写。
