# SPIKE-003 · Dependency Invalidation

**Date:** 2026-09-28
**Baseline:** `674957813b5efea39e8cc3e61621245808ccacc7`
**Result:** **PASS**（本次纯视觉 Beat 修改未让 Voice 重录）

## Evidence

仅在 `/tmp/content-os-p0-spikes.6d6PKf` 的隔离副本操作 `PRJ-bba515713057`。修改前：`VOICE` v1 `ART-ce387c3fce5546ee` 为 READY，`AUDIO_TIMING_MAP` v1 `ART-de11de6cee654e77` 为 READY，`DIRECTOR_IR` v2、`EDT` v6。通过第二阶段工作台的“导演 / 分镜”表单把 `B-01-01` 的视觉关键词从“分清职责”改成“口播与画面分工”，点击“应用节拍并刷新画面”。修改后出现 `DIRECTOR_IR` v3、`EDT` v7/v8；原 Voice 和 AudioTimingMap 仍为 READY，没有要求重录。旧 EDT、Storyboard、Render、Video QA 变为 STALE，与视觉修改需要重建画面的预期一致。

[CommandBus](../../../vnext/phase2/production.py) 的 `SET_BEAT` 只改 Director IR；界面随后用 `GENERATE_PRESERVING_AUDIO` 重建 EDT。[Store](../../../vnext/storage/store.py) 根据实际依赖边向下游传播失效；当前 Voice 依赖 H2 Script/Voice 授权，而不依赖视觉 IR。当前 GUI 这条命令未传 `expected_revision`，是 Slice 2 的独立并发保护缺口，不改变本 Spike 的 Voice 结论。

## P0 impact

不把完整依赖图重设计提升为 P0。保留当前视觉/口播依赖边，给 GUI 写操作补 revision guard，并回归验证视觉修改仍不使 Voice 失效。
