"""The engine: ``connect()``, the accounting-area handle, and the nine calls.

The API is small because SEEA fixed the surface — five accounts, fixed table shapes — not
because the design is clever. Its narrowness is a real constraint, and the two deliberate
escapes are ``stratify_by=`` on every account call and the platform's general ``query`` tool for
anything outside the accounts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .accounts import asset as asset_mod
from .accounts import condition as condition_mod
from .accounts import extent as extent_mod
from .accounts import services as services_mod
from .executors import FixtureExecutor, LocalDuckDBExecutor, MCPExecutor
from .parameters import SEEALAND, ParameterSet
from .results import Account


@dataclass(frozen=True)
class EAA:
    """An ecosystem accounting area.

    Attributes:
        name: How the area is referred to in provenance and reports.
        area_ha: Total area, used by the extent account's "total = EAA area" check.
        periods: Accounting periods the executor can compile.
        selectors: How the area was delimited, carried into provenance.
    """

    name: str
    area_ha: float
    periods: tuple[int, ...] = ()
    selectors: dict[str, Any] = field(default_factory=dict)


class Engine:
    """An account compiler bound to an executor.

    Every account call takes the same three optional arguments — ``bindings`` (which layers),
    ``parameters`` (under what assumptions) and ``stratify_by`` (grouped how) — and returns an
    :class:`~unseea.results.Account` carrying the table, the SQL, the checks and the provenance.
    """

    def __init__(self, executor: Any, parameters: ParameterSet = SEEALAND) -> None:
        self.executor = executor
        self.parameters = parameters

    def __repr__(self) -> str:
        return (
            f"<unseea.Engine executor={self.executor.name!r} "
            f"parameters={self.parameters.label!r}>"
        )

    # -- accounting area and period ------------------------------------------------------

    def eaa(self, **selectors: Any) -> EAA:
        """Delimit an ecosystem accounting area.

        Real executors accept ``country=``, ``basin=``, ``admin=``, ``hex=`` or ``geojson=``.
        The fixture holds exactly one accounting area, SEEALand, so it takes no selectors.
        """
        described = self.executor.describe()
        if "eaa" not in described:
            raise NotImplementedError(
                f"the {self.executor.name} executor cannot delimit an accounting area yet"
            )
        if selectors:
            raise ValueError(
                f"the {self.executor.name} executor has one accounting area "
                f"({described['eaa']}); it does not accept {sorted(selectors)}"
            )
        extent = self.executor.execute(
            "SELECT sum(area_ha) AS area_ha FROM et_change"
        )
        return EAA(
            name=described["eaa"],
            area_ha=float(extent.area_ha.iloc[0]),
            periods=tuple(getattr(self.executor, "periods", ())),
            selectors=dict(selectors),
        )

    def period(self, eaa: EAA, d0: Any = None, d1: Any = None) -> str:
        """Normalise an accounting period, rejecting one the executor cannot compile.

        A period the data does not cover is a silent wrong answer waiting to happen, so it is
        an error rather than an empty account.
        """
        available = eaa.periods
        requested = d0 if d0 is not None else (available[0] if available else None)
        if requested is None:
            raise ValueError("an accounting period is required")
        year = int(str(requested)[:4])
        if available and year not in available:
            raise ValueError(
                f"{eaa.name} covers {', '.join(str(p) for p in available)}; asked for {requested}"
            )
        if d1 is not None and int(str(d1)[:4]) != year:
            raise ValueError(
                f"multi-period accounts are not supported: {d0} to {d1}. Compile one period "
                "at a time and chain them."
            )
        return f"{year} (1 January - 31 December {year})"

    # -- the accounts --------------------------------------------------------------------

    def extent_account(self, eaa: EAA, date: Any = None, **options: Any) -> Account:
        """Area per ET, with additions, reductions and closing extent (Ch. 4)."""
        return extent_mod.extent_account(self, eaa, date, **options)

    def extent_change_matrix(
        self, eaa: EAA, d0: Any = None, d1: Any = None, **options: Any
    ) -> Account:
        """The from→to matrix of ET area over the period (Ch. 4)."""
        return extent_mod.extent_change_matrix(self, eaa, d0, d1, **options)

    def condition_account(self, eaa: EAA, date: Any = None, **options: Any) -> Account:
        """All three condition accounts: variables, indicators, index (Ch. 5)."""
        return condition_mod.condition_account(self, eaa, date, **options)

    def landscape_metric(self, eaa: EAA, variable: str, k: int = 1, **options: Any) -> Account:
        """Condition ECT class C1 metrics over an h3 k-ring.

        Fragmentation, connectivity and forest-area density are computed from hex
        neighbourhoods, which the fixture has none of — SEEALand supplies forest area density as
        a given variable. Needs a real-data executor (issue #7).
        """
        raise NotImplementedError(
            "landscape_metric needs an h3 executor; the fixture has no spatial neighbourhood "
            "(see https://github.com/SchmidtDSE/unseea/issues/7)"
        )

    def services_physical(self, eaa: EAA, date: Any = None, **options: Any) -> Account:
        """Ecosystem services supply and use in physical terms (Ch. 6–7)."""
        return services_mod.services_physical(self, eaa, date, **options)

    def services_monetary(
        self, eaa: EAA, date: Any = None, prices: dict[str, float] | None = None, **options: Any
    ) -> Account:
        """Monetary supply and use, and gross ecosystem product (Ch. 9)."""
        return services_mod.services_monetary(self, eaa, date, prices, **options)

    def asset_account(self, eaa: EAA, d0: Any = None, d1: Any = None, **options: Any) -> Account:
        """NPV per ET and the area/volume/price decomposition of its change (Ch. 10)."""
        return asset_mod.asset_account(self, eaa, d0, d1, **options)


def connect(
    *,
    fixture: str | Path | None = None,
    local: bool = False,
    mcp: str | None = None,
    parameters: ParameterSet | None = None,
    **options: Any,
) -> Engine:
    """Bind an engine to an executor.

    Exactly one runtime must be chosen:

    * ``fixture=path`` — the SEEALand CSVs in DuckDB, no network. The conformance tier.
    * ``local=True`` — DuckDB against the NRP catalog or the source.coop mirror (issue #4).
    * ``mcp=url`` — the deployed ``mcp-data-server`` (issue #29).

    Args:
        fixture: Directory of fixture CSVs, e.g. ``research/seealand-fixture/``.
        local: Use a local DuckDB executor.
        mcp: URL of an MCP endpoint.
        parameters: Default parameter set for accounts compiled by this engine. Defaults to
            SEEALand's assumptions when connecting to the fixture.
        **options: Passed to the executor.

    Returns:
        An :class:`Engine`.
    """
    runtimes = (("fixture", fixture), ("local", local), ("mcp", mcp))
    chosen = [name for name, value in runtimes if value]
    if len(chosen) != 1:
        raise ValueError(
            "choose exactly one executor: connect(fixture=...), connect(local=True) or "
            f"connect(mcp=url); got {chosen or 'none'}"
        )

    if fixture:
        params = parameters or SEEALAND
        return Engine(FixtureExecutor(fixture, **options), params)
    if mcp:
        return Engine(MCPExecutor(mcp, **options), parameters or SEEALAND)
    return Engine(LocalDuckDBExecutor(**options), parameters or SEEALAND)
