"""The fixture executor: the SEEALand workbook, in DuckDB, with no network.

This is the conformance tier. It is why Phase 1 is unblocked by data acquisition: the account
arithmetic and the NPV decomposition are forced correct against a published worked example
before a single real layer is trusted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from ..fixtures import seealand

#: The one accounting area the fixture knows.
FIXTURE_EAA = "SEEALand"

#: The one accounting period the fixture covers: 1 January – 31 December 2020.
FIXTURE_PERIOD = 2020


class FixtureExecutor:
    """Serve account SQL from the checked-in SEEALand CSVs."""

    name = "fixture"

    #: Accounting periods this executor can compile.
    periods: tuple[int, ...] = (FIXTURE_PERIOD,)

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.connection = duckdb.connect(":memory:")
        self.tables = seealand.register(self.connection, self.path)

    def execute(self, sql: str) -> pd.DataFrame:
        return self.connection.execute(sql).df()

    def portable_sql(self, sql: str) -> str:
        """Prepend the two lines that make the query re-runnable elsewhere.

        The fixture has no ``s3://`` paths to rewrite; what a reader needs instead is the tidy
        tables the query reads, which :func:`unseea.fixtures.seealand.register` builds from the
        same CSVs.
        """
        header = (
            "-- Executor: fixture (no network). Recreate the tables this query reads with:\n"
            "--   import duckdb; from unseea.fixtures import seealand\n"
            "--   con = duckdb.connect()\n"
            f"--   seealand.register(con, {str(self.path)!r})\n"
        )
        return header + sql

    def describe(self) -> dict[str, Any]:
        return {
            "executor": self.name,
            "eaa": FIXTURE_EAA,
            "sources": [f"{self.path}/{sheet}" for sheet in sorted(seealand.INPUT_SHEETS)],
            "licences": ["UN SEEA EA online supplement (SEEALand stylised example, v1 2021)"],
            "tables": {name: len(frame) for name, frame in self.tables.items()},
            "notes": [
                "Fixture tier: figures are the standard's own worked example, not real data.",
            ],
        }
