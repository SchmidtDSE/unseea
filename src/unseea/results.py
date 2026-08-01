"""What an account call returns: the table, the SQL, the checks, the provenance.

SEEA hands us the test suite — every account reconciles by construction — so ``checks`` are
derived from the standard rather than invented, and a failing check is a defect in the
compilation, not a warning to be tuned away.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

#: Absolute tolerance for reconciliation residuals. The workbook's own ``Check`` rows land at
#: ~1e-10 on values of order 1e6, which is float64 accumulation noise, not disagreement.
DEFAULT_TOLERANCE = 1e-6


class CheckFailure(AssertionError):
    """Raised when an account fails one of its own reconciliation identities."""


@dataclass(frozen=True)
class Check:
    """One reconciliation identity, evaluated.

    Args:
        name: The identity, stated as it appears in the standard.
        residual: Signed size of the violation; 0 when the identity holds exactly.
        tolerance: Absolute tolerance applied to ``residual``.
        detail: Where the residual arises (which ET, which service).
    """

    name: str
    residual: float
    tolerance: float = DEFAULT_TOLERANCE
    detail: str = ""

    @property
    def passed(self) -> bool:
        return abs(self.residual) <= self.tolerance

    def __str__(self) -> str:
        mark = "ok" if self.passed else "FAIL"
        suffix = f" [{self.detail}]" if self.detail else ""
        return f"{mark:4s} {self.name}{suffix}: residual={self.residual:.3g}"


@dataclass(frozen=True)
class Provenance:
    """Everything needed to judge whether an account means what it appears to mean.

    ``ect_coverage`` is not optional metadata. An ECT class that cannot be measured does not
    contribute zero to a condition index — it contributes nothing, and every measured class
    silently gains weight. Two indices built from different coverage are not comparable even
    though both are dimensionless and in [0, 1] (`DESIGN.md` §2.4).
    """

    account: str
    executor: str
    eaa: str
    period: str
    parameters: dict[str, Any] = field(default_factory=dict)
    bindings: dict[str, Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)
    licences: list[str] = field(default_factory=list)
    ect_coverage: dict[str, list[str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    unseea_version: str = ""

    @property
    def nc_encumbered(self) -> bool:
        """True when any binding carries a non-commercial restriction it passes downstream."""
        return any("NC" in licence.upper() for licence in self.licences)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account": self.account,
            "executor": self.executor,
            "eaa": self.eaa,
            "period": self.period,
            "parameters": self.parameters,
            "bindings": self.bindings,
            "sources": list(self.sources),
            "licences": list(self.licences),
            "nc_encumbered": self.nc_encumbered,
            "ect_coverage": {k: list(v) for k, v in self.ect_coverage.items()},
            "notes": list(self.notes),
            "unseea_version": self.unseea_version,
        }


@dataclass
class Account:
    """A compiled SEEA account.

    Attributes:
        name: Which account this is.
        table: The account in long form — one row per cell, stable column set. This is what
            ``sql`` returns, and what downstream code should compute on.
        tables: SEEA-shaped presentation tables pivoted from ``table``. The standard's layouts
            (entries down, ETs across) are for reading, not for joining.
        sql: The exact SQL that produced ``table``.
        checks: The account's reconciliation identities, evaluated.
        provenance: Bindings, parameters, ECT coverage, licences.
        totals: Named headline scalars, e.g. ``{"GEP": 83125.0}``.
    """

    name: str
    table: pd.DataFrame
    sql: str
    checks: list[Check] = field(default_factory=list)
    provenance: Provenance | None = None
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    totals: dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if not c.passed]

    def check(self) -> Account:
        """Raise :class:`CheckFailure` if any reconciliation identity is violated."""
        if self.failures:
            listed = "\n".join(f"  {c}" for c in self.failures)
            raise CheckFailure(f"{self.name}: {len(self.failures)} check(s) failed\n{listed}")
        return self

    def __repr__(self) -> str:
        shape = f"{len(self.table)} rows"
        state = "checks ok" if self.ok else f"{len(self.failures)} CHECKS FAILED"
        extra = f", tables={sorted(self.tables)}" if self.tables else ""
        return f"<Account {self.name!r} {shape}, {state}{extra}>"
