# Contributing

感谢你愿意继续这个项目。

## Before coding

建议先读：

1. `README.md`
2. `docs/OPEN_SOURCE_ARCHITECTURE.md`
3. `docs/LESSONS_LEARNED.md`
4. `docs/MAINTAINER_HANDOFF.md`

## Architectural constraints

PR 尽量不要破坏以下边界：

- Evidence / Fact / Claim / Script 可追溯；
- Director / ShotPlan 不拥有 pixel geometry；
- Alignment 不决定 semantic boundary；
- Visual Compiler 是 numeric geometry/motion owner；
- Renderer 不重新做 creative policy；
- registered media 禁止 non-uniform stretch；
- declared motion capability 必须有真实 consumer；
- Human Gate 不应被同一模型自审替代。

## Tests

Python：

```bash
CONTENT_OS_TEST_NO_KEYCHAIN=1 .venv/bin/python -m pytest vnext/tests -q
```

Remotion / TypeScript：

```bash
cd vnext/renderers/remotion/project
npm ci
npx tsc --noEmit
npm run build:monitor
```

涉及视觉行为的 PR，建议提供：
- before / after；
- exact input hash 或 fixture；
- mechanical QA；
- manual review note；
- regression result。

## Security

不要提交：
- API keys；
- cookies；
- Keychain export；
- 用户声音；
- private media；
- model weights；
- 未确认再分发许可的字体。

## Scope discipline

“能做”不代表“应该现在做”。

如果新 capability 无法说明：
- 谁消费它；
- 如何回退；
- 如何审查；
- 如何失效；
- 是否真的改善成片；

请先做 spike，不要直接塞 production path。
