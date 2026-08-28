# Handoff Guard — Development Handoff

Use this template only after the handoff emission gate allows generation, or when the user explicitly requests a handoff. It must not be appended automatically by a Work / implementation task after execution, testing, or a checkpoint.

## Recommended model

- Provider: `<provider>`
- Model: `<model>`
- Model tier: `<budget | general | strong | vision>`

## Reasoning effort

`<low | medium | high>`

## Preflight

- Current model: `<provider/model/tier>`
- Status: `<PASS | BLOCK | UNVERIFIED>`
- Execution allowed: `<yes | no>`
- Reason: `<short explanation>`

## Current state

<What is true now.>

## Completed

- <Completed item>

## Checkpoint

`<commit SHA, tag, file checkpoint, or none>`

## Next objective

<One concrete outcome for the receiving agent.>

## Locked decisions / boundaries

- <Decision that is already settled>
- <Implementation boundary>

## Do-not / guardrails

- Do not re-plan the locked architecture.
- Do not expand scope or perform a broad refactor.
- <Task-specific guardrail>
