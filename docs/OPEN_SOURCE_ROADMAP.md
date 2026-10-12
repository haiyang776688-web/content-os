# Open Source Roadmap

这不是承诺时间表，而是给接手者的优先级建议。

## P0 — Product closure

- [ ] 将最新 DirectorIR → ShotPlan 路径接入 Production GUI
- [ ] Storyboard Review 使用 exact artifact/hash approval
- [ ] GUI 显示 stale / blocked / fallback 状态
- [ ] Motion Design 做成受控 opt-in
- [ ] Alignment 做成受控 opt-in
- [ ] 完成 GUI-only E2E
- [ ] Final Human Review / H3
- [ ] Export

## P1 — Real production validation

- [ ] 连续生产多条真实 3–5 分钟视频
- [ ] 记录哪些步骤仍需要人工修复
- [ ] 验证中英混合、数字、专有名词、不同语速
- [ ] 决定 ALIGNED 是否值得成为默认
- [ ] 决定 Motion Design 是否值得成为默认

## P2 — Quality ceiling

只有 P0/P1 完成后再考虑：

- [ ] SeeCut-style QA / local repair loop
- [ ] Reference Library / Creative Direction
- [ ] Motion ↔ SFX
- [ ] Creative Composer
- [ ] more motion phrases

## Explicitly avoid

除非有真实生产证据，不建议优先：

- 再增加模型数量；
- 再增加几十种模板；
- 用 raw ASR segmentation 做语义；
- 让 Renderer 自己选创作策略；
- 让 LLM 直接生成 production Remotion code；
- 为了 schema 完整而增加没人消费的字段。
