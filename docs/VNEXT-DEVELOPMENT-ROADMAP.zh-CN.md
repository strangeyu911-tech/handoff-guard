# Handoff Guard vNext 开发主路线（中文审阅版）

状态：中文审阅副本  
英文 canonical：[`docs/VNEXT-DEVELOPMENT-ROADMAP.md`](./VNEXT-DEVELOPMENT-ROADMAP.md)  
最后核验：2026-09-04  
基线：`main`，HEAD `59b338908fd1d69b3e8a4dd1cad706e89322bc48`

本文是英文 canonical roadmap 的中文审阅版，供产品、架构和阶段决策审核。
后续实施状态仍应回写英文 canonical 文件；如两份文件出现冲突，以英文
canonical 为准，并在下一次文档更新时同步修正中文版本。

本文将上一轮 competitor / prior-art architecture audit 转化为分阶段的
实现与验收路线。它是开发路线，不是竞品报告。未来 Work / Codex 任务应在
handoff 中明确当前 phase，并在 phase 状态变化时更新路线文档。

## 状态追踪

| Phase | 状态 | Exit criteria | 当前证据 | 下一步 |
|---|---|---|---|---|
| Phase 0 — 证据修复与产品清理 | NOT STARTED | 产品声明、canonical runtime、schema 引用和测试基线对齐，并明确范围 | 当前基线已记录；72 discovered / 43 passed / 29 failed | 修复 drift 或撤回未经支持的声明 |
| Phase 1 — Contract foundation | NOT STARTED | 版本化 contract 具备语义校验、矛盾检查和迁移测试 | 尚无 vNext contract 实现 | Phase 0 后定义 MVP contract |
| Phase 2 — Native Codex path | NOT STARTED | Codex adapter 完成 contract 映射，并在真实可行路径上返回 normalized result | 本轮未实现 adapter | contract foundation 后实现 |
| Phase 3 — External context reuse | NOT STARTED | ContextProvider 可替换、有边界、并与 execution 独立测试 | 尚无 provider 集成 | 增加 Repomix / evidence provider |
| Phase 4 — Readiness / risk policy | NOT STARTED | 风险策略可解释，并以 false block / unsafe allow benchmark 验证 | 当前 selector 仅为旧基线 | 建立 policy 输入和 benchmark |
| Phase 5 — Boundary detector + decision freeze | NOT STARTED | 基于 corpus 的 boundary 与 decision-drift 指标达到约定阈值 | 当前行为主要由 prompt / Custom Instructions 驱动 | 先建立 evaluation harness |
| Phase 6 — Acceptance / completion gate | NOT STARTED | 完成必须有 contract fulfillment evidence，并能处理 partial / drift outcome | 当前 validator 只检查标签 | 定义结果证据模型 |
| Phase 7 — Durable runtime / advanced adapters | NOT STARTED | journal、幂等、恢复和可选 adapter 具备故障测试 contract | 已明确延期 | 核心语义稳定后再评估 |

不能仅因为代码存在或 unit tests 通过就把 phase 标为完成。状态必须包含
支持它的证据以及真实用户路径上的验收结果。

## 1. vNext North Star

### 产品定位

Handoff Guard 是面向 Chat-first development workflow 的**执行边界策略、
契约与验证层**。它的作用是判断对话是否已经到达安全执行边界，冻结不应
漂移的决策，表达可验证的 execution contract，并判断实际工作是否履行了
该 contract。

一句话架构边界：

> Handoff Guard 拥有 boundary、decision、contract、readiness 和 acceptance
> 语义；外部 executor 负责 transport 与进程执行。

### HG owns

- boundary detection，以及显式 / 隐式 approval 语义；
- decision freeze、contradiction detection，以及 locked / mutable 状态；
- 与 transport 无关的版本化 execution contract；
- readiness 与 execution-risk policy，包括可见解释；
- semantic acceptance、partial completion、escalation 和 retry / replan 信号；
- evaluation harness 与 outcome benchmark；
- 独立于具体 executor 的 normalized result 语义。

### HG does not own

- repository packing 或自有 context-packing 格式；
- browser engine、DOM selector 库或 ChatGPT UI automation 路径；
- 通用 provider / model gateway 或自动 provider switching；
- 在 durable-runtime phase 之前的 executor transport、process lease 或
  crash-safe runtime primitive；
- 作为主要产品价值主张的 installer。

### 复用边界与原因

Codex transport 优先复用 Codex SDK / App Server，repository context 复用
Repomix，CLI / MCP bridge 复用已有 adapter，浏览器 fallback 只考虑 Oracle
或 chatgpt-use，并且必须是可选路径。

该决策为 **REPOSITION AND REUSE**：这些相邻能力已有更成熟的 prior art 或
第一方支持。重新实现会增加维护和集成面，却不会增强 HG 的核心语义贡献。

model / reasoning recommendation 仍可作为 contract strategy field 和
readiness input，但不是 vNext moat，也不能演化成 provider gateway。

## 2. 当前基线

### 仓库与已核验状态

- branch：`main`。
- 上一轮基线 HEAD：`a492c224e7f4c39f9efbc28aac4d88d37e15f31f`。
- 本中文副本创建前工作树：clean。
- 当前路线 checkpoint HEAD：`59b338908fd1d69b3e8a4dd1cad706e89322bc48`。
- 现有 roadmap / architecture 文档：此前没有 vNext implementation
  roadmap；`docs/design-decisions.md` 记录当前设计决策，
  `docs/windows-installer.md` 记录 installer 约束。英文文件是唯一
  canonical vNext implementation roadmap，本文件只是中文审阅副本。

### 现有实现面

- `runtime/`：中文和英文 Custom Instructions canonical template。
- `CUSTOM-INSTRUCTIONS.md` 与 `CUSTOM-INSTRUCTIONS.en.md`：生成的手动安装
  artifact。
- `scripts/select_model.py`：确定性的 tier / provider recommendation 和
  execution preflight。它将工作量复杂度与独立风险分开，选择配置中的
  provider/model，返回 reasoning effort，并依据当前可见的 model、reasoning、
  quota 和 tier metadata 返回 `PASS`、`BLOCK` 或 `UNVERIFIED`。它是旧策略
  基线，不是最终 vNext readiness policy。
- `scripts/validate_handoff.py`：Markdown / JSON handoff validator。它主要
  查找必需标签或非空 JSON key；尚未校验 typed、versioned contract、矛盾、
  可执行 acceptance criteria、evidence、drift 或语义完成。
- `references/handoff-spec.md`：当前 Markdown handoff 字段和 emission boundary。
- `references/routing-policy.md` 与 `references/provider-profiles.json`：
  当前 heuristic 和 model catalog。
- `handoff_guard_installer/`、`installer.py` 与 build scripts：Windows
  Guided Install adapter，负责本地 generate / copy / update / removal /
  repair / local validation；不能写入或验证 ChatGPT account settings。
- `skills/handoff-guard/` 与根目录 `SKILL.md`：备用 Skill runtime adapter，
  依赖 host，不是主要产品路径。
- `evals/`：routing 与 handoff-emission regression fixtures。
- `tests/`：selector、validator、emission、runtime parity、documentation、
  plugin 和 installer tests。

### Boundary 与 contract 的现实状态

Boundary detection 目前主要存在于 prompt / Custom Instructions runtime
规则中。Markdown handoff format 和 `validate_handoff.py` 提供结构，但不
提供独立可执行的 semantic contract。当前 runtime 中的 routing instruction
也比 validator 能验证的内容更详细。

### 测试与证据基线

2026-09-03 使用仓库已有 bundled Python environment 实际执行测试：
**72 个测试被发现，43 个通过，29 个失败**。这是需要修复或明确替代的
基线，不是 vNext effectiveness 证据。

失败集中在 `tests/test_custom_instructions.py`：

- 生成的 `CUSTOM-INSTRUCTIONS.md` 不等于当前中文
  `runtime/custom-instructions.txt` payload；
- installer canonical payload 不等于 runtime source；
- loaded payload 中缺失预期的 routing dimensions 与 handoff terms。

Routing fixtures、handoff-emission fixtures、handoff validator tests、plugin
structure tests 和 installer lifecycle tests 在该次运行中通过。fixture suite
只能证明确定性规则回归，不能证明 boundary quality、routing outcome quality、
readiness safety 或 completion correctness。

README 中“当前运行 72 个 automated tests”的表述必须在 Phase 0 修复、限定
范围或撤回；不能用它声称当前 72 个测试全部通过。

## 3. 目标架构

```text
Chat / conversation evidence
          |
          v
HG Core: Boundary -> Freeze -> Contract -> Readiness -> Execute -> Accept
          |                                  |                 |
          |                                  +-> policy result  +-> normalized result
          v
Providers / adapters（可替换）
  ContextProvider | TransportAdapter | Session/Git evidence | Result normalizer
          |
          v
External implementations
  Codex SDK/App Server | Repomix | optional MCP/CLI bridges
  optional Oracle/chatgpt-use browser fallback（非默认、opt-in）
```

### HG Core

- **Boundary Detector**：判断 source conversation 是否处于可靠的 ordinary
  Chat surface，以及是否已经到达具体 execution boundary。必须区分
  premature handoff、missed handoff、unresolved architecture、explicit approval
  和 implicit approval。
- **Decision Freeze**：记录 locked decisions、mutable implementation choices、
  unresolved questions 和 contradictions。consumer 不能静默重新打开 locked
  decisions。
- **Execution Contract**：创建和校验第 4 节定义的 versioned semantic payload。
- **Readiness / Risk Policy**：评估 execution surface、approval、reversibility、
  blast radius、data integrity、cross-system contract、historical failure 和
  user override，并解释 `PASS`、`BLOCK`、`UNVERIFIED` 或未来等价结果。
- **Acceptance / Escalation**：基于 contract 判断 complete、partial、retry、
  replan、user-review 或 blocked outcome。
- **Evaluation Harness**：运行 regression fixture、adversarial case、real
  anonymized corpus 和 outcome benchmark，并输出明确指标。

### Providers 与 adapters

- **ContextProvider**：提供有边界的 repository、file、conversation 或 session
  context，以及包含 provenance 和 omissions 的 manifest。
- **TransportAdapter**：将已校验的 HG contract 映射到 executor，并返回 raw
  execution reference 供 normalized result 使用。
- **Session / Git evidence provider**：提供 branch、HEAD、dirty-tree、
  checkpoint、test、artifact 等可观测证据，不得编造事实。
- **Result normalizer**：把 executor-specific output 转换成与 transport 无关的
  result semantics，供 acceptance 使用。

Core 不能依赖某个具体 executor、browser transport、repository packer、model
provider 或 installer。Adapter 可以依赖 Core contract；Core 只能依赖稳定的
provider interface。

## 4. 版本化 execution contract

下表是正式 design target，不是本轮的 schema implementation。未来 contract
必须区分 HG-owned semantics 与 executor-owned mechanics。

| 字段 | MVP | 所有权 / 意图 |
|---|---|---|
| `contract_version` | Required | HG-owned 版本和迁移 discriminator |
| `handoff_id` | Required | HG-owned 幂等 / trace identity |
| `source_context` | Required | HG-owned provenance summary；不得编造事实 |
| `objective` | Required | HG-owned executable objective |
| `current_state` | Required | HG-owned factual baseline |
| `checkpoint` | Required | HG-owned evidence reference 或明确的 `none` |
| `locked_decisions` | Required | HG-owned；除非显式 supersede，否则不可变 |
| `mutable_implementation_choices` | Required | HG-owned 允许的实现选择范围 |
| `constraints` | Required | HG-owned scope 和 operating constraints |
| `do_not` | Required | HG-owned safety boundary 和 non-goal |
| `context_manifest` | Required | HG-owned provenance、selection、budget 和 omissions |
| `execution_surface` | Required | HG-owned readiness input；由 adapter 映射 |
| `model` | recommendation 必需 | HG strategy field；除非 executor 所有，不自动切换 |
| `reasoning_effort` | recommendation 必需 | HG strategy field；不是 quality claim |
| `sandbox` | MVP 必需 | HG semantic requirement；由 executor 映射 capability |
| `approval_requirements` | Required | HG-owned explicit approval / escalation rules |
| `preflight` | Required | HG-owned readiness result 和 evidence |
| `acceptance_criteria` | Required | HG-owned executable / observable completion conditions |
| `result_schema` | Required | HG-owned normalized result shape |
| `retry_policy` | 初期延期，预留设计位 | HG policy；durable runtime 可实现 mechanics |

MVP 必须实现所有标记为 Required 的字段，并进行 semantic validation，而不只是
 label presence。`retry_policy` 可以延期到 partial-result semantics 稳定后，
但必须保留其 versioning slot。Executor job id、process handle、lease、cursor、
raw log 和 provider-specific request option 属于 transport/runtime-owned fields。
它们可以通过 `source_context`、`preflight` 或 normalized result 被引用，但不能
定义 HG Core semantics。

Contract 设计规则：

1. 缺失事实表示为 `unknown` / `UNVERIFIED`，不能编造值。
2. 必须检查 locked decisions 与 `do_not` constraints 的 contradiction。
3. Acceptance criteria 必须指定可观测 evidence，不能只写“works”这类愿望。
4. Contract version 必须显式迁移；unsupported version 要以可行动结果拒绝。
5. Markdown 是 presentation / compatibility format；semantic source of truth
   是 versioned contract object。

## 5. 分阶段实施计划

### Phase 0 — Evidence repair & product cleanup

**Objective** — 在增加 vNext semantics 前，恢复一个真实且内部一致的 baseline。

**Inputs / dependencies** — 当前 runtime template、generated artifact、README
 claims、`references/` 文档、当前 tests / fixtures、installer 行为和本路线图。

**Deliverables**

- 声明一个 canonical Custom Instructions source，并同步生成 artifact；如果
  保留两个语言 artifact，则明确 parity / compatibility rule；
- 统一 runtime、references、tests 中的 handoff / routing terminology；
- 将 README 与 docs 声明限定到实际可观察证据；
- 建立 baseline report，记录 discovered、passed、failed、skipped 和
  environment-dependent tests；
- 明确 installer、Skill、selector 和 browser experiments 的 adapter / legacy
  身份，降低它们在产品定位中的中心性。

**Tests / evaluation** — regenerate/check artifact；执行 bundled suite；直接
运行 selector 和 validator；确认 fixture count 没有被写成 outcome effectiveness。

**Exit criteria**

- 在承诺 parity 的地方，canonical runtime 与 generated artifact byte-for-byte
  一致；
- 每一个 documented test-count claim 都有可复现命令和 status；
- README 或 runtime 不再声称代码无法证明的 automatic model switching、
  crash-safe runtime 或 semantic acceptance；
- deviations 和剩余 legacy limitation 已记录在本路线图或 ADR 中。

**Explicit non-goals** — 不实现 Codex adapter、schema、installer 删除、browser
 automation、第三方安装或大范围重构。

**What becomes stable** — truthful baseline、当前 compatibility boundary 和
后续 phase 使用的 vocabulary。

### Phase 1 — Contract foundation

**Objective** — 建立 versioned semantic contract，不与 automatic transport 耦合。

**Inputs / dependencies** — Phase 0 baseline、当前 handoff spec（作为
compatibility input）和第 4 节 contract field table。

**Deliverables**

- versioned JSON schema 或等价 typed representation；
- 带有 ownership、requiredness、unknown-state 和 contradiction check 的
  semantic validator；
- explicit locked-versus-mutable decision representation；
- executable acceptance-criteria primitives；
- migration / version compatibility rules 和 fixtures；
- Markdown import / export compatibility layer。

**Tests / evaluation** — valid / invalid contract、missing evidence、contradiction、
locked-decision mutation、unsupported version、acceptance-criteria parsing 和
round-trip serialization。

**Exit criteria** — contract 可以创建、校验、迁移、拒绝和 round-trip，不选择或
启动 executor；semantic error 可行动且有测试覆盖。

**Explicit non-goals** — 不做 automatic transport、browser control、provider
gateway、repository packer 或 durable journal。

**What becomes stable** — contract fields、validation semantics、migration policy
和 compatibility behavior。

### Phase 2 — Native Codex path

**Objective** — 以 Codex SDK / App Server 作为第一个 native execution adapter。

**Inputs / dependencies** — 已校验的 Phase 1 contract、Codex SDK / App Server
interface 和 adapter capability map。

**Deliverables**

- Codex SDK / App Server 的 `TransportAdapter`；
- model、reasoning、sandbox、approval、objective 到 executor 的映射；
- start、resume 和 result retrieval；
- 包含 executor reference、observable evidence 和 unknowns 的 normalized result；
- 保留 HG semantics 的 adapter-specific error mapping。

**Tests / evaluation** — contract mapping、mocked / local adapter integration、
start / resume / retrieval、approval mismatch、normalized-result fixtures，以及
在 credentials 和 host policy 允许时执行一条真实 supported executor path。

**Exit criteria** — validated contract 能通过 supported adapter 到达 Codex，结果
可取回并规范化，且 acceptance 不需要检查 Codex-specific internals。

**Explicit non-goals** — 不手写 ChatGPT browser automation，不建设 provider
gateway，不把 agent 启动等同于任务完成。

**What becomes stable** — Codex adapter boundary、parameter mapping 和 normalized
start / resume / result semantics。

### Phase 3 — External context reuse

**Objective** — 通过可替换 provider 提供有边界且带 provenance 的 context。

**Inputs / dependencies** — Phase 1 contract、Phase 2 adapter interface、Repomix
或其他批准的 external context implementation，以及 Git / session evidence access。

**Deliverables**

- Repomix-backed `ContextProvider`；
- Git / session evidence provider；
- 带 token / size budget、provenance 和 omissions 的 selective context manifest；
- secret-scan warning boundary 和 user-visible handling；
- provider capability 和 failure normalization。

**Tests / evaluation** — deterministic manifest、token-budget、omitted-file
transparency、secret warning、dirty-tree / checkpoint evidence、provider failure
以及 adapter-independent contract tests。

**Exit criteria** — context 可以替换或省略而不改变 Core semantics；每个包含项
都有 provenance；budget 和 omissions 可见；secret 按明确规则 warning 或排除。

**Explicit non-goals** — 不建设 proprietary repo packer，不让 Core 依赖某个
provider-specific context。

**What becomes stable** — `ContextProvider` interface、context manifest semantics、
evidence provenance 和 budget behavior。

### Phase 4 — Readiness / risk policy

**Objective** — 把现有 generic model routing 演化为 execution-boundary risk / 
approval policy。

**Inputs / dependencies** — Phase 1 contract、Phase 2 executor capability、Phase 3
evidence metadata 和第 7 节 benchmark 定义。

**Deliverables**

- normalized risk inputs：irreversibility、destructiveness、blast radius、data
  integrity、cross-system contract、historical failure 和 user override；
- 带 explainability 的 readiness result，支持 `PASS`、`BLOCK`、`UNVERIFIED` 和
  audit-only semantics；
- model / reasoning recommendation 作为 strategy field，而不是 gateway；
- approval requirements 和 visible reason codes；
- benchmark-backed thresholds 和 calibration record。

**Tests / evaluation** — false-BLOCK rate、unsafe-allow、wrong-surface routing、
premium-model overuse、user override、unknown metadata、declared quota conflict
以及 one-tier / material tier mismatch。

**Exit criteria** — policy decision 可复现且有解释；benchmark 达到约定阈值；未知
信息不会静默变成安全事实；model recommendation 不暗示自动 switching。

**Explicit non-goals** — 不做 online price claim、provider gateway，不能在没有
outcome evidence 时假定当前 selector heuristic 有效。

**What becomes stable** — readiness input vocabulary、reason codes、approval
semantics 和 benchmark reporting。

### Phase 5 — Boundary detector + decision freeze

**Objective** — 从真实 boundary 和 decision-drift evidence 出发，建设 HG 最有
潜力的 moat candidate；先做 evaluation，再做复杂 detector。

**Inputs / dependencies** — Phase 1 contract、Phase 4 risk vocabulary 和经过审核
的 anonymized conversation corpus policy。

**Deliverables**

- anonymized conversation 的 labeled corpus protocol；
- detector evaluation harness 和 human-label guidance；
- 支持 explicit / implicit approval 的 decision-freeze representation；
- contradiction 和 decision-drift report；
- 以当前 prompt / rule behavior 为 baseline 的 detector。

**Tests / evaluation** — premature handoff、missed handoff、unresolved architecture、
explicit / implicit approval、decision drift、surface uncertainty，以及 real
corpus 上的 inter-rater agreement。Synthetic case 只能补充，不能替代真实匿名样本。

**Exit criteria** — benchmark label 和 metric 可复现；baseline precision / recall
和 error category 已知；detector 变更可与 baseline 对比；没有 outcome evidence
前不得宣称 moat 或 effectiveness。

**Explicit non-goals** — 不做 automatic browser execution，不假定 prompt-only
detection 足够。

**What becomes stable** — corpus format、detector metric、freeze semantics 和
decision-drift reporting。

### Phase 6 — Acceptance / completion gate

**Objective** — 通过 contract fulfillment，而不是 process termination，判断完成。

**Inputs / dependencies** — Phase 2 normalized result、Phase 3 evidence provider、
Phase 4 readiness semantics 以及 contract / freeze state。

**Deliverables**

- artifact、test、checkpoint、dirty-tree 和 contract-drift evidence model；
- semantic completion evaluator；
- partial-completion result 和 escalation state；
- retry / replan / blocked policy；
- false-completion 和 evidence-insufficiency report。

**Tests / evaluation** — artifact evidence、test evidence、dirty tree、checkpoint
mismatch、partial failure、contract drift、false-positive completion、missing
evidence、retry、replan 和 user-review。

**Exit criteria** — “process ended” 单独不能产生 `complete`；完成必须满足声明的
acceptance criteria 并有 observable evidence；partial 和 drifted outcome 必须
保留且可行动。

**Explicit non-goals** — 先不实现 crash recovery journal 或 lease。

**What becomes stable** — normalized result state、acceptance evidence semantics
以及 complete / partial / blocked decision。

### Phase 7 — Durable runtime / advanced adapters

**Objective** — 只有 Core semantics 已证明价值后，才增加 durability 和 optional
integration。

**Inputs / dependencies** — Phase 1–6 已稳定的 contract、adapter、evidence、
readiness、boundary 和 acceptance semantics。

**Deliverables**

- append-only journal；
- idempotency key 和 duplicate-submission protection；
- lease / cursor 和 crash recovery semantics；
- optional Workspace Agents 或 CLI bridge；
- optional Oracle / chatgpt-use browser fallback，opt-in、非默认；
- durability 和 adapter failure playbook。

**Tests / evaluation** — crash injection、duplicate submission、replay、concurrent
lease、cursor loss、recovery、adapter timeout、browser fallback opt-in 和 journal
integrity。

**Exit criteria** — recovery behavior deterministic 且保留 evidence；重复执行被阻止
或明确暴露；optional adapter 不能成为隐式 Core dependency；browser fallback
仍为 opt-in。

**Explicit non-goals** — 不做默认 browser automation，不替代 Codex transport，
不扩张成通用 agent platform。

**What becomes stable** — durable execution reference、recovery contract、optional
adapter boundary 和 operational failure semantics。

## 6. Phase gates 与 handoff 协议

每个未来 phase 或清晰定义的 sub-phase 都必须记录相同的 gate：

1. **Objective** — 一个 outcome，不是 broad rewrite。
2. **Inputs / dependencies** — 确切的前序 contract、evidence 和 adapter。
3. **Deliverables** — 预期的文件、interface、报告或 fixture。
4. **Tests / evaluation** — 相关 regression 和 outcome check。
5. **Exit criteria** — 可观察的停止条件。
6. **Explicit non-goals** — 必须等待的工作。
7. **What becomes stable** — 后续 phase 可以依赖的 interface 和 decision。

Phase status update 必须包含 `status`、`evidence`、`deviations` 和 `next
recommended step`。如果 architecture decision 变化，必须先更新本路线图或 ADR，
再改实现。handoff 应引用当前 phase 和 gate，不要复制整份路线图。

## 7. Evaluation strategy

Evaluation 是一条独立主线。Rule fixture 是有用的 regression check，但 fixture
数量绝不能被写成 product effectiveness。

| Evaluation line | 必须提供的证据 |
|---|---|
| Boundary detector benchmark | 真实匿名 corpus、synthetic adversarial supplement、precision / recall、premature / missed handoff rate |
| Decision-drift benchmark | locked-decision mutation、contradiction detection、unresolved architecture、explicit / implicit approval accuracy |
| Semantic contract validation | valid / invalid contract、version migration、unknown state、contradiction、acceptance-criteria semantics |
| Readiness false-BLOCK rate | reversible safe work、unknown metadata、user override、audit-only case |
| Wrong-surface routing | Chat / Work / Codex / uncertain-surface corpus 与 recursion check |
| Premium-model overuse | settled large work 与 independent-risk case 的 strong-tier recommendation rate 对比 |
| Acceptance false positive | 没有 artifact、test、checkpoint 或 contract evidence 时却完成的比例 |
| Partial-failure recovery | partial result、retry / replan / blocked classification、evidence continuity |
| Prior-art comparison | 与复用 adapter / baseline tool 的 boundary、contract、acceptance outcome 对比；不得超出测量范围声明 |

必须分开维护四类数据：

- **Regression fixtures** — 确定性的兼容性 case。
- **Synthetic adversarial cases** — 人工构造的困难输入。
- **Real anonymized conversation corpus** — 带隐私控制、由人工标注的 boundary
  与 decision evidence。
- **Outcome benchmark** — 与可观察 artifact / evidence 绑定的 execution 和
  acceptance result。

每份 benchmark report 必须说明 dataset version、exclusions、metric definition、
confidence / uncertainty 和 known blind spots。在相关 benchmark 支持之前，
“reliable”“safe”“moat”等声明保持 `UNPROVEN`。

## 8. Reuse registry

该 registry 防止重新实现已经决定复用的能力。License 和 maintenance status
是 integration gate，不能靠猜测；采用某个 upstream version 前必须重新核验。

| Dependency / project | Reuse type | Intended boundary | License | Reason | Maintenance risk | Status |
|---|---|---|---|---|---|---|
| Codex SDK / App Server | DIRECT | Native Codex execution 的 `TransportAdapter` | 集成前核验 upstream package / terms | 第一方 transport path | API / host 演进 | PLANNED |
| Repomix | DIRECT | Repository packing 的 `ContextProvider` | 预计 MIT；核验选定版本 | 成熟的 repository context reuse | 格式 / token 行为变化 | PLANNED |
| Oracle | WATCH / optional DIRECT | 非默认 browser fallback adapter | 核验 upstream | 现有 browser-agent prior art | surface breakage / policy risk | DEFERRED |
| chatgpt-use | WATCH / optional DIRECT | 非默认 browser fallback adapter | 核验 upstream | 现有 browser-control prior art | login / UI / policy 脆弱性 | DEFERRED |
| TStansel/handoff | DESIGN | Handoff transport / workflow prior art | 核验 upstream | 借鉴已有 handoff 实现 | 与 HG semantics 假设不同 | REVIEWED FOR DESIGN |
| OpenMOSS | DESIGN | Agent / handoff architecture prior art | 核验 upstream | 避免重复 broad agent workflow | scope / compatibility 不确定 | REVIEWED FOR DESIGN |
| Second Opinion | WATCH | Review / verification workflow prior art | 核验 upstream | 可能复用 acceptance / review pattern | 与产品边界重叠 | WATCH |
| Superpowers | DESIGN | Development workflow / instruction pattern | 核验 upstream | 有选择地复用成熟 workflow idea | prompt-oriented semantics 可能不可执行 | REVIEWED FOR DESIGN |
| ModelRouter | DO NOT TAKE | Provider / model gateway | N/A for HG adoption | HG 不应成为 general gateway | scope coupling | REJECTED |

`DIRECT` 表示在稳定 HG interface 后集成；`DESIGN` 表示只学习，不引入 runtime
dependency；`WATCH` 表示在证据和 license review 通过前不依赖；`DO NOT TAKE` 是
明确边界。

## 9. Deprecation / migration list

路线图阶段不要删除这些组件。必须先进行迁移，并在证明删除安全前保留兼容性。

| 现有组件 | vNext 处理 | 迁移意图 |
|---|---|---|
| `runtime/custom-instructions.txt` 与生成的 Custom Instructions | KEEP，之后 REFACTOR | 保留为当前 runtime adapter；Phase 0 对齐 source / generated artifact，Core 成熟后减少 semantic duplication |
| `runtime/custom-instructions.en.txt` 与英文 artifact | KEEP，之后 REFACTOR | 保留 language-equivalent compatibility；generated output 必须明确且有测试 |
| Skill adapter / `skills/handoff-guard/` | COMPATIBILITY-ONLY | 为支持 Skill 的 host 保留；不把它变成 guaranteed runtime 或 Core source |
| `scripts/select_model.py` | REFACTOR | 保留 deterministic compatibility API；迁移到 readiness / approval policy 并 benchmark |
| `scripts/validate_handoff.py` | REFACTOR，之后 COMPATIBILITY-ONLY | 保留 Markdown / JSON compatibility validation；semantic validation 转交 versioned contract foundation |
| Windows Guided Installer | KEEP as adapter | 保留 local Generate / Copy / Update / Removal / Repair；不扩张为 account control 或主产品 |
| Browser / UIA experiments | DEPRECATED | 仅保留 evidence 和 documentation；不做 production ChatGPT DOM / UIA automation |
| Current eval fixtures | KEEP as regression fixtures | 保留用于 rule compatibility，标记为 regression-only，另建 outcome benchmark |
| Current Markdown handoff format | COMPATIBILITY-ONLY，之后 MIGRATE | 继续为用户提供 import / export；使 versioned contract 成为 semantic source of truth |
| Provider profile catalog | KEEP，之后 REFACTOR | 保留 configurable catalog data；去除 HG 拥有 provider switching 的假设 |
| Installer build / release artifacts | KEEP | 作为 supporting adapter；只按 local acceptance surface 验证 |

## 10. Development operating rules

1. 一次只推进一个 phase 或一个清晰的 sub-phase。
2. 开始 phase 前读取本路线图的当前状态。
3. phase 结束后回写 `status`、`evidence`、`deviations` 和 `next recommended step`。
4. architecture 变化时，先更新本路线图 / ADR，再改实现。
5. 不因为 adapter 容易实现就跳过 Core contract 或 evaluation。
6. “agent 已启动”不等于 Handoff Guard 成功。
7. “tests pass”不自动等于 semantic effectiveness。
8. prior art 已解决的相邻问题优先 reuse。
9. 保留用户修改；phase work 期间不 reset 或 clean dirty tree；只有内容可归属
   时才建立 checkpoint。
10. 缺少所需 runtime 或 benchmark evidence 时，把 claim 标为 `UNPROVEN`。
11. browser fallback 如果实现，长期保持非默认、opt-in。
12. 不以 routing 名义建设 provider/model gateway 或 automatic model switching。

## 11. 本路线图之后的第一项可执行任务

第一项实现任务是 **Phase 0.1 — repair the evidence baseline**：

- 检查 Custom Instructions source / generated artifact 的确切关系；
- 选择并记录 canonical generation direction，不删除现有 artifact；
- 对齐或明确限定 runtime、references、tests 和 README claims；
- 重新执行 bundled suite，并记录新的 discovered / passed / failed counts；
- 如果发现需要产品决策的 contradiction，停止并报告，不擅自扩展范围。

验收 gate：baseline truthful 且可复现；parity claim 在声明处为真；没有开始
任何 vNext adapter 或大规模 runtime refactor。

本中文审阅版与英文 canonical roadmap 都明确停在 Phase 0 执行之前。
