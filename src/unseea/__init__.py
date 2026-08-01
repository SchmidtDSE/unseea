"""unseea — the UN SEEA-EA accounts as a library.

Five accounts behind nine calls, with a pluggable executor: the fixture tier runs the
standard's own worked example with no network, and the same code path will run against real h3
data through DuckDB or the deployed MCP server.

    >>> import unseea
    >>> eng = unseea.connect(fixture="research/seealand-fixture/")
    >>> eaa = eng.eaa()
    >>> acct = eng.services_monetary(eaa, date=2020).check()
    >>> round(acct.totals["GEP"])
    83125

Every account returns its table, the exact SQL that produced it, the reconciliation checks the
standard implies, and the provenance needed to judge what it means.
"""

from __future__ import annotations

__version__ = "0.1.0"

from . import fixtures, npv, vocab
from .engine import EAA, Engine, connect
from .parameters import SEEALAND, ParameterSet
from .results import Account, Check, CheckFailure, Provenance

__all__ = [
    "__version__",
    "connect",
    "Engine",
    "EAA",
    "Account",
    "Check",
    "CheckFailure",
    "Provenance",
    "ParameterSet",
    "SEEALAND",
    "npv",
    "vocab",
    "fixtures",
]
