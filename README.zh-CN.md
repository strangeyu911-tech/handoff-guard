# Handoff Guard（交接守卫）

[English](README.md) | 简体中文

> 一个轻量、具备模型感知能力的工作流层，把 ChatGPT 中已经确定的方案安全、完整地交给编码代理执行。

Handoff Guard 帮助普通 Chat 判断什么时候应该从规划进入 Work，保存实施契约，推荐可靠完成任务所需的最低成本模型，并在接收代理修改文件前完成检查。

```text
Chat / Architect → 结构化交接 → 执行前检查 → Work
```

它不只是一段静态提示词。仓库中包含确定性的模型选择器、版本化交接契约、校验器、回归样例、执行边界规则和完整安装生命周期。Custom Instructions 只是目前将这些能力接入 ChatGPT 的一种轻量运行适配层，不是产品的全部架构。

## 能做什么

- **判断交接时机**：只有普通 Chat 已经形成确定决策、具体实施方案或阶段检查点时，才自动生成交接。
- **保存实施契约**：传递当前状态、已完成内容、检查点、锁定决策、范围和约束。
- **推荐合适的模型**：把工作量和独立决策风险分开判断，避免“大任务必用最强模型”。
- **执行前检查**：在接收代理开始改文件前返回 `PASS`、`BLOCK` 或 `UNVERIFIED`。
- **让规则可以验证**：校验交接结构，并用回归样例持续检查模型路由策略。
- **安全管理 ChatGPT 适配层**：Windows 上支持预览、安装、升级、修复、本地备份、卸载和手动备用流程。

## 安装

### Windows 一键安装器

主要发行文件为：

```text
HandoffGuard-Installer-v0.1.0.exe
```

从仓库的 [GitHub Releases](https://github.com/strangeyu911-tech/handoff-guard/releases) 下载，先打开 ChatGPT Desktop，再运行安装器。安装器会完整展示修改前后内容，只有用户确认后才会保留已有指令、创建本地备份、写入带版本标记的 Handoff Guard 管理区块，并回读设置验证结果。

如果 Release 尚未发布安装文件，可以参照 [Windows 安装器构建与验收说明](docs/windows-installer.md)从源码构建。

安装过程会明确说明其使用 ChatGPT Custom Instructions。它是当前 ChatGPT 环境中的运行适配层；核心策略、模型路由、交接结构、校验和安装生命周期属于独立的产品层。

### 手动安装

如果 UI Automation 无法唯一识别并读取编辑框，安装器会拒绝写入，并提供 **Copy & Open Settings**。也可以打开 [CUSTOM-INSTRUCTIONS.md](CUSTOM-INSTRUCTIONS.md)，复制自动生成的运行配置，把它追加到现有 Custom Instructions 中，不能覆盖其他内容。

手动安装可以启用运行规则，但不提供受管理的升级、修复、备份和卸载能力。

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
└─ Product lifecycle（产品生命周期）
   ├─ 安装与升级
   ├─ 预览与本地备份
   ├─ 修复与写后验证
   └─ 卸载与手动 fallback
```

`runtime/custom-instructions.txt` 是 ChatGPT 运行适配层的 canonical template。Windows 安装器和自动生成的 `CUSTOM-INSTRUCTIONS.md` 都读取这一个文件，测试还会检查它是否覆盖 Core 的路由维度。因此安装器不会另外维护一套容易漂移的手写策略。

## 安全的受管理安装

Windows 适配层通过可访问控件名称使用 Microsoft UI Automation，不依赖绝对屏幕坐标。管理区块包含版本和校验和：

```text
[HANDOFF-GUARD:BEGIN version=0.1.0 sha256=...]
...
[HANDOFF-GUARD:END]
```

- **安装**：在现有内容之外追加管理区块，不覆盖其他指令。
- **升级**：只在原位置替换一个完整、有效的旧版本区块。
- **卸载**：只删除通过校验的 Handoff Guard 管理区块。
- **修复**：发现截断、重复、标记异常或校验和不一致时，重新显示预览并要求确认。
- **备份**：每次写入前把原始内容保存在 `%LOCALAPPDATA%\HandoffGuard\backups\`。
- **验证**：保存后重新读取；验证失败时明确显示备份位置。

Custom Instructions 不会上传。安装器不读取聊天记录、不索取 OpenAI 密码、不读取账号 token，也不修改 ChatGPT 本地数据库。详见 [SECURITY.md](SECURITY.md)。

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

自动测试覆盖 selector 回归、交接校验、自动生成边界、运行模板一致性、管理区块生命周期、备份、确认、写入失败、修复和 fallback。它不能证明某个 ChatGPT Desktop 版本一定暴露了所需 UI Automation 控件；正式发布前仍需按照 [docs/windows-installer.md](docs/windows-installer.md) 在真实环境验收。

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
