from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .errors import RepairRequiredError


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_PATH = ROOT / "runtime" / "custom-instructions.txt"
MANAGED_VERSION = "0.1.0"
BEGIN_PREFIX = "[HANDOFF-GUARD:BEGIN"
END_MARKER = "[HANDOFF-GUARD:END]"
BEGIN_RE = re.compile(
    r"^\[HANDOFF-GUARD:BEGIN version=(?P<version>[^\s\]]+) sha256=(?P<digest>[0-9a-f]{12})\]$",
    re.MULTILINE,
)
BLOCK_RE = re.compile(
    r"^\[HANDOFF-GUARD:BEGIN version=(?P<version>[^\s\]]+) sha256=(?P<digest>[0-9a-f]{12})\]\r?\n"
    r"(?P<payload>.*?)\r?\n\[HANDOFF-GUARD:END\]$",
    re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class ManagedBlockState:
    status: str
    version: str | None = None
    payload: str | None = None
    reason: str | None = None


def canonical_payload() -> str:
    return PAYLOAD_PATH.read_text(encoding="utf-8").strip()


def payload_digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def render_managed_block(payload: str | None = None, version: str = MANAGED_VERSION) -> str:
    payload = (payload if payload is not None else canonical_payload()).strip()
    return (
        f"[HANDOFF-GUARD:BEGIN version={version} sha256={payload_digest(payload)}]\n"
        f"{payload}\n"
        f"{END_MARKER}"
    )


def inspect_managed_block(text: str) -> ManagedBlockState:
    begin_count = text.count(BEGIN_PREFIX)
    end_count = text.count(END_MARKER)
    if begin_count == 0 and end_count == 0:
        return ManagedBlockState("absent")
    if begin_count != 1 or end_count != 1:
        return ManagedBlockState("corrupt", reason="managed block markers are missing or duplicated")
    match = BLOCK_RE.search(text)
    if not match:
        return ManagedBlockState("corrupt", reason="managed block is truncated or malformed")
    payload = match.group("payload").strip()
    if payload_digest(payload) != match.group("digest"):
        return ManagedBlockState("corrupt", reason="managed block checksum does not match")
    return ManagedBlockState("installed", version=match.group("version"), payload=payload)


def install_or_update(text: str, payload: str | None = None, version: str = MANAGED_VERSION) -> tuple[str, str]:
    state = inspect_managed_block(text)
    if state.status == "corrupt":
        raise RepairRequiredError(state.reason or "managed block requires repair")
    block = render_managed_block(payload, version)
    if state.status == "absent":
        separator = "\n\n" if text.strip() else ""
        return f"{text.rstrip()}{separator}{block}", "install"
    assert state.payload is not None
    match = BLOCK_RE.search(text)
    assert match is not None
    updated = f"{text[:match.start()]}{block}{text[match.end():]}"
    action = "noop" if match.group(0).replace("\r\n", "\n") == block else "update"
    return updated, action


def uninstall(text: str) -> tuple[str, str]:
    state = inspect_managed_block(text)
    if state.status == "corrupt":
        raise RepairRequiredError(state.reason or "managed block requires repair")
    if state.status == "absent":
        return text, "noop"
    match = BLOCK_RE.search(text)
    assert match is not None
    before = text[:match.start()].rstrip()
    after = text[match.end():].lstrip("\r\n")
    if before and after:
        return f"{before}\n\n{after}", "uninstall"
    return before or after, "uninstall"


def repair_remove_markers(text: str) -> str:
    """Conservative repair: remove only the damaged Handoff Guard region.

    The caller must show the result as a preview and obtain confirmation before saving.
    """
    first_begin = text.find(BEGIN_PREFIX)
    first_end = text.find(END_MARKER)
    if first_begin < 0 and first_end < 0:
        return text
    start = first_begin if first_begin >= 0 else first_end
    if first_end >= start:
        end = first_end + len(END_MARKER)
    else:
        end = len(text)
    return f"{text[:start].rstrip()}\n\n{text[end:].lstrip()}".strip()
