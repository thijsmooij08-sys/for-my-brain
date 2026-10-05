# Real-money transition gates

This document records future readiness knowledge only. It is not an activation
procedure and does not grant permission to submit real orders.

PolyTrader remains paper-only while `LIVE_TRADING_ENABLED=false`. A future
transition would need independently verified account eligibility, external
secret storage, a secure signer boundary, venue order and user-stream contracts,
restart-safe reconciliation, deterministic RiskManager limits, circuit
breakers, a kill switch, staged shadow evidence with realistic costs, and an
explicit operator authorization after a documented preflight.

Learning systems may not raise global capital limits, weaken maximum-loss
limits, disable circuit breakers, bypass eligibility, bypass RiskManager, or
grant themselves execution authority. Until separate authorization exists,
real-order submission must remain impossible.
