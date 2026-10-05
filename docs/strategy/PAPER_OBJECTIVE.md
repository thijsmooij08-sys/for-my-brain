# Paper-trading objective and expansion policy

The paper trader's goal is to discover strategies that make money after fees,
book-walking slippage, and latency—not to maximize an unqualified win rate.
Win rate is tracked, but it cannot be optimized alone because a strategy can
produce many tiny wins and occasional catastrophic losses.

The ordered objective is:

1. Positive net realized P&L over a pre-declared evaluation window.
2. High closed-trade success rate, with probability calibration and enough
   observations to make the estimate meaningful.
3. Controlled drawdown, exposure, liquidity usage, and loss tails under the
   deterministic RiskManager.
4. Stable performance on walk-forward and shadow data, not only the training
   sample.

The system starts with a narrow, high-liquidity set of binary Polymarket
markets. It may expand the market universe or trade frequency only after a
Champion passes minimum-sample, net-of-cost, calibration, drawdown, and
data-health gates. Expansion is staged and reversible; it never raises global
capital or loss limits and never bypasses RiskManager or eligibility.

The current `DevelopmentStrategy` remains explicitly non-validated and cannot
be treated as evidence of profitability. Learning and promotion artifacts are
advisory until the deterministic gates pass.

Phase 10's `ResearchAllocator` implements the first allocation gate: candidate
weights are capped with exact `Decimal` values and rejected for insufficient
samples, non-positive net P&L, or excessive drawdown. The result is advisory
and carries no execution authority.

`AllocationLedger` records those decisions in an append-only, hash-chained
research journal so promotion and rollback review can be reproduced.

The API surfaces this as `GET /api/v1/learning/status` and
`POST /api/v1/learning/allocation`; both are research-only and return
`execution_authority=false`.
