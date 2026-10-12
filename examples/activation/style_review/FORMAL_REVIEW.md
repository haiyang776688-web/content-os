# XIAO-Y 正式成片 · H3 审片材料

2026-09-28，项目 `PRJ-bba515713057`。用户已批准第 5 版分镜，工作台 Storyboard Gate 为 `ART-1161bdc7bf2b4403`。

![正式成片] *(private local evidence not distributed)*

正式 RENDER `ART-af53e1287e9e44c8`：1920×1080、30fps、84.821 秒。沿用锁定的 SCRIPT v4、YU_LOCAL_V1 本地配音与 EDT v6。正式渲染和已批准动态分镜画面参数相同；H.264 解码帧并非逐字节相同，整段画面 SSIM 为 0.999786。工作台已完整播放到结尾。

本地机械 QA `ART-bce6b4a73c3e4b51` 为 PASS。用户随后明确允许仅当前片中 13 张 XIAO-Y 图片改为 `ASK_BEFORE_UPLOAD`，并进行一次 MiniMax 视觉 QA。音频、样本和字体文件仍留在本机；送审副本仅有视频流，`audio_transmitted=false`，审查范围 `VISUAL_ONLY`。真实 MiniMax QA `ART-c16619f572da4846` 返回 `PASS_WITH_RISK`。请求的计费状态为 UNKNOWN，不推断具体金额。

模型共给出 1 条 WARNING 与 5 条 INFO。其中唯一 WARNING 在它标注的 0–5.5 秒并未被实际画面支持；多条 INFO 对不上所写的节拍和时间戳。模型正确指出结尾没有单独 Logo 或「关注」按钮；锁定脚本也没有要求关注口播。详细逐条核对、时间线证据和抽帧见 [MiniMax QA 复核](MINIMAX_QA_TRIAGE.md)。原始 QA artifact 不改写。终审包 `ART-3c05fee5a13d41b6` 已生成，保留 WARNING 供人工裁定；INFO 留在原报告，不计入需要确认的风险。

用户已在对话回复“通过”，H3 终审关卡 `ART-98b97704be3f4aa2` 已登记为 `APPROVE_WITH_RISK`，附 MiniMax 警告的复核结论。关卡明确记录 `publish_authorized=false`。**H4 发布尚未授权，未发布。** 若后续决定加结尾品牌 CTA，需由脚本/导演责任模块处理并重新走相应关卡，不由 QA 代写。

[机器验证记录](FORMAL_RENDER_VERIFICATION.json) · 工作台播放画面：**PRIVATE EXPERIMENT EVIDENCE NOT DISTRIBUTED**
