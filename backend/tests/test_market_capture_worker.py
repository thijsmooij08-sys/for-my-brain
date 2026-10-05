from polytrader.market_capture_worker import CaptureConfig


def test_capture_config_is_bounded_and_read_only(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_CAPTURE_MARKET_LIMIT", "1000")
    monkeypatch.setenv("MARKET_CAPTURE_RETRY_SECONDS", "1")
    config = CaptureConfig.from_environment()
    assert config.enabled is True
    assert config.market_limit == 100
    assert config.retry_seconds == 5
    assert config.database_url.startswith("sqlite:")
