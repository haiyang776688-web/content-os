# VGB-002 · Implementation record

Date: 2026-09-29
Status: RENDERED / TECHNICAL_PASS / NOT_HUMAN_ACCEPTED

## Isolation

VGB-002 使用独立入口 `src/vgb002-index.tsx`，注册 `VGB002F1` 与 `VGB002F2`。两版共用 VGB-001 已冻结的 `Film`、本地字体、配音与六条字幕，只新增手工视觉 composition。没有接入 DirectorIR、VisualResolver、VisualProgression、任务状态、Gate 或发布路径。

| File | Purpose |
| --- | --- |
| `src/vgb002/shared.tsx` | 证据镜头、品牌 chrome、短标、人工审查、来源关系等本实验内部 primitive |
| `src/vgb002/F1.tsx` | Evidence-heavy 手工 composition |
| `src/vgb002/F2.tsx` | Brand-balanced 手工 composition |
| `src/vgb002-index.tsx` | 独立 Remotion 注册入口 |
| `scripts/vgb002.py` | 仅负责渲染与同源技术验证，不写业务状态 |

## Refinement used

按本轮上限只进行一次明确问题修正：

1. 将人工审查原截图从过宽的整条裁片改为标题/说明与控件两段可读裁片。
2. F2 reaction 保留触发反应的真实规则说明，不让大脸镜头与前后证据失去关系。
3. 调整人物进退场位置，消除画面边缘残留；最终 Fact ID 镜头中人物不遮挡原文或字幕。

之后没有继续进行风格补丁或第二轮 refinement。

## Actual visual shares

比例按“某种视觉承担 PRIMARY 叙事职责”的时段计算，不按像素面积计算。

| Candidate | Direct evidence-primary | XIAO-Y visible | Interpretation |
| --- | ---: | ---: | --- |
| F1 | 约 78% | 约 27% | 直接证据时段排除开场人物主导与 11.88–15.42 的关系解释；人物多数与证据重叠且为 supporting |
| F2 | 约 60% | 约 38% | 直接证据时段排除 reaction、人工责任共同镜头、角色过渡与关系解释；符合 Brand-balanced 目标 |

“XIAO-Y visible”与“Evidence-primary”可重叠，因此两者不要求相加为 100%。F2 的人工审查镜头同时包含人物和真实 UI，但按叙事职责计为人物代表责任、证据提供产品位置。

## Render and verification

| Render | Format | Duration | Bytes | SHA-256 |
| --- | --- | ---: | ---: | --- |
| VGB-002-F1-EvidenceHeavy.mp4 | 1920×1080 / 30 fps / 574 frames | 19.178667 s | 4,114,335 | `79c1349b83722bfb880b1835058c1bca80ebdd3c1e019c35a9b89fa1aaa32e47` |
| VGB-002-F2-BrandBalanced.mp4 | 1920×1080 / 30 fps / 574 frames | 19.178667 s | 4,058,165 | `97bda94eab6fda8be603270405f211894be2bacb06ad1385cd241c2882bd0f1c` |

两版解码音轨 SHA-256 均为 `a4b438037280fe1abeaf0f78ef11737cbf1ce54e759e32bbd038098373c4995b`，与 VGB-001 A/B 相同。字幕共六条，时间连续、文字与冻结脚本一致，`Fact ID` 保持完整。TypeScript 检查通过。

最终两版分别以每秒 4 帧抽取 77 张连续图，并检查 1920×1080 的开场交接、候选边界、reaction、人工审查、来源绑定和结尾收束关键帧。未发现黑场、残片、字幕重叠、超出安全区或人物遮挡 Fact ID。

## Review limit

主线程完成的是完整时序代码检查、密集连续抽帧与原尺寸关键帧检查，**没有完成实时连续声画观看**。因此 `04_COMPARISON.md` 的 watchability、rhythm 与 continuity 是候选级判断，用户播放结果优先。技术通过不等于 Gold Master 已被用户接受。
