"""Monetary ecosystem asset account (SEEA EA Ch. 10, decomposition per Annex 10.1).

Each ecosystem asset is valued as the net present value of its expected future service flows,
and the change in that value over the accounting period is decomposed into the entries a
finance ministry can act on: degradation, enhancement, conversions, reappraisals, revaluation.

The decomposition runs on the three-factor product ``NPV = p·q·a`` (price × service intensity
per hectare × area), split symmetrically so the three effects sum exactly to ΔNPV — see
:mod:`unseea.npv`. Two joins make it an *account* rather than an arithmetic exercise: area comes
from the extent account, and the sign of the condition index decides whether a fall in expected
flows is degradation of the asset or merely new information about it.

The account is compiled by two queries over the same CTEs — the per-service workings, and the
per-ET entries — and ``acct.sql`` returns both.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .. import npv as npvmod
from .. import sql as sqlfrag
from ..parameters import ParameterSet
from ..results import Account, Check
from ._common import TOTAL, build_provenance, guard_stratify, pivot_et


def _shared_ctes(parameters: ParameterSet) -> tuple[str, ...]:
    """The CTEs both asset-account queries are built on.

    Expected flows and prices give the NPV; extent gives area; the condition account gives the
    sign that classifies a volume effect.
    """
    factor = npvmod.annuity_factor_sql(parameters)
    life = float(parameters.asset_life)
    effects = ",\n           ".join(
        f"{expression} AS {name}" for name, expression in npvmod.EFFECT_SQL.items()
    )
    condition_signal = npvmod.condition_signal_sql(
        parameters, "coalesce(any_value(c.condition_change), 0.0)"
    )
    return (
        sqlfrag.EXTENT_CTE,
        *sqlfrag.CONDITION_CTES,
        sqlfrag.CONDITION_NET_CHANGE_CTE,
        f"""
expected AS (
    SELECT f.et,
           f.service_id,
           s.service,
           s.service_order,
           f.expected_opening AS es0,
           f.expected_closing AS es1,
           f.price_opening    AS unit_price_0,
           f.price_closing    AS unit_price_1,
           f.expected_opening * f.price_opening AS exchange_value_0,
           f.expected_closing * f.price_closing AS exchange_value_1,
           f.expected_opening * f.price_opening * {factor} AS npv0,
           f.expected_closing * f.price_closing * {factor} AS npv1
    FROM es_flow f
    JOIN service s ON s.service_id = f.service_id
    WHERE coalesce(f.expected_opening, 0) <> 0 OR coalesce(f.expected_closing, 0) <> 0
)
""",
        f"""
factors AS (
    SELECT e.*,
           x.opening_ha AS a0,
           x.closing_ha AS a1,
           e.es0 * {life} AS quantity_0,
           e.es1 * {life} AS quantity_1,
           e.es0 * {life} / nullif(x.opening_ha, 0) AS q0,
           e.es1 * {life} / nullif(x.closing_ha, 0) AS q1,
           -- Value per unit of expected quantity. Where a service starts or ends at zero there
           -- is no price on that side to compare, so the other period's price is carried
           -- across: the whole change is then a volume effect, not a phantom revaluation.
           coalesce(e.npv0 / nullif(e.es0 * {life}, 0),
                    e.npv1 / nullif(e.es1 * {life}, 0)) AS p0,
           coalesce(e.npv1 / nullif(e.es1 * {life}, 0),
                    e.npv0 / nullif(e.es0 * {life}, 0)) AS p1
    FROM expected e
    JOIN extent x ON x.et = e.et
)
""",
        f"""
decomposition AS (
    SELECT et, service_id, service, service_order,
           es0, es1, unit_price_0, unit_price_1, exchange_value_0, exchange_value_1,
           npv0, npv1, npv1 - npv0 AS npv_change,
           a0, a1, quantity_0, quantity_1, q0, q1, p0, p1,
           {effects}
    FROM factors
)
""",
        f"""
et_effects AS (
    SELECT t.et_id,
           d.et,
           sum(d.npv0)          AS npv0,
           sum(d.npv1)          AS npv1,
           sum(d.area_effect)   AS area_effect,
           sum(d.volume_effect) AS volume_effect,
           sum(d.price_effect)  AS price_effect,
           coalesce(any_value(c.condition_change), 0.0) AS condition_change,
           {condition_signal} AS condition_signal
    FROM decomposition d
    JOIN ecosystem_type t ON t.et = d.et
    LEFT JOIN condition_net_change c ON c.et = d.et
    GROUP BY 1, 2
)
""",
    )


def _detail_sql(parameters: ParameterSet) -> str:
    """Per-(ET, service) NPV and Annex 10.1 workings."""
    return (
        sqlfrag.with_clause(*_shared_ctes(parameters))
        + """
SELECT t.et_id,
       d.*,
       c.condition_change
FROM decomposition d
JOIN ecosystem_type t ON t.et = d.et
LEFT JOIN condition_net_change c ON c.et = d.et
ORDER BY t.et_id, d.service_order
"""
    )


def _entries_sql(parameters: ParameterSet) -> str:
    """Per-ET asset-account entries: each effect routed to the entry the standard assigns it."""
    classified = ",\n           ".join(
        f"{npvmod.entry_sql(entry)} AS {column}"
        for entry, column in npvmod.ENTRY_COLUMNS.items()
    )
    rows = [
        "SELECT et_id, et, 0 AS entry_id, 'Opening value' AS entry, npv0 AS value FROM entries"
    ]
    for entry in npvmod.MOVEMENT_ENTRIES:
        rows.append(
            f"SELECT et_id, et, {npvmod.ENTRY_ORDER.index(entry)}, {entry!r}, "
            f"{npvmod.ENTRY_COLUMNS[entry]} FROM entries"
        )
    rows.append(
        f"SELECT et_id, et, {npvmod.ENTRY_ORDER.index('Net change in value')}, "
        "'Net change in value', npv1 - npv0 FROM entries"
    )
    rows.append(
        f"SELECT et_id, et, {npvmod.ENTRY_ORDER.index('Closing value')}, "
        "'Closing value', npv1 FROM entries"
    )
    return (
        sqlfrag.with_clause(
            *_shared_ctes(parameters),
            f"""
entries AS (
    SELECT *,
           {classified}
    FROM et_effects
)
""",
        )
        + "\nUNION ALL\n".join(rows)
        + "\nORDER BY entry_id, et_id\n"
    )


def asset_account(
    engine: Any,
    eaa: Any,
    d0: Any = None,
    d1: Any = None,
    *,
    bindings: dict[str, Any] | None = None,
    parameters: Any = None,
    stratify_by: Any = None,
) -> Account:
    """Compile the monetary ecosystem asset account and its decomposition.

    Args:
        engine: The engine holding the executor.
        eaa: Accounting-area handle.
        d0: Opening date of the accounting period.
        d1: Closing date. Defaults to the close of ``d0``'s period.
        bindings: Layer bindings; unused by the fixture executor.
        parameters: Parameter set override. Asset life, discount rate and income timing decide
            every level in this account and must be stated with any result from it
            (`DESIGN.md` §5.2).
        stratify_by: Additional grouping; not available on the fixture executor.

    Returns:
        An account whose ``table`` is the long asset account (one row per ET and entry), with
        ``tables["asset"]`` in the standard's layout, ``tables["npv"]`` per ET and service, and
        ``tables["decomposition"]`` holding the area, volume and price effects behind it.
    """
    guard_stratify(stratify_by)
    params = parameters or engine.parameters
    period = engine.period(eaa, d0, d1)

    detail_query, entries_query = _detail_sql(params), _entries_sql(params)
    detail = engine.executor.execute(detail_query)
    long = engine.executor.execute(entries_query)

    wide = pivot_et(long, index=["entry_id", "entry"], values="value").drop(columns="entry_id")
    opening = float(long.loc[long.entry == "Opening value", "value"].sum())
    closing = float(long.loc[long.entry == "Closing value", "value"].sum())

    sql = engine.executor.portable_sql(
        "-- (1) NPV and the Annex 10.1 decomposition, per ecosystem type and service\n"
        f"{detail_query.strip()};\n\n"
        "-- (2) the monetary ecosystem asset account: effects routed to accounting entries\n"
        f"{entries_query.strip()};\n"
    )

    return Account(
        name="asset_account",
        table=long,
        tables={
            "asset": wide,
            "npv": _npv_table(detail),
            "decomposition": _decomposition_table(detail),
        },
        sql=sql,
        checks=_asset_checks(detail, long),
        totals={
            "opening_value": opening,
            "closing_value": closing,
            "net_change": closing - opening,
        },
        provenance=build_provenance(
            account="asset_account",
            engine=engine,
            eaa=eaa,
            period=period,
            parameters=params,
            bindings=bindings,
            ect_coverage=_coverage(engine),
            notes=[
                "Valuation assumptions: "
                + ", ".join(f"{k}={v}" for k, v in npvmod.describe(params).items())
                + ".",
                "A volume effect is recorded as degradation or enhancement only where the "
                "condition account moves the same way; otherwise it is a reappraisal.",
            ],
        ),
    )


def _npv_table(detail: pd.DataFrame) -> pd.DataFrame:
    """Expected flows, prices, exchange values and NPV per ET and service."""
    columns = [
        "et_id",
        "et",
        "service",
        "es0",
        "es1",
        "unit_price_0",
        "unit_price_1",
        "exchange_value_0",
        "exchange_value_1",
        "npv0",
        "npv1",
        "npv_change",
    ]
    return detail[columns].copy()


def _decomposition_table(detail: pd.DataFrame) -> pd.DataFrame:
    """The Annex 10.1 workings: the p, q and a factors, and the three effects."""
    columns = [
        "et_id",
        "et",
        "service",
        "a0",
        "a1",
        "p0",
        "p1",
        "q0",
        "q1",
        "quantity_0",
        "quantity_1",
        "area_effect",
        "volume_effect",
        "price_effect",
        "npv_change",
        "condition_change",
    ]
    table = detail[columns].copy()
    table["effects_total"] = table.area_effect + table.volume_effect + table.price_effect
    return table


def _coverage(engine: Any) -> dict[str, list[str]]:
    """ECT coverage of the condition account this asset account classified against."""
    coverage = engine.executor.execute(
        sqlfrag.with_clause(*sqlfrag.CONDITION_CTES)
        + "SELECT et, list(DISTINCT ect_code ORDER BY ect_code) AS codes "
        "FROM condition_index GROUP BY et"
    )
    return {row.et: list(row.codes) for _, row in coverage.iterrows()}


def _asset_checks(detail: pd.DataFrame, long: pd.DataFrame) -> list[Check]:
    """The two identities: entries reconcile the value, and the three effects reconcile ΔNPV."""
    checks: list[Check] = []
    entries = long.pivot_table(index="et", columns="entry", values="value", aggfunc="sum")
    for et, row in entries.iterrows():
        residual = (
            row["Opening value"]
            + sum(row[entry] for entry in npvmod.MOVEMENT_ENTRIES)
            - row["Closing value"]
        )
        checks.append(
            Check("opening value + all entries = closing value", float(residual), detail=et)
        )

    per_et = detail.groupby("et", sort=False)[
        ["area_effect", "volume_effect", "price_effect", "npv_change"]
    ].sum()
    for et, row in per_et.iterrows():
        residual = row.area_effect + row.volume_effect + row.price_effect - row.npv_change
        checks.append(
            Check(
                "area effect + volume effect + price effect = change in NPV",
                float(residual),
                detail=et,
            )
        )

    totals = long.groupby("entry").value.sum()
    residual = (
        totals["Opening value"]
        + sum(totals[entry] for entry in npvmod.MOVEMENT_ENTRIES)
        - totals["Closing value"]
    )
    checks.append(Check("asset account reconciles in total", float(residual), detail=TOTAL))
    return checks
