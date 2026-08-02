"""Shared fixtures.

Every account is compiled once per session against the checked-in SEEALand CSVs. The tests then
compare them, cell by cell, with the figures published in the SEEA EA annex and its
complementary workbook. Expected values are hard-coded on purpose: computing them from the
workbook's own derived sheets would test the parser, not the arithmetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import unseea

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "research" / "seealand-fixture"

#: SEEALand's single accounting period.
PERIOD = 2020


@pytest.fixture(scope="session")
def engine() -> unseea.Engine:
    return unseea.connect(fixture=FIXTURE_DIR)


@pytest.fixture(scope="session")
def eaa(engine: unseea.Engine) -> unseea.EAA:
    return engine.eaa()


@pytest.fixture(scope="session")
def extent(engine, eaa):
    return engine.extent_account(eaa, date=PERIOD)


@pytest.fixture(scope="session")
def change_matrix(engine, eaa):
    return engine.extent_change_matrix(eaa, PERIOD)


@pytest.fixture(scope="session")
def condition(engine, eaa):
    return engine.condition_account(eaa, date=PERIOD)


@pytest.fixture(scope="session")
def physical(engine, eaa):
    return engine.services_physical(eaa, date=PERIOD)


@pytest.fixture(scope="session")
def monetary(engine, eaa):
    return engine.services_monetary(eaa, date=PERIOD)


@pytest.fixture(scope="session")
def asset(engine, eaa):
    return engine.asset_account(eaa, PERIOD)


def cell(table, row_column: str, row: str, column: str) -> float:
    """One cell of a SEEA-shaped presentation table."""
    return float(table.loc[table[row_column] == row, column].iloc[0])
