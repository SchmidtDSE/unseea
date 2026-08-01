"""The two real-data executors, declared but not yet implemented.

They are declared here rather than left out because the seam is the point: an account
compiles against whichever executor ``connect()`` was given, and a stub that names its
blocking issue is more honest than an API that silently lacks the runtime the architecture
promises.

* **Local DuckDB** needs the ET partition, the condition bindings and the h3 rollups —
  `unseea` issues #4, #5, #6, #7.
* **MCP** needs the deployed ``mcp-data-server`` and the account-library endpoint — issue #29.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class _Unimplemented:
    name = "unimplemented"
    issue = ""
    needs = ""

    def execute(self, sql: str) -> pd.DataFrame:  # pragma: no cover - guard only
        raise NotImplementedError(
            f"the {self.name} executor is not implemented yet: {self.needs} "
            f"(see https://github.com/SchmidtDSE/unseea/issues/{self.issue}). "
            "Use connect(fixture=...) for the conformance tier."
        )

    def portable_sql(self, sql: str) -> str:  # pragma: no cover - guard only
        return sql

    def describe(self) -> dict[str, Any]:  # pragma: no cover - guard only
        return {"executor": self.name, "status": "not implemented", "issue": self.issue}


class LocalDuckDBExecutor(_Unimplemented):
    """DuckDB against the NRP catalog or the source.coop mirror."""

    name = "local"
    issue = "4"
    needs = "real-data bindings for the ET partition and condition variables"

    def __init__(self, **options: Any) -> None:
        self.options = options


class MCPExecutor(_Unimplemented):
    """The deployed ``mcp-data-server``, reached over MCP."""

    name = "mcp"
    issue = "29"
    needs = "the account-library MCP endpoint"

    def __init__(self, url: str, **options: Any) -> None:
        self.url = url
        self.options = options
