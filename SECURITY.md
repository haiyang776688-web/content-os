# Security Policy

## Project scope

Content OS 当前是本地单用户工作台实验项目，不应直接暴露为公网多租户服务。

## Secrets

支持的 secret 来源应是：
- macOS Keychain；
- 开发环境变量。

Secret 不应进入：
- project artifact；
- exported JSON；
- logs；
- evidence packages；
- Git。

公开快照不包含真实 API key、用户声音、clone reference、模型权重或私有字体副本。

## Local-only data

`LOCAL_ONLY` 内容不应被自动上传到云 Provider。任何 cloud fallback 仍需满足原 capability、privacy 和 budget policy。

## Reporting

如果你发现会泄露凭据、用户媒体或本地文件的漏洞，请不要把真实 secret 放进公开 Issue。使用最小复现和脱敏日志描述问题。

当前项目处于 paused 状态，维护响应时间不保证。
