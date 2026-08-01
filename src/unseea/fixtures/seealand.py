"""Read the SEEALand workbook CSVs into tidy account-ready tables.

The fixture ships as per-sheet CSV dumps of the official complementary spreadsheet
(``research/seealand-fixture/``), which are spreadsheet *layouts*: merged headers, repeated
blocks, values indented by position. This module turns four of those sheets into the tidy
tables the account SQL runs against.

**Only input sheets are read.** ``change-matrix``, ``condition-stage-1`` (observed values),
``condition-stage-2`` (reference levels) and ``es-flows`` (physical flows and prices) are
account-ready data. Everything else in the workbook — indicators, indices, the supply-and-use
tables, NPV, the decomposition, the asset account — is *derived*, and is what the library
computes. Reading a derived sheet and calling the comparison a test would be circular, so the
derived sheets appear only in ``tests/`` as expected values.

Two sheets record an ET's name differently and the service names vary across sheets; both are
canonicalised through :mod:`unseea.vocab`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .. import vocab

#: Sheets this module reads, and what each supplies.
INPUT_SHEETS: dict[str, str] = {
    "change-matrix.csv": "ET transitions (opening and closing extent are derived from these)",
    "condition-stage-1.csv": "observed condition variable values, by ET and ECT class",
    "condition-stage-2.csv": "condition reference levels (lower, upper)",
    "es-flows.csv": "actual and expected ecosystem service flows, prices, and use by sector",
}

_ECT_GROUP_NAMES = set(vocab.ECT_GROUPS)
_ECT_CLASS_NAMES = {c.name for c in vocab.ECT_CLASSES}


def _read(path: Path) -> pd.DataFrame:
    """Read a sheet dump as a positional grid of stripped strings."""
    frame = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    return frame.map(lambda cell: " ".join(str(cell).split()).strip())


def _cell(row: pd.Series, index: int) -> str:
    return row.iloc[index] if index < len(row) else ""


def _number(text: str) -> float | None:
    """Parse a spreadsheet cell as a number, or return None for a blank."""
    text = text.replace(",", "").replace("$", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _as_et(text: str) -> str | None:
    try:
        return vocab.canonical_et(text)
    except KeyError:
        return None


# --------------------------------------------------------------------------------------
# Sheet #3 — ET change matrix
# --------------------------------------------------------------------------------------


def read_change_matrix(path: Path) -> pd.DataFrame:
    """Return one row per ET transition: ``et_from, et_to, area_ha``.

    The matrix carries area only. Whether an off-diagonal transition was *managed* is a
    judgement about land use rather than a number in the matrix, so it is applied when the
    extent account is compiled, from the parameter set — not baked in here.
    """
    grid = _read(path)

    header = next(
        (i for i, row in grid.iterrows() if _cell(row, 2) == "Ecosystem types"),
        None,
    )
    if header is None:
        raise ValueError(f"{path.name}: no 'Ecosystem types' header row")

    columns: dict[int, str] = {}
    for j in range(3, grid.shape[1]):
        et = _as_et(_cell(grid.iloc[header], j))
        if et:
            columns[j] = et

    rows: list[dict[str, object]] = []
    for i in range(header + 1, len(grid)):
        row = grid.iloc[i]
        et_from = _as_et(_cell(row, 2))
        if not et_from:
            continue
        for j, et_to in columns.items():
            area = _number(_cell(row, j))
            if area is None or area == 0:
                continue
            rows.append({"et_from": et_from, "et_to": et_to, "area_ha": area})

    if not rows:
        raise ValueError(f"{path.name}: no transitions parsed")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# Sheets #4 and #5 — condition variables and reference levels
# --------------------------------------------------------------------------------------


def _read_condition_blocks(path: Path, value_columns: dict[str, int]) -> pd.DataFrame:
    """Walk the per-ET blocks of a condition sheet.

    Both condition sheets share a layout: an ET name alone in column 0 opens a block, then
    variable rows carry the ECT group in column 1 (only on its first row), the ECT class in
    column 2 (likewise), the variable descriptor in column 3 and the unit in column 4.
    ``value_columns`` names the numeric columns to extract beyond that.

    A row whose descriptor is present but whose observed values are blank is a *declared
    absence* — SEEALand's urban area has no functional-state variable — and is skipped, which
    is what gives its five remaining ECT classes a weight of 0.20 each rather than 0.167.
    """
    grid = _read(path)
    rows: list[dict[str, object]] = []
    et: str | None = None
    group: str | None = None
    class_name: str | None = None

    for _, row in grid.iterrows():
        block_et = _as_et(_cell(row, 0))
        if block_et:
            et, group, class_name = block_et, None, None
            continue
        if et is None:
            continue

        if _cell(row, 1) in _ECT_GROUP_NAMES:
            group = _cell(row, 1)
            class_name = None
        if _cell(row, 2) in _ECT_CLASS_NAMES:
            class_name = _cell(row, 2)

        descriptor = _cell(row, 3)
        if not descriptor or group is None:
            continue
        values = {name: _number(_cell(row, j)) for name, j in value_columns.items()}
        if any(value is None for value in values.values()):
            continue

        ect = vocab.ect_class(group, class_name)
        rows.append(
            {
                "et": et,
                "ect_code": ect.code,
                "ect_group": ect.group,
                "ect_class": ect.name,
                "variable": descriptor,
                "unit": _cell(row, 4),
                **values,
            }
        )

    if not rows:
        raise ValueError(f"{path.name}: no condition variables parsed")
    return pd.DataFrame(rows)


def read_condition_variables(path: Path) -> pd.DataFrame:
    """Return observed condition variable values: the stage 1 (variable) account inputs."""
    return _read_condition_blocks(path, {"opening": 5, "closing": 6})


def read_condition_references(path: Path) -> pd.DataFrame:
    """Return the lower and upper reference levels each variable is rescaled against.

    The upper level may be numerically *below* the lower one where a variable is bad when high
    (nitrogen concentration, turbidity). That is not an error to be sorted: the rescaling is
    linear in both bounds, so the orientation is carried by the bounds themselves.
    """
    frame = _read_condition_blocks(
        path,
        {"opening": 5, "closing": 6, "lower_level": 7, "upper_level": 8},
    )
    return frame[["et", "variable", "lower_level", "upper_level"]].copy()


# --------------------------------------------------------------------------------------
# Sheet #9 — ecosystem service flows, prices, and use
# --------------------------------------------------------------------------------------

_FLOW_KINDS = {
    "actual flows": "actual",
    "opening": "expected_opening",
    "closing": "expected_closing",
}


def _service_columns(grid: pd.DataFrame) -> tuple[dict[int, str], dict[int, str]]:
    """Locate the physical-flow and price column blocks on the ES flows sheet.

    The sheet repeats the same six service names three times across the row — physical flows,
    prices, then exchange values. Exchange values are a product of the first two, so only the
    first two blocks are read.
    """
    header = None
    for i, row in grid.iterrows():
        labels = [j for j in range(grid.shape[1]) if _cell(row, j)]
        if len(labels) >= 12 and _cell(row, labels[0]).lower().startswith("wood"):
            header = i
            break
    if header is None:
        raise ValueError("ES flows: no service-name header row")

    positions = [j for j in range(grid.shape[1]) if _cell(grid.iloc[header], j)]
    services = [vocab.canonical_service(_cell(grid.iloc[header], j)).id for j in positions]
    n = len(set(services))
    physical = dict(zip(positions[:n], services[:n]))
    prices = dict(zip(positions[n : 2 * n], services[n : 2 * n]))
    return physical, prices


def read_es_flows(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(es_flow, es_use)``.

    ``es_flow`` is one row per supplying (ET, service): the actual flow of the accounting
    period, the expected flows underlying the opening and closing NPV, and the price attached
    to each. ``es_use`` is one row per (service, economic unit) on the use side.
    """
    grid = _read(path)
    physical, prices = _service_columns(grid)

    flows: dict[tuple[str, str], dict[str, object]] = {}
    uses: list[dict[str, object]] = []
    et: str | None = None
    in_users = False

    for _, row in grid.iterrows():
        label, kind_cell = _cell(row, 1), _cell(row, 2)

        if label == "Users":
            in_users, et = True, None
            continue
        if label == "Total":
            et = None
            continue

        if in_users:
            if label not in vocab.USER_KINDS:
                continue
            for j, service_id in physical.items():
                quantity = _number(_cell(row, j))
                if quantity is None:
                    continue
                price_column = next(k for k, s in prices.items() if s == service_id)
                uses.append(
                    {
                        "service_id": service_id,
                        "user": label,
                        "use_kind": vocab.USER_KINDS[label],
                        "quantity": quantity,
                        "price": _number(_cell(row, price_column)),
                    }
                )
            continue

        block_et = _as_et(label)
        if block_et:
            et = block_et
        if et is None:
            continue

        kind = _FLOW_KINDS.get(kind_cell.lower())
        if kind is None:
            continue

        for j, service_id in physical.items():
            quantity = _number(_cell(row, j))
            if quantity is None:
                continue
            price_column = next(k for k, s in prices.items() if s == service_id)
            record = flows.setdefault(
                (et, service_id),
                {
                    "et": et,
                    "service_id": service_id,
                    "unit": vocab.SERVICE_BY_ID[service_id].unit,
                    "actual_flow": None,
                    "expected_opening": None,
                    "expected_closing": None,
                    "price_actual": None,
                    "price_opening": None,
                    "price_closing": None,
                },
            )
            flow_key, price_key = {
                "actual": ("actual_flow", "price_actual"),
                "expected_opening": ("expected_opening", "price_opening"),
                "expected_closing": ("expected_closing", "price_closing"),
            }[kind]
            record[flow_key] = quantity
            record[price_key] = _number(_cell(row, price_column))

    if not flows:
        raise ValueError(f"{path.name}: no ecosystem service flows parsed")
    return pd.DataFrame(list(flows.values())), pd.DataFrame(uses)


# --------------------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------------------


def ecosystem_type_table() -> pd.DataFrame:
    """The ET partition, in presentation order."""
    return pd.DataFrame(
        {"et_id": range(1, len(vocab.ECOSYSTEM_TYPES) + 1), "et": list(vocab.ECOSYSTEM_TYPES)}
    )


def service_table() -> pd.DataFrame:
    """The selected ecosystem services, in reference-list order."""
    return pd.DataFrame(
        [
            {
                "service_id": s.id,
                "service": s.label,
                "section": s.section,
                "section_id": vocab.SERVICE_SECTIONS.index(s.section),
                "unit": s.unit,
                "service_order": i,
            }
            for i, s in enumerate(vocab.SERVICES)
        ]
    )


def load(path: str | Path) -> dict[str, pd.DataFrame]:
    """Load the SEEALand fixture as tidy tables keyed by table name.

    Args:
        path: Directory holding the per-sheet CSVs (``research/seealand-fixture/``).

    Returns:
        ``ecosystem_type``, ``et_change``, ``condition_variable``, ``condition_reference``,
        ``es_flow``, ``es_use``, ``service``.
    """
    root = Path(path)
    missing = [name for name in INPUT_SHEETS if not (root / name).exists()]
    if missing:
        raise FileNotFoundError(f"{root}: missing fixture sheets {missing}")

    condition_variable = read_condition_variables(root / "condition-stage-1.csv")
    condition_reference = read_condition_references(root / "condition-stage-2.csv")
    _assert_sheets_agree(root, condition_variable)

    es_flow, es_use = read_es_flows(root / "es-flows.csv")
    return {
        "ecosystem_type": ecosystem_type_table(),
        "et_change": read_change_matrix(root / "change-matrix.csv"),
        "condition_variable": condition_variable,
        "condition_reference": condition_reference,
        "es_flow": es_flow,
        "es_use": es_use,
        "service": service_table(),
    }


def _assert_sheets_agree(root: Path, condition_variable: pd.DataFrame) -> None:
    """Fail loudly if the two condition sheets disagree on an observed value.

    Stages 1 and 2 of the condition account restate the same observations. They agree in the
    published workbook; if a future re-export of the CSVs breaks that, the reference levels
    have been joined to the wrong variable and every downstream index is wrong.
    """
    restated = _read_condition_blocks(
        root / "condition-stage-2.csv",
        {"opening": 5, "closing": 6, "lower_level": 7, "upper_level": 8},
    )
    keys = ["et", "variable"]
    merged = condition_variable.merge(restated, on=keys, suffixes=("", "_stage2"))
    if len(merged) != len(condition_variable):
        raise ValueError(
            "condition sheets do not cover the same variables: "
            f"{len(condition_variable)} in stage 1, {len(merged)} matched in stage 2"
        )
    for column in ("opening", "closing"):
        delta = (merged[column] - merged[f"{column}_stage2"]).abs()
        if (delta > 1e-9).any():
            bad = merged.loc[delta > 1e-9, keys + [column, f"{column}_stage2"]]
            raise ValueError(f"condition sheets disagree on observed values:\n{bad}")


def register(connection, path: str | Path) -> dict[str, pd.DataFrame]:
    """Register the fixture's tidy tables on a DuckDB connection.

    This is the counterpart to ``acct.sql``: it makes any SQL the fixture executor returns
    re-runnable in a bare DuckDB session, the way the local and MCP executors' ``s3://``
    rewriting does for real data.
    """
    tables = load(path)
    for name, frame in tables.items():
        connection.register(f"_unseea_{name}", frame)
        connection.execute(f"CREATE OR REPLACE TEMP VIEW {name} AS SELECT * FROM _unseea_{name}")
    return tables
