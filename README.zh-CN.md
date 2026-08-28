# Handoff Guard（交接守卫）

[English](README.md) | 简体中文

> 交接守卫是面向编码代理的模型感知交接技能：保存已经确定的决策，推荐足够且成本最低的模型，并在接收任务的代理开始执行前检查配置。

交接守卫工作在交接和决策层：为接收任务的代理提供模型提供方和模型推荐，并在开始实施前执行检查。它不会自动切换模型或模型提供方。

## 项目简介

代理交接时，通常会同时丢失两类信息：一是当前实现状态和已经确定的架构决策，二是下一阶段应该使用什么模型。结果可能是新代理重新探索已经决定的方案、简单任务使用昂贵模型，或者复杂任务交给明显不足的模型。

交接守卫把这三件事放进一个轻量工作流中：

- **结构化交接：** 保存当前状态、已完成内容、检查点、已经确定的决策和执行约束。
- **模型推荐：** 使用透明的启发式规则，推荐模型提供方、模型档位、具体模型和推理强度。
- **执行前检查：** 在真正修改文件前检查当前配置，并返回 `PASS`、`BLOCK` 或 `UNVERIFIED`。

## 与 model router 和普通交接技能的区别

交接守卫不是运行时 LLM Gateway，也不是自动 model router。

model router 属于自动路由或自动选择模型的另一类工具，工作在模型调用层，可以直接把请求分发到不同模型或模型提供方。

普通交接技能主要负责交接哪些内容。交接守卫除了保存交接信息，还会为下一阶段推荐模型提供方和模型，并在工作代理真正执行前检查当前配置是否适合开始执行。

交接守卫不负责自动切换模型。推荐结果是提供给宿主环境和用户的决策信息，不代表它拥有自动调用其他模型、切换模型或迁移当前会话的权限。

## 交接守卫不是什么

交接守卫不是运行时大语言模型网关，也不是 model router 这一类自动路由工具。

它不能控制 ChatGPT 的模型选择器，不能自动切换模型或模型提供方，也不会自动迁移当前会话或把请求分发到另一个模型。需要切换时，它会告诉用户应该手动选择什么。

如果宿主环境无法可靠读取当前模型或推理强度，交接守卫会返回 `UNVERIFIED`（未验证），而不是把配置当成不匹配。它会明确说明无法验证，展示推荐配置，但不会因此阻止执行。

## 交接生成边界

只有在能够可靠确认当前是普通聊天 / 讨论场景，并且已经形成明确开发边界时，交接守卫才会自动生成交接。这里的开发边界包括：已经确定的架构决策、具体的下一阶段实施方案，或阶段性验收 / 检查点结论。

只要当前线程访问或修改过项目文件、运行过终端命令、修改过代码、执行过测试、进行过 Git 操作，或出现其他明显的代码实施行为，就视为工作 / 实施环境（Work / implementation 环境）。此时交接守卫不会递归生成或附带新的工作交接，即使任务已完成、已有检查点或提交，或者已经形成下一阶段计划。如果无法可靠判断当前模式，默认不自动生成。如果用户明确要求“给我一个工作交接”或“生成交接”，则可以覆盖这一自动限制。

## 核心工作流程

```text
聊天 / 架构代理
        |
        | 结构化交接
        | + 模型提供方 / 模型推荐
        v
接收任务的工作代理
        |
        v
执行前检查
        |
+----------------+----------------+----------------+
|配置合适        |明显不匹配      |无法确认        |
|                |                |当前配置        |
|                |                |                |
|PASS            |BLOCK           |UNVERIFIED      |
|                |                |                |
        v                v                v
|按范围执行      |停止执行并提醒  |说明无法验证，  |
|                |用户手动切换    |但允许继续执行  |
        \                |                /
         +---------------+----------------+
                         |
                         v
                     更新检查点
```

三种执行前检查结果的含义如下：

- **PASS：** 已知配置符合要求，按范围正常执行。
- **BLOCK：** 已确认存在明显配置不匹配，停止执行并提醒用户手动切换模型。
- **UNVERIFIED：** 无法可靠读取或确认当前模型或推理强度；明确说明无法验证，但不得因此阻止执行。

## 安装方式

将 `handoff-guard` 文件夹复制到代理可以发现的技能目录：

```text
$CODEX_HOME/skills/handoff-guard/
```

如果没有设置 `CODEX_HOME`，请使用宿主代理的标准用户技能目录（通常是 `~/.codex/skills/`）。文件夹根目录必须包含 `SKILL.md`。技能会自动被发现；界面元数据位于 `agents/openai.yaml`。

### 插件安装

仓库同时包含一个仅含技能的插件清单。插件的标准技能路径是 `skills/handoff-guard/SKILL.md`；根目录的 `SKILL.md` 仍然保留，用于直接从 GitHub 按原来的技能方式安装。插件有意不包含 MCP 服务器或应用清单。

审核并进入 OpenAI 插件目录后，这里可以补充“Install from ChatGPT Plugin Directory”的安装说明。目前交接守卫尚未上架该目录。

提交前品牌素材待办：准备经过审核且具备相应用权的标识图标后，再将路径写入 `.codex-plugin/plugin.json`。当前清单不虚构或声明任何标识图标。

## 使用方式

在普通聊天 / 讨论场景形成架构或实施边界时，请代理生成交接守卫交接。在工作 / 实施环境中，完成实施后不会自动附带交接；如确实需要，请明确请求生成。请使用 `assets/handoff-template.md`，并填写真实的提交、文件检查点，或明确写 `none`。

### 模型推荐

使用选择器：

```bash
python scripts/select_model.py --input '{"task_complexity":"moderate","task_type":"implementation","architecture_settled":true,"provider_availability":["codex","workbuddy"]}'
```

选择器会把工作量复杂度和推理 / 决策风险分开判断。文件数量、代码量、仓库数量、阅读量或提示词长度本身，绝不能单独把任务升级到 Sol / strong。

只读审计、研究、能力盘点、复用审计、文档、测试，以及在已确定架构上的大量实现，默认使用 Luna / general。只有首次定义核心架构或数据模型、高歧义、高影响范围、高不可逆性、数据完整性风险、破坏性操作、新的跨系统契约，或 Luna 已有两次明确失败等独立高风险信号，才升级到 Sol / strong。当前策略下，Luna 和 Sol 默认都使用 Medium 推理强度。

选择器支持可选的路由维度，包括 `operation_mode`、`decision_novelty`、`ambiguity`、`blast_radius`、`irreversibility`、`cross_system_contract`、`data_integrity_risk`、`destructive` 和 `prior_failed_attempts`。选择器只输出推荐，不会调用或切换宿主中的模型。

### 执行前检查

当宿主能提供这些信息时，把 `current_model` 和 `current_reasoning_effort` 一起传入。结果会包含：

- `PASS`：当前模型已知且合适，可以继续。
- `BLOCK`：当前模型明显过强或过弱，应停止并请用户手动切换。
- `UNVERIFIED`：宿主没有可靠提供模型或推理强度信息。显示推荐并允许继续执行。

推理强度在 `medium` / `high` 之间的轻微差异默认不会阻止执行。

### 无法确认模型时的行为

无法确认只提供提示，不会阻止执行：无法检测当前模型不等于模型不匹配。交接守卫会显示推荐模型和推理强度，提示用户按需手动核对，但不会仅因无法确认而拒绝执行。

回归示例：

- 首次定义 Conversation Pair / Relationship 核心数据模型，并处理上下文边界、缓存兼容和 Runtime 行为 → `Sol`、Medium。
- 只读审计 OpenSelf、Talky、Crush.skill、ex-skill、Chat-Style-Bot 和 WeChat-AI → `Luna`、Medium，即使涉及多个仓库。

这些只是路由策略检查，不能证明宿主一定提供对应模型，也不能证明真实产品对话中一定触发 Skill。

## 模型提供方回退 / WorkBuddy 示例

当用户表示 GPT / Codex 没有额度，或者希望节省 GPT 额度时，这是**回退推荐**，不是**自动切换模型提供方**。

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
推荐模型提供方：WorkBuddy
推荐模型：HY3
推荐推理强度：Medium
操作：请根据当前宿主环境手动切换
```

默认 WorkBuddy 配置包含 Auto、HY3、GLM-5.3、GLM-5.2、GLM-5.1、GLM-5V-Turbo、MiniMax-M3、Kimi-K3、Kimi-K2.7-Code、Kimi-K2.6、Deepseek-V4-Flash 和 Deepseek-V4-Pro。模型档位和成本类别是可维护的启发式配置，不是基准排名，也没有把未确认的倍率写死。

## 交接校验

校验 Markdown 或 JSON 格式的交接：

```bash
python scripts/validate_handoff.py path/to/handoff.md
```

缺少必要字段时会返回错误并使用非零退出码。

## 真实 ChatGPT Chat 环境人工 A/B 验收

仓库内 selector 测试不能验证 ChatGPT Chat 模式是否发现并触发该 Skill，也不能验证 Skill 与 Custom Instructions 冲突时的行为。仓库测试通过后，需要在真实产品环境中人工验收。

### A. Skill-only

1. 备份当前 Handoff 自定义指令。
2. 暂时移除或禁用这些自定义指令。
3. 安装 GitHub 发布的 Handoff Guard Skill。
4. 新建普通 Chat 对话。
5. 依次测试固定任务：README 修改；小型 UI bug；复杂但只读的 GitHub reuse audit；已定架构下的大量实现；首次定义 Relationship Skill 架构；destructive database migration；以及 Luna 已两次明确失败后的复杂 bug。
6. 记录 Skill 是否触发、推荐模型、推荐推理强度、handoff 是否正确，以及是否出现不必要的 `BLOCK` / `UNVERIFIED`。

### B. Custom-Instructions-only

禁用或卸载 Skill，恢复原 Handoff 自定义指令，在新对话中重复相同或语义等价的任务，并记录相同指标。

### C. 对比

对比触发稳定性、模型推荐准确率、是否经常过度升级 Sol、错误阻断、handoff 格式一致性，以及 token / 指令长度负担。不要在没有人工测试数据前声称 Skill 一定优于 Custom Instructions。

如果已经安装 Skill，可选用以下最小自定义指令：

```text
开发任务形成 handoff 时，优先使用已安装的 Handoff Guard Skill 生成并验证 handoff 与模型推荐。
```

这只是触发建议；核心路由策略应保留在 Skill 内，避免两套完整规则发生漂移。

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

## 插件提交测试

`evals/plugin-submission-tests.json` 包含 7 个正向和 8 个反向用例，用于插件审核。它们覆盖普通聊天中创建交接、用户明确请求、工作环境防递归、已知模型执行前检查、明显不匹配、模型提供方回退，以及模型或推理元数据不可用时返回 `UNVERIFIED` 且不阻断执行的规则。

## 限制

- 路由使用透明的启发式规则，不是基准测试，也不是实时价格比较。
- 模型提供方是否可用由调用方提供；技能不会调用模型提供方接口。
- 成本类别是粗粒度配置标签，应由项目维护者维护。
- 交接不能证明实施一定正确；它只能保存执行契约并校验必要字段。

## 后续计划

- 在不改变选择器逻辑的前提下增加更多模型提供方配置。
- 保持核心交接契约小而稳定，同时支持项目级可选字段。
- 为更多代理环境增加独立评测用例。

## 许可证

MIT，详见 [LICENSE](LICENSE)。
