# SPIKE-001 · Strict Script Edit

**Date:** 2026-09-28
**Baseline:** `674957813b5efea39e8cc3e61621245808ccacc7`
**Result:** **FAIL**（GUI 修改正式脚本后不能形成可审计的新 `SCRIPT` 版本）

## Evidence

在 `/tmp/content-os-p0-spikes.6d6PKf` 的隔离数据副本、`127.0.0.1:8767` 工作台中选择 `PRJ-bba515713057`。原正式脚本为 `SCRIPT` v4，`ART-bef1d4cecaf94b5d`。通过浏览器把首句“想让视觉时间线跟着声音走，第一步是分清职责。”改为“要让视觉时间线跟着声音走，先要分清各自的职责。”，点击“保存新版本”。界面提示操作完成，但正式脚本仍为 v4；历史仅新增 `SCRIPT_REFERENCE` v1 `ART-f52db563f3844d00`。这不是新 H2 候选稿。测试没有改动真实项目数据。

代码路径：[主界面](../../../vnext/apps/workbench/workbench.js) 的 `saveScript` 调用 `/api/projects/{id}/script`；[旧文本编辑器](../../../vnext/core/editing.py) 在 `phase2_enabled` 项目中强制转为 `SCRIPT_REFERENCE`。正式绑定稿实际由 [Knowledge.bound_script](../../../vnext/phase2/knowledge.py) 建立，要求文本与段落一致、Fact ID 存在且受支持；strict 合同还校验 Claim Unit。现有 [CommandBus](../../../vnext/phase2/production.py) 已有 `REPLACE_SCRIPT` 和 `expected_revision`，但主界面没有使用。机械检查对缺失 Fact 绑定报告 `UNBOUND_CLAIM`。

## P0 impact

Slice 1 需要将普通文本编辑映射为逐段正式脚本修订，并在同一 GUI 提供最小 Claim ↔ Fact/Evidence 修正入口；保留审计和 H2 的独立步骤。不能直接把纯文本声明为合法 strict Script。修复后重测：新 `SCRIPT` version、绑定有效、机械无因 GUI 编辑产生的 blocker、H2 可继续。
