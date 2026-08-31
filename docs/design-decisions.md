# Handoff Guard design decisions

This document records the decisions that explain the current product shape. It
uses `Decision → Evidence → Consequence` rather than a chronological change log.

## Policy layer, not installer or Skill

**Decision** → Treat Handoff Guard Core as the policy, routing, handoff-schema,
and preflight layer. Treat Custom Instructions, the Skill adapter, and the
Windows Guided Installer as runtime or distribution adapters.

**Evidence** → The core behavior is exercised by the deterministic selector,
validator, fixtures, and execution-boundary tests. The installer only generates
and transforms local text; it cannot modify ChatGPT account settings. Skill
loading is host-dependent.

**Consequence** → Product value is evaluated by handoff quality, routing
recommendations, preflight semantics, and regression evidence—not by whether an
installer can silently change an account setting or whether a Skill happens to
be injected on a particular surface.

## Custom Instructions is the current stable runtime

**Decision** → Use ChatGPT Custom Instructions as the current stable runtime
adapter, with a generated managed block and a manual final save.

**Evidence** → No public Custom Instructions API is available for the current
product path. The tested desktop editor did not provide a reliable supported
contract for automatic account-setting writes.

**Consequence** → Guided Install is limited to Generate / Copy / Open ChatGPT /
Manual Save, plus local update, removal, repair, backup, and validation of text
the user supplies. It does not claim to install, verify, back up, repair, or
uninstall ChatGPT settings.

## Skill injection is scoped platform evidence

**Decision** → Keep the Skill adapter available, but do not present it as the
primary or guaranteed Chat runtime.

**Evidence** → Personal Skill injection could not be treated as reliable on the
currently tested ChatGPT Plus ordinary-Chat target surface.

**Consequence** → README and runtime documentation describe Skill as an
alternative adapter and state the tested scope. The result is not generalized
to every plan or future product version.

## UIA is not a production installation workaround

**Decision** → Do not use UI Automation, coordinate automation, OCR, private Web
APIs, tokens, cookies, internal endpoints, or guessed deep links to write ChatGPT
settings.

**Evidence** → The tested ChatGPT Desktop Custom Instructions editor could not
be reliably read or written through the validated UIA path. The product also has
no public API contract for this operation.

**Consequence** → The executable opens only the public ChatGPT Web URL and
reports local success only. UIA remains documented as explored platform
evidence, not as a supported install path.

## Complexity does not imply Sol

**Decision** → Separate workload size from independent decision risk. Complexity,
file count, repository count, reading volume, prompt length, or `task_complexity`
alone must not escalate a task to Sol / strong.

**Evidence** → Regression cases cover large read-only audits and large settled
implementations that remain Luna / general, alongside architecture, destructive
migration, cross-system contract, and repeated-failure cases that select Sol /
strong.

**Consequence** → Sol is reserved for novelty, ambiguity, blast radius,
irreversibility, data-integrity risk, destructive work, new cross-system
contracts, unsettled architecture, unbounded bugfixes, or at least two evidenced
prior failures.

## Recommendation reasons stay outside the handoff payload

**Decision** → Show a concise explanation for model and reasoning recommendations
in Chat, but keep the handoff payload limited to the selected model, reasoning
effort, and execution context.

**Evidence** → Users need a reason to audit a recommendation and catch silent
misrouting. Work needs a compact, stable execution contract rather than the
selector's conversational explanation.

**Consequence** → Recommendation explanations improve inspectability without
adding repeated prose to every handoff or turning the handoff into a second
routing policy.

## Routing information comes first

**Decision** → Put `Model` and `Reasoning effort` on the first line or at the top
of every handoff.

**Evidence** → The receiving user needs to choose the model and reasoning tier
before reading the rest of the project context.

**Consequence** → A handoff is immediately actionable after pasting into Work,
and the routing choice is not hidden at the end of a long context block.

## Handoffs stay compact

**Decision** → Aim to keep a handoff near 10,000 characters.

**Evidence** → Actual ChatGPT Desktop use showed that very long pasted or added
handoffs can introduce delay or a stuck interaction.

**Consequence** → Keep only execution-critical context in the payload. Use a text
file attachment as a fallback for genuinely oversized context, recognizing that
it adds manual work and handoff time. The figure is an observed product
constraint, not an official ChatGPT hard limit.

## Unknown metadata is UNVERIFIED, not automatically BLOCK

**Decision** → Return `UNVERIFIED` when model or reasoning metadata cannot be
confirmed, unless the missing fact is material to safe continuation.

**Evidence** → A host may hide its active model or reasoning metadata while the
task itself remains low-risk and reversible. Blocking every unknown state
prevented otherwise safe work.

**Consequence** → `BLOCK` is reserved for confirmed material tier mismatch or
declared quota conflict. `UNVERIFIED` shows the recommendation, asks for manual
verification when useful, and allows execution to continue.

## Sandbox absence is not host absence

**Decision** → Distinguish sandbox capability from the user's host environment.

**Evidence** → A command can be unavailable inside a restricted execution
environment while being available in the real user environment.

**Consequence** → Never infer that Python, `py`, `pip`, or another tool is absent
from the user's computer solely because the sandbox cannot resolve it. If the
tool is necessary, try the real execution environment with normal approval
handling.

## Work is detected semantically and does not recurse

**Decision** → Treat local project access, file edits, terminal execution, code
changes, tests, or Git operations as evidence of a Work / execution environment,
regardless of a product mode label. Do not automatically generate another Work
handoff there.

**Evidence** → Emission fixtures cover completed edits, tests, commits, next-stage
plans, and uncertain surfaces containing implementation signals.

**Consequence** → Handoff Guard avoids recursive handoffs, duplicate context,
and unnecessary token use. Only an explicit user request overrides the automatic
emission gate.
