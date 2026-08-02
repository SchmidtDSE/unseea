"""The executor seam.

``connect()`` picks a runtime; the accounts do not know which one they ran on. All three
executors answer the same two questions — run this SQL, and tell me what you ran against —
which is what lets the conformance tier (fixture, no network) test the same code path the
deployed app uses.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class Executor(Protocol):
    """Runs account SQL and describes what it ran against."""

    name: str

    def execute(self, sql: str) -> pd.DataFrame:
        """Run ``sql`` and return the result."""

    def portable_sql(self, sql: str) -> str:
        """Return ``sql`` in the form a reader can re-run themselves.

        For the real-data executors this rewrites ``s3://`` to the public HTTPS endpoint, the
        way the geo-agent chat export already does, so the SQL runs in any DuckDB with
        ``httpfs`` and no credentials.
        """

    def describe(self) -> dict[str, Any]:
        """Sources, licences and anything else provenance should carry."""
