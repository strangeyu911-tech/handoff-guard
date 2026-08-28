# Handoff specification

A handoff is a compact execution contract between agents. It must preserve decisions that should not be re-planned and provide enough routing/preflight data for the next agent.

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

The receiving agent should:

- run routing/preflight before implementation;
- stop for a clear model-tier mismatch and ask the user to switch;
- treat locked decisions and guardrails as binding;
- implement the next objective within scope;
- update the checkpoint and completed state when handing off again.
