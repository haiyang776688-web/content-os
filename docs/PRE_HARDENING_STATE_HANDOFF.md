# Content OS 当前状态交接包

日期：2026-09-26。当前版本：**Content OS vNext Phase 2 Preview + CAP-022/023/024 Closure**。这是一份继续实施和人工验收的实际状态，不代表24项全部完成。

## 当前项目与运行

- 可编辑工作项目：`${LOCAL_ROOT}/Documents/Codex/2026-09-22/referenced-chatgpt-conversation-this-is-an/work/content-os-vnext-phase1`。目录名沿用Phase1，内部已增量加入Phase2；无需移动，避免已有产物绝对路径失效。
- 后端数据：上述目录的 `phase2_preview_data`。当前 UI：`http://127.0.0.1:8766/`。
- 本轮交付目录：`${LOCAL_ROOT}/Documents/Codex/2026-09-22/referenced-chatgpt-conversation-this-is-an/outputs/content-os-vnext-phase2-closure`。
- 压缩包：同级 `content-os-vnext-phase2-closure.zip`。
- 冻结Phase2 Preview：同级 `content-os-vnext-phase2-preview` 与其zip，保持原样。
- 冻结Phase1：同级 `content-os-vnext-phase1`、`content-os-vnext-phase1.zip`；旧服务8765保持独立。
- Legacy：`${EXTERNAL_VOLUME}/AI味检测/xiao-y-remotion-calibration/content-os-core-with-xiao-y-hd-assets`，只读迁移来源。

## 最新验收项目

- 全链诊断：`PRJ-b417f4c7957a`，60秒；主稿/Editor/Audit/Director和VideoQA全为Mock；H2、Storyboard、H3都是模拟确认。真实渲染12张起止帧和H264/AAC MP4；声音为440Hz测试音，不是用户口播。
- 字体诊断：`PRJ-3e7963af47cc`。三种本地字体家族、五个文件；Regular400 / Medium500 / Bold700 / Italic / TTC faces / Variable均有实际渲染。已走Storyboard、10秒测试音、MechanicalQA、Remotion、MockVideoQA、NativeExport、ReviewPack。
- 60秒原生草稿：`${EXTERNAL_VOLUME}/剪映草稿/JianyingPro Drafts/ContentOS-EXP-3e9232ba31`。
- 原生UI验证：剪映11.5.0-beta5打开；把独立文字改为“来源先行 · Native 测试”；保存、关闭、重开后仍有修改；已成功导出本地MP4。修改只在导出副本，不回流Script/IR/EDT。
- 字体原生草稿：同目录 `ContentOS-EXP-4ae432ee9a`，本轮未逐项原生UI验收字体工程；主60秒工程已验证读取编辑输出。

## 实际闭环

Research/SourceLedger → FactPack → BoundScript → BlindAudit FAIL → owner ChangeRequest → 08 ErrorConfirmed → 相同摘要 ERROR_RECURRED关联旧error_id → 新规则CREATED/ACTIVE → 下一轮有效规则快照 → Owner修复Script新版本 → 新审计PASS → H2 → DirectorIR/Scene/Beat/DesignTable → Media → EDT V2 → Storyboard真实起止帧 → Gate → Voice → MechanicalQA → Remotion → MockVideoQA → NativeExport → ReferenceReviewPack → 模拟风险H3。

中途08规则变更会使初始Primary/Editor缓存DIRTY。它们不能作为正式审计或生产输入；只有可追溯的历史父Script可用于Editor阶段回放。最新修复稿和下游是当前有效版本。不要把DIRTY缓存改成完成以美化结果。

## 关键约束

1. 规则与错误正式写入者只有08/EVOLUTION。其他部门只读，可以提交候选和Finding。
2. 新规则目录RULE_CATALOG含所有有效Rule ID，避免第一次激活规则没使旧生产失效。
3. 下游不能改上游，只能Change Request。模型分歧DISAGREEMENT不得多数投票，必须责任Owner提交当前证据解决。
4. H2绑定当前Script和审计；Storyboard绑定当前视觉；H3绑定当前ReviewPack。全部FAIL否决；有风险必须明确接受。
5. FontProfile不是普通Media。字体哈希锁定、缺字严格阻断、fallback明确；字体字节不分发、不自动上传。
6. JSX/Remotion/剪映都消费EDT；没有剪映反向导入。
7. 当前是可信单用户localhost；角色权限不是账户认证。不能直接公开服务。
8. 不进入Phase3，不制作正式4分钟视频，不自动发布。H3不等于H4。

## 验证与文件

- 自动测试78项通过（新增23项Closure）；12项Phase1回归包含在内。JavaScript语法与Remotion TypeScript通过。日志见 `examples/phase2/PYTEST_RESULT.txt`。
- 93个受保护资产/Pack/校准文件与冻结Phase1完全相同；Phase1zip SHA仍为 `2690875a81cd156095b8ed4a30b7d6bcf56c42dd60ecaef09b4c82d780597c34`。
- 本轮没有原地运行Legacy回归，不能把旧报告结果当成新测试。
- 逐项24能力：`CAPABILITY_ROADMAP.json`、`CONTENT_OS_VNEXT_PHASE2_REPORT.md`。当前13个READY（有限能力）、11个IMPLEMENTING；没有虚报整体验收。
- 样本：`examples/phase2/` 内FactPack、SourceLedger、Script历史、IR、设计表、EDT、分镜、MechanicalQA、MockVideoQA、ReviewPack、规则账本、错误复发、字体与原生回归结果。
- 启动、真实Worker、可选本地向量模型、剪映路径和EDT迁移命令见README。

## 本轮 CAP-023 / CAP-024 实际状态

同一工作目录增量修改，没有新建用户工程。交付快照：`outputs/content-os-vnext-phase2-closure` 与同级zip；原Phase2 Preview冻结包保持不动。

Timeline 已接入真实 Remotion Player，预览与Render共用解析器与scene。播放/暂停、Space、逐帧、时间码、Fit/50%/100%、安全框、片段/Inspector同步已通过实际界面检查。预览不创建生产Artifact，EDT是唯一真源。

526个集中翻译键、187个canonical显示映射。中文/English各10个主页面和6个编辑面板已检查。语言切换保留页面、片段、Beat/Pattern、字体与输入草稿；两组实际UI操作前后项目、Artifacts、Stage、日志完全相同。

现有字体工程完成Italic缩放、加入/替换XACT素材、TITLE Arial Bold700/58，形成Typography v2和EDT v17（`ART-3e71212525bc4faa`）。显式重新审查分镜的审核人是 `SIMULATED_CLOSURE_UI_ACCEPTANCE`，不是用户真实确认。新Render `ART-9d2854cfb07548ec`，10秒/30fps/1920×1080/测试音。旧QA和Review已过期，没有虚报H3/H4。

预览与正式渲染props逐项相同，第90帧已作实际截图对比；归一到459×258的SSIM约0.950836，受浏览器缩放、截图JPEG和视频编码影响，不宣称像素完全一致。完整报告：`CONTENT_OS_VNEXT_PHASE2_CLOSURE_REPORT.md`，证据：`examples/phase2_closure/`。

字体草稿更新后，正式渲染前须“同步最新依赖”并重新分镜审查。导演应用节拍是明确的视觉重建动作，保留音轨，但会替换手动画面调整。所有真实修改走Unified Commands。

## 未完成项与下一轮顺序

先在当前Phase2补齐高级Pattern表达、全面机械几何/安全区/信息密度检查、所有编辑Command及阶段调度，再完善Typography预设和可搬迁字体依赖。真实DeepSeek/Doubao/OpenAI/GLM/MiniMax调用及真实配音未验收；没有使用本机任何API key调用云服务。Optional本地embedding适配器存在，但未安装实际模型；自动ASR未实现。

剪映字体选择被替换为系统字体，字幕阴影未映射；尺寸/字重/间距仅近似。报告保留UNSUPPORTED/APPROXIMATED。不能因为原生工程可编辑就声称字体或完整视觉一致。其他剪映版本未验收。

H1/H4的新工作台界面、真正平台发布、队列/取消、团队账户、反向剪映导入仍没有实现。本轮交付用于用户审查和继续Phase2，不自动进入新阶段。
