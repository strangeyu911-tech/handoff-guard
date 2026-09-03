# Handoff Guard vNext Development Roadmap

Status: canonical implementation source of truth  
Last verified: 2026-09-04
Baseline: `main` at `e2c281aeb72626265b6419950785a3b082191399`

This document turns the prior competitor / prior-art architecture audit into a
staged implementation and acceptance plan. It is a development roadmap, not a
competitor report. Future Work / Codex tasks should name the active phase and
update this document when that phase changes.

## Status tracker

| Phase | Status | Exit criteria | Evidence | Next |
|---|---|---|---|---|
| Phase 0 — Evidence repair & product cleanup | COMPLETE | Claims, canonical runtime, schema references, and test baseline are aligned and explicitly scoped | Generated artifacts checked; 72 discovered / 72 passed / 0 failed; 40 regression fixtures classified; README claims narrowed | Establish Phase 0 checkpoint, then implement Phase 1 |
| Phase 1 — Contract foundation | COMPLETE | Versioned contract has semantic validation, contradiction checks, and migration tests | `handoff_guard_core` typed contract/schema, 22 contract tests, Markdown compatibility; 94/94 bundled tests pass | Stop for Phase 2 review |
| Phase 2 — Native Codex path | NOT STARTED | Codex adapter maps the contract and returns normalized results in an exercised path | No adapter implementation in this roadmap change | Implement after contract foundation |
| Phase 3 — External context reuse | NOT STARTED | Context providers are replaceable, bounded, and tested independently of execution | No provider integration yet | Add Repomix / evidence providers |
| Phase 4 — Readiness / risk policy | NOT STARTED | Risk policy is explainable and benchmarked for false blocks and unsafe allows | Current selector is a legacy baseline only | Build policy inputs and benchmark |
| Phase 5 — Boundary detector + decision freeze | NOT STARTED | Corpus-backed boundary and decision-drift metrics meet agreed thresholds | Current behavior is mainly prompt / Custom Instructions driven | Build evaluation harness first |
| Phase 6 — Acceptance / completion gate | NOT STARTED | Completion requires contract-fulfillment evidence and handles partial / drifted outcomes | Current validator checks labels, not outcome quality | Define result evidence model |
| Phase 7 — Durable runtime / advanced adapters | NOT STARTED | Journal, idempotency, recovery, and optional adapters have failure-tested contracts | Explicitly deferred | Reassess only after core semantics stabilize |

No phase is complete merely because code exists or unit tests pass. Status must
include the evidence and the real user-path acceptance that supports it.

## 1. vNext North Star

### Product position

Handoff Guard is an **execution-boundary policy, contract, and verification
layer** for Chat-first development workflows. Its purpose is to decide when a
conversation has reached a safe execution boundary, freeze the decisions that
must not drift, express a verifiable execution contract, and determine whether
the resulting work actually fulfilled that contract.

One-sentence architecture boundary:

> Handoff Guard owns boundary, decision, contract, readiness, and acceptance
> semantics; an external executor owns transport and process execution.

### HG owns

- boundary detection and explicit / implicit approval semantics;
- decision freeze, contradiction detection, and locked-versus-mutable state;
- a versioned, transport-independent execution contract;
- readiness and execution-risk policy, including visible explanations;
- semantic acceptance, partial completion, escalation, and retry / replan signals;
- evaluation harnesses and outcome benchmarks;
- normalized result semantics independent of a particular executor.

### HG does not own

- repository packing or a proprietary context-packing format;
- a browser engine, DOM selector library, or ChatGPT UI automation path;
- a general provider / model gateway or automatic provider switching;
- executor transport, process leases, or crash-safe runtime primitives before
  the durable-runtime phase;
- an installer as the primary product value proposition.

### Reuse boundary and rationale

Reuse Codex SDK / App Server for Codex transport, Repomix for repository
context, existing CLI / MCP bridges for adapters, and Oracle or chatgpt-use as
an optional browser fallback. The decision is **REPOSITION AND REUSE** because
these adjacent capabilities already have stronger prior art or first-party
support. Rewriting them would increase maintenance and integration surface
without improving HG's core semantic contribution.

Model and reasoning recommendation remains a contract strategy field and a
readiness input. It is not the vNext moat and must not become a provider gateway.

## 2. Current baseline

### Repository and verified state

- Branch: `main`.
- HEAD at Phase 0 start: `e2c281aeb72626265b6419950785a3b082191399`.
- Working tree: clean at preflight; Phase 0 changes are attributable to the
  artifact repair and documentation cleanup described below.
- Existing roadmap / architecture documents: no prior vNext implementation
  roadmap; `docs/design-decisions.md` records current design decisions and
  `docs/windows-installer.md` records installer constraints. This file is the
  single canonical vNext implementation roadmap.

### Existing implementation surface

- `runtime/`: canonical Chinese and English Custom Instructions templates.
- `CUSTOM-INSTRUCTIONS.md` and `CUSTOM-INSTRUCTIONS.en.md`: generated manual
  installation artifacts.
- `scripts/select_model.py`: deterministic tier / provider recommendation and
  execution preflight. It separates workload complexity from independent risk,
  selects a configured provider/model, returns recommended reasoning effort,
  and emits `PASS`, `BLOCK`, or `UNVERIFIED` based on currently visible model,
  reasoning, quota, and tier metadata. It is a legacy policy baseline, not yet
  the vNext readiness policy.
- `scripts/validate_handoff.py`: Markdown / JSON handoff validator. It mostly
  finds required labels or non-empty JSON keys; it does not validate a typed,
  versioned contract, contradictions, executable acceptance criteria, evidence,
  drift, or semantic completion.
- `references/handoff-spec.md`: current Markdown handoff fields and emission
  boundary.
- `references/routing-policy.md` and `references/provider-profiles.json`:
  current heuristic and model catalog.
- `handoff_guard_installer/`, `installer.py`, and build scripts: Windows Guided
  Install adapter for local generate / copy / update / removal / repair / local
  validation. It cannot write or verify ChatGPT account settings.
- `skills/handoff-guard/` and root `SKILL.md`: alternative Skill runtime
  adapter, host-dependent and not the primary product path.
- `evals/`: routing and handoff-emission regression fixtures.
- `tests/`: selector, validator, emission, runtime parity, documentation,
  plugin, and installer tests.

### Boundary and contract reality

Boundary detection currently lives mainly in the prompt / Custom Instructions
runtime rule set. The Markdown handoff format and `validate_handoff.py` provide
structure, but not an independently enforceable semantic contract. The current
runtime also contains routing instructions that are more detailed than the
validator can verify.

### Test and evidence baseline

On 2026-09-04, the bundled interpreter at
`.installer-venv\\Scripts\\python.exe` ran
`-m unittest discover -s tests -v`: **72 tests discovered, 72 passed, 0
failed**. `scripts/generate_custom_instructions.py --check` also passed.

Phase 0 repaired the stale `CUSTOM-INSTRUCTIONS.md` artifact. The canonical
direction is explicit: `runtime/custom-instructions.txt` is the Chinese
installer/default source, `runtime/custom-instructions.en.txt` is the
language-equivalent English source, and the generator produces the matching
manual artifacts. The installer reads only the Chinese source.

The repository contains 40 declared regression fixtures: 25 routing cases, 7
positive handoff-emission cases, and 8 negative handoff-emission cases. They
prove deterministic compatibility behavior only; they do not prove boundary
quality, routing outcome quality, readiness safety, semantic acceptance, or
completion correctness.

The README's test-count claim is scoped to the reproducible bundled-suite
command above. Current implementation claims now include the implemented
versioned semantic execution contract; readiness, boundary, and completion
capabilities remain on the later roadmap phases.

## 3. Target architecture

```text
Chat / conversation evidence
          |
          v
HG Core: Boundary -> Freeze -> Contract -> Readiness -> Execute -> Accept
          |                                  |                 |
          |                                  +-> policy result  +-> normalized result
          v
Providers / adapters (replaceable)
  ContextProvider | TransportAdapter | Session/Git evidence | Result normalizer
          |
          v
External implementations
  Codex SDK/App Server | Repomix | optional MCP/CLI bridges
  optional Oracle/chatgpt-use browser fallback (non-default, opt-in)
```

### HG Core

- **Boundary Detector**: determines whether the source conversation is a
  reliably ordinary Chat surface and whether a concrete execution boundary has
  been reached. It must distinguish explicit approval, settled decisions,
  unresolved architecture, premature handoff, and missed handoff.
- **Decision Freeze**: records locked decisions, mutable implementation
  choices, unresolved questions, and contradictions. A consumer must not
  silently reopen locked decisions.
- **Execution Contract**: creates and validates the versioned semantic payload
  described in Section 4.
- **Readiness / Risk Policy**: evaluates execution surface, approval,
  reversibility, blast radius, data integrity, cross-system contracts,
  historical failures, and user overrides. It explains `PASS`, `BLOCK`,
  `UNVERIFIED`, or an equivalent future policy result.
- **Acceptance / Escalation**: evaluates evidence against the contract and
  decides complete, partial, retry, replan, user-review, or blocked outcomes.
- **Evaluation Harness**: runs regression fixtures, adversarial cases, real
  anonymized corpus cases, and outcome benchmarks with explicit metrics.

### Providers and adapters

- **ContextProvider**: supplies bounded repository, file, conversation, or
  session context and a manifest describing provenance and omissions.
- **TransportAdapter**: maps a validated HG contract to an executor and returns
  raw execution references plus normalized result input.
- **Session / Git evidence provider**: supplies branch, HEAD, dirty-tree,
  checkpoint, test, artifact, and other observable evidence without making
  those facts up.
- **Result normalizer**: converts executor-specific output into transport-
  independent result semantics for acceptance.

The Core must not depend on one specific executor, browser transport,
repository packer, model provider, or installer. Adapters may depend on the
Core contract; the Core may only depend on stable provider interfaces.

## 4. Versioned execution contract

The following is the formal design target, not a schema implementation in this
phase. A future contract must preserve the distinction between HG-owned
semantics and executor-owned mechanics.

| Field | MVP | Ownership / intent |
|---|---|---|
| `contract_version` | Required | HG-owned version and migration discriminator |
| `handoff_id` | Required | HG-owned idempotency / trace identity |
| `source_context` | Required | HG-owned provenance summary; no invented facts |
| `objective` | Required | HG-owned executable objective |
| `current_state` | Required | HG-owned factual baseline |
| `checkpoint` | Required | HG-owned evidence reference or explicit `none` |
| `locked_decisions` | Required | HG-owned; immutable unless superseded explicitly |
| `mutable_implementation_choices` | Required | HG-owned allowed choice surface |
| `constraints` | Required | HG-owned scope and operating constraints |
| `do_not` | Required | HG-owned safety boundaries and non-goals |
| `context_manifest` | Required | HG-owned provenance, selection, budget, and omissions |
| `execution_surface` | Required | HG-owned readiness input; adapter maps it |
| `model` | Required for recommendation | HG strategy field; selection remains manual unless executor owns it |
| `reasoning_effort` | Required for recommendation | HG strategy field; not a quality claim |
| `sandbox` | Required for MVP readiness | HG semantic requirement; executor maps capability |
| `approval_requirements` | Required | HG-owned explicit approval / escalation rules |
| `preflight` | Required | HG-owned readiness result and evidence |
| `acceptance_criteria` | Required | HG-owned executable / observable completion conditions |
| `result_schema` | Required | HG-owned normalized result shape |
| `retry_policy` | Deferred initially, design reserved | HG policy; durable runtime may implement mechanics |

MVP requires all fields marked Required, with semantic validation rather than
label presence. `retry_policy` may be deferred until partial-result semantics
are stable, but its versioning slot must remain reserved. Transport/runtime-
owned fields include executor job ids, process handles, leases, cursors, raw
logs, and provider-specific request options. They may be referenced through
`source_context`, `preflight`, or normalized results but must not define HG Core
semantics.

Contract design rules:

1. A missing fact is `unknown` / `UNVERIFIED`, not an invented value.
2. Locked decisions and `do_not` constraints are checked for contradiction.
3. Acceptance criteria must identify observable evidence, not merely a prose
   aspiration such as “works.”
4. Contract versions migrate explicitly; consumers reject unsupported versions
   with an actionable result.
5. Markdown remains a presentation / compatibility format. The semantic source
   of truth is the versioned contract object.

## 5. Phased implementation plan

### Phase 0 — Evidence repair & product cleanup

**Objective** — restore a truthful, internally aligned baseline before adding
vNext semantics.

**Inputs / dependencies** — current runtime templates, generated artifacts,
README claims, `references/` documents, current tests / fixtures, installer
behavior, and this roadmap.

**Deliverables**

- one declared canonical Custom Instructions source and synchronized generated
  artifacts, or an explicit compatibility rule if two language artifacts remain;
- aligned handoff / routing terminology across runtime, references, and tests;
- README and docs claims scoped to observed evidence;
- a short baseline report recording discovered, passed, failed, skipped, and
  environment-dependent tests;
- architecture boundary language that names the installer, Skill, selector,
  and browser experiments as adapters / legacy surfaces where appropriate.

**Tests / evaluation** — regenerate/check artifacts; run the complete bundled
  suite; run the selector and validator directly; verify that fixture counts are
  not presented as outcome effectiveness.

**Exit criteria**

- canonical runtime and generated artifacts agree byte-for-byte where parity is
  promised;
- every documented test-count claim has a reproducible command and status;
- no README or runtime text claims automatic model switching, crash-safe
  runtime, or semantic acceptance that the code cannot prove;
- deviations and remaining legacy limitations are recorded here or in an ADR.

**Explicit non-goals** — no Codex adapter, schema implementation, installer
  deletion, browser automation, third-party installation, or broad refactor.

**Stable after this phase** — truthful baseline, current compatibility boundary,
  and the vocabulary used by later phases.

### Phase 1 — Contract foundation

**Objective** — establish the versioned semantic contract without coupling it to
  automatic transport.

**Inputs / dependencies** — Phase 0 baseline; current handoff spec as a
  compatibility input; contract field table in Section 4.

**Deliverables**

- versioned JSON schema or equivalent typed representation;
- semantic validator with field ownership, requiredness, unknown-state, and
  contradiction checks;
- explicit locked-versus-mutable decision representation;
- executable acceptance-criteria primitives;
- migration / version compatibility rules and fixtures;
- Markdown import / export only as a compatibility layer.

**Tests / evaluation** — valid / invalid contract cases, missing evidence,
  contradiction cases, locked-decision mutation, unsupported versions,
  acceptance-criteria parsing, and round-trip serialization.

**Exit criteria** — a contract can be created, validated, migrated, rejected,
  and round-tripped without selecting or starting an executor; semantic errors
  are actionable and covered by tests.

**Explicit non-goals** — no automatic transport, browser control, provider
  gateway, repository packer, or durable journal.

**Stable after this phase** — contract fields, validation semantics, migration
  policy, and compatibility behavior.

### Phase 2 — Native Codex path

**Objective** — make Codex SDK / App Server the first native execution adapter.

**Inputs / dependencies** — validated Phase 1 contract; Codex SDK / App Server
  interface; adapter capability map.

**Deliverables**

- `TransportAdapter` for Codex SDK / App Server;
- contract-to-executor mapping for model, reasoning, sandbox, approval, and
  objective fields;
- start, resume, and result retrieval operations;
- normalized result including executor reference, observable evidence, and
  unknowns;
- adapter-specific error mapping that preserves HG semantics.

**Tests / evaluation** — contract mapping tests, mocked / local adapter
  integration tests, start / resume / retrieval tests, approval mismatch tests,
  normalized-result fixtures, and one real supported executor path where
  credentials and host policy permit.

**Exit criteria** — a validated contract reaches Codex through the supported
  adapter, the result can be retrieved and normalized, and acceptance can
  consume it without inspecting Codex-specific internals.

**Explicit non-goals** — no hand-written ChatGPT browser automation, no
  provider gateway, and no claim that starting an agent means the task is
  complete.

**Stable after this phase** — Codex adapter boundary, parameter mapping,
  normalized start / resume / result semantics.

### Phase 3 — External context reuse

**Objective** — provide bounded, provenance-aware context through replaceable
  providers.

**Inputs / dependencies** — Phase 1 contract and Phase 2 adapter interfaces;
  Repomix or another approved external context implementation; Git / session
  evidence access.

**Deliverables**

- Repomix-backed `ContextProvider`;
- Git / session evidence provider;
- selective context manifest with token / size budget, provenance, and
  omissions;
- secret-scan warning boundary and user-visible handling;
- provider capability and failure normalization.

**Tests / evaluation** — deterministic manifest tests, token-budget behavior,
  omitted-file transparency, secret warning cases, dirty-tree / checkpoint
  evidence, provider failure cases, and adapter-independent contract tests.

**Exit criteria** — context can be replaced or omitted without changing Core
  semantics; every included item has provenance; budgets and omissions are
  visible; secrets are warned about or excluded according to an explicit rule.

**Explicit non-goals** — no proprietary repo packer and no provider-specific
  context requirement in the Core.

**Stable after this phase** — `ContextProvider` interface, context manifest
  semantics, evidence provenance, and budget behavior.

### Phase 4 — Readiness / risk policy

**Objective** — evolve current generic model routing into an execution-boundary
  risk and approval policy.

**Inputs / dependencies** — Phase 1 contract, Phase 2 executor capabilities,
  Phase 3 evidence metadata, and benchmark definitions from Section 7.

**Deliverables**

- normalized risk inputs: irreversibility, destructiveness, blast radius, data
  integrity, cross-system contract, historical failure, and user override;
- explainable readiness result with `PASS`, `BLOCK`, `UNVERIFIED`, and audit-only
  semantics as needed;
- model / reasoning recommendation as a strategy field, not a gateway;
- approval requirements and visible reason codes;
- benchmark-backed thresholds and calibration record.

**Tests / evaluation** — false-BLOCK rate, unsafe-allow cases, wrong-surface
  routing, premium-model overuse, user override, unknown metadata, declared
  quota conflict, and one-tier versus material tier mismatch cases.

**Exit criteria** — policy decisions are reproducible and explained; benchmark
  results meet agreed thresholds; unknown information does not silently become
  a safe fact; model recommendation does not imply automatic switching.

**Explicit non-goals** — no online price claims, no provider gateway, and no
  assumption that the current selector heuristics are effective without outcome
  evidence.

**Stable after this phase** — readiness input vocabulary, reason codes,
  approval semantics, and benchmark reporting.

### Phase 5 — Boundary detector + decision freeze

**Objective** — build HG's strongest moat candidate on real boundary and
  decision-drift evidence, starting with evaluation rather than a complex model.

**Inputs / dependencies** — Phase 1 contract, Phase 4 risk vocabulary, and a
  reviewed conversation corpus policy.

**Deliverables**

- labeled corpus protocol for anonymized conversations;
- detector evaluation harness and human-label guidance;
- decision-freeze representation with explicit / implicit approval;
- contradiction and decision-drift reports;
- baseline detector using current prompt / rule behavior for comparison.

**Tests / evaluation** — premature handoff, missed handoff, unresolved
  architecture, explicit versus implicit approval, decision drift, surface
  uncertainty, and inter-rater agreement on the real corpus. Synthetic cases
  supplement but do not replace real anonymized examples.

**Exit criteria** — benchmark labels and metrics are reproducible; baseline
  precision / recall and error categories are known; detector changes are
  compared against the baseline; no “moat” or effectiveness claim is made
  before outcome evidence supports it.

**Explicit non-goals** — no automatic browser execution and no assumption that
  prompt-only detection is sufficient.

**Stable after this phase** — corpus format, detector metrics, freeze semantics,
  and decision-drift reporting.

### Phase 6 — Acceptance / completion gate

**Objective** — decide completion by contract fulfillment rather than process
  termination.

**Inputs / dependencies** — normalized results from Phase 2, evidence providers
  from Phase 3, readiness semantics from Phase 4, and contract / freeze state.

**Deliverables**

- artifact, test, checkpoint, dirty-tree, and contract-drift evidence model;
- semantic completion evaluator;
- partial-completion result and escalation states;
- explicit retry versus replan versus blocked policy;
- false-completion and evidence insufficiency reporting.

**Tests / evaluation** — artifact evidence, test evidence, dirty tree,
  checkpoint mismatch, partial failure, contract drift, false positive
  completion, missing evidence, retry, replan, and user-review cases.

**Exit criteria** — “process ended” cannot alone produce `complete`; completion
  requires the declared acceptance criteria and observable evidence; partial and
  drifted outcomes are preserved and actionable.

**Explicit non-goals** — no crash recovery journal or lease implementation yet.

**Stable after this phase** — normalized result states, acceptance evidence
  semantics, and completion / partial / blocked decisions.

### Phase 7 — Durable runtime / advanced adapters

**Objective** — add durability and optional integrations only after the Core
  semantics have demonstrated value.

**Inputs / dependencies** — stable contract, adapter, evidence, readiness,
  boundary, and acceptance semantics from Phases 1–6.

**Deliverables**

- append-only journal;
- idempotency keys and duplicate-submission protection;
- lease / cursor and crash recovery semantics;
- optional Workspace Agents or CLI bridges;
- optional Oracle / chatgpt-use browser fallback, opt-in and non-default;
- durability and adapter failure playbooks.

**Tests / evaluation** — crash injection, duplicate submission, replay,
  concurrent lease, cursor loss, recovery, adapter timeout, browser fallback
  opt-in, and journal integrity tests.

**Exit criteria** — recovery behavior is deterministic and evidence-preserving;
  duplicate execution is prevented or explicitly surfaced; optional adapters
  cannot become a hidden Core dependency; browser fallback remains opt-in.

**Explicit non-goals** — no default browser automation, no replacement for
  Codex transport, and no expansion into a general agent platform.

**Stable after this phase** — durable execution references, recovery contract,
  optional adapter boundaries, and operational failure semantics.

## 6. Phase gates and handoff protocol

Every future phase or clearly scoped sub-phase must record the same gate:

1. **Objective** — one outcome, not a broad rewrite.
2. **Inputs / dependencies** — exact prior contract, evidence, and adapters.
3. **Deliverables** — files, interfaces, reports, or fixtures expected.
4. **Tests / evaluation** — relevant regression and outcome checks.
5. **Exit criteria** — observable stop conditions.
6. **Explicit non-goals** — work that must wait.
7. **What becomes stable** — the interfaces and decisions later phases may use.

The phase status update must include `status`, `evidence`, `deviations`, and
`next recommended step`. If an architecture decision changes, update this
roadmap or an ADR before changing implementation. A handoff should reference
the active phase and its gate instead of copying the full roadmap.

## 7. Evaluation strategy

Evaluation is a first-class workstream. Rule fixtures are useful regression
checks, but their count must never be presented as product effectiveness.

| Evaluation line | Required evidence |
|---|---|
| Boundary detector benchmark | Labeled real anonymized corpus, synthetic adversarial supplement, precision / recall, premature and missed handoff rates |
| Decision-drift benchmark | Locked-decision mutation, contradiction detection, unresolved architecture, explicit / implicit approval accuracy |
| Semantic contract validation | Valid / invalid contracts, version migration, unknown state, contradiction, acceptance-criteria semantics |
| Readiness false-BLOCK rate | Reversible safe work, unknown metadata, user override, and audit-only cases |
| Wrong-surface routing | Chat / Work / Codex / uncertain-surface corpus with recursion checks |
| Premium-model overuse | Strong-tier recommendation rate on settled large work versus independent-risk cases |
| Acceptance false positive | Process termination without artifact, test, checkpoint, or contract evidence |
| Partial-failure recovery | Partial result preservation, retry / replan / blocked classification, evidence continuity |
| Prior-art comparison | Boundary, contract, and acceptance outcomes compared with reused adapters / baseline tools; no claim beyond measured scope |

Maintain four separate data classes:

- **Regression fixtures** — deterministic compatibility cases.
- **Synthetic adversarial cases** — deliberately difficult constructed inputs.
- **Real anonymized conversation corpus** — human-labeled boundary and decision
  evidence with privacy controls.
- **Outcome benchmark** — execution and acceptance results tied to observable
  artifacts and evidence.

Each benchmark report must state dataset version, exclusions, metric definition,
confidence / uncertainty, and known blind spots. Claims such as “reliable,”
“safe,” or “moat” remain `UNPROVEN` until the relevant benchmark supports them.

## 8. Reuse registry

This registry prevents re-implementing capabilities already marked for reuse.
License and maintenance status are integration gates, not assumptions; verify
them against the selected upstream version before adoption.

| Dependency / project | Reuse type | Intended boundary | License | Reason | Maintenance risk | Status |
|---|---|---|---|---|---|---|
| Codex SDK / App Server | DIRECT | `TransportAdapter` for native Codex execution | Verify upstream package / terms before integration | First-party transport path | API / host evolution | PLANNED |
| Repomix | DIRECT | `ContextProvider` repository packing | MIT expected; verify selected version | Mature repository context reuse | Format / token behavior changes | PLANNED |
| Oracle | WATCH / optional DIRECT | Non-default browser fallback adapter | Verify upstream | Existing browser-agent prior art | Surface breakage and policy risk | DEFERRED |
| chatgpt-use | WATCH / optional DIRECT | Non-default browser fallback adapter | Verify upstream | Existing browser-control prior art | Login / UI / policy fragility | DEFERRED |
| TStansel/handoff | DESIGN | Handoff transport / workflow prior art | Verify upstream | Learn from existing handoff implementation | Different assumptions from HG semantics | REVIEWED FOR DESIGN |
| OpenMOSS | DESIGN | Agent / handoff architecture prior art | Verify upstream | Avoid duplicating broad agent workflow ideas | Scope and compatibility uncertainty | REVIEWED FOR DESIGN |
| Second Opinion | WATCH | Review / verification workflow prior art | Verify upstream | Potential acceptance / review patterns | Product boundary overlap | WATCH |
| Superpowers | DESIGN | Development workflow / instruction patterns | Verify upstream | Reuse proven workflow ideas selectively | Prompt-oriented semantics may not be executable | REVIEWED FOR DESIGN |
| ModelRouter | DO NOT TAKE | Provider / model gateway | N/A for HG adoption | HG must not become a general gateway | Gateway scope and coupling | REJECTED |

`DIRECT` means integrate behind a stable HG interface; `DESIGN` means learn
without taking a runtime dependency; `WATCH` means no dependency until evidence
and license review justify it; `DO NOT TAKE` is an explicit boundary.

## 9. Deprecation and migration list

Do not delete these components in the roadmap phase. Migrate them deliberately
and preserve compatibility until a later phase proves removal is safe.

| Existing component | vNext treatment | Migration intent |
|---|---|---|
| `runtime/custom-instructions.txt` and generated Custom Instructions | KEEP, then REFACTOR | Keep as the current runtime adapter; align source and generated artifacts in Phase 0, then reduce semantic duplication as Core matures |
| `runtime/custom-instructions.en.txt` and English artifact | KEEP, then REFACTOR | Keep language-equivalent compatibility; generated output must be explicit and tested |
| Skill adapter / `skills/handoff-guard/` | COMPATIBILITY-ONLY | Keep for hosts that load it; do not make it the guaranteed runtime or Core source |
| `scripts/select_model.py` | REFACTOR | Preserve deterministic compatibility API; migrate its policy role into readiness / approval policy and benchmark it |
| `scripts/validate_handoff.py` | REFACTOR, then COMPATIBILITY-ONLY | Keep Markdown / JSON compatibility validation; delegate semantic validation to the versioned contract foundation |
| Windows Guided Installer | KEEP as adapter | Keep local Generate / Copy / Update / Removal / Repair flow; do not expand it into account control or primary product scope |
| Browser / UIA experiments | DEPRECATED | Retain evidence and documentation only; no production ChatGPT DOM / UIA automation |
| Current eval fixtures | KEEP as regression fixtures | Preserve for rule compatibility, label them as regression only, and add outcome benchmarks separately |
| Current Markdown handoff format | COMPATIBILITY-ONLY, then MIGRATE | Continue import / export for users; make the versioned contract the semantic source of truth |
| Provider profile catalog | KEEP, then REFACTOR | Keep configurable catalog data; remove assumptions that HG owns provider switching |
| Installer build / release artifacts | KEEP | Treat distribution as a supporting adapter and verify it only by its local acceptance surface |

## 10. Development operating rules

1. Advance one phase or one clearly scoped sub-phase at a time.
2. Read this roadmap's current status before starting a phase.
3. At phase end, write back `status`, `evidence`, `deviations`, and `next
   recommended step`.
4. When architecture changes, update this roadmap / an ADR before changing
   implementation.
5. Do not skip Core contract or evaluation work because an adapter is easy to
   implement.
6. “The agent started” is not Handoff Guard success.
7. “Tests pass” is not automatically semantic effectiveness.
8. Prefer reuse when prior art has already solved the adjacent problem.
9. Preserve user changes and do not reset or clean a dirty tree during phase
   work; establish a checkpoint only when its contents are attributable.
10. Label claims as `UNPROVEN` when the required runtime or benchmark evidence
    is absent.
11. Keep browser fallback non-default and opt-in if it is ever implemented.
12. Do not add a provider/model gateway or automatic model switching under the
    name of routing.

## 11. First executable task after this roadmap

The Phase 1 implementation is complete and the next action is **Phase 2 review**.
The implementation provides the versioned semantic execution contract, typed
wrapper, JSON Schema, semantic validator, migration from the explicitly supported
0.1 shape, locked/mutable mutation checks, observable acceptance primitives, and
Markdown compatibility import/export. The bundled suite reports 94 discovered,
94 passed, and 0 failed tests.

Phase 2 remains intentionally unstarted. It requires a new review before any
Codex SDK / App Server transport, executor startup, Repomix integration,
readiness policy, boundary detector, acceptance completion gate, or durable
runtime work begins.
