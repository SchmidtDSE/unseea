"""Ecosystem extent account and ET change matrix (SEEA EA Ch. 4).

Both are derived from one table of ET transitions, which is what makes them incapable of
disagreeing: the change matrix's row sums *are* the opening extent and its column sums *are*
the closing extent.
"""

from __future__ import annotations

from typing import Any

from .. import sql as sqlfrag
from ..results import Account, Check
from ._common import TOTAL, build_provenance, guard_stratify, pivot_et


def _managed_predicate(parameters: Any) -> str:
    """SQL testing whether a transition is attributable to management.

    SEEA separates managed from unmanaged expansion and reduction because they mean different
    things to a decision maker: one is a choice, the other is something that happened. Land
    cover cannot tell them apart, so the attribution is a declared parameter — and an empty
    declaration means nothing is claimed as managed, not that everything is.
    """
    if not parameters.managed_transitions:
        return "false"
    pairs = " OR ".join(
        f"(et_from = {et_from!r} AND et_to = {et_to!r})"
        for et_from, et_to in parameters.managed_transitions
    )
    return f"({pairs})"


def _extent_sql(parameters: Any) -> str:
    managed = _managed_predicate(parameters)
    return (
        sqlfrag.with_clause(
            sqlfrag.EXTENT_CTE,
            f"""
transitions AS (
    SELECT *, {managed} AS managed FROM et_change WHERE et_from <> et_to
)
""",
            """
additions AS (
    SELECT et_to AS et,
           sum(CASE WHEN managed THEN area_ha ELSE 0.0 END)     AS managed,
           sum(CASE WHEN NOT managed THEN area_ha ELSE 0.0 END) AS unmanaged
    FROM transitions GROUP BY 1
)
""",
            """
reductions AS (
    SELECT et_from AS et,
           sum(CASE WHEN managed THEN area_ha ELSE 0.0 END)     AS managed,
           sum(CASE WHEN NOT managed THEN area_ha ELSE 0.0 END) AS unmanaged
    FROM transitions GROUP BY 1
)
""",
            """
account AS (
    SELECT e.et_id,
           e.et,
           e.opening_ha,
           coalesce(a.managed, 0.0)   AS managed_expansion,
           coalesce(a.unmanaged, 0.0) AS unmanaged_expansion,
           coalesce(r.managed, 0.0)   AS managed_reduction,
           coalesce(r.unmanaged, 0.0) AS unmanaged_reduction,
           e.closing_ha
    FROM extent e
    LEFT JOIN additions  a ON a.et = e.et
    LEFT JOIN reductions r ON r.et = e.et
)
""",
        )
        + """
SELECT * FROM (
    SELECT et_id, et, 1 AS entry_id, 'Opening extent' AS entry, opening_ha AS area_ha
    FROM account
    UNION ALL
    SELECT et_id, et, 2,             'Managed expansion',          managed_expansion   FROM account
    UNION ALL
    SELECT et_id, et, 3,             'Unmanaged expansion',        unmanaged_expansion FROM account
    UNION ALL
    SELECT et_id, et, 4,             'Managed reductions',         managed_reduction   FROM account
    UNION ALL
    SELECT et_id, et, 5,             'Unmanaged reductions',       unmanaged_reduction FROM account
    UNION ALL
    SELECT et_id, et, 6,             'Net change in extent',
           managed_expansion + unmanaged_expansion
           - managed_reduction - unmanaged_reduction FROM account
    UNION ALL
    SELECT et_id, et, 7,             'Closing extent',             closing_ha          FROM account
)
ORDER BY entry_id, et_id
"""
    )


_MATRIX_SQL = """
SELECT f.et_id  AS from_id,
       f.et     AS et_from,
       t.et_id  AS to_id,
       t.et     AS et_to,
       coalesce(sum(c.area_ha), 0.0) AS area_ha
FROM ecosystem_type f
CROSS JOIN ecosystem_type t
LEFT JOIN et_change c ON c.et_from = f.et AND c.et_to = t.et
GROUP BY 1, 2, 3, 4
ORDER BY from_id, to_id
"""


def extent_account(
    engine: Any,
    eaa: Any,
    date: Any,
    *,
    bindings: dict[str, Any] | None = None,
    parameters: Any = None,
    stratify_by: Any = None,
) -> Account:
    """Compile the ecosystem extent account for one accounting period.

    Args:
        engine: The engine holding the executor.
        eaa: Accounting-area handle from :meth:`unseea.Engine.eaa`.
        date: The accounting period.
        bindings: Layer bindings; unused by the fixture executor.
        parameters: Parameter set override. ``managed_transitions`` decides which off-diagonal
            transitions are recorded as managed rather than unmanaged.
        stratify_by: Additional grouping; not available on the fixture executor.

    Returns:
        An :class:`~unseea.results.Account` whose ``table`` is long
        (``et``, ``entry``, ``area_ha``) and whose ``tables["extent"]`` is the standard's
        layout, entries down and ETs across.
    """
    guard_stratify(stratify_by)
    params = parameters or engine.parameters
    period = engine.period(eaa, date)
    query = _extent_sql(params)
    sql = engine.executor.portable_sql(query)
    long = engine.executor.execute(query)

    wide = pivot_et(long, index=["entry_id", "entry"], values="area_ha")
    wide = wide.drop(columns="entry_id")

    return Account(
        name="extent_account",
        table=long[["et_id", "et", "entry_id", "entry", "area_ha"]],
        tables={"extent": wide},
        sql=sql,
        checks=_extent_checks(long, wide, eaa),
        provenance=build_provenance(
            account="extent_account",
            engine=engine,
            eaa=eaa,
            period=period,
            parameters=params,
            bindings=bindings,
        ),
        totals={
            "opening_ha": float(wide.loc[wide.entry == "Opening extent", TOTAL].iloc[0]),
            "closing_ha": float(wide.loc[wide.entry == "Closing extent", TOTAL].iloc[0]),
        },
    )


def _extent_checks(long: Any, wide: Any, eaa: Any) -> list[Check]:
    """opening + additions − reductions = closing, per ET; and total extent = EAA area."""
    pivot = long.pivot_table(index="et", columns="entry", values="area_ha", aggfunc="sum")
    checks: list[Check] = []
    for et, row in pivot.iterrows():
        residual = (
            row["Opening extent"]
            + row["Managed expansion"]
            + row["Unmanaged expansion"]
            - row["Managed reductions"]
            - row["Unmanaged reductions"]
            - row["Closing extent"]
        )
        checks.append(
            Check(
                name="opening + additions - reductions = closing",
                residual=float(residual),
                detail=et,
            )
        )
    for entry in ("Opening extent", "Closing extent"):
        total = float(wide.loc[wide.entry == entry, TOTAL].iloc[0])
        checks.append(
            Check(
                name="total extent = EAA area",
                residual=total - eaa.area_ha,
                detail=f"{entry} {total:g} ha vs EAA {eaa.area_ha:g} ha",
            )
        )
    return checks


def extent_change_matrix(
    engine: Any,
    eaa: Any,
    d0: Any = None,
    d1: Any = None,
    *,
    bindings: dict[str, Any] | None = None,
    parameters: Any = None,
    stratify_by: Any = None,
) -> Account:
    """Compile the ET change matrix: area moving from each ET to each other ET.

    Args:
        engine: The engine holding the executor.
        eaa: Accounting-area handle.
        d0: Opening date of the period.
        d1: Closing date. Defaults to the close of ``d0``'s accounting period.
        bindings: Layer bindings; unused by the fixture executor.
        parameters: Parameter set override.
        stratify_by: Additional grouping; not available on the fixture executor.

    Returns:
        An account whose ``table`` is long (``et_from``, ``et_to``, ``area_ha``) and whose
        ``tables["matrix"]`` is the from→to matrix with opening and closing margins.
    """
    guard_stratify(stratify_by)
    params = parameters or engine.parameters
    period = engine.period(eaa, d0, d1)
    sql = engine.executor.portable_sql(_MATRIX_SQL)
    long = engine.executor.execute(_MATRIX_SQL)

    matrix = long.pivot_table(
        index=["from_id", "et_from"], columns="et_to", values="area_ha", aggfunc="sum", sort=False
    )
    order = [et for et in long.sort_values("to_id").et_to.unique()]
    matrix = matrix.reindex(columns=order)
    matrix["Opening extent"] = matrix.sum(axis=1)
    matrix = matrix.reset_index().drop(columns="from_id")
    closing = {"et_from": "Closing extent", **matrix[order].sum().to_dict()}
    closing["Opening extent"] = matrix["Opening extent"].sum()
    matrix.loc[len(matrix)] = closing

    return Account(
        name="extent_change_matrix",
        table=long,
        tables={"matrix": matrix},
        sql=sql,
        checks=_matrix_checks(long, engine),
        provenance=build_provenance(
            account="extent_change_matrix",
            engine=engine,
            eaa=eaa,
            period=period,
            parameters=params,
            bindings=bindings,
        ),
    )


def _matrix_checks(long: Any, engine: Any) -> list[Check]:
    """Row sums = opening extent, column sums = closing extent."""
    extent = engine.executor.execute(
        sqlfrag.with_clause(sqlfrag.EXTENT_CTE) + "SELECT * FROM extent ORDER BY et_id"
    ).set_index("et")
    rows = long.groupby("et_from").area_ha.sum()
    columns = long.groupby("et_to").area_ha.sum()
    checks: list[Check] = []
    for et, expected in extent.opening_ha.items():
        checks.append(
            Check("change matrix row sums = opening extent", float(rows[et] - expected), detail=et)
        )
    for et, expected in extent.closing_ha.items():
        checks.append(
            Check(
                "change matrix column sums = closing extent",
                float(columns[et] - expected),
                detail=et,
            )
        )
    return checks
