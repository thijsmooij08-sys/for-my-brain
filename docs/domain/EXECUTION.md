# Execution

PaperExecutionEngine takes only an approved OrderIntent. Buys walk asks; sells walk bids. A fill cannot exceed order quantity or displayed book liquidity. Partial fills are explicit. A live submission call raises `LiveTradingDisabledError` unconditionally in Phase 1.

