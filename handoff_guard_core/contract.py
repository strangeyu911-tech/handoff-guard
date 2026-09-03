"""Versioned, executor-independent semantic execution contract."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping


CURRENT_CONTRACT_VERSION = "1.0"
MIGRATABLE_CONTRACT_VERSIONS = {"0.1"}
UNKNOWN_VALUES = {"unknown", "UNVERIFIED"}
REQUIRED_FIELDS = (
    "contract_version", "handoff_id", "source_context", "objective",
    "current_state", "checkpoint", "locked_decisions",
    "mutable_implementation_choices", "constraints", "do_not",
    "context_manifest", "execution_surface", "model", "reasoning_effort",
    "sandbox", "approval_requirements", "preflight", "acceptance_criteria",
    "result_schema",
)


@dataclass(frozen=True)
class ValidationResult:
    """Actionable semantic validation result."""

    errors: tuple[dict[str, str], ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": [dict(error) for error in self.errors]}


@dataclass(frozen=True)
class ExecutionContract:
    """Typed wrapper around the canonical JSON-compatible contract payload."""

    data: Mapping[str, Any]

    def __post_init__(self) -> None:
        result = validate_contract(self.data)
        if not result.valid:
            raise ValueError("invalid execution contract: " + "; ".join(error["message"] for error in result.errors))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionContract":
        return cls(deepcopy(dict(data)))

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.data))


def _issue(errors: list[dict[str, str]], code: str, path: str, message: str, action: str) -> None:
    errors.append({"code": code, "path": path, "message": message, "action": action})


def _dict(value: Any, path: str, errors: list[dict[str, str]]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        _issue(errors, "wrong_type", path, f"{path} must be an object", "Provide an object with the documented fields.")
        return None
    return value


def _list(value: Any, path: str, errors: list[dict[str, str]]) -> list[Any] | None:
    if not isinstance(value, list):
        _issue(errors, "wrong_type", path, f"{path} must be an array", "Provide an array, even when it is empty.")
        return None
    return value


def _nonempty_string(value: Any, path: str, errors: list[dict[str, str]]) -> bool:
    if not isinstance(value, str) or not value.strip():
        _issue(errors, "missing_value", path, f"{path} must be a non-empty string", "Supply a concrete value or an explicit unknown state.")
        return False
    return True


def _enum(value: Any, allowed: set[str], path: str, errors: list[dict[str, str]]) -> bool:
    if value not in allowed:
        _issue(errors, "invalid_value", path, f"{path} must be one of: {', '.join(sorted(allowed))}", "Use a supported value or an explicit unknown state.")
        return False
    return True


def _status(obj: dict[str, Any], path: str, errors: list[dict[str, str]], allowed: set[str] | None = None) -> str | None:
    value = obj.get("status")
    if not isinstance(value, str):
        _issue(errors, "implicit_unknown", f"{path}.status", f"{path} must declare status explicitly", "Use known, unknown, or UNVERIFIED; do not infer a missing fact.")
        return None
    _enum(value, allowed or {"known", *UNKNOWN_VALUES}, f"{path}.status", errors)
    return value


def _validate_source_context(value: Any, errors: list[dict[str, str]]) -> None:
    obj = _dict(value, "source_context", errors)
    if obj is None:
        return
    _status(obj, "source_context", errors)
    _enum(obj.get("surface"), {"chat", "work", "codex", "unknown"}, "source_context.surface", errors)
    _nonempty_string(obj.get("summary"), "source_context.summary", errors)
    _nonempty_string(obj.get("provenance"), "source_context.provenance", errors)


def _validate_objective(value: Any, errors: list[dict[str, str]]) -> None:
    obj = _dict(value, "objective", errors)
    if obj is None:
        return
    _nonempty_string(obj.get("statement"), "objective.statement", errors)
    requirements = _list(obj.get("requires"), "objective.requires", errors)
    if requirements is not None:
        for index, item in enumerate(requirements):
            _nonempty_string(item, f"objective.requires[{index}]", errors)


def _validate_current_state(value: Any, errors: list[dict[str, str]]) -> None:
    obj = _dict(value, "current_state", errors)
    if obj is None:
        return
    _status(obj, "current_state", errors)
    _nonempty_string(obj.get("summary"), "current_state.summary", errors)
    completed = _list(obj.get("completed"), "current_state.completed", errors)
    if completed is not None:
        for index, item in enumerate(completed):
            _nonempty_string(item, f"current_state.completed[{index}]", errors)


def _validate_checkpoint(value: Any, errors: list[dict[str, str]]) -> None:
    obj = _dict(value, "checkpoint", errors)
    if obj is None:
        return
    status = obj.get("status")
    _enum(status, {"present", "none", *UNKNOWN_VALUES}, "checkpoint.status", errors)
    reference = obj.get("reference")
    if status == "present":
        _nonempty_string(reference, "checkpoint.reference", errors)
    elif status == "none" and reference not in (None, ""):
        _issue(errors, "incompatible_fields", "checkpoint.reference", "A checkpoint with status none cannot carry a reference", "Remove the reference or mark the checkpoint present.")
    elif status in UNKNOWN_VALUES and reference not in (None, ""):
        _issue(errors, "incompatible_fields", "checkpoint.reference", "An unknown checkpoint cannot carry an asserted reference", "Use status present when the reference is verified.")


def _validate_decisions(value: Any, path: str, errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    entries = _list(value, path, errors) or []
    seen: set[str] = set()
    for index, item in enumerate(entries):
        item_path = f"{path}[{index}]"
        obj = _dict(item, item_path, errors)
        if obj is None:
            continue
        identifier = obj.get("id")
        _nonempty_string(identifier, f"{item_path}.id", errors)
        if isinstance(identifier, str) and identifier in seen:
            _issue(errors, "duplicate_id", f"{item_path}.id", f"Duplicate decision id: {identifier}", "Give each decision a stable unique id.")
        if isinstance(identifier, str):
            seen.add(identifier)
        _nonempty_string(obj.get("decision"), f"{item_path}.decision", errors)
        _nonempty_string(obj.get("subject"), f"{item_path}.subject", errors)
        _enum(obj.get("effect"), {"allow", "prohibit"}, f"{item_path}.effect", errors)
    return entries


def _validate_mutable(value: Any, errors: list[dict[str, str]]) -> None:
    entries = _list(value, "mutable_implementation_choices", errors) or []
    seen: set[str] = set()
    for index, item in enumerate(entries):
        path = f"mutable_implementation_choices[{index}]"
        obj = _dict(item, path, errors)
        if obj is None:
            continue
        identifier = obj.get("id")
        _nonempty_string(identifier, f"{path}.id", errors)
        if isinstance(identifier, str) and identifier in seen:
            _issue(errors, "duplicate_id", f"{path}.id", f"Duplicate mutable choice id: {identifier}", "Give each mutable choice a stable unique id.")
        if isinstance(identifier, str):
            seen.add(identifier)
        _nonempty_string(obj.get("choice"), f"{path}.choice", errors)


def _validate_constraints(value: Any, errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    entries = _list(value, "constraints", errors) or []
    for index, item in enumerate(entries):
        path = f"constraints[{index}]"
        obj = _dict(item, path, errors)
        if obj is None:
            continue
        _nonempty_string(obj.get("id"), f"{path}.id", errors)
        _nonempty_string(obj.get("subject"), f"{path}.subject", errors)
        _enum(obj.get("type"), {"must", "must_not"}, f"{path}.type", errors)
    return entries


def _validate_do_not(value: Any, errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    entries = _list(value, "do_not", errors) or []
    for index, item in enumerate(entries):
        path = f"do_not[{index}]"
        obj = _dict(item, path, errors)
        if obj is None:
            continue
        _nonempty_string(obj.get("id"), f"{path}.id", errors)
        _nonempty_string(obj.get("rule"), f"{path}.rule", errors)
        _nonempty_string(obj.get("subject"), f"{path}.subject", errors)
        if obj.get("action") != "prohibit":
            _issue(errors, "invalid_value", f"{path}.action", f"{path}.action must be prohibit", "Represent do_not entries as prohibitions.")
    return entries


def _validate_manifest(value: Any, errors: list[dict[str, str]]) -> None:
    obj = _dict(value, "context_manifest", errors)
    if obj is None:
        return
    items = _list(obj.get("items"), "context_manifest.items", errors) or []
    for index, item in enumerate(items):
        path = f"context_manifest.items[{index}]"
        entry = _dict(item, path, errors)
        if entry is None:
            continue
        _nonempty_string(entry.get("path"), f"{path}.path", errors)
        _nonempty_string(entry.get("provenance"), f"{path}.provenance", errors)
    omissions = _list(obj.get("omissions"), "context_manifest.omissions", errors) or []
    for index, omission in enumerate(omissions):
        path = f"context_manifest.omissions[{index}]"
        entry = _dict(omission, path, errors)
        if entry is None:
            continue
        _nonempty_string(entry.get("reason"), f"{path}.reason", errors)
        _enum(entry.get("status"), {"known", *UNKNOWN_VALUES}, f"{path}.status", errors)
    budget = _dict(obj.get("budget"), "context_manifest.budget", errors)
    if budget is not None:
        status = _status(budget, "context_manifest.budget", errors)
        if status == "known":
            _nonempty_string(budget.get("unit"), "context_manifest.budget.unit", errors)
            if not isinstance(budget.get("limit"), int) or budget["limit"] < 0:
                _issue(errors, "invalid_value", "context_manifest.budget.limit", "A known context budget needs a non-negative integer limit", "Provide a measured budget or mark it unknown.")


def _validate_strategy(data: dict[str, Any], errors: list[dict[str, str]]) -> None:
    _enum(data.get("execution_surface"), {"work", "codex", "unknown"}, "execution_surface", errors)
    model = _dict(data.get("model"), "model", errors)
    if model is not None:
        status = _status(model, "model", errors)
        _nonempty_string(model.get("name"), "model.name", errors)
        _enum(model.get("tier"), {"budget", "general", "strong", "unknown"}, "model.tier", errors)
        if status == "known" and model.get("name") == "unknown":
            _issue(errors, "implicit_unknown", "model.name", "Known model metadata cannot use the unknown placeholder", "Mark model status unknown instead.")
    _enum(data.get("reasoning_effort"), {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra", *UNKNOWN_VALUES}, "reasoning_effort", errors)
    sandbox = _dict(data.get("sandbox"), "sandbox", errors)
    if sandbox is not None:
        _status(sandbox, "sandbox", errors)
        _enum(sandbox.get("mode"), {"workspace-write", "read-only", "unknown"}, "sandbox.mode", errors)
        _enum(sandbox.get("network"), {"allowed", "blocked", "unknown"}, "sandbox.network", errors)
    approval = _dict(data.get("approval_requirements"), "approval_requirements", errors)
    if approval is not None:
        _status(approval, "approval_requirements", errors)
        mode = approval.get("mode")
        _enum(mode, {"explicit", "implicit", "none", "unknown"}, "approval_requirements.mode", errors)
        required = approval.get("required")
        if required not in (True, False, *UNKNOWN_VALUES):
            _issue(errors, "invalid_value", "approval_requirements.required", "approval_requirements.required must be boolean or an explicit unknown state", "Declare whether approval is required.")
        if mode == "none" and required is True:
            _issue(errors, "incompatible_fields", "approval_requirements", "Approval mode none conflicts with required=true", "Use explicit or implicit approval, or set required=false.")
    preflight = _dict(data.get("preflight"), "preflight", errors)
    if preflight is not None:
        _enum(preflight.get("status"), {"PASS", "BLOCK", "UNVERIFIED"}, "preflight.status", errors)
        evidence = _list(preflight.get("evidence"), "preflight.evidence", errors) or []
        for index, item in enumerate(evidence):
            _nonempty_string(item, f"preflight.evidence[{index}]", errors)


def _validate_acceptance(value: Any, errors: list[dict[str, str]]) -> None:
    entries = _list(value, "acceptance_criteria", errors) or []
    if not entries:
        _issue(errors, "missing_value", "acceptance_criteria", "At least one acceptance criterion is required", "Add an observable criterion, including explicit unavailable evidence when necessary.")
    for index, item in enumerate(entries):
        path = f"acceptance_criteria[{index}]"
        obj = _dict(item, path, errors)
        if obj is None:
            continue
        _nonempty_string(obj.get("id"), f"{path}.id", errors)
        description = obj.get("description")
        if not _nonempty_string(description, f"{path}.description", errors):
            continue
        if isinstance(description, str) and description.strip().lower() in {"works", "done", "complete", "it works"}:
            _issue(errors, "non_observable_acceptance", f"{path}.description", f"{path}.description is not observable", "Name the artifact, test, checkpoint, runtime evidence, or explicit unavailable evidence.")
        evidence = _list(obj.get("evidence"), f"{path}.evidence", errors) or []
        if not evidence:
            _issue(errors, "non_observable_acceptance", f"{path}.evidence", f"{path} must declare observable evidence", "Add at least one evidence item with type, status, and observable.")
        for evidence_index, evidence_item in enumerate(evidence):
            evidence_path = f"{path}.evidence[{evidence_index}]"
            evidence_obj = _dict(evidence_item, evidence_path, errors)
            if evidence_obj is None:
                continue
            _enum(evidence_obj.get("type"), {"artifact", "test", "checkpoint", "git", "runtime", "unknown"}, f"{evidence_path}.type", errors)
            _enum(evidence_obj.get("status"), {"known", *UNKNOWN_VALUES}, f"{evidence_path}.status", errors)
            _nonempty_string(evidence_obj.get("observable"), f"{evidence_path}.observable", errors)


def _validate_result_schema(value: Any, errors: list[dict[str, str]]) -> None:
    obj = _dict(value, "result_schema", errors)
    if obj is None:
        return
    _nonempty_string(obj.get("version"), "result_schema.version", errors)
    states = _list(obj.get("states"), "result_schema.states", errors) or []
    if not states:
        _issue(errors, "missing_value", "result_schema.states", "result_schema.states cannot be empty", "Declare normalized result states such as complete, partial, or blocked.")
    for index, state in enumerate(states):
        _nonempty_string(state, f"result_schema.states[{index}]", errors)
    fields = _list(obj.get("evidence_fields"), "result_schema.evidence_fields", errors) or []
    for index, field in enumerate(fields):
        _nonempty_string(field, f"result_schema.evidence_fields[{index}]", errors)


def validate_contract(data: Mapping[str, Any]) -> ValidationResult:
    """Validate contract shape and semantic relationships."""

    errors: list[dict[str, str]] = []
    if not isinstance(data, dict):
        _issue(errors, "wrong_type", "$", "Contract must be an object", "Provide a JSON object.")
        return ValidationResult(tuple(errors))
    version = data.get("contract_version")
    if version != CURRENT_CONTRACT_VERSION:
        code = "unsupported_contract_version" if isinstance(version, str) else "missing_value"
        _issue(errors, code, "contract_version", f"Unsupported contract_version: {version!r}", f"Use supported version {CURRENT_CONTRACT_VERSION} or migrate explicitly.")
    for field in REQUIRED_FIELDS:
        if field not in data:
            _issue(errors, "missing_required_field", field, f"Missing required field: {field}", "Add the field; use an explicit unknown state where the fact is unavailable.")
        elif data[field] is None:
            _issue(errors, "missing_value", field, f"Required field {field} cannot be null", "Provide a value or the field's explicit unknown representation.")
    if not isinstance(data.get("handoff_id"), str) or not data.get("handoff_id", "").strip():
        _issue(errors, "missing_value", "handoff_id", "handoff_id must be a non-empty string", "Use a stable trace identity; do not invent one during validation.")
    _validate_source_context(data.get("source_context"), errors)
    _validate_objective(data.get("objective"), errors)
    _validate_current_state(data.get("current_state"), errors)
    _validate_checkpoint(data.get("checkpoint"), errors)
    locked = _validate_decisions(data.get("locked_decisions"), "locked_decisions", errors)
    _validate_mutable(data.get("mutable_implementation_choices"), errors)
    constraints = _validate_constraints(data.get("constraints"), errors)
    do_not = _validate_do_not(data.get("do_not"), errors)
    _validate_manifest(data.get("context_manifest"), errors)
    _validate_strategy(data, errors)
    _validate_acceptance(data.get("acceptance_criteria"), errors)
    _validate_result_schema(data.get("result_schema"), errors)
    if "retry_policy" in data and data["retry_policy"] is not None and not isinstance(data["retry_policy"], dict):
        _issue(errors, "wrong_type", "retry_policy", "retry_policy must be an object or null", "Keep the reserved slot null until retry mechanics are implemented.")
    objective = data.get("objective") if isinstance(data.get("objective"), dict) else {}
    required_subjects = {item for item in objective.get("requires", []) if isinstance(item, str)}
    prohibited_subjects = {
        item.get("subject") for item in locked + do_not
        if isinstance(item, dict) and item.get("effect", "prohibit") == "prohibit" and item.get("subject") != "unknown"
    }
    for subject in sorted(required_subjects & prohibited_subjects):
        _issue(errors, "contradiction", "objective.requires", f"Objective requires prohibited subject: {subject}", "Remove the requirement or explicitly supersede the locked prohibition.")
    constraint_types: dict[str, set[str]] = {}
    for item in constraints:
        if isinstance(item, dict) and isinstance(item.get("subject"), str):
            constraint_types.setdefault(item["subject"], set()).add(str(item.get("type")))
    for subject, types in constraint_types.items():
        if {"must", "must_not"} <= types:
            _issue(errors, "constraint_contradiction", f"constraints[{subject}]", f"Constraint set both requires and forbids: {subject}", "Keep only one compatible constraint or revise the scope.")
    return ValidationResult(tuple(errors))


def validate_mutation(original: Mapping[str, Any], candidate: Mapping[str, Any]) -> ValidationResult:
    """Ensure a candidate change does not silently mutate locked decisions."""

    errors = list(validate_contract(original).errors) + list(validate_contract(candidate).errors)
    if errors:
        return ValidationResult(tuple(errors))
    original_locked = {item["id"]: item for item in original["locked_decisions"]}
    candidate_locked = {item["id"]: item for item in candidate["locked_decisions"]}
    for identifier, decision in original_locked.items():
        if candidate_locked.get(identifier) != decision:
            _issue(errors, "locked_decision_mutation", f"locked_decisions[{identifier}]", f"Locked decision mutated or removed: {identifier}", "Keep locked decisions byte-stable or create an explicit superseding contract outside this mutation.")
    for identifier in set(candidate_locked) - set(original_locked):
        _issue(errors, "locked_decision_mutation", f"locked_decisions[{identifier}]", f"New locked decision added during mutation: {identifier}", "Declare new locked semantics in a new decision checkpoint.")
    return ValidationResult(tuple(errors))


def _unknown_acceptance() -> list[dict[str, Any]]:
    return [{"id": "acceptance-unavailable", "description": "Acceptance evidence was unavailable in the compatibility source.", "required": True, "evidence": [{"type": "unknown", "status": "unknown", "observable": "No acceptance evidence was supplied."}]}]


def migrate_contract(data: Mapping[str, Any]) -> dict[str, Any]:
    """Migrate the explicitly supported 0.1 handoff shape into contract 1.0."""

    if not isinstance(data, dict):
        raise ValueError("migration source must be an object")
    version = data.get("contract_version")
    if version == CURRENT_CONTRACT_VERSION:
        return deepcopy(data)
    if version not in MIGRATABLE_CONTRACT_VERSIONS:
        raise ValueError(f"No migration is defined for contract_version {version!r}")
    completed = data.get("completed", [])
    if isinstance(completed, str):
        completed = [completed] if completed.strip() else []
    locked_values = data.get("locked_decisions", [])
    if isinstance(locked_values, str):
        locked_values = [locked_values] if locked_values.strip() else []
    guardrails = data.get("guardrails", data.get("do_not", []))
    if isinstance(guardrails, str):
        guardrails = [guardrails] if guardrails.strip() else []
    checkpoint_value = data.get("checkpoint", "none")
    migrated = {
        "contract_version": CURRENT_CONTRACT_VERSION,
        "handoff_id": data.get("handoff_id") or "migrated-0.1",
        "source_context": {"status": "unknown", "surface": "unknown", "summary": "Source context was not represented in contract 0.1.", "provenance": "contract-0.1-migration"},
        "objective": {"statement": data.get("next_objective") or "Objective was not represented in contract 0.1.", "requires": []},
        "current_state": {"status": "known" if data.get("current_state") else "unknown", "summary": data.get("current_state") or "Current state was not represented in contract 0.1.", "completed": completed},
        "checkpoint": {"status": "none" if checkpoint_value in ("none", "") else "present", "reference": None if checkpoint_value in ("none", "") else checkpoint_value},
        "locked_decisions": [{"id": f"legacy-locked-{index}", "decision": value, "subject": "unknown", "effect": "allow"} for index, value in enumerate(locked_values) if isinstance(value, str) and value.strip()],
        "mutable_implementation_choices": [],
        "constraints": [],
        "do_not": [{"id": f"legacy-guardrail-{index}", "rule": value, "subject": "unknown", "action": "prohibit"} for index, value in enumerate(guardrails) if isinstance(value, str) and value.strip()],
        "context_manifest": {"items": [], "omissions": [{"status": "unknown", "reason": "Context manifest was not represented in contract 0.1."}], "budget": {"status": "unknown"}},
        "execution_surface": "unknown",
        "model": {"status": "known" if data.get("recommended_model") else "unknown", "name": data.get("recommended_model") or "unknown", "tier": "unknown"},
        "reasoning_effort": data.get("reasoning_effort") or "unknown",
        "sandbox": {"status": "unknown", "mode": "unknown", "network": "unknown"},
        "approval_requirements": {"status": "unknown", "mode": "unknown", "required": "unknown"},
        "preflight": {"status": data.get("preflight") if data.get("preflight") in {"PASS", "BLOCK", "UNVERIFIED"} else "UNVERIFIED", "evidence": ["Preflight was migrated from contract 0.1 or was unavailable."]},
        "acceptance_criteria": _unknown_acceptance(),
        "result_schema": {"version": "1.0", "states": ["complete", "partial", "blocked", "unknown"], "evidence_fields": ["observable", "unknowns"]},
        "retry_policy": None,
    }
    result = validate_contract(migrated)
    if not result.valid:
        raise ValueError("migration produced an invalid contract: " + "; ".join(error["message"] for error in result.errors))
    return migrated
