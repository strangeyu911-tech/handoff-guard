# Handoff Guard

Handoff Guard is a small, open-source Agent Skill for coding-agent boundaries:

> Preserve decisions, choose the cheapest sufficient model, and stop the next agent from re-planning settled work.

## Why it exists

Agent handoffs often lose two things at once: the implementation contract and the model decision. The receiving agent then spends tokens re-discovering architecture, or runs a simple task on an unnecessarily expensive model, or starts a complex task on a model that is unlikely to finish it reliably.

Handoff Guard joins those concerns:

- **Model Router:** decides who should do the work.
- **Handoff Skill:** decides what should be handed over.
- **Handoff Guard:** decides what to hand over, which model should do the next stage, and whether that agent may start.

## Workflow

```text
Chat / Architect Agent
        |
        | structured handoff + routing recommendation
        v
Receiving Work Agent -----> preflight
                              |
                 +------------+------------+
                 |                         |
             tier aligned              mismatch
                 |                         |
                 v                         v
           implement scope          stop and ask to switch
                 |
                 v
          update checkpoint
```

## Installation

Copy the `handoff-guard` folder into a discoverable Agent Skills directory:

```text
$CODEX_HOME/skills/handoff-guard/
```

If `CODEX_HOME` is not set, use the standard user skills directory for your agent (commonly `~/.codex/skills/`). The folder must contain `SKILL.md` at its root. The skill is discoverable automatically; the UI metadata is in `agents/openai.yaml`.

## Usage

When ending an architecture or implementation conversation, ask the agent to create a Handoff Guard handoff. Use the template in `assets/handoff-template.md` and include a real commit/file checkpoint or explicitly write `none`.

For deterministic routing:

```bash
python scripts/select_model.py --input '{"task_complexity":"moderate","task_type":"implementation","architecture_settled":true,"provider_availability":["codex","workbuddy"]}'
```

For preflight, include `current_model` in the input. The result contains `block_current_execution`; a true result means the receiving agent should stop and ask the user to switch.

For validation:

```bash
python scripts/validate_handoff.py path/to/handoff.md
```

The validator returns JSON and a non-zero exit status when a required field is missing.

## Provider fallback

Provider choice is configuration-driven. If the user says GPT/Codex has no quota, set `quota_unavailable: true` and identify `quota_provider`; the default profile routes to an available WorkBuddy provider. If the user explicitly prefers WorkBuddy, set `preferred_provider: "workbuddy"`.

The default WorkBuddy catalog in `references/provider-profiles.json` includes Auto, HY3, GLM-5.3, GLM-5.2, GLM-5.1, GLM-5V-Turbo, MiniMax-M3, Kimi-K3, Kimi-K2.7-Code, Kimi-K2.6, Deepseek-V4-Flash, and Deepseek-V4-Pro. The tier/cost-class values are editable heuristics, not benchmark claims, and no unresolved multiplier values are hard-coded.

## Project structure

```text
handoff-guard/
├── SKILL.md
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
    ├── test_select_model.py
    └── test_validate_handoff.py
```

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
