> **历史交付快照提醒（2026-09-29 更新）**  
> 本文件原文描述的是 **2026-09-28 Phase 2.1 / 84.821 秒样片交付包**，不是当前 P0 GUI-Only E2E 最新状态。  
> 当前状态请先读 `docs/project-brain/HANDOFF_2026-09-29_P0_GUI_E2E.md`、`CURRENT_STATE.md` 和 `IMPLEMENTATION_STATE.md`。  
> 当前活动 P0 分支已推进到 Track B fresh live GUI acceptance（61.46 秒），而且创作质量仍为 FAIL / pending redesign。  
> 不要用本历史 README 中的 189 tests、旧 H3 或旧样片结论覆盖较新的 Project Brain / P0 branch 证据。

# Content OS vNext Phase 2.1 · 完整交付说明

交付快照：2026-09-28；当前任务 `PRJ-bba515713057`。解压后先打开 `DELIVERY_INDEX.html`，即可直接观看正式成片并进入审片记录，不需要启动后端。

本包包含现有工程源码、Python 与 npm 依赖清单、测试、规则/契约/文档、`phase2_preview_data` 数据库和项目目录、已登记的 XIAO-Y 图片、项目音频、分镜、正式 MP4、MiniMax 审查原始记录、独立复核、H3 终审记录及历史证据。包内 `DELIVERY_MANIFEST.json` 列出文件 SHA-256；压缩包另有同名 `.sha256` 校验文件。

当前正式 MP4 为 `phase2_preview_data/projects/PRJ-bba515713057/renders/RUN-2f3f2604f1.mp4`，84.821 秒、1080p。机械 QA 为 PASS，MiniMax 无音轨视觉 QA 为 PASS_WITH_RISK，H3 关卡 `ART-98b97704be3f4aa2` 已按带风险确认通过。模型的唯一 WARNING 与实际所指时段不符，详情见 `examples/activation/style_review/MINIMAX_QA_TRIAGE.md`。**H4 未授权，也未发布。**

压缩包不含 `.venv`、`node_modules`、Remotion 的 `public` 临时渲染缓存、Python 字节码和测试缓存。它们可以从依赖清单重新安装或生成；正式成片和项目源素材均已包含。macOS Keychain 中的 API 密钥不会进入包，换机使用真实模型时需重新配置。项目字体缓存包含在项目数据中，但系统字体安装源和本地声音模型权重不在包内。

若要在有依赖的本机启动工作台，在解压后的工程目录运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
(cd vnext/renderers/remotion/project && npm ci)
CONTENT_OS_DATA=phase2_preview_data .venv/bin/python -m uvicorn vnext.apps.workbench.server:app --host 127.0.0.1 --port 8766
```

访问 `http://127.0.0.1:8766/`。需要 Python 3.11+、Node.js/npm、FFmpeg/FFprobe 与 Chrome/Chromium。项目历史记录和数据库中的媒体路径保留原机器绝对路径，以维护原有审计哈希；如果解压到另一目录或机器，静态入口和包内 MP4 仍可直接使用，但在工作台继续编辑历史任务前，需恢复原目录布局或重新关联媒体/字体。不要直接改写历史 artifact 的路径与哈希。

测试命令：

```bash
CONTENT_OS_TEST_NO_KEYCHAIN=1 .venv/bin/python -m pytest vnext/tests -q
```

交付时 189 项测试通过，另有一条既有 Starlette 弃用警告。此包不包含真实平台发布 API；H3 通过并不执行 H4。
