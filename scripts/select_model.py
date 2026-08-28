#!/usr/bin/env python3
"""Deterministic model/provider routing and execution preflight for Handoff Guard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TIERS = ("budget", "general", "strong")
TIER_RANK = {name: index for index, name in enumerate(TIERS)}
EFFORT_FOR_TIER = {"budget": "low", "general": "medium", "strong": "high", "vision": "high"}
KNOWN_REASONING_EFFORTS = {"low", "medium", "high"}
DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "references" / "provider-profiles.json"


def load_profiles(path: str | Path = DEFAULT_PROFILE) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data.get("providers"), dict) or not data["providers"]:
        raise ValueError("profiles must contain a non-empty providers object")
    return data


def canonical_provider(profiles: dict[str, Any], value: str | None) -> str | None:
    if not value:
        return None
    value = value.lower().strip()
    for provider, profile in profiles["providers"].items():
        aliases = {provider.lower(), *(str(alias).lower() for alias in profile.get("aliases", []))}
        if value in aliases:
            return provider
    return value if value in profiles["providers"] else None


def available_providers(profiles: dict[str, Any], availability: Any) -> list[str]:
    if availability is None:
        return list(profiles["providers"])
    if isinstance(availability, dict):
        values = [key for key, item in availability.items() if item is True or (isinstance(item, dict) and item.get("available", False))]
    elif isinstance(availability, list):
        values = availability
    else:
        raise ValueError("provider_availability must be a list or object")
    result = []
    for value in values:
        provider = canonical_provider(profiles, str(value))
        if provider and provider not in result:
            result.append(provider)
    return result


def task_tier(task: dict[str, Any]) -> tuple[str, str]:
    complexity = str(task.get("task_complexity", "moderate")).lower()
    task_type = str(task.get("task_type", "other")).lower()
    if complexity not in {"simple", "moderate", "complex"}:
        raise ValueError("task_complexity must be simple, moderate, or complex")
    if task_type == "vision":
        return "vision", "Vision work requests a vision-capable tier."
    if complexity == "simple":
        return "budget", "Simple or mechanical work only needs the budget tier."
    if complexity == "complex" or task_type in {"architecture", "bugfix"} or task.get("architecture_settled") is False:
        return "strong", "Architecture work or a difficult cross-module bug needs the strong tier."
    if task.get("cost_sensitivity") == "high":
        return "budget", "Cost sensitivity permits the budget tier for moderate work."
    return "general", "Settled, moderate implementation work fits the general tier."


def select_model_for_provider(profile: dict[str, Any], desired_tier: str, task_type: str) -> tuple[dict[str, Any], str | None]:
    models = profile.get("models", [])
    if not models:
        raise ValueError("provider profile has no models")
    compatible = [model for model in models if desired_tier in model.get("capabilities", [])]
    exact = [model for model in models if model.get("tier") == desired_tier]
    candidates = exact or compatible
    fallback_note = None
    if not candidates and desired_tier == "vision":
        candidates = [model for model in models if model.get("tier") == "general"]
        fallback_note = "No vision tier is configured; fell back to general."
    if not candidates:
        desired_rank = TIER_RANK.get(desired_tier, 1)
        ranked = sorted(models, key=lambda model: abs(TIER_RANK.get(model.get("tier"), desired_rank) - desired_rank))
        candidates = ranked
        fallback_note = f"The provider has no {desired_tier} tier; selected the nearest configured tier."
    # Profile order is intentionally stable: maintainers can choose the default model.
    return candidates[0], fallback_note


def model_tier(profiles: dict[str, Any], current: Any) -> tuple[str | None, str | None]:
    if current is None:
        return None, None
    if isinstance(current, str):
        current = {"model": current}
    if not isinstance(current, dict):
        raise ValueError("current_model must be a string or object")
    provider = canonical_provider(profiles, current.get("provider"))
    if current.get("tier") in TIER_RANK or current.get("tier") == "vision":
        return current["tier"], provider
    model_name = current.get("model")
    for provider_name, profile in profiles["providers"].items():
        for model in profile.get("models", []):
            if model.get("name") == model_name:
                return model.get("tier"), provider or provider_name
    return None, provider


def choose_provider(profiles: dict[str, Any], available: list[str], desired_tier: str, task: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    if not available:
        raise ValueError("no available providers remain after applying constraints")
    preferred = canonical_provider(profiles, task.get("preferred_provider"))
    quota_provider = canonical_provider(profiles, task.get("quota_provider"))
    quota_unavailable = bool(task.get("quota_unavailable"))
    if quota_unavailable and quota_provider is None:
        quota_provider = "codex"

    if preferred in available and not (quota_unavailable and preferred == quota_provider):
        provider = preferred
        reason = f"Preferred provider {provider} is available."
    else:
        eligible = [name for name in available if not (quota_unavailable and name == quota_provider)]
        if not eligible:
            raise ValueError("all available providers are excluded by quota_unavailable")

        def cost_key(name: str) -> tuple[int, int]:
            model, _ = select_model_for_provider(profiles["providers"][name], desired_tier, str(task.get("task_type", "other")))
            return ({"low": 0, "medium": 1, "high": 2}.get(model.get("cost_class"), 1), available.index(name))

        provider = sorted(eligible, key=cost_key)[0]
        if quota_unavailable and quota_provider and provider != quota_provider:
            reason = f"Quota for {quota_provider} is unavailable; routed to fallback provider {provider}."
        else:
            reason = f"Selected the lowest configured cost class among available providers: {provider}."
    model, fallback_note = select_model_for_provider(profiles["providers"][provider], desired_tier, str(task.get("task_type", "other")))
    if fallback_note:
        reason = f"{reason} {fallback_note}"
    return provider, model, reason


def select(task: dict[str, Any], profiles: dict[str, Any] | None = None) -> dict[str, Any]:
    profiles = profiles or load_profiles()
    desired_tier, tier_reason = task_tier(task)
    available = available_providers(profiles, task.get("provider_availability"))
    provider, model, provider_reason = choose_provider(profiles, available, desired_tier, task)
    current_tier, current_provider = model_tier(profiles, task.get("current_model"))
    block = False
    preflight_status = "UNVERIFIED"
    preflight_reason = (
        "The host does not expose the active model reliably. "
        "Please verify the model manually if needed. Execution may continue."
    )
    if current_tier:
        current_rank = TIER_RANK.get(current_tier)
        desired_rank = TIER_RANK.get(desired_tier)
        if current_tier == "vision" and desired_tier != "vision":
            current_rank = TIER_RANK["general"]
        if desired_tier == "vision" and current_tier != "vision":
            desired_rank = TIER_RANK["strong"]
        distance = (current_rank - desired_rank) if current_rank is not None and desired_rank is not None else 0
        quota_provider = canonical_provider(profiles, task.get("quota_provider")) or ("codex" if task.get("quota_unavailable") else None)
        if task.get("quota_unavailable") and current_provider == quota_provider:
            block = True
            preflight_status = "BLOCK"
            preflight_reason = f"Current provider {current_provider} is unavailable under the declared quota constraint."
        elif distance >= 2:
            block = True
            preflight_status = "BLOCK"
            preflight_reason = f"Current tier {current_tier} is clearly stronger than required tier {desired_tier}; switch down before execution."
        elif distance <= -2:
            block = True
            preflight_status = "BLOCK"
            preflight_reason = f"Current tier {current_tier} is clearly weaker than required tier {desired_tier}; switch up before execution."
        else:
            current_effort = str(task.get("current_reasoning_effort", "")).lower()
            if current_effort not in KNOWN_REASONING_EFFORTS:
                preflight_reason = (
                    f"Current model tier {current_tier} is suitable, but the host does not expose reasoning effort reliably. "
                    "Please verify it manually if needed. Execution may continue."
                )
            elif distance:
                preflight_status = "PASS"
                preflight_reason = f"Current tier {current_tier} differs by one tier from required tier {desired_tier}; proceed unless quality signals disagree."
            else:
                preflight_status = "PASS"
                preflight_reason = "Current model tier is aligned with the required tier."
    return {
        "recommended_provider": provider,
        "recommended_model": model.get("name"),
        "recommended_model_tier": model.get("tier"),
        "recommended_reasoning_effort": EFFORT_FOR_TIER.get(model.get("tier"), EFFORT_FOR_TIER.get(desired_tier, "medium")),
        "required_task_tier": desired_tier,
        "available_providers": available,
        "reason": f"{tier_reason} {provider_reason}",
        "status": preflight_status,
        "execution_allowed": not block,
        "preflight": {
            "current_model": task.get("current_model"),
            "current_reasoning_effort": task.get("current_reasoning_effort"),
            "status": preflight_status,
            "block_current_execution": block,
            "execution_allowed": not block,
            "reason": preflight_reason,
        },
        "block_current_execution": block,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON object or path to a JSON file; defaults to stdin")
    parser.add_argument("--profiles", default=str(DEFAULT_PROFILE), help="Path to provider-profiles.json")
    args = parser.parse_args()
    try:
        raw = args.input
        if raw:
            possible_path = Path(raw)
            raw = possible_path.read_text(encoding="utf-8") if possible_path.exists() else raw
        else:
            raw = sys.stdin.read()
        result = select(json.loads(raw), load_profiles(args.profiles))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
