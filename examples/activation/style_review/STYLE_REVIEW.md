# XIAO-Y 动态讲解 · 视觉修订审查

用户目标：参考XIAO-Y视频模板，避免PPT感。2026-09-28完成当前项目增量修订。

![动态分镜完整预览] *(private local evidence not distributed)*

视频容器实测84.821秒，1920×1080，30fps，包含原本地克隆配音；原始配音84.76秒，保持本机，没有重新合成、变速或上传。

这是一份动态分镜审查预览（ART-f0e9fd4957414934），尚非已批准终稿。当前分镜第5版 ART-21f9a5f47d5e42bd，EDT第6版 ART-a539dfcdeacc4c0f。

## 已实现的视觉变化

- 沿用现有XIAO-Y动作与模板。8种构图、13个动作，人物全身、脸部特写、左右镜头、纯文字、对比区交替。
- 本机Hiragino Sans GB W6真实600字重，重点大字134px。黄色划线、红色强调、红黄编号和灰黄对比均由帧时间决定。
- 要点依序进入，文字上移或轻微放大；文字和人物各自有入场时序，不再全部统一FADE。
- 45屏短字幕，最长16字，保持单行白字阴影。按标点拆句，按字符比例在实测段落边界内分配，不宣称逐词精确对齐。
- 使用已注册PNG动作切换与镜头、文字动画；没有把它描述为角色骨骼动画或口型同步。

## 检查与边界

当前机械报告 ART-62ce28372dc34cbe 为PASS，无问题项。整段视音频解码成功，18个节拍各抽帧检查。浏览器实际持续播放后暂停至70.68秒。186项全量测试通过，随后30项相关闭环测试通过；TypeScript检查通过。85个受保护包文件和两个既有诊断项目均保持不变。没有新增云模型调用。

旧第3版Gate ART-8e713ecd20464456 的实际用户批准和基线渲染历史保留。视觉、字号、动作和字幕已经改变，旧批准不转授当前版本。新版Storyboard Gate、正式RENDER、当前成片MiniMax视觉审查、H3仍待完成。H4没有授权。

按用户原始需求第60节“真实 Provider 接入后仍保持：H2 / Storyboard Gate / H3”，看过本动态预览后批准当前分镜，才可正式渲染并送成片审查。之后再单独确认H3。

## 实际视频抽帧

![动态预览抽帧1] *(private local evidence not distributed)*

![动态预览抽帧2] *(private local evidence not distributed)*

![动态预览抽帧3] *(private local evidence not distributed)*

![工作台预览] *(private local evidence not distributed)*
