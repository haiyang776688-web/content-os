# SPIKE-002 · Fresh Project Voice

**Date:** 2026-09-28
**Baseline:** `674957813b5efea39e8cc3e61621245808ccacc7`
**Result:** **FAIL**（全新项目无法仅靠当前 GUI 到达正式 Voice → AudioTimingMap → Final EDT）；正式生成耗时 **UNKNOWN**。

## Evidence

在隔离数据副本通过浏览器新建 `P0 Spike Fresh Voice 2026-09-28`（`PRJ-589b72f8417d`），从下拉框选择 `YU_LOCAL_V1`。新建表单目前只有项目名称，没有 Topic / Content Type。设置页显示本地 CosyVoice3“已配置”、已找到模型和参考音频、哈希相符，授权复选框为已勾选。全新项目的本地声音试听成功，浏览器出现播放器，并明确显示“仅试听，未创建正式生产产物 · 4.08s”。这是音频时长，不是正式生成的墙钟耗时。

在同一新项目点击“为批准脚本生成正式配音”，界面返回“需要重新审核并确认分镜”。新项目没有 H2、Storyboard Gate、正式 `VOICE` 或 `AUDIO_TIMING_MAP`，没有复用旧项目 Voice。这个拒绝是正确的前置校验，但也证明当前新项目 GUI 闭环未达到 Spike 通过标准。

[真实 Voice 入口](../../../vnext/providers/workflow.py) 在 `require_storyboard` 之后按已批准脚本逐段运行本地/云 TTS、测量段落音频并创建 `VOICE` 与 `AUDIO_TIMING_MAP`；无词时间戳时使用测得的段落边界，不伪称逐词对齐。[基础 Voice 入口](../../../vnext/apps/workbench/server.py) 缺时间戳会返回 `VOICE_TIMING_ALIGNMENT_REQUIRED`。本 Spike 没有触发正式 Voice，因此不能确认全新项目的 Final EDT，也不能把旧 84.821 秒样片算作通过。

## P0 impact

先完成新项目 Source/Fact/Script/H2 与 Director/Storyboard Gate 的 GUI 路径，再在全新项目实测正式本地 Voice、时间图和 Final EDT。试听成功只说明适配器可用的一个子集；正式流程仍需独立验收。
