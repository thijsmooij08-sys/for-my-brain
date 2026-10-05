from fastapi.testclient import TestClient

from polytrader.api.app import app


def test_health_reports_paper_only_system() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "trading_mode": "PAPER", "live_execution": False}


def test_metrics_endpoint_is_available_for_local_observability() -> None:
    response = TestClient(app).get("/metrics")
    assert response.status_code == 200
    assert "polytrader_api_requests_total" in response.text
    assert "polytrader_live_execution_enabled 0.0" in response.text
    assert 'polytrader_trading_mode{mode="PAPER"} 1.0' in response.text
    assert "polytrader_paper_cash" in response.text
    assert "polytrader_paper_equity" in response.text
    assert "polytrader_paper_fill_count" in response.text
    assert "polytrader_paper_win_rate_percent" in response.text


def test_phase_one_state_endpoints_do_not_expose_orm_models() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/portfolio").json()["trading_mode"] == "PAPER"
    assert client.get("/api/v1/positions").json() == {"items": []}
    assert client.get("/api/v1/orders").json() == {"items": []}


def test_phase_eight_readiness_is_redacted_and_disabled() -> None:
    payload = TestClient(app).get("/api/v1/live-readiness").json()
    assert payload["state"] == "DISABLED"
    assert payload["eligible"] is False
    assert payload["live_execution"] is False
    assert payload["credentials_loaded"] is False
    assert payload["signer_available"] is False
    assert "live_execution_disabled" in payload["reasons"]


def test_phase_nine_preflight_exposes_paper_state_without_live_authority() -> None:
    payload = TestClient(app).get("/api/v1/live-preflight").json()
    assert payload["activation_allowed"] is False
    assert payload["live_execution"] is False
    assert payload["paper_operational"] is True
    assert set(payload["paper_account"]) == {"cash", "equity", "open_positions", "fills"}


def test_phase_ten_learning_api_is_research_only() -> None:
    client = TestClient(app)
    assert client.get("/api/v1/learning/status").json() == {
        "mode": "RESEARCH_ONLY", "allocation_authority": False,
        "risk_bypass": False, "live_execution": False,
    }
    response = client.post("/api/v1/learning/allocation", json={
        "strategy_id": "candidate", "requested_weight": "0.50",
        "closed_samples": 40, "net_realized_pnl": "2.00", "max_drawdown": "0.02",
    })
    payload = response.json()
    assert response.status_code == 200
    assert payload["approved_weight"] == "0.25"
    assert payload["execution_authority"] is False
    assert payload["live_execution"] is False

    rejected = client.post("/api/v1/learning/allocation", json={
        "strategy_id": "weak", "requested_weight": "0.90",
        "closed_samples": 2, "net_realized_pnl": "-0.01", "max_drawdown": "0.20",
    }).json()
    assert rejected["approved"] is False
    assert rejected["approved_weight"] == "0"
    assert rejected["execution_authority"] is False
    assert rejected["live_execution"] is False


def test_paper_performance_is_honest_with_no_closed_trades() -> None:
    payload = TestClient(app).get("/api/v1/paper/performance").json()
    assert payload == {
        "fills": 0, "exits": 0, "wins": 0, "losses": 0, "win_rate": "0",
        "closed_trade_sample": 0, "realized_pnl": "0", "total_fees": "0",
    }
