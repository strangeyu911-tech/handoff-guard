# Handoff Guard

English | [简体中文](README.zh-CN.md)

> A lightweight model-aware workflow layer that turns settled ChatGPT planning into safe, structured coding-agent execution.

Handoff Guard helps a Chat conversation decide when planning is ready to move into Work, preserves the implementation contract, recommends the cheapest model that is reliably sufficient, and checks the receiving agent before files change.

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
- **Guides installation safely:** generates, validates, and copies a managed block for the user to save manually in ChatGPT on Windows.

## Installation

### Windows — Guided Install

The primary distribution artifact is:

```text
HandoffGuard-Installer-v0.1.0.exe
```

Download it from the repository's [GitHub Releases](https://github.com/strangeyu911-tech/handoff-guard/releases) and run the installer. It generates the versioned Handoff Guard managed block, copies it to the clipboard, and opens [ChatGPT Web](https://chatgpt.com/). The final paste and save are always performed by you in `Settings → Personalization → Custom Instructions`.

The installer does not read, write, save, verify, back up, repair, or uninstall ChatGPT account settings. It has no supported Custom Instructions API or settings deep link to use. Its local update/removal helpers operate only on text you explicitly paste into the installer.
It does not use guessed `chatgpt://` links; **Open ChatGPT Web** opens only the public web URL.

Status example: `Handoff Guard block copied. No ChatGPT account setting was changed.`

If a release artifact is not published yet, see [Windows installer build and acceptance](docs/windows-installer.md) to build it from source.

The installer is transparent about using ChatGPT Custom Instructions. That setting is the runtime adapter; Core policy, routing, schema, and validation remain separate product layers.

### Manual installation

You can also open [CUSTOM-INSTRUCTIONS.md](CUSTOM-INSTRUCTIONS.md), copy its generated managed payload, and paste it alongside—not over—your existing Custom Instructions.

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
└─ Guided install lifecycle
   ├─ generate and copy
   ├─ local update/removal transformation
   └─ manual save in ChatGPT
```

`runtime/custom-instructions.txt` is the canonical ChatGPT runtime template. Both the Windows installer and the generated `CUSTOM-INSTRUCTIONS.md` consume that file, and tests enforce parity with the Core routing dimensions. This prevents the installer from acquiring a second, handwritten policy.

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

Automatic handoff generation is allowed only in a reliably ordinary Chat / discussion conversation after a concrete development boundary. Any file access or edit, terminal command, code change, test run, Git operation, or other implementation signal makes the thread a Work / implementation environment. Handoff Guard does not append a new Work handoff there. If the surface is uncertain, it fails closed. An explicit user request for a handoff overrides the automatic-emission gate.

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

## Routing policy

The selector evaluates operation mode separately from independent decision risk. File count, repository count, code volume, reading volume, prompt length, or `task_complexity` alone never escalates work to Sol / strong.

- **Luna / general, Medium:** research, read-only audits, inventories, documentation, tests, and implementation against settled architecture—even when the workload is large.
- **Sol / strong, Medium:** high novelty, ambiguity, blast radius, or irreversibility; a new cross-system contract; data-integrity risk; destructive operations; unsettled architecture; an unbounded bugfix; or two evidenced prior failures.
- **Budget / Low:** simple mechanical or cost-sensitive work when no independent risk rule requires more.

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
├── skills/handoff-guard/        # alternative Skill adapter
├── CUSTOM-INSTRUCTIONS.md       # generated manual-install artifact
├── SECURITY.md
└── LICENSE
```

## License

MIT. See [LICENSE](LICENSE).
