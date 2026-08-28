# Handoff Guard

English | [简体中文](README.zh-CN.md)

> Handoff Guard is a model-aware handoff skill for coding agents. It preserves settled decisions, recommends the cheapest sufficient model, and checks the receiving agent's configuration before execution.

It operates at the handoff and decision layer: it gives the receiving agent a provider/model recommendation and runs a preflight check before implementation begins. It does not automatically switch models or providers.

## Why it exists

Agent handoffs often lose two things at once: the implementation contract and the model decision. The receiving agent then spends tokens re-discovering architecture, or runs a simple task on an unnecessarily expensive model, or starts a complex task on a model that is unlikely to finish it reliably.

## What Handoff Guard is

Handoff Guard combines three bounded capabilities:

- **Structured handoff:** preserves current state, completed work, checkpoints, locked decisions, and execution guardrails.
- **Model recommendation:** recommends a provider, model tier/model, and reasoning effort using a transparent heuristic.
- **Execution preflight:** checks the current configuration before files are changed and returns `PASS`, `BLOCK`, or `UNVERIFIED`.

## What Handoff Guard is not

Handoff Guard is not a runtime LLM gateway or automatic model router. A model router belongs to a different category of tools: it automatically routes requests to different models or providers at the invocation layer.

Handoff Guard does not control ChatGPT's model picker, automatically switch models or providers, migrate the current session, or guarantee that the host exposes the exact underlying model identity. It gives the user a recommendation for a manual switch when one is needed.

If the active model or reasoning effort cannot be detected reliably, Handoff Guard returns `UNVERIFIED` rather than treating the configuration as mismatched. It explains that the configuration could not be verified, shows the recommendation, and allows execution to continue.

## Handoff emission boundary

Handoff Guard generates a handoff automatically only in a reliably ordinary Chat / discussion conversation after a concrete development boundary has been reached: a settled architecture decision, a specific next-stage implementation plan, or a stage-level acceptance/checkpoint conclusion.

Any project file access or edit, terminal command, code change, test run, Git operation, or other clear implementation activity makes the current thread a Work / implementation environment. Handoff Guard will not recursively generate or append a new Work handoff there—even when the task is complete, a checkpoint or commit exists, or a next-stage plan has been written. If the mode cannot be determined reliably, it fails closed and does not generate an automatic handoff. An explicit request such as “give me a Work handoff” or “generate a handoff” overrides this automatic restriction.

## Workflow

```text
Chat / Architect Agent
        |
        | structured handoff
        | + provider / model recommendation
        v
Receiving Work Agent
        |
        v
Execution preflight
        |
+----------------+----------------+----------------+
|                |                |
configuration    clear mismatch  cannot confirm
aligned          detected         current settings
|                |                |
PASS             BLOCK            UNVERIFIED
|                |                |
        v                v                v
Execute in       Stop and ask     State unable
scope            the user to      to verify;
                 switch manually  continue
        \                |                /
         +---------------+----------------+
                         |
                         v
                 Update checkpoint
```

The three preflight outcomes have these meanings:

- **PASS:** the known configuration is suitable; execute normally within scope.
- **BLOCK:** a clear configuration mismatch is confirmed; stop and ask the user to switch models manually.
- **UNVERIFIED:** the current model or reasoning effort cannot be read or confirmed reliably; explain that it could not be verified, but do not block execution.

## Installation

Copy the `handoff-guard` folder into a discoverable Agent Skills directory:

```text
$CODEX_HOME/skills/handoff-guard/
```

If `CODEX_HOME` is not set, use the standard user skills directory for your agent (commonly `~/.codex/skills/`). The folder must contain `SKILL.md` at its root. The skill is discoverable automatically; the UI metadata is in `agents/openai.yaml`.

### Plugin installation

This repository also contains a skills-only Plugin manifest. The canonical Plugin Skill is at `skills/handoff-guard/SKILL.md`; the root `SKILL.md` remains available for direct GitHub Skill installation. The Plugin intentionally has no MCP server or app manifest.

The “Install from ChatGPT Plugin Directory” option can be documented here after Handoff Guard is reviewed and listed by OpenAI. It is not published in that directory yet.

Branding TODO before directory submission: add a reviewed logo/icon asset with the appropriate usage rights, then add its paths to `.codex-plugin/plugin.json`. No logo or icon is claimed by the current manifest.

## Usage

When a Chat / discussion conversation reaches an architecture or implementation boundary, ask the agent to create a Handoff Guard handoff. In a Work / implementation environment, no handoff is appended automatically after implementation; request one explicitly if needed. Use the template in `assets/handoff-template.md` and include a real commit/file checkpoint or explicitly write `none`.

For deterministic routing:

```bash
python scripts/select_model.py --input '{"task_complexity":"moderate","task_type":"implementation","architecture_settled":true,"provider_availability":["codex","workbuddy"]}'
```

### Model recommendation

The selector separates workload complexity from reasoning and decision risk. File count, code volume, repository count, reading volume, or prompt length alone MUST NOT escalate a task to Sol/strong.

Luna/general is the default for read-only audits, research, capability inventories, reuse audits, documentation, tests, and large implementation work against a settled architecture. Sol/strong is reserved for independent high-risk signals such as first-time core architecture or data models, high ambiguity, high blast radius, high irreversibility, data-integrity risk, destructive operations, a new cross-system contract, or two evidenced prior failures. Both Luna and Sol use Medium reasoning by default in the current policy.

The selector accepts optional routing dimensions such as `operation_mode`, `decision_novelty`, `ambiguity`, `blast_radius`, `irreversibility`, `cross_system_contract`, `data_integrity_risk`, `destructive`, and `prior_failed_attempts`. The output is a recommendation for the host; it does not invoke or switch the selected model.

For preflight, include `current_model` and `current_reasoning_effort` when the host exposes them. The result contains an explicit `status`: `PASS`, `BLOCK`, or `UNVERIFIED`, plus `block_current_execution`. Only a material mismatch or declared quota constraint blocks execution.

If the host cannot reliably expose the active model or reasoning effort, Handoff Guard returns `UNVERIFIED`, shows the recommendation, and allows execution to continue. Unknown is advisory, not blocking; the user can verify the model picker manually if needed.

Regression examples:

- First-time Conversation Pair / Relationship core data model, including context boundaries, cache compatibility, and Runtime behavior → `Sol`, Medium.
- Read-only audit of OpenSelf, Talky, Crush.skill, ex-skill, Chat-Style-Bot, and WeChat-AI → `Luna`, Medium, even though it spans many repositories.

These are routing-policy checks, not proof that a model is available or that the Skill triggers in a product conversation.

For validation:

```bash
python scripts/validate_handoff.py path/to/handoff.md
```

The validator returns JSON and a non-zero exit status when a required field is missing.

## Real ChatGPT Chat A/B acceptance

Repository selector tests cannot verify whether ChatGPT Chat mode discovers this Skill, triggers it in a real conversation, or resolves conflicts between a Skill and Custom Instructions. Perform that acceptance manually after the repository tests pass.

### A. Skill-only

1. Back up the current Handoff Guard Custom Instructions.
2. Temporarily remove or disable those instructions.
3. Install the GitHub-published Handoff Guard Skill.
4. Start a new ordinary Chat conversation.
5. Run the same fixed tasks: README modification; small UI bug; complex read-only GitHub reuse audit; large implementation against settled architecture; first-time Relationship Skill architecture; destructive database migration; and a complex bug after two explicit Luna failures.
6. Record whether the Skill triggered, the recommended model and reasoning effort, whether the handoff was correct, and whether it produced unnecessary `BLOCK` or `UNVERIFIED` results.

### B. Custom-Instructions-only

Disable or uninstall the Skill for the test, restore the original Handoff Custom Instructions, and repeat the same or semantically equivalent tasks in new conversations. Record the same indicators.

### C. Compare

Compare trigger stability, model recommendation accuracy, unnecessary Sol escalation, false blocks, handoff-format consistency, and token/instruction-length overhead. Do not assume the Skill is better than Custom Instructions before collecting results.

When the Skill is installed, an optional minimal Custom Instruction is:

```text
When a development task forms a handoff, prefer the installed Handoff Guard Skill to generate and validate the handoff and model recommendation.
```

This is a trigger suggestion only; the routing policy should remain in the Skill so two full rule sets do not drift.

## Provider fallback

Provider recommendation is configuration-driven. If the user says GPT/Codex has no quota, set `quota_unavailable: true` and identify `quota_provider`; the default profile recommends an available WorkBuddy provider. If the user explicitly prefers WorkBuddy, set `preferred_provider: "workbuddy"`. The user may then switch provider manually according to the host environment.

Example recommendation:

```text
Recommended provider: WorkBuddy
Recommended model: HY3
Recommended reasoning: Medium
Action: switch manually if the current host requires it
```

The default WorkBuddy catalog in `references/provider-profiles.json` includes Auto, HY3, GLM-5.3, GLM-5.2, GLM-5.1, GLM-5V-Turbo, MiniMax-M3, Kimi-K3, Kimi-K2.7-Code, Kimi-K2.6, Deepseek-V4-Flash, and Deepseek-V4-Pro. The tier/cost-class values are editable heuristics, not benchmark claims, and no unresolved multiplier values are hard-coded.

## Project structure

```text
handoff-guard/
├── .codex-plugin/plugin.json
├── SKILL.md
├── skills/handoff-guard/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── README.md
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

## Plugin submission tests

`evals/plugin-submission-tests.json` contains seven positive and eight negative fixtures for Plugin review. They cover ordinary-Chat handoff creation, explicit handoff requests, Work-environment no-recursion cases, known-model preflight, material mismatches, provider fallback, and the rule that unavailable model/reasoning metadata returns `UNVERIFIED` without blocking execution.

## Limitations

- Routing is a transparent heuristic, not a benchmark or live price comparison.
- Provider availability is supplied by the caller; the skill does not call provider APIs.
- Cost classes are coarse configuration labels and should be maintained by the project owner.
- A handoff cannot prove that an implementation is correct; it only preserves the execution contract and validates required fields.

## Roadmap

- Add more provider profiles without changing selector logic.
- Add optional project-specific handoff fields while keeping the core contract small.
- Add independent evaluation fixtures for more agent environments.

## License

MIT. See [LICENSE](LICENSE).
