from __future__ import annotations

import difflib
import secrets
from dataclasses import dataclass

from .adapters import SettingsAdapter
from .backup import BackupRecord, LocalBackupStore
from .errors import (
    ConfirmationRequiredError,
    RepairRequiredError,
    SettingsUnavailableError,
    UnsafeReadError,
    VerificationError,
)
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
    backup: BackupRecord | None
    verified: bool


class InstallerService:
    def __init__(self, adapter: SettingsAdapter, backups: LocalBackupStore | None = None):
        self.adapter = adapter
        self.backups = backups or LocalBackupStore()

    def _read(self) -> str:
        if not self.adapter.is_chatgpt_available():
            raise SettingsUnavailableError("ChatGPT Desktop was not found")
        self.adapter.open_personalization()
        current = self.adapter.read_custom_instructions()
        if current is None:
            raise UnsafeReadError(
                "Existing Custom Instructions could not be read. Nothing was changed; use Copy & Open Settings."
            )
        return current

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

    def prepare(self, operation: str) -> ChangePlan:
        before = self._read()
        if operation == "install":
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

    def apply(self, plan: ChangePlan, confirmation_token: str) -> ApplyResult:
        if not secrets.compare_digest(plan.token, confirmation_token):
            raise ConfirmationRequiredError("Confirm the displayed preview before applying changes")
        if plan.action == "noop":
            return ApplyResult(action="noop", backup=None, verified=True)
        current = self.adapter.read_custom_instructions()
        if current is None or current != plan.before:
            raise VerificationError("Custom Instructions changed after preview; refresh before installing")
        backup = self.backups.save(plan.before, plan.action)
        try:
            self.adapter.write_custom_instructions(plan.after)
        except Exception as exc:
            raise VerificationError(f"Write failed. Restore from backup: {backup.path}") from exc
        saved = self.adapter.read_custom_instructions()
        if saved != plan.after:
            raise VerificationError(f"Save verification failed. Restore from backup: {backup.path}")
        return ApplyResult(action=plan.action, backup=backup, verified=True)
