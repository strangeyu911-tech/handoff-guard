from __future__ import annotations

import difflib
import secrets
from dataclasses import dataclass

from .backup import BackupRecord, LocalBackupStore
from .errors import ConfirmationRequiredError, RepairRequiredError
from .managed_block import (
    MANAGED_VERSION,
    canonical_payload,
    inspect_managed_block,
    install_or_update,
    repair_remove_markers,
    uninstall,
)


@dataclass(frozen=True)
class ChangePlan:
    token: str
    operation: str
    action: str
    before: str
    after: str
    preview: str


@dataclass(frozen=True)
class ApplyResult:
    action: str
    output: str
    backup: BackupRecord | None
    validated: bool


class InstallerService:
    """Generate and validate local text changes for a guided install.

    This service deliberately has no ChatGPT or desktop adapter. The caller
    supplies any existing text, and the returned result is only a local value
    that the user may copy and save in ChatGPT themselves.
    """

    def __init__(self, backups: LocalBackupStore | None = None):
        self.backups = backups or LocalBackupStore()

    @staticmethod
    def _preview(before: str, after: str) -> str:
        return "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile="Current Custom Instructions",
                tofile="After confirmation",
            )
        ) or "No changes required."

    def prepare(self, operation: str, current: str = "") -> ChangePlan:
        if not isinstance(current, str):
            raise TypeError("current Custom Instructions must be text")
        before = current
        if operation in {"install", "update"}:
            after, action = install_or_update(before, canonical_payload(), MANAGED_VERSION)
        elif operation == "uninstall":
            after, action = uninstall(before)
        elif operation == "repair":
            state = inspect_managed_block(before)
            if state.status != "corrupt":
                raise RepairRequiredError("Repair is available only for a damaged managed block")
            cleaned = repair_remove_markers(before)
            after, _ = install_or_update(cleaned, canonical_payload(), MANAGED_VERSION)
            action = "repair"
        else:
            raise ValueError(f"unsupported operation: {operation}")
        return ChangePlan(
            token=secrets.token_urlsafe(24),
            operation=operation,
            action=action,
            before=before,
            after=after,
            preview=self._preview(before, after),
        )

    def apply(
        self,
        plan: ChangePlan,
        confirmation_token: str,
        *,
        save_local_backup: bool = False,
    ) -> ApplyResult:
        """Confirm a local transformation; never writes to ChatGPT.

        A backup is opt-in and only contains text explicitly supplied by the
        user to this service.
        """
        if not secrets.compare_digest(plan.token, confirmation_token):
            raise ConfirmationRequiredError("Confirm the displayed local preview before copying")
        backup = self.backups.save(plan.before, plan.action) if save_local_backup else None
        return ApplyResult(action=plan.action, output=plan.after, backup=backup, validated=True)

    def backup_text(self, text: str, operation: str = "user-provided") -> BackupRecord:
        """Back up text the user explicitly supplied to the local installer."""
        return self.backups.save(text, operation)
