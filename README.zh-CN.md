# Handoff Guard

[English](README.md) | 简体中文

> Handoff Guard 是面向 coding agent 的 model-aware handoff skill：保存已经确定的决策，推荐足够且成本最低的模型，并阻止明显不合适的模型开始执行。

它工作在 handoff / decision 层：根据任务信息给出 provider、model 和 reasoning effort 建议，并在执行前检查当前配置是否明显不合适。

## 项目简介

Agent 交接时，通常会同时丢失两类信息：一是当前实现状态和已确定的架构决策，二是下一阶段应该使用什么模型。结果可能是新 Agent 重新探索已经决定的方案、简单任务使用昂贵模型，或者复杂任务交给明显不足的模型。

Handoff Guard 把这三件事放在一个轻量工作流中：

- **Model-aware handoff：** 保存当前状态、已完成内容、checkpoint、锁定决策和 guardrails。
- **Model recommendation：** 使用透明 heuristic 推荐 provider、model tier/model 和 reasoning effort。
- **Execution preflight：** 在真正修改文件前返回 `PASS`、`BLOCK` 或 `UNVERIFIED`。

## 和 Model Router、普通 Handoff Skill 的区别

传统 Model Router 工作在模型调用层，可以直接把请求 dispatch 到不同模型或 Provider。

普通 Handoff Skill 主要负责交接什么内容。Handoff Guard 除了保存交接信息，还会推荐下一阶段应该使用的模型/provider，并检查当前模型是否适合开始执行。

Handoff Guard 的推荐结果是给宿主环境和用户使用的决策信息，不代表它拥有自动调用其他模型的权限。

## Handoff Guard 不是什么

Handoff Guard 不是运行时 LLM Gateway，也不是真正意义上的自动 Model Router。

它不能控制 ChatGPT 的模型选择器，不能保证自动切换模型或 Provider，也不会自动迁移当前会话或把请求 dispatch 到另一个模型。需要切换时，它会告诉用户应该手动选择什么。

如果宿主环境无法可靠读取当前模型，Handoff Guard 会将其标记为“未验证”，而不是“模型不匹配”；它会展示推荐配置，但不会因此阻止执行。Unknown is advisory, not blocking。

## 核心工作流程

```text
Chat / Architect Agent
        |
        | 结构化 handoff + 模型/provider 推荐
        v
接收任务的 Work Agent -----> execution preflight
                              |
                 +------------+------------+
                 |                         |
             配置合适                    明显不匹配
                 |                         |
                 v                         v
             按范围执行              BLOCK，提醒用户手动切换
                 |
                 v
            更新 checkpoint
```

## 安装方式

将 `handoff-guard` 文件夹复制到 Agent Skills 可发现的目录：

```text
$CODEX_HOME/skills/handoff-guard/
```

如果没有设置 `CODEX_HOME`，请使用宿主 Agent 的标准用户 skills 目录（通常是 `~/.codex/skills/`）。文件夹根目录必须包含 `SKILL.md`。

### Plugin 安装

仓库同时包含一个纯 skills-only Plugin manifest。Plugin 的标准 Skill 路径是 `skills/handoff-guard/SKILL.md`；根目录 `SKILL.md` 仍然保留，用于直接从 GitHub 按原来的 GitHub Skill 方式安装。Plugin 不包含 MCP Server，也不包含 App manifest。

审核并进入 OpenAI Plugin Directory 后，这里可以补充“Install from ChatGPT Plugin Directory”的安装说明。目前 Handoff Guard 尚未上架该目录。

提交前品牌素材待办：准备经过审核且具备相应用权的 logo/icon 后，再将路径写入 `.codex-plugin/plugin.json`。当前 manifest 不虚构或声明任何 logo/icon。

## 使用方式

在架构或实现阶段交接时，请 Agent 生成 Handoff Guard handoff，并使用 `assets/handoff-template.md`。checkpoint 应填写真实 commit、文件 checkpoint，或明确写 `none`。

### 模型推荐

使用 selector：

```bash
python scripts/select_model.py --input '{"task_complexity":"moderate","task_type":"implementation","architecture_settled":true,"provider_availability":["codex","workbuddy"]}'
```

一般规则是：简单文档或机械修改使用 `budget`，已确定方案的普通实现使用 `general`，复杂架构和疑难 bug 使用 `strong`。selector 只输出推荐，不会调用或切换宿主中的模型。

### Preflight

当宿主能提供这些信息时，把 `current_model` 和 `current_reasoning_effort` 一起传入。结果会包含：

- `PASS`：当前模型已知且合适，可以继续。
- `BLOCK`：当前模型明显过强或过弱，应停止并请用户手动切换。
- `UNVERIFIED`：宿主没有可靠提供模型或 reasoning 信息。显示推荐并允许继续执行。

Medium / High reasoning effort 的轻微差异默认不会阻止执行。

### Unknown model 行为

Unknown is advisory, not blocking：无法检测当前模型不等于模型不匹配。Handoff Guard 会显示推荐模型和 reasoning effort，提示用户按需手动核对，但不会仅因 unknown 状态拒绝执行。

## Provider fallback / WorkBuddy 示例

当用户表示 GPT / Codex 没有额度，或者希望节省 GPT 额度时，这是 **fallback recommendation**，不是 **automatic provider switch**。

输入中可以声明：

```json
{
  "task_complexity": "moderate",
  "task_type": "implementation",
  "preferred_provider": "codex",
  "quota_unavailable": true,
  "quota_provider": "codex",
  "provider_availability": ["codex", "workbuddy"]
}
```

推荐结果示例：

```text
Recommended provider: WorkBuddy
Recommended model: HY3
Recommended reasoning: Medium
Action: 请根据当前宿主环境手动切换
```

默认 WorkBuddy profile 包含 Auto、HY3、GLM-5.3、GLM-5.2、GLM-5.1、GLM-5V-Turbo、MiniMax-M3、Kimi-K3、Kimi-K2.7-Code、Kimi-K2.6、Deepseek-V4-Flash 和 Deepseek-V4-Pro。tier 和 cost class 是可维护的 heuristic，不是 benchmark 排名，也没有把未确认的倍率写死。

## Handoff 校验

校验 Markdown 或 JSON handoff：

```bash
python scripts/validate_handoff.py path/to/handoff.md
```

缺少必要字段时会返回错误并使用非零退出码。

## 项目结构

```text
handoff-guard/
├── .codex-plugin/plugin.json
├── SKILL.md
├── skills/handoff-guard/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── README.md
├── README.zh-CN.md
├── LICENSE
├── references/
│   ├── handoff-spec.md
│   ├── provider-profiles.json
│   ├── provider-profiles.md
│   └── routing-policy.md
├── assets/handoff-template.md
├── scripts/
│   ├── select_model.py
│   └── validate_handoff.py
├── evals/evals.json
└── tests/
    ├── test_plugin_structure.py
    ├── test_select_model.py
    └── test_validate_handoff.py
```

## Plugin submission 测试

`evals/plugin-submission-tests.json` 包含 5 个 positive 和 3 个 negative fixture，覆盖 handoff 创建、已知模型 preflight、明显不匹配、Provider fallback、普通请求不触发，以及无法读取模型/reasoning metadata 时返回 `UNVERIFIED` 且不阻断执行。

## Limitations

- 路由是透明 heuristic，不是 benchmark，也不是实时价格比较。
- Provider 是否可用由调用方提供；Skill 不调用 Provider API。
- cost class 是粗粒度配置标签，不代表实时价格。
- Skill 不能证明实现一定正确，只能保存交接契约并校验必要字段。
- 是否能读取当前模型取决于宿主环境；无法读取时进入 advisory / unverified 模式。

## Roadmap

- 在不改变 selector 核心逻辑的前提下增加更多 provider profile。
- 保持核心 handoff 契约小而稳定，同时支持项目级可选字段。
- 为更多 Agent 环境增加独立 eval fixture。

## License

MIT，详见 [LICENSE](LICENSE)。
