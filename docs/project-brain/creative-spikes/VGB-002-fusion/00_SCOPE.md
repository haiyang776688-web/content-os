# VGB-002 · XIAO-Y Evidence Editorial Fusion

Date: 2026-09-29
Status: EXPERIMENT / SHOTLIST_FROZEN / AWAITING_RENDER
Branch: `p0/visual-gold-benchmark-2`
Baseline: `p0/visual-gold-benchmark-1@29af792e78e7ad35fe6fd269274ec6c531b4237a`

## Human direction

用户对 VGB-001 的明确反馈是：Direction A 与 Direction B 都很好，融合会更理想。本轮据此收敛为 **XIAO-Y Evidence Editorial**，不继续探索 Direction C 或第四种视觉语言。

核心职责分工：真实证据负责证明，XIAO-Y 负责解释与人格，动态短词负责强调，镜头运动负责引导注意力。一个时刻只有一个 PRIMARY；人物、截图、文字与箭头不能同时抢夺注意力。

## Frozen comparison inputs

| Item | Frozen value |
| --- | --- |
| Source interval | CS-001 5.56–24.68 s，源内容 19.12 s |
| Script | ART-278087e926034f3b，SEG-02/03/04，不改字义与顺序 |
| Voice | ART-7ef0a1a38f894364 的同一区间，不重新合成、不变速 |
| Facts | F-dc561e10da、F-71b1b7f9d0 |
| Screenshots | `research.png`、`script.png`，与 VGB-001 A/B 相同 |
| Output | 1920×1080、30 fps、574 frames；目标 MP4 容器与 VGB-001 对齐 |
| Captions | 沿用 VGB-001 六条完整 cue，Fact ID 不拆分 |

唯一实验变量是视觉语言。两版都通过独立手工 Remotion composition 制作，不调用 DirectorIR、VisualResolver 或 VisualProgression，不写生产项目状态。

## Fusion candidates

- **F1 — Evidence-heavy：**真实 UI 和源像素约占 75% 的叙事时间；XIAO-Y 只负责开场引路和人工责任节点。目标是保留 A 的证据清晰度，同时加入足够的品牌人格。
- **F2 — Brand-balanced：**真实 UI / 源像素约占 60%；XIAO-Y / editorial 节拍约占 40%。目标是保留 B 的角色节奏，但每次人物出现都必须推动引入、反应、责任或收束，证据始终可回到同一视觉空间。

比例是叙事占比，不是逐帧像素面积的伪精确测量。最终实现与抽帧检查会记录实际角色出现区间及证据主角区间。

## Evidence boundary

`research.png` 只显示空的本地导入入口和“模型总结不直接成为事实”等界面说明；它不显示上传成功、候选生成或确认完成。`script.png` 显示脚本方向中的 Fact ID 要求和人工审查区；它不能单独证明程序已执行引用校验。所有关系表达均须标注为流程示意，不能伪装成产品操作录屏。

## Success and stop rule

只有在 Evidence readability 不低于 A、Brand identity 不低于 B、PPT 感低于 A/B、Text overload 不高于 A、人物不与证据竞争、切镜连续、字幕无缺陷时，代理才可以建议进入下一轮工程化评估。该建议仍需用户明确 `ACCEPT F1` 或 `ACCEPT F2`。

如果两版都不足，本轮最多允许一次针对明确问题的 refinement；仍不达标则记录 `Fusion hypothesis rejected` 并停止。无论结果如何，本轮不修改生产 Pipeline、`DECISIONS.md`、DirectorIR、VisualResolver，不制作全长片，也不开始 Reverse Engineering。
