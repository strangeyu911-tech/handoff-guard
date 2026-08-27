#!/usr/bin/env python3
"""Validate the required sections of a Handoff Guard Markdown or JSON handoff."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED = {
    "recommended_model": ("recommended model", "model recommendation"),
    "reasoning_effort": ("reasoning effort",),
    "preflight": ("preflight",),
    "current_state": ("current state",),
    "completed": ("completed",),
    "checkpoint": ("checkpoint", "commit"),
    "next_objective": ("next objective", "next goal"),
    "locked_decisions_boundaries": ("locked decisions", "boundaries", "locked decisions / boundaries"),
    "do_not_guardrails": ("do-not", "do not", "guardrails"),
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def has_content(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return bool(value) and any(has_content(item) for item in value.values())
    if isinstance(value, list):
        return bool(value) and any(has_content(item) for item in value)
    return value is not None


def json_fields(data: Any) -> set[str]:
    values: set[str] = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if has_content(value):
                values.add(normalize(str(key)))
            values.update(json_fields(value))
    elif isinstance(data, list):
        for value in data:
            values.update(json_fields(value))
    return values


def markdown_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            if current:
                sections[current] = "\n".join(buffer).strip()
            current = normalize(heading.group(1))
            buffer = []
        elif current:
            buffer.append(line)
    if current:
        sections[current] = "\n".join(buffer).strip()
    for match in re.finditer(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?([^:\n]+?)(?:\*\*)?\s*:\s*(.+?)\s*$", text):
        sections.setdefault(normalize(match.group(1)), match.group(2).strip())
    return sections


def validate(text: str) -> dict[str, Any]:
    found: set[str] = set()
    parsed_json = None
    try:
        parsed_json = json.loads(text)
    except json.JSONDecodeError:
        pass
    if parsed_json is not None:
        found = json_fields(parsed_json)
        searchable = " ".join(found)
    else:
        sections = markdown_sections(text)
        found = {name for name, content in sections.items() if content.strip()}
        searchable = " ".join(found)
        found.update(normalize(line.split(":", 1)[0]) for line in text.splitlines() if ":" in line and line.split(":", 1)[1].strip())
    errors = []
    present = {}
    for field, aliases in REQUIRED.items():
        match = next((alias for alias in aliases if normalize(alias) in found or normalize(alias) in searchable), None)
        present[field] = match is not None
        if match is None:
            errors.append(f"Missing required field: {field}")
    return {"valid": not errors, "errors": errors, "fields": present}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", nargs="?", help="Markdown/JSON file; defaults to stdin")
    args = parser.parse_args()
    try:
        text = Path(args.handoff).read_text(encoding="utf-8") if args.handoff else sys.stdin.read()
        result = validate(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["valid"] else 1
    except OSError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
