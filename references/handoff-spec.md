# Handoff specification

A Markdown handoff is a compact compatibility representation of an execution contract between agents. The versioned contract object is the semantic source of truth; Markdown preserves decisions that should not be re-planned and provides enough routing/preflight data for the next agent.

## Emission boundary

Automatic handoff generation is allowed only in a reliably ordinary Chat / discussion conversation that has reached a settled architecture decision, a concrete next-stage implementation plan, or a stage-level acceptance/checkpoint conclusion. A thread with project file access or edits, terminal commands, code changes, tests, Git operations, or other clear implementation activity is a Work / implementation environment. Do not generate or append a new Work handoff there, even after completion, a checkpoint, a commit, or a next-stage plan. If the mode is uncertain, do not generate automatically. An explicit user request for a handoff overrides this automatic gate.

Required sections or labels:

1. `Recommended model`
2. `Reasoning effort`
3. `Preflight`
4. `Current state`
5. `Completed`
6. `Checkpoint` (commit, tag, file checkpoint, or an explicit `none`)
7. `Next objective`
8. `Locked decisions / boundaries`
9. `Do-not / guardrails`

The validator accepts Markdown headings or `Label: value` lines, case-insensitively. A section must contain non-whitespace content. Keep the handoff factual: distinguish completed work from intended work, and state uncertainty instead of inventing a checkpoint or model price.

Phase 1 contract primitives live in `handoff_guard_core/contract.py`. Use
`handoff_guard_core.markdown` to import legacy Markdown or export a human-readable
document containing the canonical JSON contract. The Markdown compatibility layer
fills unavailable legacy facts with explicit `unknown` / `UNVERIFIED` states; it
does not infer executor, sandbox, approval, context, or acceptance evidence.

The receiving agent should:

- run routing/preflight before implementation;
- stop for a clear model-tier mismatch and ask the user to switch;
- treat locked decisions and guardrails as binding;
- implement the next objective within scope;
- update the checkpoint and completed state when handing off again.
