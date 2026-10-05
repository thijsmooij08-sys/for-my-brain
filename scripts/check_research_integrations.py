"""Verify the optional, safe research integrations without starting services."""

import subprocess
from importlib import import_module
from pathlib import Path

MODULES = {
    "alpaca-py": "alpaca",
    "pandas": "pandas",
    "polars": "polars",
    "scikit-learn": "sklearn",
    "statsmodels": "statsmodels",
    "PyPortfolioOpt": "pypfopt",
    "Riskfolio-Lib": "riskfolio",
    "quantstats": "quantstats",
    "vectorbt": "vectorbt",
    "prometheus-client": "prometheus_client",
    "duckdb": "duckdb",
    "pyarrow": "pyarrow",
    "pandera": "pandera",
    "hypothesis": "hypothesis",
    "opentelemetry-api": "opentelemetry",
    "opentelemetry-sdk": "opentelemetry.sdk",
    "mlflow": "mlflow",
    "optuna": "optuna",
}


for package, module_name in MODULES.items():
    module = import_module(module_name)
    print(f"{package}: {getattr(module, '__version__', 'installed')}")

print("disabled services: alpaca-mcp-server, FinRL, Quantopian Zipline, sec-edgar-mcp")

root = Path(__file__).resolve().parents[1]
for package, distribution_name, environment in (
    ("feast", "feast", ".feast-venv"),
    ("prefect", "prefect", ".prefect-venv"),
    ("nasdaqdatalink", "Nasdaq-Data-Link", ".nasdaq-venv"),
    ("openbb", "openbb", ".openbb-venv"),
):
    executable = root / "backend" / environment / "Scripts" / "python.exe"
    if not executable.exists():
        raise RuntimeError(f"{package} isolated environment is missing: {executable}")
    result = subprocess.run(
        [
            str(executable),
            "-c",
            f"import importlib.metadata; print(importlib.metadata.version({distribution_name!r}))",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"{package} (isolated): {result.stdout.strip()}")
