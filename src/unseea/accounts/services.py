"""Ecosystem services supply-and-use accounts (SEEA EA Ch. 6–7 physical, Ch. 9 monetary).

One shape, two units: the physical account records service flows in their own units, the
monetary account records the same flows at exchange values. Both must balance service by
service — total supply equals total use — which is the account's own audit.

Gross ecosystem product is the headline: total supply of *final* ecosystem services, net of
intermediate services supplied from one ecosystem asset to another.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ..parameters import ParameterSet
from ..results import Account, Check
from ..vocab import ECOSYSTEM_TYPES, SERVICE_SECTIONS, USER_KINDS
from ._common import build_provenance, guard_stratify

_LONG_COLUMNS = [
    "block",
    "section_id",
    "section",
    "service_order",
    "service_id",
    "service",
    "unit",
    "counterparty",
    "counterparty_kind",
    "flow",
    "price",
    "value",
]


def _price_expression(parameters: ParameterSet, price: str, service_id: str) -> str:
    """Price to value flows at: the parameter set's override, else the observed price.

    Overriding a price is a legitimate account choice — a national carbon price, a sensitivity
    run — so it belongs in the parameter set and in provenance, not in a patched input table.
    """
    if not parameters.prices:
        return price
    branches = " ".join(
        f"WHEN {key!r} THEN {float(value)!r}" for key, value in sorted(parameters.prices.items())
    )
    return f"(CASE {service_id} {branches} ELSE {price} END)"


def _sut_sql(parameters: ParameterSet, *, monetary: bool) -> str:
    """Build the supply-and-use query.

    The supply side is per ecosystem asset (the ET that generated the service); the use side is
    per economic unit. Both are returned in one long table with a ``block`` column so a reader
    can see the balance the account asserts.
    """
    supply_price = _price_expression(parameters, "f.price_actual", "f.service_id")
    use_price = _price_expression(parameters, "u.price", "u.service_id")
    value = "flow * price" if monetary else "NULL"
    return f"""
WITH supply AS (
    SELECT 'supply'      AS block,
           s.section_id,
           s.section,
           s.service_order,
           f.service_id,
           s.service,
           s.unit,
           f.et          AS counterparty,
           'ecosystem asset' AS counterparty_kind,
           f.actual_flow AS flow,
           {supply_price} AS price
    FROM es_flow f
    JOIN service s ON s.service_id = f.service_id
    WHERE f.actual_flow IS NOT NULL
),
use_side AS (
    SELECT 'use'         AS block,
           s.section_id,
           s.section,
           s.service_order,
           u.service_id,
           s.service,
           s.unit,
           u.user        AS counterparty,
           u.use_kind    AS counterparty_kind,
           u.quantity    AS flow,
           {use_price}   AS price
    FROM es_use u
    JOIN service s ON s.service_id = u.service_id
),
sut AS (SELECT * FROM supply UNION ALL SELECT * FROM use_side)
SELECT block, section_id, section, service_order, service_id, service, unit,
       counterparty, counterparty_kind, flow, price, {value} AS value
FROM sut
ORDER BY block DESC, section_id, service_order, counterparty
"""


def _counterparty_order(part: pd.DataFrame) -> list[str]:
    """Columns in the standard's order: ecosystem assets by ET, economic units by institution."""
    present = set(part.counterparty)
    ordered = [*ECOSYSTEM_TYPES, *USER_KINDS]
    return [name for name in ordered if name in present] + sorted(present.difference(ordered))


def _tables(long: pd.DataFrame, column: str) -> dict[str, pd.DataFrame]:
    """Supply and use tables in the standard's layout: services down, counterparties across."""
    tables: dict[str, pd.DataFrame] = {}
    for block in ("supply", "use"):
        part = long[long.block == block]
        wide = part.pivot_table(
            index=["section_id", "section", "service_order", "service", "unit"],
            columns="counterparty",
            values=column,
            aggfunc="sum",
            sort=False,
        )
        wide = wide.reindex(columns=_counterparty_order(part))
        wide[f"TOTAL {block.upper()}"] = wide.sum(axis=1)
        table = wide.reset_index().drop(columns=["section_id", "service_order"])
        totals = {
            "section": "TOTAL",
            "service": "",
            "unit": "",
            **{c: table[c].sum() for c in table.columns if c not in ("section", "service", "unit")},
        }
        if column == "value":
            table.loc[len(table)] = totals
        tables[block] = table
    return tables


def _balance_checks(long: pd.DataFrame, column: str) -> list[Check]:
    """Total supply = total use, service by service."""
    supply = long[long.block == "supply"].groupby("service")[column].sum()
    use = long[long.block == "use"].groupby("service")[column].sum()
    services = sorted(set(supply.index) | set(use.index))
    return [
        Check(
            "total supply = total use",
            float(supply.get(service, 0.0) - use.get(service, 0.0)),
            detail=service,
        )
        for service in services
    ]


def services_physical(
    engine: Any,
    eaa: Any,
    date: Any,
    *,
    bindings: dict[str, Any] | None = None,
    parameters: Any = None,
    stratify_by: Any = None,
) -> Account:
    """Compile the ecosystem services supply-and-use account in physical terms.

    Args:
        engine: The engine holding the executor.
        eaa: Accounting-area handle.
        date: The accounting period.
        bindings: Layer bindings; unused by the fixture executor.
        parameters: Parameter set override.
        stratify_by: Additional grouping; not available on the fixture executor.

    Returns:
        An account whose ``table`` is long (supply and use rows) and whose ``tables`` hold the
        ``supply`` and ``use`` tables in the standard's layout.
    """
    guard_stratify(stratify_by)
    params = parameters or engine.parameters
    period = engine.period(eaa, date)
    query = _sut_sql(params, monetary=False)
    long = engine.executor.execute(query)

    return Account(
        name="services_physical",
        table=long[_LONG_COLUMNS],
        tables=_tables(long, "flow"),
        sql=engine.executor.portable_sql(query),
        checks=_balance_checks(long, "flow"),
        provenance=build_provenance(
            account="services_physical",
            engine=engine,
            eaa=eaa,
            period=period,
            parameters=params,
            bindings=bindings,
        ),
    )


def services_monetary(
    engine: Any,
    eaa: Any,
    date: Any,
    prices: dict[str, float] | None = None,
    *,
    bindings: dict[str, Any] | None = None,
    parameters: Any = None,
    stratify_by: Any = None,
) -> Account:
    """Compile the monetary supply-and-use account and gross ecosystem product.

    Args:
        engine: The engine holding the executor.
        eaa: Accounting-area handle.
        date: The accounting period.
        prices: Per-service exchange-value overrides, ``{service_id: price}``. Recorded in
            provenance, since a reported GEP is meaningless without the prices behind it.
        bindings: Layer bindings; unused by the fixture executor.
        parameters: Parameter set override.
        stratify_by: Additional grouping; not available on the fixture executor.

    Returns:
        An account with ``totals["GEP"]``, plus the monetary ``supply`` and ``use`` tables.
    """
    guard_stratify(stratify_by)
    params = parameters or engine.parameters
    if prices:
        params = params.with_(prices={**params.prices, **prices})
    period = engine.period(eaa, date)
    query = _sut_sql(params, monetary=True)
    long = engine.executor.execute(query)

    supply = long[long.block == "supply"]
    # Intermediate services -- one ecosystem asset supplying another -- are netted off GEP.
    # The fixture has none to net (see the provenance note below), so this is zero rather than
    # absent: the subtraction is the definition, and a real compilation will fill it.
    intermediate = 0.0
    gep = float(supply.value.sum() - intermediate)

    checks = _balance_checks(long, "value")
    checks.append(
        Check(
            "GEP = total supply of final services",
            gep - float(long[long.block == "use"].value.sum()),
            detail=f"GEP {gep:,.2f}",
        )
    )

    return Account(
        name="services_monetary",
        table=long[_LONG_COLUMNS],
        tables=_tables(long, "value"),
        sql=engine.executor.portable_sql(query),
        checks=checks,
        totals={"GEP": gep},
        provenance=build_provenance(
            account="services_monetary",
            engine=engine,
            eaa=eaa,
            period=period,
            parameters=params,
            bindings=bindings,
            notes=[
                "GEP is total supply of final ecosystem services. SEEALand records no "
                "intermediate service flows between ecosystem assets, so nothing is netted "
                "off here; a compilation that does have them needs an ecosystem-asset use "
                "side (see https://github.com/SchmidtDSE/unseea/issues/8).",
                f"Sections priced: {', '.join(SERVICE_SECTIONS)}.",
            ],
        ),
    )
