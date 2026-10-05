from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from polytrader.research.external_catalog import ExternalResearchCatalog, UnknownExternalSource
from polytrader.research.external_replay import ExternalReplayImporter


def test_catalog_approves_only_research_boundaries() -> None:
    catalog = ExternalResearchCatalog.default()

    source = catalog.require("openmarket")

    assert source.research_only is True
    assert any("replay" in pattern for pattern in source.accepted_patterns)
    assert source.execution_authority is False


def test_catalog_rejects_live_capable_sources() -> None:
    catalog = ExternalResearchCatalog.default()

    source = catalog.require("homerun")

    assert source.research_only is False
    assert source.execution_authority is False
    assert source.decision == "reject-runtime"


def test_catalog_rejects_unknown_source() -> None:
    with pytest.raises(UnknownExternalSource):
        ExternalResearchCatalog.default().require("not-reviewed")


def _event(sequence: int, source_timestamp: str, *, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = payload or {"price": "0.42", "size": "2"}
    return {
        "event_id": f"event-{sequence}", "sequence": sequence,
        "source_timestamp": source_timestamp, "collected_at": source_timestamp,
        "token_id": "token-1", "kind": "book",
        "payload": body, "payload_hash": hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def test_external_replay_import_preserves_exact_values_and_provenance(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(_event(1, "2026-01-01T00:00:00+00:00")) + "\n", encoding="utf-8")

    imported = ExternalReplayImporter().from_jsonl(
        path, source_id="openmarket", license_ref="dataset-terms-v1"
    )

    assert imported.source_id == "openmarket"
    assert imported.license_ref == "dataset-terms-v1"
    assert imported.dataset.events[0].payload["price"] == "0.42"
    assert len(imported.input_sha256) == 64


def test_external_replay_import_rejects_binary_float_payload(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps(_event(1, "2026-01-01T00:00:00+00:00", payload={"price": 0.42})) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="numeric payload values must be decimal strings"):
        ExternalReplayImporter().from_jsonl(path, source_id="openmarket", license_ref="terms")


def test_external_replay_import_rejects_time_regression_and_duplicate_sequence(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join([
            json.dumps(_event(1, "2026-01-01T00:00:01+00:00")),
            json.dumps(_event(1, "2026-01-01T00:00:02+00:00")),
        ]) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate replay sequence"):
        ExternalReplayImporter().from_jsonl(path, source_id="openmarket", license_ref="terms")


def test_external_replay_import_rejects_timestamp_regression(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join([
            json.dumps(_event(1, "2026-01-01T00:00:02+00:00")),
            json.dumps(_event(2, "2026-01-01T00:00:01+00:00")),
        ]) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="timestamp regression"):
        ExternalReplayImporter().from_jsonl(path, source_id="openmarket", license_ref="terms")


def test_external_replay_import_rejects_unapproved_runtime_source(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(_event(1, "2026-01-01T00:00:00+00:00")) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="not approved for research import"):
        ExternalReplayImporter().from_jsonl(path, source_id="vibe-trading", license_ref="terms")


def test_external_replay_import_rejects_naive_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(_event(1, "2026-01-01T00:00:00")) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="timezone"):
        ExternalReplayImporter().from_jsonl(path, source_id="openmarket", license_ref="terms")
