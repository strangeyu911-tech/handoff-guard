"""Markdown compatibility import/export for the canonical execution contract."""

from __future__ import annotations

import json
import re
from typing import Any

from .contract import ExecutionContract


_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def _sections(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            if current is not None:
                result[current] = "\n".join(buffer).strip()
            current = re.sub(r"[^a-z0-9]+", " ", heading.group(1).lower()).strip()
            buffer = []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        result[current] = "\n".join(buffer).strip()
    for match in re.finditer(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?([^:\n]+?)(?:\*\*)?\s*:\s*(.+?)\s*$", text):
        key = re.sub(r"[^a-z0-9]+", " ", match.group(1).lower()).strip()
        result.setdefault(key, match.group(2).strip())
    return result


def _value(sections: dict[str, str], *names: str) -> str:
    for name in names:
        key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
        if sections.get(key, "").strip():
            return sections[key].strip()
    return ""


def _lines(value: str) -> list[str]:
    return [line.lstrip(" -*\t").strip() for line in value.splitlines() if line.lstrip(" -*\t").strip()]


def import_markdown(text: str) -> ExecutionContract:
    """Import canonical embedded JSON or map the legacy Markdown handoff fields."""

    match = _JSON_BLOCK.search(text)
    if match:
        return ExecutionContract.from_dict(json.loads(match.group(1)))
    sections = _sections(text)
    recommended_model = _value(sections, "recommended model", "model recommendation")
    reasoning = _value(sections, "reasoning effort") or "unknown"
    preflight = _value(sections, "preflight")
    preflight_status = preflight.split()[0].upper() if preflight else "UNVERIFIED"
    if preflight_status not in {"PASS", "BLOCK", "UNVERIFIED"}:
        preflight_status = "UNVERIFIED"
    current_state = _value(sections, "current state")
    completed = _lines(_value(sections, "completed"))
    checkpoint = _value(sections, "checkpoint", "commit")
    locked = _lines(_value(sections, "locked decisions boundaries", "locked decisions"))
    guardrails = _lines(_value(sections, "do not guardrails"))
    objective = _value(sections, "next objective", "next goal")
    payload: dict[str, Any] = {
        "contract_version": "1.0", "handoff_id": "markdown-import",
        "source_context": {"status": "unknown", "surface": "unknown", "summary": "Source context was not represented in legacy Markdown.", "provenance": "markdown-compatibility-import"},
        "objective": {"statement": objective or "Objective was not supplied in Markdown.", "requires": []},
        "current_state": {"status": "known" if current_state else "unknown", "summary": current_state or "Current state was not supplied in Markdown.", "completed": completed},
        "checkpoint": {"status": "none" if checkpoint.lower() == "none" or not checkpoint else "present", "reference": None if checkpoint.lower() == "none" or not checkpoint else checkpoint},
        "locked_decisions": [{"id": f"markdown-locked-{index}", "decision": value, "subject": "unknown", "effect": "allow"} for index, value in enumerate(locked)],
        "mutable_implementation_choices": [], "constraints": [],
        "do_not": [{"id": f"markdown-guardrail-{index}", "rule": value, "subject": "unknown", "action": "prohibit"} for index, value in enumerate(guardrails)],
        "context_manifest": {"items": [], "omissions": [{"status": "unknown", "reason": "Legacy Markdown did not include a context manifest."}], "budget": {"status": "unknown"}},
        "execution_surface": "unknown",
        "model": {"status": "known" if recommended_model else "unknown", "name": recommended_model or "unknown", "tier": "unknown"},
        "reasoning_effort": reasoning if reasoning in {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"} else "unknown",
        "sandbox": {"status": "unknown", "mode": "unknown", "network": "unknown"},
        "approval_requirements": {"status": "unknown", "mode": "unknown", "required": "unknown"},
        "preflight": {"status": preflight_status, "evidence": [preflight or "Preflight was not supplied in Markdown."]},
        "acceptance_criteria": [{"id": "markdown-acceptance", "description": "Acceptance evidence was unavailable in the compatibility source.", "required": True, "evidence": [{"type": "unknown", "status": "unknown", "observable": "No acceptance evidence was supplied."}]}],
        "result_schema": {"version": "1.0", "states": ["complete", "partial", "blocked", "unknown"], "evidence_fields": ["observable", "unknowns"]},
        "retry_policy": None,
    }
    return ExecutionContract.from_dict(payload)


def export_markdown(contract: ExecutionContract | dict[str, Any]) -> str:
    """Render a human-readable compatibility document with canonical JSON embedded."""

    if not isinstance(contract, ExecutionContract):
        contract = ExecutionContract.from_dict(contract)
    data = contract.to_dict()
    model = data["model"]
    current = data["current_state"]
    checkpoint = data["checkpoint"]
    locked = "\n".join(f"- {item['decision']}" for item in data["locked_decisions"]) or "- none declared"
    guards = "\n".join(f"- {item['rule']}" for item in data["do_not"]) or "- none declared"
    completed = "\n".join(f"- {item}" for item in current["completed"]) or "- none declared"
    checkpoint_value = checkpoint["reference"] if checkpoint["status"] == "present" else checkpoint["status"]
    json_payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    return f"""# Handoff

Recommended model: {model['name']}
Reasoning effort: {data['reasoning_effort']}

## Preflight

{data['preflight']['status']}: {'; '.join(data['preflight']['evidence'])}

## Current state

{current['summary']}

## Completed

{completed}

## Checkpoint

{checkpoint_value}

## Next objective

{data['objective']['statement']}

## Locked decisions / boundaries

{locked}

## Do-not / guardrails

{guards}

## Canonical execution contract (JSON)

```json
{json_payload}
```
"""
