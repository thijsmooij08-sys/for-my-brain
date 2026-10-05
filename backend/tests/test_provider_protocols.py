from polytrader.providers.protocols import DataHealth, MarketDataProvider


def test_provider_protocol_defines_public_data_and_health_boundary() -> None:
    assert DataHealth.FRESH.value == "FRESH"
    assert DataHealth.STALE.value == "STALE"
    assert hasattr(MarketDataProvider, "list_markets")
    assert hasattr(MarketDataProvider, "order_book")
