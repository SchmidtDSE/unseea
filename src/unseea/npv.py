"""Net present value, its decomposition, and the accounting entries it maps to.

This is the hardest computational piece in the standard (SEEA EA Ch. 10 and Annex 10.1), and
the reason Phase 1 exists: reproduce it against a published answer before real data arrives.

The change in an ecosystem asset's value is the change in a **three-factor product**

    NPV = p · q · a          price × volume (service intensity per hectare) × area

and SEEA asks for it split into an area effect, a volume effect and a price effect that sum
*exactly* to ΔNPV. The naive form ``p₀q₀(a₁−a₀)`` does not: it leaves a residual that has to be
pushed somewhere. The split used here is the **symmetric (Shapley) decomposition** — each
factor's effect is its change weighted by the average of the other factors over every order in
which the three changes could have been applied. For three factors that average is
``(x₀y₀ + x₁y₁)/3 + (x₀y₁ + x₁y₀)/6``, and the three effects sum to ΔNPV identically.

Every formula here is emitted as SQL text so that ``acct.sql`` contains the actual arithmetic
and there is one implementation rather than a SQL one and a Python one that drift.
"""

from __future__ import annotations

from typing import Any

import duckdb

from .parameters import ParameterSet

#: The p·q·a factors, as ``(opening column, closing column)`` pairs.
PRICE = ("p0", "p1")
VOLUME = ("q0", "q1")
AREA = ("a0", "a1")


def annuity_factor_sql(parameters: ParameterSet) -> str:
    """SQL for the present value of one unit of income per year over the asset life.

    SEEALand assumes income at period end, so the first year's income is discounted by a full
    year. ``income_timing="start"`` shifts the whole series forward one year.
    """
    n, r = parameters.asset_life, parameters.discount_rate
    factor = f"((1.0 - power(1.0 + {r!r}, -{n})) / {r!r})"
    return factor if parameters.income_timing == "end" else f"({factor} * (1.0 + {r!r}))"


def symmetric_effect_sql(
    factor: tuple[str, str],
    others: tuple[tuple[str, str], tuple[str, str]],
) -> str:
    """SQL for one factor's symmetric (Shapley) effect in a three-factor product.

    Args:
        factor: The ``(opening, closing)`` columns of the factor whose effect this is.
        others: The two remaining factors, as ``(opening, closing)`` column pairs.
    """
    f0, f1 = factor
    (x0, x1), (y0, y1) = others
    weighted = f"(({x0} * {y0} + {x1} * {y1}) / 3.0 + ({x0} * {y1} + {x1} * {y0}) / 6.0)"
    return f"(({f1} - {f0}) * {weighted})"


#: The three effects ΔNPV decomposes into, keyed by the accounting concept each drives.
EFFECT_SQL: dict[str, str] = {
    "area_effect": symmetric_effect_sql(AREA, (PRICE, VOLUME)),
    "volume_effect": symmetric_effect_sql(VOLUME, (PRICE, AREA)),
    "price_effect": symmetric_effect_sql(PRICE, (VOLUME, AREA)),
}


def decompose(
    *,
    p0: float,
    p1: float,
    q0: float,
    q1: float,
    a0: float,
    a1: float,
    connection: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, float]:
    """Decompose ΔNPV for a single ``p·q·a`` triple.

    Runs :data:`EFFECT_SQL`, so this is the same arithmetic the account SQL performs rather
    than a second implementation of it.

    Returns:
        ``area_effect``, ``volume_effect``, ``price_effect``, and their ``total``.
    """
    columns = ", ".join(f"{expression} AS {name}" for name, expression in EFFECT_SQL.items())
    # Cast explicitly: DuckDB reads a decimal literal as DECIMAL, which overflows on the
    # products this decomposition takes.
    factors = ", ".join(
        f"CAST({value!r} AS DOUBLE) AS {name}"
        for name, value in (("p0", p0), ("p1", p1), ("q0", q0), ("q1", q1), ("a0", a0), ("a1", a1))
    )
    con = connection or duckdb.connect(":memory:")
    row = con.execute(f"WITH f AS (SELECT {factors}) SELECT {columns} FROM f").fetchone()
    effects = dict(zip(EFFECT_SQL, row))
    effects["total"] = sum(effects.values())
    return effects


# --------------------------------------------------------------------------------------
# Effects to accounting entries (Annex 10.1)
# --------------------------------------------------------------------------------------

#: How each effect becomes an entry in the monetary ecosystem asset account.
#:
#: The volume effect is the interesting one: the *same* change in expected service intensity is
#: degradation or a reappraisal depending on whether the condition account agrees that the
#: ecosystem itself changed. A decline in expected flows with no measured decline in condition
#: is new information about the asset, not a loss of it.
#:
#: ``condition_signal`` is the ET's net change in condition index, zeroed where it falls within
#: ``ParameterSet.condition_change_tolerance`` — see :func:`condition_signal_sql`.
ENTRY_RULES: dict[str, str] = {
    "Ecosystem enhancement": "volume_effect > 0 AND condition_signal > 0",
    "Ecosystem degradation": "volume_effect < 0 AND condition_signal < 0",
    "Upward reappraisals": "volume_effect > 0 AND condition_signal <= 0",
    "Downwards reappraisals": "volume_effect < 0 AND condition_signal >= 0",
    "Ecosystem conversions: additions": "area_effect > 0",
    "Ecosystem conversions: reductions": "area_effect < 0",
    "Revaluations": "price_effect <> 0",
}

#: Which effect supplies the value for each entry.
ENTRY_SOURCE: dict[str, str] = {
    "Ecosystem enhancement": "volume_effect",
    "Ecosystem degradation": "volume_effect",
    "Upward reappraisals": "volume_effect",
    "Downwards reappraisals": "volume_effect",
    "Ecosystem conversions: additions": "area_effect",
    "Ecosystem conversions: reductions": "area_effect",
    "Revaluations": "price_effect",
}

#: SQL-safe column name for each entry.
ENTRY_COLUMNS: dict[str, str] = {
    "Ecosystem enhancement": "enhancement",
    "Ecosystem degradation": "degradation",
    "Upward reappraisals": "upward_reappraisal",
    "Downwards reappraisals": "downward_reappraisal",
    "Ecosystem conversions: additions": "conversion_additions",
    "Ecosystem conversions: reductions": "conversion_reductions",
    "Revaluations": "revaluation",
}

#: Asset account row order (SEEA EA Table 10.1).
ENTRY_ORDER: tuple[str, ...] = (
    "Opening value",
    "Ecosystem enhancement",
    "Ecosystem degradation",
    "Ecosystem conversions: additions",
    "Ecosystem conversions: reductions",
    "Upward reappraisals",
    "Downwards reappraisals",
    "Revaluations",
    "Net change in value",
    "Closing value",
)


def entry_sql(entry: str) -> str:
    """SQL for one asset-account entry, evaluated per ecosystem type.

    Classification is applied to the ET-level *total* of an effect, not service by service: an
    asset is degraded or enhanced as a whole, and SEEALand's workbook sums before classifying.
    """
    source, rule = ENTRY_SOURCE[entry], ENTRY_RULES[entry]
    return f"CASE WHEN {rule} THEN {source} ELSE 0.0 END"


def condition_signal_sql(parameters: ParameterSet, condition_change: str) -> str:
    """SQL for the condition change the entry rules are applied to.

    Applying the rules to the raw sign makes an arbitrarily small condition movement decide
    whether a large volume effect is degradation or a reappraisal. The tolerance is how much
    condition movement counts as evidence, and it is a parameter because it is a judgement:
    the default of 0 is the standard's rule as stated.
    """
    tolerance = float(parameters.condition_change_tolerance)
    if tolerance == 0.0:
        return condition_change
    return (
        f"(CASE WHEN abs({condition_change}) <= {tolerance!r} "
        f"THEN 0.0 ELSE {condition_change} END)"
    )


#: The entries that move value between opening and closing, in row order.
MOVEMENT_ENTRIES: tuple[str, ...] = tuple(e for e in ENTRY_ORDER if e in ENTRY_SOURCE)


def describe(parameters: ParameterSet) -> dict[str, Any]:
    """The valuation assumptions, for provenance and for stating before any result."""
    return {
        "asset_life_years": parameters.asset_life,
        "discount_rate": parameters.discount_rate,
        "income_timing": parameters.income_timing,
        "annuity_factor": parameters.annuity_factor(),
        "condition_change_tolerance": parameters.condition_change_tolerance,
        "decomposition": "symmetric (Shapley) three-factor split of price x volume x area",
    }
