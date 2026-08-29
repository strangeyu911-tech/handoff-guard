# Handoff Guard（交接守卫）

[English](README.md) | 简体中文

> 一个轻量、具备模型感知能力的工作流层，把 ChatGPT 中已经确定的方案安全、完整地交给编码代理执行。

Handoff Guard 帮助普通 Chat 判断什么时候应该从规划进入 Work，保存实施契约，推荐可靠完成任务所需的最低成本模型，并在接收代理修改文件前完成检查。

```text
Chat / Architect → 结构化交接 → 执行前检查 → Work
```

它不只是一段静态提示词。仓库中包含确定性的模型选择器、版本化交接契约、校验器、回归样例和执行边界规则。Custom Instructions 只是目前将这些能力接入 ChatGPT 的一种轻量运行适配层，不是产品的全部架构。

## 能做什么

- **判断交接时机**：只有普通 Chat 已经形成确定决策、具体实施方案或阶段检查点时，才自动生成交接。
- **保存实施契约**：传递当前状态、已完成内容、检查点、锁定决策、范围和约束。
- **推荐合适的模型**：把工作量和独立决策风险分开判断，避免“大任务必用最强模型”。
- **执行前检查**：在接收代理开始改文件前返回 `PASS`、`BLOCK` 或 `UNVERIFIED`。
- **让规则可以验证**：校验交接结构，并用回归样例持续检查模型路由策略。
- **引导安全安装**：Windows 上生成、校验并复制管理区块，由用户手动保存到 ChatGPT。

## 安装

### Windows Guided Install 引导安装器

主要发行文件为：

```text
HandoffGuard-Installer-v0.1.0.exe
```

从仓库的 [GitHub Releases](https://github.com/strangeyu911-tech/handoff-guard/releases) 下载并运行安装器。它会生成带版本标记的 Handoff Guard 管理区块，复制到剪贴板，并打开 [ChatGPT Web](https://chatgpt.com/)。最终粘贴和保存始终由你本人在 `Settings → Personalization → Custom Instructions` 中完成。

安装器不会读取、写入、保存、验证、备份、修复或卸载 ChatGPT 账户设置。当前没有公开的 Custom Instructions API，也没有可依赖的设置深链。安装器中的本地升级/移除工具只处理你主动粘贴进去的文本。

状态示例：`Handoff Guard 管理区块已复制。你的 ChatGPT 账户设置尚未发生任何变化。`

如果 Release 尚未发布安装文件，可以参照 [Windows 安装器构建与验收说明](docs/windows-installer.md)从源码构建。

安装过程会明确说明其使用 ChatGPT Custom Instructions。它是当前 ChatGPT 环境中的运行适配层；核心策略、模型路由、交接结构和校验属于独立的产品层。

### 手动安装

也可以打开 [CUSTOM-INSTRUCTIONS.md](CUSTOM-INSTRUCTIONS.md)，复制自动生成的运行配置，把它追加到现有 Custom Instructions 中，不能覆盖其他内容。

手动安装可以启用运行规则。请保留管理区块完整，以便按本地 Generate、Update 和 Removal 指引操作。

### Skill 适配层（高级）

现有 Skill 适配层继续保留，供能够加载 Agent Skills 的宿主使用。可以把仓库目录复制到宿主的标准 skills 目录，也可以使用 `.codex-plugin/plugin.json` 中仅包含 Skill 的 Plugin 清单。Plugin 的 canonical Skill 位于 `skills/handoff-guard/SKILL.md`，根目录 `SKILL.md` 可用于直接安装。

它是备用运行适配层，不是 Windows 主安装叙事。仓库不会把自己宣传为 OpenAI 官方集成，也不声称已经通过公开 Plugin Directory 的独立验证。

## 产品架构

```text
Handoff Guard
├─ Core（核心能力）
│  ├─ 交接边界策略
│  ├─ 模型与推理强度推荐
│  ├─ 交接结构
│  └─ 执行前检查
├─ Validation（验证层）
│  ├─ 确定性 selector 与 validator
│  ├─ eval 回归样例
│  └─ 自动测试
├─ Runtime adapters（运行适配层）
│  ├─ Windows Installer / Custom Instructions
│  └─ Skill adapter
└─ Guided install lifecycle（引导安装生命周期）
   ├─ 生成与复制
   ├─ 本地升级/移除文本变换
   └─ 在 ChatGPT 中手动保存
```

`runtime/custom-instructions.txt` 是 ChatGPT 运行适配层的 canonical template。Windows 安装器和自动生成的 `CUSTOM-INSTRUCTIONS.md` 都读取这一个文件，测试还会检查它是否覆盖 Core 的路由维度。因此安装器不会另外维护一套容易漂移的手写策略。

## Guided Install 管理区块

Windows 安装器不使用 UI Automation、桌面 selector、坐标点击、OCR、私有接口、token 或 cookie。管理区块包含版本和校验和：

```text
[HANDOFF-GUARD:BEGIN version=0.1.0 sha256=...]
...
[HANDOFF-GUARD:END]
```

- **生成**：在本地生成 canonical 管理区块。
- **复制**：把生成的区块或本地变换结果放到剪贴板。
- **升级**：对用户提供的文本只替换一个有效旧区块，并保留区块外内容。
- **移除**：生成仅删除 Handoff Guard 区块后的文本。
- **修复**：用户提供损坏区块后，在本地重新生成 canonical 区块。
- **校验**：在本地检查 payload、版本、标记格式和校验和；不能验证 ChatGPT 是否已粘贴、保存或同步。

安装器不会将 Custom Instructions 发送到自己的服务器或第三方，也不会访问 ChatGPT 凭据。当你手动把生成的区块保存到 ChatGPT 后，相关内容将按照 [OpenAI 的 ChatGPT 数据实践](https://openai.com/policies/how-your-data-is-used-to-improve-model-performance/)处理和同步。详见 [SECURITY.md](SECURITY.md)。

## 交接与执行前检查契约

只有能够可靠确认当前是普通 Chat / discussion，并且已经形成明确开发边界时，才允许自动生成交接。任何项目文件访问或修改、终端命令、代码变更、测试或 Git 操作，都表示当前是 Work / implementation 环境；Handoff Guard 不会在这里递归生成新的 Work handoff。无法确定环境时默认不自动生成。用户明确要求交接时，可以覆盖这个自动生成限制。

有效交接必须包含：

1. 推荐模型
2. 推理强度
3. 执行前检查
4. 当前状态
5. 已完成内容
6. 检查点（真实 commit、tag、文件检查点或 `none`）
7. 下一目标
8. 锁定决策与边界
9. 禁止事项与约束

请使用 [assets/handoff-template.md](assets/handoff-template.md)，并通过 `scripts/validate_handoff.py` 校验。

三种检查结果有严格边界：

- `PASS`：已知配置适合当前任务。
- `BLOCK`：已经确认存在明显模型档位不匹配或模型提供方额度冲突。
- `UNVERIFIED`：宿主无法提供可靠的模型或推理强度信息；给出人工核对提醒后允许继续。

未知信息只提醒，不阻断。Handoff Guard 不是运行时 LLM Gateway 或自动模型路由器，不控制 ChatGPT 模型选择器，也不会自动切换模型或提供方。

## 模型路由策略

Selector 会把任务类型与独立决策风险分开判断。文件数量、仓库数量、代码量、阅读量、提示词长度或 `task_complexity` 本身都不会把任务自动升级到 Sol / strong。

- **Luna / general、Medium**：研究、只读审计、能力盘点、文档、测试，以及在已确定架构上的实施，即使工作量很大也一样。
- **Sol / strong、Medium**：高新颖度、高歧义、高影响范围或高不可逆性；新的跨系统契约；数据完整性风险；破坏性操作；未确定架构；无边界 bugfix；或已经有两次可验证的失败。
- **Budget / Low**：不存在独立高风险信号时的简单机械工作或成本敏感任务。

模型名称和成本分类是可维护配置，不是基准测试声明。推荐结果只提示用户或宿主手动操作。

## 开发与验证

运行确定性 selector：

```bash
python scripts/select_model.py --input '{"task_complexity":"moderate","operation_mode":"implementation","architecture_settled":true,"provider_availability":["codex","workbuddy"]}'
```

重新生成或检查手动运行配置：

```bash
python scripts/generate_custom_instructions.py
python scripts/generate_custom_instructions.py --check
```

运行全部测试：

```bash
python -m unittest discover -s tests -v
```

自动测试覆盖 selector 回归、交接校验、自动生成边界、运行模板一致性、管理区块生命周期、本地文本变换、本地备份、确认、修复和 Guided Install 流程。它不会验证 ChatGPT 是否收到或保存了任何内容；账户变更有意留在安装器边界之外。

## 仓库结构

```text
handoff-guard/
├── handoff_guard_installer/     # Windows 界面与安装生命周期
├── runtime/                     # canonical ChatGPT 运行模板
├── references/                  # 交接、路由和模型提供方契约
├── scripts/                     # selector、validator、生成与构建脚本
├── evals/                       # 回归样例
├── tests/                       # Core 与安装器测试
├── skills/handoff-guard/        # 备用 Skill 适配层
├── CUSTOM-INSTRUCTIONS.md       # 自动生成的手动安装文件
├── SECURITY.md
└── LICENSE
```

## 许可证

MIT，详见 [LICENSE](LICENSE)。
