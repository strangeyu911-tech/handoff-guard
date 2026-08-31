# Handoff Guard

English | [简体中文](README.zh-CN.md)

## 🚀 Spend less Codex / Work quota; save tokens for real execution

I built Handoff Guard for a simple reason: I do not want to spend scarce
Codex / Work coding-agent tokens and quota on discussions, decisions, and
repeated exploration that could happen in ordinary Chat first. Ordinary Chat
is typically metered separately from Work / Codex coding-agent quota, but exact
limits depend on the host product and plan.

Do not make a coding agent do all of the upfront thinking for you:

```text
Ordinary Chat / Architect
  → discuss architecture, break down work, choose a model, organize context
  → Handoff Guard forms a clear execution contract
  → Work / Codex receives only implementation work with decisions locked
```

Handoff Guard recommends the cheapest model that is reliably sufficient, so
simple or low-risk work stays on Luna / general instead of escalating to Sol
just because it has many files, lots of code, heavy reading, or a long prompt.
The goal is less repeated exploration, fewer wrong model-tier choices, and less
meaningless coding-agent token / quota consumption—so Plus / Pro users can make
their coding-agent allowance last longer.

> A lightweight policy layer for ChatGPT → coding-agent workflows that decides whether to hand off, what context to preserve, and which model/reasoning tier to use.

Ordinary Chat / Architect does the thinking; Handoff Guard turns settled plans
into a structured handoff, recommends the right model, and runs the execution
preflight; Work / Codex does the actual file changes and implementation. The
product itself is the policy and contract layer; Custom Instructions, Skills,
and the Guided Installer are runtime adapters around it.

```text
Chat / Architect → structured handoff → execution preflight → Work
```

It is more than a static prompt. The repository contains a deterministic model selector, a versioned handoff contract, a validator, regression fixtures, and execution-boundary rules. Custom Instructions are one lightweight runtime adapter used to activate those behaviors in ChatGPT—not the product's entire architecture.

## What it does

- **Finds the handoff boundary:** emits an automatic handoff only after a settled decision, concrete implementation plan, or stage checkpoint in an ordinary Chat conversation.
- **Preserves the contract:** carries forward current state, completed work, checkpoints, locked decisions, scope, and guardrails.
- **Recommends an appropriate model:** separates workload size from independent decision risk so large settled work does not automatically consume the strongest model.
- **Checks before execution:** returns `PASS`, `BLOCK`, or `UNVERIFIED` before a receiving agent starts changing files.
- **Keeps behavior testable:** validates handoff structure and runs routing policy against regression fixtures.
- **Offers a safe runtime path:** generates, validates, and copies a managed block for the user to save manually in ChatGPT on Windows.

## Complexity ≠ Sol

Complexity measures workload, not automatic escalation to Sol. Many files, lots
of code, heavy reading, a long prompt, or batch implementation against a settled
architecture are not risk signals by themselves. Sol / strong is for independent
risk such as high novelty, ambiguity, blast radius, irreversibility, data
integrity, a cross-system contract, or repeated failures.

## Evaluation and regression evidence

The repository currently runs **72 automated tests** and maintains **40 declared evaluation cases** across routing and handoff-emission fixtures. Representative regression categories include:

- complexity does not automatically escalate a settled task to Sol;
- destructive migration and cross-system contract risk select Sol / strong;
- repeated failure escalation selects Sol / strong;
- low-risk implementation and large read-only work remain Luna / general;
- first-time architecture decisions remain high-risk even when the workload is moderate;
- model and reasoning recommendation, quota fallback, `PASS`, `BLOCK`, and `UNVERIFIED` behavior remain explicit;
- Work-environment and uncertain-surface cases do not recursively emit a handoff.

See the [routing fixtures](evals/evals.json), [handoff-emission fixtures](evals/plugin-submission-tests.json), [routing tests](tests/test_select_model.py), and [policy tests](tests/test_handoff_emission_policy.py).

## Installation

### Windows — Guided Install adapter

The Windows executable is a local Guided Install adapter, not the product's core. It helps place the runtime policy into ChatGPT Custom Instructions; the final paste and save remain manual.

The current Windows distribution artifact is:

```text
HandoffGuard-Installer-v0.1.0.exe
```

Download it from the repository's [GitHub Releases](https://github.com/strangeyu911-tech/handoff-guard/releases) and run the installer. It generates the versioned Handoff Guard managed block, copies it to the clipboard, and opens [ChatGPT Web](https://chatgpt.com/). The final paste and save are always performed by you in `Settings → Personalization → Custom Instructions`.

The installer does not read, write, save, verify, back up, repair, or uninstall ChatGPT account settings. It has no supported Custom Instructions API or settings deep link to use. Its local update/removal helpers operate only on text you explicitly paste into the installer.
It does not use guessed `chatgpt://` links; **Open ChatGPT Web** opens only the public web URL.

Status example: `Handoff Guard block copied. No ChatGPT account setting was changed.`

If a release artifact is not published yet, see [Windows installer build and acceptance](docs/windows-installer.md) to build it from source.

The installer is transparent about using ChatGPT Custom Instructions. That setting is the current stable runtime adapter; Core policy, routing, schema, and validation remain separate product layers.

### Manual installation

You can also open [CUSTOM-INSTRUCTIONS.en.md](CUSTOM-INSTRUCTIONS.en.md) for the generated English manual-installation artifact, or use the default [CUSTOM-INSTRUCTIONS.md](CUSTOM-INSTRUCTIONS.md) Chinese artifact. Copy the generated managed payload alongside—not over—your existing Custom Instructions.

Manual installation activates the runtime rules. Keep the managed block intact so the local Generate, Update, and Removal instructions remain easy to follow.

### Skill adapter (advanced)

The existing Skill adapter remains available for hosts that load Agent Skills. Copy the repository folder to the host's standard skills directory, or use the skills-only Plugin manifest in `.codex-plugin/plugin.json`. The canonical Plugin Skill is `skills/handoff-guard/SKILL.md`; the root `SKILL.md` supports direct Skill installation.

This is an alternative runtime adapter, not the main Windows installation story. The repository does not claim an OpenAI-official integration or an independently verified public Plugin Directory listing.

## Product architecture

```text
Handoff Guard
├─ Core
│  ├─ handoff boundary policy
│  ├─ model / reasoning recommendation
│  ├─ handoff schema
│  └─ execution preflight
├─ Validation
│  ├─ deterministic selector and validator
│  ├─ eval fixtures
│  └─ regression tests
├─ Runtime adapters
│  ├─ Windows Installer / Custom Instructions
│  └─ Skill adapter
└─ Adapter support
   ├─ guided generate / copy / open-web flow
   ├─ local update/removal transformation
   └─ manual save in ChatGPT
```

`runtime/custom-instructions.txt` is the canonical Chinese default runtime template consumed by the Windows installer and generated `CUSTOM-INSTRUCTIONS.md`. The generated English manual artifact is built from the language-equivalent `runtime/custom-instructions.en.txt` by the same generator; tests enforce parity and routing dimensions for both. This keeps each runtime artifact tied to a canonical source without adding a second installer policy.

## Guided managed-block installation

The Windows installer does not use UI Automation, desktop selectors, coordinates, OCR, private endpoints, tokens, or cookies. Its managed region is versioned and checksummed:

```text
[HANDOFF-GUARD:BEGIN version=0.1.0 sha256=...]
...
[HANDOFF-GUARD:END]
```

- **Generate:** creates the canonical block locally.
- **Copy:** puts only the generated block or local result on the clipboard.
- **Install:** guides the user through pasting the copied block and saving it manually.
- **Update:** replaces one valid older block in text supplied by the user and preserves text outside it.
- **Uninstall:** generates removal instructions; the user deletes the managed block and saves manually.
- **Removal:** generates text with only the Handoff Guard block removed.
- **Repair:** regenerates a canonical block after a damaged managed region is supplied locally.
- **Backup:** is available only for text the user explicitly supplies locally.
- **Verification:** locally checks payload, version, marker format, and checksum; it cannot verify a ChatGPT paste, save, or sync.

The installer does not send Custom Instructions to its own servers or third parties and does not access ChatGPT credentials. When you manually save the generated block in ChatGPT, that content is handled and synchronized according to [OpenAI's ChatGPT data practices](https://openai.com/policies/how-your-data-is-used-to-improve-model-performance/). See [SECURITY.md](SECURITY.md).

## Handoff and preflight contract

Automatic handoff generation is allowed only in a reliably ordinary Chat / discussion conversation after a concrete development boundary. Any file access or edit, terminal command, code change, test run, Git operation, or other implementation signal makes the thread a Work / implementation environment. Handoff Guard does not append a new Work handoff there. If the Chat-versus-Work surface is uncertain, automatic emission fails closed. An explicit user request for a handoff overrides the automatic-emission gate.

A valid handoff includes:

1. Recommended model
2. Reasoning effort
3. Preflight
4. Current state
5. Completed
6. Checkpoint (a real commit, tag, file checkpoint, or `none`)
7. Next objective
8. Locked decisions / boundaries
9. Do-not / guardrails

Use [assets/handoff-template.md](assets/handoff-template.md) and validate it with `scripts/validate_handoff.py`.

Preflight results have narrow meanings:

- `PASS`: the known configuration is suitable.
- `BLOCK`: a material tier mismatch or declared provider quota conflict is confirmed.
- `UNVERIFIED`: the host cannot expose reliable model or reasoning metadata; execution may continue with a manual verification warning.

Unknown is advisory, not blocking. Handoff Guard is not a runtime LLM gateway or automatic model router, does not control ChatGPT's model picker, and never switches providers or models automatically.

## Validated platform constraints

These are scoped engineering conclusions from the currently tested ChatGPT Plus ordinary-Chat surface and the currently tested ChatGPT Desktop version; they are not claims about every future version or plan:

- Personal Skill injection could not be treated as a reliable runtime on the tested ChatGPT Plus ordinary-Chat target surface.
- ChatGPT Desktop Custom Instructions could not be reliably read or written through the tested UI Automation (UIA) path.
- No public Custom Instructions API is available for the current product path, so Handoff Guard does not rely on one.
- Handoff Guard does not use private Web APIs, tokens, cookies, internal endpoints, coordinate automation, or OCR as a production workaround.

Therefore, Custom Instructions is the current stable runtime. Skill and UIA remain documented as explored adapters and platform evidence, not as guaranteed installation paths. See [design decisions](docs/design-decisions.md), [Windows installer constraints](docs/windows-installer.md), and [SECURITY.md](SECURITY.md).

## Design principles and lessons

- **Explain model recommendations.** Show a short reason with every model and reasoning recommendation so users can audit the choice and catch silent misrouting. Keep that reason in Chat; the Work handoff stores only the selected model and reasoning effort plus execution context.
- **Put routing information first.** Put `Model` and `Reasoning effort` on the first line or at the very top of a handoff, because the receiving user needs the selection before the rest of the context.
- **Keep handoffs compact.** Aim for about 10,000 characters. This is a product constraint observed in actual ChatGPT Desktop use, not an official ChatGPT hard limit. If a handoff must be longer, attach a text file as a fallback; that adds manual work and handoff time.
- **Prefer `UNVERIFIED` over unnecessary blocking.** If metadata cannot be confirmed but continuing is not a high-risk irreversible action, report `UNVERIFIED` and ask for manual verification. Use `BLOCK` only when verification is material to safe continuation.
- **Sandbox absence is not host absence.** A sandbox that cannot resolve Python, `py`, `pip`, or another tool does not prove the user's host lacks it. Distinguish sandbox capability from host capability and, when the tool is necessary, try the real execution environment with normal approval handling.
- **Detect execution environments semantically.** Local project access, file edits, terminal execution, code changes, tests, or Git operations make the thread a Work / execution environment regardless of its product mode label. Do not generate another Work handoff there; this prevents recursive context and token waste.

For the rationale and evidence behind these rules, see [design decisions](docs/design-decisions.md).

## Routing policy

The selector evaluates operation mode separately from independent decision risk. File count, repository count, code volume, reading volume, prompt length, or `task_complexity` alone never escalates work to Sol / strong.

- **Luna / general, Medium:** research, read-only audits, inventories, documentation, tests, and implementation against settled architecture—even when the workload is large.
- **Sol / strong, Medium:** high novelty, ambiguity, blast radius, or irreversibility; a new cross-system contract; data-integrity risk; destructive operations; unsettled architecture; an unbounded bugfix; or two evidenced prior failures.
- **Budget / Low:** simple mechanical or cost-sensitive work when no independent risk rule requires more.
- **Provider fallback:** when a declared Codex/GPT quota constraint makes the preferred provider unavailable, recommend the first compatible fallback (the default profile includes WorkBuddy); any provider or model switch remains manual.

Model names and cost classes are configuration, not benchmark claims. The recommendation is for manual action by the user or host.

## Development and verification

Run the deterministic selector:

```bash
python scripts/select_model.py --input '{"task_complexity":"moderate","operation_mode":"implementation","architecture_settled":true,"provider_availability":["codex","workbuddy"]}'
```

Regenerate or check the manual runtime artifact:

```bash
python scripts/generate_custom_instructions.py
python scripts/generate_custom_instructions.py --check
```

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The automated suite covers selector regressions, handoff validation, emission boundaries, runtime-template parity, managed-block lifecycle, local transformation, local backup, confirmation, repair, and Guided Install behavior. It does not verify that ChatGPT has received or saved anything; final account changes are deliberately outside the installer.

## Repository structure

```text
handoff-guard/
├── handoff_guard_installer/     # Windows UI and managed lifecycle
├── runtime/                     # canonical ChatGPT runtime template
├── references/                  # handoff, routing, and provider contracts
├── scripts/                     # selector, validator, generator, build
├── evals/                       # regression fixtures
├── tests/                       # Core and installer tests
├── docs/                        # platform constraints and design decisions
├── skills/handoff-guard/        # alternative Skill adapter
├── CUSTOM-INSTRUCTIONS.md       # generated manual-install artifact
├── CUSTOM-INSTRUCTIONS.en.md    # generated English manual-install artifact
├── SECURITY.md
└── LICENSE
```

## License

MIT. See [LICENSE](LICENSE).
