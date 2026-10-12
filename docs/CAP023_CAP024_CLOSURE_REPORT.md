# Content OS vNext Phase 2 Closure — CAP-023 / CAP-024 验收报告

日期：2026-09-26。基于当前 Phase 2 Preview 原工作目录增量修改。未新建用户项目、未重写 Core、未进入 Phase 3。CAP-023 与 CAP-024 的本轮有限范围已经实现并验收；原22项中的11项 IMPLEMENTING 仍保持原状态。

## CAP-023 画面预览

Timeline 上部为真实 Remotion Player，随后是播放/暂停、逐帧、时间码、缩放、安全框、播放头和现有时间线。点击片段会使播放头定位到入点，并让编辑选择与右侧 Inspector 使用同一个 clip_id。重叠片段在同轨内分行显示，便于选择。

预览与正式渲染调用 `CompositionResolver.resolve()` 并导入同一个 `Composition.tsx` scene。它们消费相同的 EDT timing、源范围、geometry、层次、crop、transform、media bindings、字体字节与音频时序。浏览器只把相对资源地址转换为本机只读资产接口。安全框不进入 scene。

`PREVIEW_FRAME` 是 derived projection，不保存成生产 Artifact。预览缓存是按输入哈希生成的本地字节副本，可重建。播放头、播放状态、选中片段、缩放、安全框只存在 UI。音频与画面共用 Remotion Player 的 frame/audio clock，没有第二套播放计时器。主页面或预览获得焦点时，Space 均能控制播放；输入框和模态编辑时不截获空格。

真实编辑仍经过 Unified Commands。字体改变后可立即查看最新字体的草稿投影，但过期 EDT 的警告会保留；使用显式 REFRESH_DEPENDENCIES 重新锁定当前依赖后才可以正式渲染。它拒绝过期 Script/Director IR，保留已编辑的 clips，不悄悄改上游。导演应用节拍包含明确的视觉重建动作并保留 VOICE/BGM/SFX 时序；界面说明原手动视觉调整会被替换。

## 已有诊断工程的实际 UI 验收

使用已有字体项目 `PRJ-3e7963af47cc`，没有创建新的用户工程。原60秒项目 `PRJ-b417f4c7957a` 保持原状。

- 实际拖动播放头、播放/暂停、Space（主页面/iframe）、逐帧步进、安全框及 Fit/50%/100% 已检查。逐帧显示 00:00:00:00 → 00:00:00:01 → 00:00:00:00；50% 为960px，100% 为1920px。
- 选中 `CLP-ea4acb7a26` 后 Inspector 与编辑选择一致；切换语言仍保留 ID、时间码与未提交的 1.37 编辑值。
- 实际统一命令把 Italic 片段缩放到1.25，加入现有 XACT-001，然后重新绑定现有 XACT-002。素材位置为 x=.17/y=.52。
- TITLE 从 Arial Regular400/48 改成 Arial Bold700/58。形成 TypographyProfile v2、FontSnapshot v2。显式同步形成 EDT v17 `ART-3e71212525bc4faa`；未重写原Script或DirectorIR。
- 重建分镜并以 `SIMULATED_CLOSURE_UI_ACCEPTANCE` 做诊断审核，再生成正式10秒 H264/AAC 渲染 `ART-9d2854cfb07548ec`。视频为1920×1080、30fps、300frames，声音是原测试音。
- `composition-equivalence.json` 证明正式渲染 props 与预览解析 props 逐项相同；`preview-frame-090.png` 与 `render-frame-090.png` 是同一第90帧（3秒）。人工检查字体、角色、位置与层次一致。浏览器截图裁剪与正式帧缩小到459×258后的 SSIM 为0.950836。缩放、浏览器抗锯齿、JPEG截图及H264压缩存在像素差异，不能声称逐像素相同。

本次诊断审核不是用户真实 H3/H4 确认。字体/EDT变化使旧QA/Review失效；没有把它们改回就绪，也没有发布或重新导出剪映。

## CAP-024 集中双语显示

`vnext/i18n/zh-CN.json`、`en-US.json` 和 `registry.json` 集中管理526个键、187个 canonical presentation mapping。HTML/JS 不再散放中英文 UI 文案。导航、Inspector、底栏、状态、能力、Gate、模型可用性、字体状态、素材隐私、错误/警告、空状态、撤销/重做和预览控制均通过同一显示层。

数据库 Enum、Artifact ID/hash、Prompt ID、模型品牌与用户文本没有被翻译或改写。原始技术数据通过明确的“查看原始数据 / View raw data”折叠区显示。未知后端错误默认显示本地化说明，允许查看原文；不自动翻译用户内容。

Locale 使用浏览器 `vnext_locale` 偏好，仅GET字典，不 PATCH 项目，不触发 Stage DIRTY。已检查中文/English 各十个主页面（Research、Script、Audit、Director、Visual、Media、Voice、Timeline、Render、QA），以及各六个 Phase2 编辑面板。实际切换保留片段选择、节拍Pattern、关键词、字体字号草稿。

`ui_preference_integrity.json` 和 `final-ui-only-integrity.json` 记录两组真实界面操作前后的项目、Artifacts、Stages、日志摘要，均 unchanged=true。实际生产修改另行形成版本，不混入 UI-only 比较。

## 自动验证与证据

自动测试共78项通过（新增23项，其中用户要求的10项Preview和10项i18n测试全部覆盖），保留所有55项原有回归。另检查了三份 Remotion TypeScript 和四份浏览器模块语法，并成功重建 monitor bundle。仅有 Starlette/httpx 的一条弃用提示。

- `pytest-final.txt`：完整测试输出。
- `zh-pages-final.json` / `en-pages-final.json` / `modal-pages-final.json`：最终页面与编辑面板检查记录。
- `workbench-zh-final.png` / `workbench-en-final.png`：两种语言下的工作台截图。
- `diagnostic-closure-10s.mp4`：正式渲染视频。
- `composition-equivalence.json`、两个第90帧PNG与 `frame-comparison.json`：预览/渲染参数和画面对比。
- `CAPABILITY_ROADMAP.json`：共24项，13 READY、11 IMPLEMENTING；phase2_complete=false。

当前项目保持 localhost 单用户模式。新机器不带数据库、系统字体、缓存和密钥；诊断JSON里的绝对路径是本机证据，不是可搬迁工程。复杂视频性能、真实口播/供应商、完整几何QA以及原 Phase2 未完成项仍按原Roadmap继续。本轮不增加其他能力。
