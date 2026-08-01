"""Condition accounts against SEEALand (SEEA EA Ch. 5).

Expected values: workbook sheets #4 (variables), #5 (indicators), #6 (index) and #8 (indices
summary).
"""

from __future__ import annotations

import pytest
from conftest import cell

#: Sheet #8, opening and closing condition index per ET.
INDEX = {
    "Forest": (0.6707407407407406, 0.6117592592592591),
    "Lake": (0.6261039886039885, 0.6717149702149702),
    "Cropland": (0.46791666666666665, 0.47133333333333327),
    "Urban area": (0.5044047619047619, 0.4852142857142857),
    "Wetland": (0.5912619047619048, 0.5559761904761905),
    "Seagrass": (0.4450202991452991, 0.36907051282051284),
}

#: Sheet #5, forest indicator values (opening, closing) after rescaling.
FOREST_INDICATORS = {
    "Vegetation water content - NDWI": (0.655, 0.645),
    "Soil organic carbon stock": (0.4, 0.38),
    "Foliar or litter nitrogen concentration": (0.38888888888888884, 0.36111111111111116),
    "Tree species richness": (0.6, 0.5),
    "Tree cover": (0.81, 0.75),
    "Vegetation index - NDVI": (0.825, 0.815),
    "Forest area density": (0.74, 0.59),
}

#: Sheet #6, forest change by ECT group.
FOREST_GROUP_CHANGES = {
    "Change in abiotic ecosystem characteristics": -0.005648148148148152,
    "Change in biotic ecosystem characteristics": -0.02833333333333332,
    "Change in landscape/seascape level characteristics": -0.024999999999999994,
}


def test_checks_pass(condition):
    condition.check()


def test_all_three_stages_are_returned(condition):
    assert set(condition.tables) == {"variables", "indicators", "index", "summary"}


def test_stage_1_keeps_observations_in_their_own_units(condition):
    variables = condition.tables["variables"]
    forest_soc = variables.query(
        "et == 'Forest' and variable == 'Soil organic carbon stock'"
    ).iloc[0]
    assert (forest_soc.opening, forest_soc.closing, forest_soc.unit) == (100.0, 95.0, "tC/ha")
    assert forest_soc.change == -5.0


@pytest.mark.parametrize("variable,expected", FOREST_INDICATORS.items())
def test_stage_2_rescales_forest_variables(condition, variable, expected):
    row = condition.tables["indicators"].query(
        "et == 'Forest' and variable == @variable"
    ).iloc[0]
    assert row.indicator_opening == pytest.approx(expected[0])
    assert row.indicator_closing == pytest.approx(expected[1])


def test_stage_2_rescales_against_reversed_bounds(condition):
    """A variable that is bad when high has its upper reference level below its lower one."""
    row = condition.tables["indicators"].query(
        "et == 'Lake' and variable == 'Nitrogen concentration'"
    ).iloc[0]
    assert (row.lower_level, row.upper_level) == (2.0, 0.0)
    assert row.indicator_opening == pytest.approx(0.45)
    assert row.indicator_closing == pytest.approx(0.55)


def test_stage_2_clamps_rather_than_extrapolating(condition):
    """Seagrass patch size falls below its lower reference level; the indicator floors at 0."""
    row = condition.tables["indicators"].query(
        "et == 'Seagrass' and variable == 'Average patch size'"
    ).iloc[0]
    assert row.closing < row.lower_level
    assert row.indicator_opening == pytest.approx(0.23333333333333334)
    assert row.indicator_closing == 0.0


@pytest.mark.parametrize("et,expected", INDEX.items())
def test_stage_3_index_opening_and_closing(condition, et, expected):
    summary = condition.tables["summary"]
    assert cell(summary, "row", "Opening condition value", et) == pytest.approx(expected[0])
    assert cell(summary, "row", "Closing condition value", et) == pytest.approx(expected[1])


@pytest.mark.parametrize("row,expected", FOREST_GROUP_CHANGES.items())
def test_forest_change_by_ect_group(condition, row, expected):
    assert cell(condition.tables["summary"], "row", row, "Forest") == pytest.approx(expected)


def test_net_change_equals_the_sum_of_group_changes(condition):
    """Sheet #8's own Check row: two routes to the net change must agree."""
    summary = condition.tables["summary"]
    for et in INDEX:
        parts = sum(cell(summary, "row", row, et) for row in FOREST_GROUP_CHANGES)
        net = cell(summary, "row", "Net change in condition", et)
        assert net == pytest.approx(parts, abs=1e-12)


def test_weights_are_one_equal_vote_per_ect_class_split_within_it(condition):
    """Forest measures all six classes, with two variables sharing the chemical-state vote."""
    forest = condition.table.query("et == 'Forest'")
    assert forest.weight.sum() == pytest.approx(1.0)
    by_class = forest.groupby("ect_code").weight.sum().to_dict()
    classes = ("A1", "A2", "B1", "B2", "B3", "C1")
    assert by_class == pytest.approx(dict.fromkeys(classes, 1 / 6))
    chemical = forest.query("ect_code == 'A2'")
    assert len(chemical) == 2
    assert list(chemical.weight) == pytest.approx([1 / 12, 1 / 12])


def test_an_unmeasured_ect_class_reweights_the_rest(condition):
    """Urban area has no functional-state variable, so its five classes weigh 0.20, not 0.167.

    This is the weight-dilution hazard (`DESIGN.md` §2.4): the missing class contributes
    nothing rather than zero, and every measured class silently gains weight.
    """
    urban = condition.table.query("et == 'Urban area'")
    assert set(urban.ect_code) == {"A1", "A2", "B1", "B2", "C1"}
    by_class = urban.groupby("ect_code").weight.sum().to_dict()
    assert by_class == pytest.approx(dict.fromkeys(("A1", "A2", "B1", "B2", "C1"), 0.2))
    assert urban.weight.sum() == pytest.approx(1.0)


def test_ect_coverage_travels_in_provenance(condition):
    coverage = condition.provenance.ect_coverage
    assert coverage["Urban area"] == ["A1", "A2", "B1", "B2", "C1"]
    assert coverage["Forest"] == ["A1", "A2", "B1", "B2", "B3", "C1"]
    assert any("ECT coverage" in note for note in condition.provenance.notes)


def test_reference_basis_is_recorded_per_et(condition):
    """Natural and anthropogenic reference conditions are not comparable, so both are stated."""
    basis = condition.provenance.parameters["reference_basis"]
    assert basis["Forest"] == basis["Lake"] == basis["Wetland"] == basis["Seagrass"] == "natural"
    assert basis["Cropland"] == basis["Urban area"] == "anthropogenic"


def test_summary_has_no_total_column(condition):
    """SEEA does not average condition across ETs: it would aggregate reference conditions."""
    assert "TOTAL" not in condition.tables["summary"].columns
