import pytest

from polytrader.learning.registry import ArtifactRegistry


def test_registry_content_addresses_research_artifacts(tmp_path) -> None:
    registry = ArtifactRegistry(tmp_path / "registry.jsonl")
    first = registry.register("model-a", "1", "model", {"features": ["price"], "seed": 7})
    repeat = registry.register("model-a", "1", "model", {"features": ["price"], "seed": 7})
    assert repeat == first
    assert first.content_hash
    assert first.actionable is False
    assert len(registry.read()) == 1


def test_registry_rejects_replacing_a_version(tmp_path) -> None:
    registry = ArtifactRegistry(tmp_path / "registry.jsonl")
    registry.register("model-a", "1", "model", {"seed": 7})
    with pytest.raises(ValueError, match="immutable"):
        registry.register("model-a", "1", "model", {"seed": 8})
