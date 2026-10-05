"""Research-only integrations.

These helpers may analyze snapshots and paper history, but they cannot submit
orders, mutate canonical accounting, or bypass the risk pipeline.
"""

from .analytics import performance_summary, portfolio_weights
from .metrics import record_paper_fill

__all__ = ["performance_summary", "portfolio_weights", "record_paper_fill"]
