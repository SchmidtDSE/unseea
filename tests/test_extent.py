"""Extent account and change matrix against SEEALand (SEEA EA Ch. 4).

Expected values: workbook sheets #2 (extent account) and #3 (change matrix).
"""

from __future__ import annotations

import pytest
from conftest import cell

OPENING = {"Forest": 40, "Lake": 30, "Cropland": 60,
           "Urban area": 50, "Wetland": 20, "Seagrass": 50}
CLOSING = {"Forest": 38, "Lake": 30, "Cropland": 62,
           "Urban area": 50, "Wetland": 20, "Seagrass": 50}


def test_checks_pass(extent):
    extent.check()


@pytest.mark.parametrize("et,expected", OPENING.items())
def test_opening_extent(extent, et, expected):
    assert cell(extent.tables["extent"], "entry", "Opening extent", et) == expected


@pytest.mark.parametrize("et,expected", CLOSING.items())
def test_closing_extent(extent, et, expected):
    assert cell(extent.tables["extent"], "entry", "Closing extent", et) == expected


def test_totals_are_250_ha_at_both_ends(extent):
    assert extent.totals["opening_ha"] == 250
    assert extent.totals["closing_ha"] == 250


def test_the_single_conversion_is_recorded_as_managed(extent):
    """2 ha of forest becomes cropland, and the standard distinguishes managed from unmanaged."""
    table = extent.tables["extent"]
    assert cell(table, "entry", "Managed expansion", "Cropland") == 2
    assert cell(table, "entry", "Managed reductions", "Forest") == 2
    assert cell(table, "entry", "Managed expansion", "TOTAL") == 2
    assert cell(table, "entry", "Managed reductions", "TOTAL") == 2
    for entry in ("Unmanaged expansion", "Unmanaged reductions"):
        assert cell(table, "entry", entry, "TOTAL") == 0


def test_net_change_is_zero_overall_and_offsetting_by_et(extent):
    table = extent.tables["extent"]
    assert cell(table, "entry", "Net change in extent", "Forest") == -2
    assert cell(table, "entry", "Net change in extent", "Cropland") == 2
    assert cell(table, "entry", "Net change in extent", "TOTAL") == 0


def test_change_matrix_has_one_off_diagonal_cell(change_matrix):
    change_matrix.check()
    off_diagonal = change_matrix.table.query("et_from != et_to and area_ha != 0")
    assert len(off_diagonal) == 1
    row = off_diagonal.iloc[0]
    assert (row.et_from, row.et_to, row.area_ha) == ("Forest", "Cropland", 2.0)


def test_change_matrix_margins_are_the_extent_account(change_matrix, extent):
    """Row sums are the opening extent and column sums the closing extent, by construction."""
    matrix = change_matrix.table
    rows = matrix.groupby("et_from").area_ha.sum()
    columns = matrix.groupby("et_to").area_ha.sum()
    for et in OPENING:
        assert rows[et] == cell(extent.tables["extent"], "entry", "Opening extent", et)
        assert columns[et] == cell(extent.tables["extent"], "entry", "Closing extent", et)


def test_managed_attribution_is_a_parameter_not_a_fact_in_the_matrix(engine, eaa):
    """Land cover cannot say whether a conversion was a decision; the parameter set declares it."""
    undeclared = engine.parameters.with_(managed_transitions=(), label="nothing declared managed")
    account = engine.extent_account(eaa, date=2020, parameters=undeclared).check()
    table = account.tables["extent"]
    assert cell(table, "entry", "Managed reductions", "Forest") == 0
    assert cell(table, "entry", "Unmanaged reductions", "Forest") == 2
    assert cell(table, "entry", "Unmanaged expansion", "Cropland") == 2
    assert account.provenance.parameters["managed_transitions"] == []
