"""Research-only integrations.

These helpers may analyze snapshots and paper history, but they cannot submit
orders, mutate canonical accounting, or bypass the risk pipeline.
"""

from .analytics import performance_summary, portfolio_weights
from .debate import DebateArtifact, DebatePosition, ResearchDebate
from .external_catalog import ExternalResearchCatalog, ExternalResearchSource
from .external_replay import ExternalReplayDataset, ExternalReplayImporter
from .metrics import record_paper_fill

__all__ = [
    "performance_summary", "portfolio_weights", "record_paper_fill",
    "ExternalResearchCatalog", "ExternalResearchSource", "ExternalReplayDataset",
    "ExternalReplayImporter",
    "DebateArtifact", "DebatePosition", "ResearchDebate",
]
