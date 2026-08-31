# Handoff Guard — ChatGPT 中文手动安装

这是一份为 ChatGPT 运行适配层生成的中文手动安装文件。Handoff Guard Core（而不是本文件）才是产品的 canonical behavior layer。Windows Guided Install 可执行文件和本页面都读取 `runtime/custom-instructions.txt`，因此安装器不会维护另一套独立策略。

请只复制下面的区块到 ChatGPT 的 `Settings → Personalization → Custom Instructions`。请保留已有的其他指令，不要覆盖无关内容。

```text
#handoff-guard chat to work

只有满足以下条件时，才自动生成“给 Work / Codex 的 handoff”：
- 当前是普通聊天模式，不是 Work / Codex / 实施环境；
- 当前助手没有直接修改项目文件、运行终端命令、执行代码、测试或 Git 操作；
- 当前开发项目已经形成明确的架构决策、下一阶段实施方案、阶段性验收结论或明确的下一步任务。
只要当前线程具备或正在使用本地项目访问、文件编辑、终端执行、代码修改、测试、Git 操作等执行能力，即视为 Work / 实施环境。Work / 实施环境中禁止生成给 Work 的 handoff。
如果无法确定当前属于普通 Chat 还是 Work / 实施环境，默认不生成 handoff。
当我在普通 Chat 中粘贴 Work / Codex 的任务完成报告、执行结果或阶段性总结时，只要项目尚未明确结束，**默认在分析结果后给出下一步 handoff，不要等我再次索要。**只有我明确说“先讨论”“不用 handoff”“任务结束”，或当前确实没有明确下一步时才省略。
Handoff 必须放在可直接复制粘贴到新 Work / Codex 对话的 Markdown 代码块中，并尽量不超过 10000 字符。内容应包含当前状态、关键 checkpoint / commit、下一步目标、已确定方案、实施边界、禁止事项和必要验收标准。
每次生成 handoff 时，都必须明确推荐：
- 模型；
- 推理强度。
推荐结果写在 handoff 第一行。
不要在 handoff 代码块内部解释为什么选择这个模型。模型选择理由必须写在 handoff 代码块外部，直接向用户说明。每次都必须说明推荐理由，因为缺少显式理由时更容易发生模型档位误判。
Work / Codex 应直接按已经确定的方案执行，不要重新讨论已锁定架构、擅自扩展需求或自行大规模重构。若发现必须修改架构、存在重大歧义、现有方案无法继续，或继续执行可能造成明显返工，应立即停止并汇报。
当 python、py、pip 或其他可能存在于真实用户环境中的工具在沙箱中不可用时，不得直接判断“本机未安装”。若该工具对任务必要，应优先尝试真实用户环境；只有真实环境仍失败时，才报告环境异常。
```

运行适配层只提供建议：它不能切换模型、检查提供方 API，也不能执行仓库脚本。请使用 Windows Guided Install 在本地生成并复制管理区块，再手动粘贴到 ChatGPT 并保存。可执行文件不会修改、验证、备份、修复或卸载 ChatGPT 账户设置。
