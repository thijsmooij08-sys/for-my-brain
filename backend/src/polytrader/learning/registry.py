from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    name: str
    version: str
    artifact_type: str
    content_hash: str
    metadata_json: str
    actionable: bool = False


class ArtifactRegistry:
    """Append-only content-addressed registry for research artifacts."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def register(self, name: str, version: str, artifact_type: str, payload: dict[str, Any]) -> RegistryEntry:
        if not name or not version or not artifact_type:
            raise ValueError("artifact identity fields are required")
        metadata_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        content_hash = hashlib.sha256(metadata_json.encode("utf-8")).hexdigest()
        for existing in self.read():
            if (existing.name, existing.version, existing.artifact_type) == (name, version, artifact_type):
                if existing.content_hash != content_hash:
                    raise ValueError("registry versions are immutable")
                return existing
        entry = RegistryEntry(name, version, artifact_type, content_hash, metadata_json, False)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "name": name, "version": version, "artifact_type": artifact_type,
                "content_hash": content_hash, "metadata_json": metadata_json, "actionable": False,
            }, sort_keys=True) + "\n")
        return entry

    def read(self) -> tuple[RegistryEntry, ...]:
        if not self.path.exists():
            return ()
        return tuple(RegistryEntry(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines())
