# Routing policy

Handoff Guard uses an explainable heuristic rather than online pricing, benchmarks, or provider API calls. The target is the cheapest model tier that is sufficient for the task.

## Selector input

`select_model.py` accepts a JSON object with these fields:

```json
{
  "task_complexity": "simple | moderate | complex",
  "task_type": "docs | implementation | architecture | bugfix | tests | other",
  "operation_mode": "read_only_audit | research | inventory | reuse_audit | capability_review | documentation | tests | implementation | architecture | bugfix | migration",
  "decision_novelty": "low | medium | high",
  "ambiguity": "low | medium | high",
  "blast_radius": "low | medium | high",
  "irreversibility": "low | medium | high",
  "cross_system_contract": false,
  "data_integrity_risk": false,
  "destructive": false,
  "prior_failed_attempts": 0,
  "architecture_settled": true,
  "provider_availability": ["codex", "workbuddy"],
  "preferred_provider": "workbuddy",
  "quota_unavailable": false,
  "quota_provider": "codex",
  "cost_sensitivity": "low | medium | high",
  "current_model": {"provider": "codex", "tier": "general"},
  "current_reasoning_effort": "medium"
}
```

Only `task_complexity` is required for backwards-compatible routing. The risk fields are optional, but should be supplied when the task is a bugfix, migration, architecture decision, or cross-system change. Missing availability means every provider in the profile is considered available. `current_model` is optional; without it, routing is returned with `UNVERIFIED` status and execution remains allowed.

## Tier heuristic

- `Luna` is the default general tier for read-only audits, research, inventory, reuse audits, documentation, tests, and implementation against a settled architecture—even when the workload is large.
- `Sol` is reserved for independent high-risk signals: high decision novelty, ambiguity, blast radius, irreversibility, data-integrity risk, destructive operations, a new cross-system contract, or at least two prior failed attempts.
- An unsettled architecture and an unbounded bugfix remain strong-tier defaults for backwards compatibility. A bugfix explicitly bounded as low ambiguity, low blast radius, and low irreversibility is Luna-tier.
- A reversible migration without independent risk signals is Luna-tier; a destructive or high-irreversibility migration is Sol-tier.
- `task_complexity` describes workload size only. Complexity alone MUST NOT escalate a task to Sol/strong. A simple mechanical task may still use `budget` when no operation mode calls for Luna.
- A vision task requests `vision` when that tier exists; otherwise the selector falls back to `general` and explains it.

Cost sensitivity can move an otherwise low-risk task to `budget` when the provider has one. It does not downgrade a task with independent high-risk signals.

Model and reasoning recommendations are separate. The default regression policy recommends Medium reasoning for both Luna and Sol; a vision fallback keeps High effort.

## Provider selection

1. A requested `preferred_provider` wins when it is available.
2. If the preferred/quota provider is unavailable because the user says GPT/Codex quota is unavailable, choose the first available fallback provider with a compatible tier. This is the WorkBuddy path in the default profile.
3. If no preference or quota constraint applies, choose the available provider with the lowest configured cost class for the selected tier. Cost classes are coarse labels (`low`, `medium`, `high`), not price claims.
4. Model names, aliases, tier mappings, and cost classes come from `provider-profiles.json`. Do not add model names to selector code.

## Preflight

The selected task tier and current model tier are compared on the ordinal `budget < general < strong`; `vision` is compatible with `general` for non-vision work. The preflight state machine is explicit: known and suitable is `PASS`, known and materially mismatched is `BLOCK`, and unknown/unavailable model or reasoning metadata is `UNVERIFIED`. Block only when the current model is at least two tiers away from the required tier, or when the current provider is unavailable due to a declared quota constraint. A one-tier difference is acceptable and reported as an advisory. Reasoning effort differences, especially Medium vs High, do not by themselves block.

Unknown is advisory, not blocking. If the host cannot reliably expose the active model, Handoff Guard shows the recommendation, asks the user to verify it manually if needed, and allows execution to continue.

The output always includes `block_current_execution`, a recommended provider/model, a reasoning effort, and a short reason suitable for showing to the user.
