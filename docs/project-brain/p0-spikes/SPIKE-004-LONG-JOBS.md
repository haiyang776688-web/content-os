# SPIKE-004 · Long Jobs

**Date:** 2026-09-28
**Baseline:** `674957813b5efea39e8cc3e61621245808ccacc7`
**Result:** **FAIL**（当前不具备快速返回、single-flight 和服务重启恢复的最小后台合同）

## Timing evidence

| Operation | Measured wall time | Evidence / limit |
| --- | ---: | --- |
| Voice production | **UNKNOWN** | 新项目只完成本地声音试听；试听音频长 4.08 秒，不能当作生成耗时或正式 Voice 耗时。生产路由在同一 HTTP 请求中 `run_in_threadpool` 后等待完成。 |
| Storyboard Stills | **UNKNOWN** | 路由同步等待 `Production.storyboard`；该函数逐 Beat 调用 Remotion still、每 Beat 两帧。现有产物没有任务起止时间，不能由创建时间推断耗时。 |
| Render | **154.920 秒**（另一次 157.462 秒） | 已有 `PRJ-bba515713057` 的 `RENDER_VIDEO` Job `started_at` / `finished_at` 差值；84.821 秒样片历史记录。不是本次新项目渲染。 |
| MiniMax QA | **UNKNOWN** | 已有真实 `VIDEO_QA` v1 记录 MiniMax-M3、2 attempts，但没有 Job 起止时间。本轮未将新的敏感视频送云端。路由同样等待 `run_in_threadpool` 完成。 |

## Contract check

| Item | Current state | Evidence |
| --- | --- | --- |
| Quick `job_id` response | **FAIL** | [Render 路由](../../../vnext/apps/workbench/server.py) 调用 Remotion 并等待返回产物；[Voice/MiniMax](../../../vnext/providers/workflow.py) 等待 threadpool；[Storyboard](../../../vnext/phase2/api.py) 同步运行。 |
| Single-flight | **FAIL** | Render 只复用已 COMPLETED 的有效产物，没有 RUNNING 防重复；[JobEngine](../../../vnext/core/jobs/engine.py) 也没有针对并发请求的原子占用。 |
| Orphan recovery | **FAIL** | 服务启动没有扫描遗留 RUNNING 并写 `SERVER_RESTARTED`。 |
| Retry | **PARTIAL** | 失败的同步请求可以重新提交；没有明确的后台 Job Retry 合同或 orphan 处理。 |
| Refresh recovery | **PARTIAL** | 项目详情返回持久化 Render jobs，浏览器任务面板可读；Voice/Storyboard/MiniMax 正式流程没有同等 Job 状态。 |
| Revision binding | **PARTIAL** | Render idempotency key 含 EDT artifact ID；没有完工时与当前 EDT revision 比较并标记 STALE 的完整后台合同。 |
| Progress | **FAIL** | 没有可靠的阶段/已用时间 Job UI；不应伪造百分比。 |

## P0 impact

Slice 4 只建立本机最小持久 Job：目标 revision、single-flight、启动 orphan recovery、refresh 查询、安全 Retry、真实阶段和耗时。不要建设分布式队列。当前 Job 枚举叫 `COMPLETED`，若 UI 使用 `SUCCEEDED`，需明确映射，不静默改变历史数据。
