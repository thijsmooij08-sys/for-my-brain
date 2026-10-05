"""Reviewed boundaries for external research projects.

This module records what PolyTrader may learn from external projects. It does
not import or execute any third-party trading code.
"""

from __future__ import annotations

from dataclasses import dataclass


class UnknownExternalSource(KeyError):
    """Raised when an unreviewed external source is requested."""


@dataclass(frozen=True, slots=True)
class ExternalResearchSource:
    source_id: str
    name: str
    url: str
    decision: str
    license_status: str
    accepted_patterns: tuple[str, ...]
    research_only: bool
    execution_authority: bool = False


@dataclass(frozen=True, slots=True)
class ExternalResearchCatalog:
    sources: tuple[ExternalResearchSource, ...]

    @classmethod
    def default(cls) -> "ExternalResearchCatalog":
        return cls(
            (
                ExternalResearchSource(
                    "openmarket", "OpenMarket", "https://github.com/gregyoung14/openmarket",
                    "add-research", "review dataset terms before import",
                    ("timestamped replay", "paired-market benchmark", "null-result reporting"), True,
                ),
                ExternalResearchSource(
                    "oraclebook", "oraclebook", "https://github.com/jabrahamtech/oraclebook",
                    "extract-patterns", "verify repository license before copying",
                    ("event bus", "composable risk gates", "recorded-order-flow replay"), True,
                ),
                ExternalResearchSource(
                    "hftbacktest", "hftbacktest", "https://github.com/nkaz001/hftbacktest",
                    "extract-patterns", "verify package license and version before use",
                    ("queue position", "latency model", "L2/L3 replay"), True,
                ),
                ExternalResearchSource(
                    "polymarket-backtest", "polymarket-backtest",
                    "https://github.com/cengizmandros/polymarket-backtest", "extract-patterns",
                    "verify repository license before copying",
                    ("V2 fee model", "no-lookahead replay", "performance metrics"), True,
                ),
                ExternalResearchSource(
                    "order-book-sim", "order-book-sim", "https://github.com/truenopg/order-book-sim",
                    "extract-patterns", "verify repository license before copying",
                    ("matching-engine tests", "event-log replay", "microstructure metrics"), True,
                ),
                ExternalResearchSource(
                    "polybench", "PolyBench", "https://arxiv.org/abs/2604.14199", "benchmark-only",
                    "paper and dataset terms require review",
                    ("timestamp-locked evaluation", "confidence-weighted metrics"), True,
                ),
                ExternalResearchSource(
                    "predictionmarketbench", "PredictionMarketBench",
                    "https://arxiv.org/abs/2602.00133", "benchmark-only",
                    "paper and dataset terms require review",
                    ("agent benchmark", "LOB replay evaluation"), True,
                ),
                ExternalResearchSource(
                    "alpha-lake", "alpha-lake", "https://github.com/mblaauw/alpha-lake",
                    "extract-patterns", "verify repository license before copying",
                    ("bitemporal facts", "provenance-aware lakehouse"), True,
                ),
                ExternalResearchSource(
                    "pmxt", "PMXT", "https://github.com/pmxt-dev/pmxt", "review-only",
                    "unified API terms require review",
                    ("venue normalization",), True,
                ),
                ExternalResearchSource(
                    "marketlens", "Marketlens", "https://marketlenstrade.github.io/", "review-only",
                    "data license and provider terms require review",
                    ("historical L2 data", "queue-aware replay"), True,
                ),
                ExternalResearchSource(
                    "polymarket-trader", "Polymarket Trader",
                    "https://github.com/Thomas-quinn7/Polymarket_trader", "compare-only",
                    "repository license must be verified",
                    ("modular adapter comparison", "paper-fill comparison"), True,
                ),
                ExternalResearchSource(
                    "homerun", "Homerun", "https://github.com/braedonsaunders/homerun",
                    "reject-runtime", "not accepted into runtime",
                    ("dashboard comparison",), False,
                ),
                ExternalResearchSource(
                    "openpoly", "OpenPoly", "https://github.com/KoNananachan/OpenPoly",
                    "reject-runtime", "not accepted into runtime",
                    ("news-signal comparison",), False,
                ),
                ExternalResearchSource(
                    "newworldtrading", "NewWorldTrading",
                    "https://github.com/TrentonNewWorld/NewWorldTrading", "reject-runtime",
                    "not accepted into runtime", ("paper-workflow comparison",), False,
                ),
                ExternalResearchSource(
                    "vibe-trading", "Vibe-Trading", "https://github.com/HKUDS/Vibe-Trading",
                    "reject-runtime", "not accepted into runtime",
                    ("agent-orchestration comparison",), False,
                ),
            )
        )

    def require(self, source_id: str) -> ExternalResearchSource:
        for source in self.sources:
            if source.source_id == source_id:
                return source
        raise UnknownExternalSource(source_id)
