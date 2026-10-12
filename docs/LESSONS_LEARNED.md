# Lessons Learned

这份文档只写能从代码、测试或受控实验中得到支持的结论。公开快照保留结构化结果和方法，但私有声音、模型、字体、截图和实验视频不分发。无法由公开材料复核的观点会标记为设计假设。

每一节按“问题、原因、错误思路、修复、验证、限制、可复用经验”记录。

## 1. 多模型数量增加，成片质量未必提升

**问题。** 早期设计倾向给 Research、Script、Audit、Director、Visual QA 分配不同模型，希望模型之间自然形成可靠制衡。

**原因。** 如果事实 contract、角色权限、输入隔离和裁决路径没有先定义，多一个模型只会多一个输出、成本和失败模式。多个模型还可能共享相似训练偏差。

**错误思路。** 用多数票代替证据；让生产模型阅读自己的解释后再“独立”审计；把 Provider 名称等同于角色能力。

**修复。** 建立角色 contract、Blind Review、ModelRun provenance、确定性 Validator 和 Human Gate。Proposal 不自动成为 Decision，模型分歧回流到 Research/owner，不自动多数投票。

**验证。** Provider/角色边界与 secret redaction 由 `vnext/tests/test_provider_activation.py` 和 Model Council 文档覆盖。

**限制。** 公开快照不含真实 Provider 凭据，跨 Provider 质量不是本次发布的实时基准。

**经验。** 先收紧 contract，再评估 model diversity；模型数不是质量指标。

## 2. Director 与 Renderer 权责不清

**问题。** ShotPlan 声明了语义意图，但 Renderer 又按 layer/type 自行选择构图和动画，导致同一 artifact 在不同路径含义不一致。

**原因。** `WHAT`、`HOW` 和 pixel execution 没有明确 owner。

**错误思路。** 把 x/y、width/height、CSS、crop pixels、easing 和 spring 参数交给 Director；或让 Renderer 为缺失字段“聪明补全”。

**修复。** Director 只决定 Visual Job、Mode、PRIMARY、Evidence Treatment、Character Role 和 Motion Semantic；Visual Compiler 拥有 geometry/numeric motion；Renderer 只消费 resolved artifact。

**验证。** [VLA Adapter Contract](project-brain/creative-spikes/VLA-001-director-shotplan/01_ADAPTER_CONTRACT.md)、[Open Source Architecture](OPEN_SOURCE_ARCHITECTURE.md) 和 visual-language tests 验证了 owner 边界。

**限制。** 最新 Director 路径尚未完整接入默认 Production GUI。

**经验。** 不要用“模型更聪明”掩盖责任不唯一；每个字段必须有一个权威 producer 和真实 consumer。

## 3. AI 生成视频为什么容易出现 PPT 感

**问题。** 画面虽有转场和元素动画，观看体验仍像页面模板轮播。

**原因。** 主要症状是一个镜头只有一个静态 layout state、所有元素同一 progress 同时出现、PRIMARY 不明确、缺少因果连续性和 secondary response。

**错误思路。** 增加更多模板、飞入效果或更强 easing；让 XIAO-Y 每镜都做动作；用装饰性动画掩盖信息职责不清。

**修复。** `XIAO-Y Evidence Editorial` 规定 Evidence proves、XIAO-Y explains、Typography emphasizes、Motion guides attention；一个时刻一个 PRIMARY；引入 Motion phrase 与 anticipation/action/impact/response/settle/hold 阶段。

**验证。** [VGB-002 comparison](project-brain/creative-spikes/VGB-002-fusion/04_COMPARISON.md)、[VPS results](project-brain/creative-spikes/VPS-001-visual-progression/04_RESULTS.md) 与 [MDC results](project-brain/creative-spikes/MDC-001-motion-design-contract/05_RESULTS.md) 记录了受控比较。

**限制。** 受控短样片通过不等于完整 3–5 分钟视频稳定无 PPT regression。

**经验。** PPT 感是视觉责任和时间结构问题，动画数量通常不是答案。

## 4. ShotPlan 与实际 Renderer 行为不一致

**问题。** ShotPlan 字段存在并不代表输出真的使用它；有些字段只被序列化，没有消费点。

**原因。** Producer schema 与 Renderer implementation 分开增长，没有 capability conformance test。

**错误思路。** 看到 JSON 字段就宣布能力完成；对未知值静默退化为默认动画。

**修复。** 为 ShotPlan/Visual Compiler/Renderer 建立明确消费链；unknown/unsupported contract fail-fast；preview 和 render 共享同一个 resolved composition。

**验证。** `vnext/tests/test_director_shotplan_adapter_v1.py`、`test_visual_language_v1.py`、`test_motion_primitive_hardening_v1.py` 和 preview/render equivalence tests。

**限制。** GUI 中对所有字段的人工编辑体验仍不完整。

**经验。** 完成标准应是“字段改变能导致可解释、可测试的输出改变”，而不是“字段出现在 schema”。

## 5. 真实 Evidence 被非等比拉伸

**问题。** 一次真实回归中，截图 region 的 width 和 height 分别参与反向缩放，导致 Evidence 形变。

**原因。** CropImage 将矩形填满误实现为独立 `scaleX/scaleY`，没有区分 registered media 与 procedural geometry。

**错误思路。** 用“刚好填满框”作为视觉正确性；仅靠 contact sheet 人眼发现形变。

**修复。** 建立 Asset Aspect-Ratio Invariant：真实图片、视频、角色 PNG、logo、imported SVG 只允许 contain、uniform cover+crop、uniform focus zoom/pan；程序化线/框/path 可形变。机械 QA 增加 `ASSET_ASPECT_RATIO_DISTORTED` BLOCKER。

**验证。** [Post-review incident](project-brain/creative-spikes/VLA-001-director-shotplan/POST_REVIEW_ASSET_DISTORTION.md) 与 aspect-ratio/visual-language regression tests。

**限制。** 语义 focus crop 仍需正确 locator；保持比例不保证裁切内容有意义。

**经验。** 媒体比例是 invariant，应由代码阻止，不能只靠视觉审片。

## 6. 音频时序与语义断句混淆

**问题。** “音频这里有停顿”“字幕应在这里换行”“镜头应在这里切”被当成同一判断。

**原因。** 系统用一套 segment 同时承担声学观测、语义结构与视觉时序。

**错误思路。** 让 ASR timestamp 覆盖 Script/Director 的 beat；把 TTS 不自然停顿修成镜头切点。

**修复。** 明确三层：Prosody 处理音频本身如何说；Semantic system 决定 WHAT/是否分段；Alignment 只提供批准文本锚点在最终音频中的 WHEN。

**验证。** [TCU consumers](project-brain/creative-spikes/TCU-001-timing-consumer/02_CONSUMERS.md) 与 [FAI runtime](project-brain/creative-spikes/FAI-001-alignment-runtime/02_RUNTIME_LIFECYCLE.md)。

**限制。** 公开快照不含私有音频；ATS 的精度结论主要来自 Sample A。

**经验。** 准确时间戳不能替代语义政策，也不能修复坏的 TTS prosody。

## 7. Whisper 分段不能直接作为镜头切点

**问题。** ATS-001 中 raw Whisper segmentation 在禁止切分区制造错误边界。

**原因。** ASR 为识别优化，会受停顿、韵律和模型窗口影响；segment boundary 不是作者批准的叙事结构。

**错误思路。** 把 Whisper segments 直接转换为 Beat/Shot/Subtitles。

**修复。** 对 approved text anchors 做 transcript alignment；raw segments 只作为观测，semantic boundary 仍由 Script/Director contract 决定。

**验证。** [TCU Sample A A/B](project-brain/creative-spikes/TCU-001-timing-consumer/03_SAMPLE_A_AB.md) 记录禁止切分区和 consumer 比较。

**限制。** 多说话人、双语、数字和专有名词仍需更广样本。

**经验。** 使用 ASR 的强项定位 WHEN，不要让它越权决定 WHETHER TO CUT。

## 8. Timing 精度提高，但下游没有消费

**问题。** 更准 word timing 生成成功，字幕或镜头却没有变化。

**原因。** 上游 capability 没有映射到 EDT consumer；或者 consumer 仍读取旧 beat timing。

**错误思路。** 仅用 alignment accuracy 宣布产品价值；先生产化昂贵能力，再找用途。

**修复。** TCU-001 逐个审计 Existing Beat、Subtitle 等 consumer，要求 provenance 显示实际 timing source，并保留 CURRENT fallback。

**验证。** [TCU results](project-brain/creative-spikes/TCU-001-timing-consumer/04_RESULTS.md) 明确 Existing Beat Timing 受益，而 Subtitle 当时没有证明收益。

**限制。** ALIGNED 仍为 opt-in，不是 production default。

**经验。** 先证明 consumer 吃到了变化，再升级 upstream capability。

## 9. TTS Prosody 与 Alignment 是两个问题

**问题。** Alignment 可以告诉系统坏停顿发生在何时，却不能让已生成音频重新自然表达。

**原因。** Prosody 属于合成阶段，Alignment 属于后验定位阶段。

**错误思路。** 用时间映射或画面重切“修复”声音本身；把听感问题归因于 timestamp 不准。

**修复。** Voice artifact 保留 provider/profile/provenance；Prosody QA 与 Alignment runtime 分离，失败各自回到 owner。

**验证。** Voice registry/secret tests 与 timing spike 文档验证了结构边界；真正 prosody 自动修复仍未完成。

**限制。** 这是部分验证、部分设计结论；公开快照没有形成 production Prosody QA。

**经验。** 先判定声音坏了还是同步坏了，再决定重合成或重对齐。

## 10. Motion Primitive 声明与实现不一致

**问题。** vocabulary 中存在 `MATCHED_WIPE`、`DRAW_CONNECTION` 等 primitive，但 Renderer 曾未完整消费，造成能力幻觉。

**原因。** schema、compiler 与 renderer 独立扩展；未知 primitive 静默 fallback。

**错误思路。** 把 enum 数量当 motion 能力；让 unsupported layer/primitive 自动当成 NONE。

**修复。** MPH-001 建立权威 primitive/layer matrix、真实 consumer、fail-fast 和 gallery contract。

**验证。** [Primitive contract](project-brain/creative-spikes/MPH-001-motion-primitive-hardening/02_PRIMITIVE_CONTRACT.md)、[render validation](project-brain/creative-spikes/MPH-001-motion-primitive-hardening/03_RENDER_VALIDATION.md) 与 motion primitive tests。

**限制。** 支持 primitive 不保证镜头设计质量。

**经验。** `declared capability == rendered capability`；明确不支持比假支持更安全。

## 11. Motion Design 缺少主次、错相和收束

**问题。** primitive 都能动，但所有元素仍同时开始、同强度、无响应，镜头缺乏导演感。

**原因。** Primitive 描述局部效果，不描述镜头整体 attention order 和 phrase structure。

**错误思路。** 添加更多 primitive；用统一 progress 驱动所有 layer。

**修复。** MDC-001 引入 renderer-neutral phrase、PRIMARY/SECONDARY responsibility、phase offset、intensity、settle/hold，再由 compiler 生成帧与曲线。

**验证。** [MDC contract](project-brain/creative-spikes/MDC-001-motion-design-contract/01_MOTION_DESIGN_CONTRACT.md)、[deterministic compiler](project-brain/creative-spikes/MDC-001-motion-design-contract/02_DETERMINISTIC_COMPILER.md) 和 MDC tests。

**限制。** Motion Design 默认仍关闭，未完整接入 GUI。

**经验。** 运动系统要表达注意力和因果顺序，而不仅是组件动画 API。

## 12. 静态 Storyboard 不能完整审查动态效果

**问题。** Contact sheet 能看构图和文字，却看不到 simultaneous motion、overshoot、secondary 抢焦、settle 生硬或 phase offset 缺失。

**原因。** 动态问题在时间轴上发生，静态抽帧丢失运动轨迹和节奏。

**错误思路。** 只看代表帧就批准 motion；或完全跳过 render 前 Storyboard Gate。

**修复。** Storyboard Review 仍负责 semantic/asset/PRIMARY；Motion Preview/temporal strip 负责动态 contract；最终视频还需 H3 人工审片。

**验证。** [MDC manual review](project-brain/creative-spikes/MDC-001-motion-design-contract/04_MANUAL_REVIEW.md) 记录了双视角审查。

**限制。** 公开快照移除了原视频/contact sheet 二进制；结论和结构化结果保留。

**经验。** 静态和动态审查互补，任何一方都不能替代另一方。

## 13. 模型自检不等于独立审查

**问题。** 同一模型生成后解释自己的选择，往往会合理化原输出；即使换模型，如果看到主模型完整推理，也会被锚定。

**原因。** 审查输入不独立、权限不隔离、审查标准不结构化。

**错误思路。** 把“请检查一下”当 QA；允许 QA 直接修稿；让模型同时生产、裁决和批准。

**修复。** Blind Review 首轮只看原资料、产物和 rubric；QA 有否决权无修稿权；修复由 owner 完成；Human Gate 做最终判断。

**验证。** `WORKFLOW_CONSTITUTION.md`、Council protocol、Audit/QA contract tests。

**限制。** 真正异构模型的独立性仍受供应商和训练数据影响。

**经验。** 独立审查是输入、角色、权限和裁决流程的属性，不是模型品牌标签。

## 14. 多分支并行导致已修复问题重新出现

**问题。** FAI 与 Asset Aspect Ratio Hardening 从共同基线分叉；直接沿一条分支继续会重新带回另一条已修复的 crop 缺陷。

**原因。** 以“最新日期/最高 commit”代替 capability matrix；实验分支缺少集成基线。

**错误思路。** 把所有分支无选择 merge；或只挑看似最新的一条继续。

**修复。** 建立 `p0/v1-integration-baseline-1`，先验证 timing、visual、fallback 和 aspect-ratio 能力共同存在，再开展 MPH/MDC。

**验证。** [Integration baseline](project-brain/creative-spikes/V1-INTEGRATION-BASELINE-1.md) 与之后 270-test regression。

**限制。** 私有仓库仍保留复杂历史；公开仓库因此使用 fresh snapshot history。

**经验。** 并行实验合并前按能力矩阵验收，不按分支名字猜完整性。

## 15. 后端 E2E 通过不等于 GUI 产品可用

**问题。** API、测试和脚本可以创建 artifact、渲染和导出，但普通用户仍可能需要 curl、Terminal、手改 JSON 或 DB。

**原因。** 工程验收覆盖函数和接口，却没有覆盖用户只通过 UI 完成任务的路径、失败恢复和长任务反馈。

**错误思路。** 把 TestClient/API chain 称为产品 E2E；把 exporter 代码存在称为已完成真实交接。

**修复。** 将 GUI-only E2E 定为 P0：创建项目到 Export 不允许内部逃生通道；明确代码实现、GUI 可用和当前项目产物是三件事。

**验证。** 现有 GUI interim 证据只证明部分链路。GUI-001 未完成，未提交工作树不进入公开基线。

**限制。** 这是当前最大缺口。

**经验。** 产品完成定义必须从用户行为写，不从模块清单写。

## 16. 功能范围持续扩大导致开发周期失控

**问题。** Research、Writer、Director、Voice、Timeline、QA、Analytics、Publish、Jianying、Provider、Creative Composer 等同时扩张，维护面增长快于生产价值。

**原因。** 每次发现问题都倾向增加 Agent、schema 或子系统，而不是先问现有 consumer 是否需要、默认路径是否闭环。

**错误思路。** 为了架构完整继续补齐所有角色；在 GUI-only E2E 之前开发新的视觉或模型系统。

**修复。** Roadmap 收缩：P0 只做 GUI-001；ALIGNED/Motion 保持 opt-in；Creative Composer 必须由真实 expressive gap 触发。

**验证。** [Open Source Roadmap](OPEN_SOURCE_ROADMAP.md) 和 [Maintainer Handoff](MAINTAINER_HANDOFF.md) 固化优先级。

**限制。** 收缩本身尚未完成 GUI-001，只阻止继续扩大。

**经验。** 新 capability 必须回答谁消费、如何回退、如何审查、何时失效、是否改善成片。

## 17. 为什么最终选择暂停，而不是继续堆功能

**问题。** 核心实验持续 PASS，但系统仍未成为普通用户可稳定日用的产品。

**原因。** 视频生产链很长，单人维护成本高；生态工具快速变化；更多局部优化的边际收益下降；最大的剩余工作是产品收口而非算法数量。

**错误思路。** 因为实验成功就继续增加新模型、模板、motion phrase 或 creative generator；把 sunk cost 当成继续开发理由。

**最终处理。** 停止主动功能开发，冻结最新通过回归的 MDC baseline，做 sanitized snapshot、fresh history、安全/许可证审计和诚实交接。

**验证。** 开源快照在删除私有资产、加入 synthetic fixtures 后重新运行 270 tests、TypeScript 和 Workbench/render smoke；发布报告记录实际结果。

**限制。** 暂停不证明商业可行，也不否定架构价值；它只是当前维护决策。

**经验。** 工程研究成果可以在产品尚未完成时有价值。诚实标注边界、失败和未完成项，比继续扩大一个无人能维护的系统更有用。
