"""Monetary asset account against SEEALand (SEEA EA Ch. 10 and Annex 10.1).

Expected values: workbook sheets #12 (NPV by ET), #13 (NPV decomposition) and #14 (monetary
asset account).

Three published cells are *not* asserted here as compiled by the library, because the workbook
disagrees with itself on them. They are pinned in ``test_npv_math.py`` instead, which shows the
arithmetic is identical and isolates the disagreement to its inputs.
"""

from __future__ import annotations

import pytest
from conftest import cell

MONEY = 1e-6

#: Sheet #12, opening and closing NPV per ET.
NPV = {
    "Forest": (905065.384442367, 788699.8350140627),
    "Lake": (1078320.75803562, 1141244.3514301847),
    "Cropland": (484856.455951268, 549503.983411437),
    "Urban area": (522567.51363636664, 565881.35703468),
    "Wetland": (51718.02196813526, 51459.431858294585),
    "Seagrass": (529678.7416569853, 526661.8570421773),
}

#: Sheet #13, forest decomposition by service: (area, volume, price).
FOREST_EFFECTS = {
    "Wood provisioning services": (
        -18586.164144798604,
        -62180.71391234683,
        29048.85608901011,
    ),
    "Global climate regulation services": (
        -8006.085900725149,
        -30448.985433739617,
        6131.307604380276,
    ),
    "Recreation-related services": (
        -16842.38215409668,
        -15481.381575987865,
        0.0,
    ),
}


def test_checks_pass(asset):
    asset.check()


@pytest.mark.parametrize("et,expected", NPV.items())
def test_npv_per_ecosystem_type(asset, et, expected):
    table = asset.tables["asset"]
    assert cell(table, "entry", "Opening value", et) == pytest.approx(expected[0], abs=MONEY)
    assert cell(table, "entry", "Closing value", et) == pytest.approx(expected[1], abs=MONEY)


def test_forest_npv_by_service(asset):
    """Sheet #12: the three services forest supplies, valued over a 100-year asset life at 2%."""
    forest = asset.tables["npv"].query("et == 'Forest'").set_index("service")
    assert forest.npv0.to_dict() == pytest.approx(
        {
            "Wood provisioning services": 387885.16476101446,
            "Global climate regulation services": 172393.40656045085,
            "Recreation-related services": 344786.8131209017,
        },
        abs=MONEY,
    )


def test_forest_change_in_npv_is_minus_116366(asset):
    """The headline decomposition target."""
    table = asset.tables["asset"]
    assert cell(table, "entry", "Net change in value", "Forest") == pytest.approx(
        -116365.54942830431, abs=MONEY
    )


def test_total_opening_asset_value(asset):
    assert asset.totals["opening_value"] == pytest.approx(3572206.8756907415, abs=MONEY)
    assert asset.totals["closing_value"] == pytest.approx(3623450.8157908367, abs=MONEY)


@pytest.mark.parametrize("service,expected", FOREST_EFFECTS.items())
def test_forest_decomposition_by_service(asset, service, expected):
    """Sheet #13: area, volume and price effects, cell for cell."""
    row = asset.tables["decomposition"].query("et == 'Forest' and service == @service").iloc[0]
    assert row.area_effect == pytest.approx(expected[0], abs=MONEY)
    assert row.volume_effect == pytest.approx(expected[1], abs=MONEY)
    assert row.price_effect == pytest.approx(expected[2], abs=MONEY)


def test_forest_effects_sum_to_the_change_in_value(asset):
    forest = asset.tables["decomposition"].query("et == 'Forest'")
    assert forest.area_effect.sum() == pytest.approx(-43434.632199620435, abs=MONEY)
    assert forest.volume_effect.sum() == pytest.approx(-108111.08092207431, abs=MONEY)
    assert forest.price_effect.sum() == pytest.approx(35180.16369339039, abs=MONEY)
    assert forest.npv_change.sum() == pytest.approx(-116365.54942830431, abs=MONEY)


def test_every_ecosystem_type_reconciles_effects_to_change_in_npv(asset):
    """The identity that makes the decomposition an account: no residual, anywhere."""
    per_et = asset.tables["decomposition"].groupby("et")
    for et, rows in per_et:
        total = rows.area_effect.sum() + rows.volume_effect.sum() + rows.price_effect.sum()
        assert total == pytest.approx(rows.npv_change.sum(), abs=MONEY), et


def test_conversion_entries_follow_the_two_hectares(asset):
    """The 2 ha forest→cropland conversion, valued: forest loses, cropland gains, net negative."""
    table = asset.tables["asset"]
    assert cell(table, "entry", "Ecosystem conversions: reductions", "Forest") == pytest.approx(
        -43434.632199620435, abs=MONEY
    )
    assert cell(table, "entry", "Ecosystem conversions: additions", "Cropland") == pytest.approx(
        16943.90840689915, abs=MONEY
    )
    net = cell(table, "entry", "Ecosystem conversions: additions", "TOTAL") + cell(
        table, "entry", "Ecosystem conversions: reductions", "TOTAL"
    )
    assert net < 0


def test_degradation_is_recorded_for_forest_wetland_and_seagrass(asset):
    """Condition fell in three ETs, and their expected service flows fell with it."""
    table = asset.tables["asset"]
    degraded = {"Forest", "Wetland", "Seagrass"}
    for et in NPV:
        entry = cell(table, "entry", "Ecosystem degradation", et)
        assert (entry < 0) is (et in degraded), et


def test_wetland_degradation_and_revaluation(asset):
    """Sheet #13: wetland's small numbers still split cleanly."""
    table = asset.tables["asset"]
    assert cell(table, "entry", "Ecosystem degradation", "Wetland") == pytest.approx(
        -1099.007966822874, abs=MONEY
    )
    assert cell(table, "entry", "Revaluations", "Wetland") == pytest.approx(
        840.4178569821986, abs=MONEY
    )


def test_urban_area_is_a_reappraisal_not_enhancement(asset):
    """Urban expected recreation rose while its condition fell: new information, not enhancement."""
    table = asset.tables["asset"]
    assert cell(table, "entry", "Upward reappraisals", "Urban area") == pytest.approx(
        43098.35164011271, abs=MONEY
    )
    assert cell(table, "entry", "Ecosystem enhancement", "Urban area") == 0.0
    assert cell(table, "entry", "Revaluations", "Urban area") == pytest.approx(
        215.49175820056377, abs=MONEY
    )


def test_revaluation_affects_every_ecosystem_type_except_cropland(asset):
    """Cropland's price is unchanged over the period, so it has nothing to revalue."""
    table = asset.tables["asset"]
    for et in NPV:
        revaluation = cell(table, "entry", "Revaluations", et)
        assert (revaluation == 0.0) is (et == "Cropland"), et


def test_lake_is_the_largest_single_asset(asset):
    opening = asset.table.query("entry == 'Opening value'").set_index("et").value
    assert opening.idxmax() == "Lake"
    assert opening.max() == pytest.approx(1078320.75803562, abs=MONEY)


def test_entries_reconcile_opening_to_closing_for_every_et(asset):
    """SEEA EA Table 10.1: opening + all entries = closing."""
    table = asset.tables["asset"]
    movement = [
        "Ecosystem enhancement",
        "Ecosystem degradation",
        "Ecosystem conversions: additions",
        "Ecosystem conversions: reductions",
        "Upward reappraisals",
        "Downwards reappraisals",
        "Revaluations",
    ]
    for et in [*NPV, "TOTAL"]:
        opening = cell(table, "entry", "Opening value", et)
        entries = sum(cell(table, "entry", entry, et) for entry in movement)
        assert opening + entries == pytest.approx(
            cell(table, "entry", "Closing value", et), abs=1e-6
        ), et


def test_valuation_assumptions_are_stated_in_provenance(asset):
    parameters = asset.provenance.parameters
    assert (parameters["asset_life"], parameters["discount_rate"]) == (100, 0.02)
    assert parameters["income_timing"] == "end"
    assert any("asset_life_years=100" in note for note in asset.provenance.notes)


def test_a_higher_discount_rate_lowers_every_asset_value(engine, eaa, asset):
    """The discount rate decides every level in this account, which is why it must be stated."""
    parameters = engine.parameters.with_(discount_rate=0.04, label="4% real")
    at_four_percent = engine.asset_account(eaa, 2020, parameters=parameters).check()
    assert at_four_percent.totals["opening_value"] < asset.totals["opening_value"]
    assert at_four_percent.provenance.parameters["discount_rate"] == 0.04


def test_condition_tolerance_reclassifies_a_marginal_volume_effect(engine, eaa, asset):
    """Cropland's condition rose by 0.003 — evidence of enhancement, or noise?

    Under the standard's rule applied on the sign alone (the default), cropland's positive
    volume effect is enhancement. The published workbook records it as an upward reappraisal
    instead, which is what a tolerance of half a percentage point of index produces. Both are
    defensible; the point is that the choice is a declared parameter rather than a hidden one.
    """
    table = asset.tables["asset"]
    assert cell(table, "entry", "Ecosystem enhancement", "Cropland") == pytest.approx(
        47703.619053269904, abs=MONEY
    )
    assert cell(table, "entry", "Upward reappraisals", "Cropland") == 0.0

    tolerant = engine.parameters.with_(condition_change_tolerance=0.005, label="0.005 tolerance")
    workbook = engine.asset_account(eaa, 2020, parameters=tolerant).check()
    workbook_table = workbook.tables["asset"]
    assert cell(workbook_table, "entry", "Ecosystem enhancement", "Cropland") == 0.0
    assert cell(workbook_table, "entry", "Upward reappraisals", "Cropland") == pytest.approx(
        47703.619053269904, abs=MONEY
    )
    # Sheet #14's published total for upward reappraisals: cropland plus urban area.
    assert cell(workbook_table, "entry", "Upward reappraisals", "TOTAL") == pytest.approx(
        90801.97069338261, abs=MONEY
    )
    # The reclassification moves value between entries; it cannot change the value itself.
    assert workbook.totals["net_change"] == pytest.approx(asset.totals["net_change"], abs=MONEY)
