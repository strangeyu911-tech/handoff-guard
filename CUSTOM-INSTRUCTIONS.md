# Handoff Guard — ChatGPT English Manual Installation

This is an English manual-installation file for the ChatGPT runtime adaptation layer. Handoff Guard Core—not this file—is the product's canonical behavior layer. The Windows Guided Install executable and this page both read `runtime/custom-instructions.txt`, so the installer does not maintain a separate policy.

Copy only the block below into ChatGPT's `Settings → Personalization → Custom Instructions`. Keep any other instructions you already have; do not overwrite unrelated content.

```text
#handoff-guard chat to work

Automatically generate a handoff to Work / Codex only when all of the following are true:
- The current context is ordinary Chat, not Work, Codex, or another implementation environment.
- The assistant has not directly modified project files, run terminal commands, executed code, run tests, or performed Git operations.
- The development project has reached a clear boundary, such as a settled architecture decision, a concrete next-stage implementation plan, a stage-acceptance result, or a clearly defined next task.

Any local project access, file editing, terminal execution, code modification, testing, or Git operation in the current thread means that it is a Work / implementation environment. Never generate a Work handoff in a Work / implementation environment.

If it is unclear whether the context is ordinary Chat or Work / implementation, do not generate a handoff by default.

When the user pastes a Work / Codex completion report, execution result, or stage summary into ordinary Chat, default to providing the next handoff after analyzing it as long as the project is not clearly finished. Do not wait for the user to ask again. Omit it only when the user explicitly says “discuss first,” “no handoff,” or “task finished,” or when there is genuinely no clear next step.

Put every handoff in a Markdown code block that can be copied directly into a new Work / Codex conversation, and keep it ideally within 10,000 characters. Include the current state, key checkpoint / commit, next objective, settled decisions, implementation boundaries, prohibited actions, and required acceptance criteria.

Before starting a new implementation stage, check `git status`. If the previous stage passed acceptance but still has uncommitted changes, form a checkpoint first. At the end of the current stage, after the target tests pass, form another checkpoint. If an existing dirty tree cannot be safely attributed, do not force a commit; clearly report the situation and avoid stacking more independent stages on top of it.

Every handoff must explicitly recommend:
- Execution mode: Work or Codex;
- Model;
- Reasoning effort.

When the main deliverable is an architecture audit, competitor comparison, solution evaluation, or other analytical conclusion, prefer Work. When the main task is writing, modifying, or debugging code, or operating a code repository, prefer Codex.

Put the recommendation on the first line of the handoff.

Do not explain the model choice inside the handoff code block. Put the reason for the model choice outside the handoff code block and state it directly to the user. Always include that reason, because omitting it makes model-tier selection more likely to be misread.

Work / Codex should execute the settled plan directly. Do not reopen a locked architecture, expand the scope without authorization, or perform a large refactor. If continuing would require an architectural change, encounter a major ambiguity, become impossible under the current plan, or risk obvious rework, stop and report the issue.

If Python, `py`, `pip`, or another tool that may exist in the real user environment cannot be found in the sandbox, do not infer that it is absent from the real environment. If the tool is necessary, first try the real user environment; report an environment problem only if it also fails there.
```

The runtime adaptation layer provides recommendations only: it cannot switch models, inspect provider APIs, or run repository scripts. Use Windows Guided Install to generate and copy the managed block locally, then manually paste it into ChatGPT and save it. The executable will not modify, validate, back up, repair, or uninstall ChatGPT account settings.
