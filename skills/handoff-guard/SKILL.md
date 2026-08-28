---
name: handoff-guard
description: Create and consume model-aware development handoffs, recommend the cheapest sufficient provider/model for the next task, and block execution when the current model is clearly too strong or too weak. Use when a coding task crosses agents, an architecture decision is already settled, quota/provider fallback matters, or a Work agent needs a preflight check.
---

# Handoff Guard

Use this skill at an agent boundary. Preserve settled decisions, choose the cheapest model that is reliably sufficient, and make the next agent perform a short preflight before changing files.

## Handoff emission gate

Apply this gate before generating a handoff automatically. A handoff may be generated automatically only when both conditions are true:

1. The current conversation is reliably an ordinary Chat / discussion conversation, not a Work / implementation environment.
2. The conversation has reached a concrete development boundary: a settled architecture decision, a specific next-stage implementation plan, or a stage-level acceptance/checkpoint conclusion.

Treat the current thread as a Work / implementation environment if it has access to or uses any implementation capability, including project file access or edits, terminal commands, code changes, tests, Git status/diff/commit/push, or other clear coding activity. One such signal is sufficient. This classification remains true after the task is finished and after a checkpoint, commit, or next-stage plan is formed. Do not append a new Work handoff in that environment; this is the no-recursion rule.

If the Chat-versus-Work mode cannot be determined reliably, fail closed: do not generate an automatic handoff. Terminal or file-operation evidence is implementation evidence, not ordinary Chat evidence.

An explicit user request for a handoff (for example, “give me a Work handoff” or “generate a handoff”) overrides this automatic-emission gate. When the user explicitly asks, generate and validate the handoff normally. This gate changes only automatic handoff emission; it does not change model routing or preflight behavior.

## Core workflow

1. After the emission gate allows a handoff, produce the fields in [handoff-spec.md](../../references/handoff-spec.md), using [handoff-template.md](../../assets/handoff-template.md) when useful.
2. Recommend the next stage's provider/model with `../../scripts/select_model.py`. Read [routing-policy.md](../../references/routing-policy.md) for the input shape and decision rules.
3. Run the receiving agent's preflight before implementation. Known and suitable is `PASS`; a material model mismatch is `BLOCK`; unavailable model/reasoning metadata is `UNVERIFIED` and execution may continue. If the selector says the current model is clearly overpowered or underpowered, stop and ask the user to switch models. A small Medium/High reasoning mismatch is advisory, not a blocker.
4. Once preflight passes, execute only the stated next objective. Do not re-open locked architecture decisions, brainstorm alternatives, expand scope, or perform a broad refactor unless the handoff explicitly changes.
5. Validate a handoff with `../../scripts/validate_handoff.py`; fix every reported required-field error before passing it onward.

## References and scripts

- Read [routing-policy.md](../../references/routing-policy.md) when selecting a provider/model or interpreting preflight output.
- Read [provider-profiles.md](../../references/provider-profiles.md) when editing the model catalog or adding a provider. The data source is [provider-profiles.json](../../references/provider-profiles.json); model names and cost metadata are not part of selector logic.
- Read [handoff-spec.md](../../references/handoff-spec.md) when creating or reviewing a handoff.
- Call `select_model.py` for deterministic routing and `validate_handoff.py` for deterministic field validation. Both accept JSON/stdin-friendly interfaces; use `--help` for CLI details.

## Boundary

This skill coordinates handoffs and preflight only. It recommends a manual model/provider choice; it does not control a host's model picker, automatically switch models/providers, migrate a session, or dispatch a request to another model. It is not an LLM gateway, API proxy, benchmark system, billing system, MCP server, or general agent orchestration framework.

Unknown is advisory, not blocking. If the host cannot reliably expose the active model, Handoff Guard treats the configuration as unverified rather than mismatched, shows the recommendation, and allows execution to continue.
