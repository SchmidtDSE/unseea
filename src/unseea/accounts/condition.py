"""Ecosystem condition account (SEEA EA Ch. 5): all three nested accounts.

The three stages answer different questions and the standard expects all three, so one call
returns all three rather than making the caller choose:

* **variables** — what was measured, in its own units.
* **indicators** — the same measurements rescaled to [0, 1] against reference levels.
* **index** — indicators weighted into ECT-class sub-indices and an overall index.

Two properties of this account are hazards rather than details, and both are surfaced rather
than hidden. Reference levels are a *choice* (`DESIGN.md` §5.3) and travel in provenance; and
ECT coverage silently reweights the index (§2.4), so it travels too.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .. import sql as sqlfrag
from ..results import Account, Check
from ..vocab import ECT_GROUPS
from ._common import build_provenance, guard_stratify, pivot_et

_CONDITION_SQL = sqlfrag.with_clause(*sqlfrag.CONDITION_CTES) + """
SELECT c.*, t.et_id
FROM condition_index c
JOIN ecosystem_type t ON t.et = c.et
ORDER BY t.et_id, c.ect_code, c.variable
"""

#: Rows of the per-ET condition indices summary (workbook sheet #8).
SUMMARY_ROWS: tuple[str, ...] = (
    "Opening condition value",
    "Change in abiotic ecosystem characteristics",
    "Change in biotic ecosystem characteristics",
    "Change in landscape/seascape level characteristics",
    "Net change in condition",
    "Closing condition value",
)


def condition_account(
    engine: Any,
    eaa: Any,
    date: Any,
    *,
    bindings: dict[str, Any] | None = None,
    parameters: Any = None,
    stratify_by: Any = None,
) -> Account:
    """Compile all three ecosystem condition accounts for one accounting period.

    Args:
        engine: The engine holding the executor.
        eaa: Accounting-area handle.
        date: The accounting period.
        bindings: Layer bindings; unused by the fixture executor.
        parameters: Parameter set override. ``reference_basis`` records, per ET, whether the
            reference condition is natural or anthropogenic — the two are not comparable, and
            SEEA forbids averaging condition across them.
        stratify_by: Additional grouping; not available on the fixture executor.

    Returns:
        An account whose ``table`` is the long index account (one row per ET and variable) and
        whose ``tables`` hold ``variables``, ``indicators``, ``index`` (with ECT-class and
        group subtotals) and ``summary``.
    """
    guard_stratify(stratify_by)
    params = parameters or engine.parameters
    period = engine.period(eaa, date)
    sql = engine.executor.portable_sql(_CONDITION_SQL)
    long = engine.executor.execute(_CONDITION_SQL)

    coverage = {
        et: sorted(group.ect_code.unique()) for et, group in long.groupby("et", sort=False)
    }
    notes = [
        "ECT coverage: "
        + "; ".join(f"{et} {len(codes)}/6 ({','.join(codes)})" for et, codes in coverage.items()),
        "Condition indices are not comparable across ETs with different ECT coverage, or "
        "across natural and anthropogenic reference bases.",
    ]

    return Account(
        name="condition_account",
        table=long,
        tables={
            "variables": _variables_table(long),
            "indicators": _indicators_table(long),
            "index": _index_table(long),
            "summary": _summary_table(long),
        },
        sql=sql,
        checks=_condition_checks(long),
        provenance=build_provenance(
            account="condition_account",
            engine=engine,
            eaa=eaa,
            period=period,
            parameters=params,
            bindings=bindings,
            ect_coverage=coverage,
            notes=notes,
        ),
    )


_KEYS = ["et_id", "et", "ect_code", "ect_group", "ect_class", "variable"]


def _variables_table(long: pd.DataFrame) -> pd.DataFrame:
    """Stage 1: observed values in their own units."""
    return long[[*_KEYS, "unit", "opening", "closing", "change"]].copy()


def _indicators_table(long: pd.DataFrame) -> pd.DataFrame:
    """Stage 2: rescaled to [0, 1] against the reference levels used."""
    columns = [
        *_KEYS,
        "unit",
        "opening",
        "closing",
        "lower_level",
        "upper_level",
        "indicator_opening",
        "indicator_closing",
        "indicator_change",
    ]
    return long[columns].copy()


def _index_table(long: pd.DataFrame) -> pd.DataFrame:
    """Stage 3: weighted contributions, with ECT-class and group subtotals per ET."""
    variables = long[
        [
            *_KEYS,
            "indicator_opening",
            "indicator_closing",
            "weight",
            "index_opening",
            "index_closing",
            "index_change",
        ]
    ].copy()
    variables["level"] = "variable"

    rows: list[pd.DataFrame] = []
    for level, keys, label in (
        ("class", ["et_id", "et", "ect_group", "ect_code", "ect_class"], "ect_class"),
        ("group", ["et_id", "et", "ect_group"], "ect_group"),
        ("total", ["et_id", "et"], None),
    ):
        block = (
            long.groupby(keys, sort=False)[
                ["weight", "index_opening", "index_closing", "index_change"]
            ]
            .sum()
            .reset_index()
        )
        block["level"] = level
        block["variable"] = (
            block[label].map(lambda name: f"Total {name}") if label else "Total condition index"
        )
        rows.append(block)

    combined = pd.concat([variables, *rows], ignore_index=True)
    combined["level_order"] = combined.level.map(
        {"variable": 0, "class": 1, "group": 2, "total": 3}
    )
    return combined.sort_values(["et_id", "level_order", "ect_group", "ect_code"]).reset_index(
        drop=True
    )


def _summary_table(long: pd.DataFrame) -> pd.DataFrame:
    """The condition indices account: opening, change by ECT group, net change, closing."""
    per_et = long.groupby(["et_id", "et"], sort=True)[["index_opening", "index_closing"]].sum()
    by_group = (
        long.groupby(["et", "ect_group"], sort=False).index_change.sum().unstack("ect_group")
    ).reindex(columns=ECT_GROUPS)

    rows: list[dict[str, Any]] = []
    for (et_id, et), values in per_et.iterrows():
        changes = by_group.loc[et].fillna(0.0)
        rows.extend(
            [
                {"et_id": et_id, "et": et, "row": SUMMARY_ROWS[0], "value": values.index_opening},
                {"et_id": et_id, "et": et, "row": SUMMARY_ROWS[1], "value": changes.iloc[0]},
                {"et_id": et_id, "et": et, "row": SUMMARY_ROWS[2], "value": changes.iloc[1]},
                {"et_id": et_id, "et": et, "row": SUMMARY_ROWS[3], "value": changes.iloc[2]},
                {
                    "et_id": et_id,
                    "et": et,
                    "row": SUMMARY_ROWS[4],
                    "value": values.index_closing - values.index_opening,
                },
                {"et_id": et_id, "et": et, "row": SUMMARY_ROWS[5], "value": values.index_closing},
            ]
        )

    summary = pd.DataFrame(rows)
    summary["row_id"] = summary.row.map({name: i for i, name in enumerate(SUMMARY_ROWS)})
    # No TOTAL column: averaging a condition index across ecosystem types would aggregate
    # across different reference conditions, which SEEA explicitly does not recommend.
    wide = pivot_et(summary, index=["row_id", "row"], values="value", total=False)
    return wide.drop(columns="row_id")


def _condition_checks(long: pd.DataFrame) -> list[Check]:
    """Weights sum to 1, indicators in [0, 1], and ECT-group changes sum to the net change."""
    checks: list[Check] = []
    for et, group in long.groupby("et", sort=False):
        checks.append(
            Check("condition weights sum to 1", float(group.weight.sum() - 1.0), detail=et)
        )
        net = float(group.index_closing.sum() - group.index_opening.sum())
        by_group = float(group.index_change.sum())
        checks.append(
            Check(
                "sum of ECT-group changes = net change in condition",
                by_group - net,
                detail=et,
            )
        )
        for bound, series in (
            ("opening", group.indicator_opening),
            ("closing", group.indicator_closing),
        ):
            excess = float(
                (series - series.clip(0.0, 1.0)).abs().sum()
            )
            checks.append(
                Check(f"indicator values in [0, 1] ({bound})", excess, detail=et)
            )
        index_total = float(group.index_closing.sum())
        checks.append(
            Check(
                "condition index in [0, 1] (closing)",
                max(0.0, index_total - 1.0) + max(0.0, -index_total),
                detail=et,
            )
        )
    return checks
