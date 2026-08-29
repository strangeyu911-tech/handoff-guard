from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class BackupRecord:
    path: Path
    created_at: str


class LocalBackupStore:
    def __init__(self, directory: Path | None = None):
        if directory is None:
            import os

            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            directory = base / "HandoffGuard" / "backups"
        self.directory = directory

    def save(self, original: str, operation: str) -> BackupRecord:
        self.directory.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
        path = self.directory / f"custom-instructions-{stamp}.json"
        document = {
            "schema_version": 1,
            "created_at": now.isoformat(),
            "operation": operation,
            "custom_instructions": original,
            "upload": False,
        }
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        return BackupRecord(path=path, created_at=document["created_at"])
