"""The NPV arithmetic itself, and where the published workbook disagrees with itself.

The decomposition is the hardest piece of the standard, so it is tested twice: as a property
(the three effects sum to ΔNPV, always) and against the published cells of sheet #13.

Three of those cells cannot be reproduced from the workbook's own inputs, because the
decomposition sheet's expected-flow column contradicts both sheet #9 and the NPV it is paired
with. Rather than quietly matching or quietly diverging, the disagreements are pinned below:
fed the workbook's numbers, this code reproduces the workbook's answer exactly, which shows the
arithmetic agrees and the *inputs* do not.
"""

from __future__ import annotations

import pytest

from unseea import npv
from unseea.parameters import SEEALAND

MONEY = 1e-6


def test_annuity_factor_is_100_years_at_2_percent_with_income_at_period_end():
    assert SEEALAND.annuity_factor() == pytest.approx(43.09835164011273)


def test_npv_is_the_expected_exchange_value_times_the_annuity_factor():
    """Sheet #12: forest wood, $9,000 of expected annual exchange value."""
    assert 9000 * SEEALAND.annuity_factor() == pytest.approx(387885.16476101446, abs=MONEY)


def test_income_at_period_start_is_worth_one_year_more():
    at_start = SEEALAND.with_(income_timing="start")
    assert at_start.annuity_factor() == pytest.approx(SEEALAND.annuity_factor() * 1.02)


@pytest.mark.parametrize(
    "triple",
    [
        dict(p0=1.0, p1=1.0, q0=1.0, q1=1.0, a0=1.0, a1=1.0),
        dict(p0=25.86, p1=28.01, q0=375.0, q1=315.79, a0=40.0, a1=38.0),
        dict(p0=2.5, p1=0.5, q0=100.0, q1=250.0, a0=12.0, a1=3.0),
        dict(p0=0.1, p1=9.9, q0=1e5, q1=1.0, a0=1.0, a1=1e4),
    ],
)
def test_the_three_effects_always_sum_to_the_change_in_npv(triple):
    """The property that makes the split an account entry rather than an approximation."""
    effects = npv.decompose(**triple)
    change = triple["p1"] * triple["q1"] * triple["a1"] - triple["p0"] * triple["q0"] * triple["a0"]
    # The identity is exact in arithmetic; the tolerance is float64 cancellation, and the last
    # triple is deliberately brutal (factors spanning five orders of magnitude in both
    # directions) to show how much room that actually needs.
    assert effects["total"] == pytest.approx(change, rel=1e-9)


def test_a_change_in_one_factor_alone_is_wholly_that_factor_s_effect():
    effects = npv.decompose(p0=2.0, p1=3.0, q0=10.0, q1=10.0, a0=5.0, a1=5.0)
    assert effects["price_effect"] == pytest.approx(50.0)
    assert effects["area_effect"] == 0.0
    assert effects["volume_effect"] == 0.0


def test_the_naive_split_leaves_a_residual_and_the_symmetric_one_does_not():
    """Why the symmetric split: p0q0(a1-a0) + ... does not add up, and the difference is real."""
    triple = dict(p0=25.86, p1=28.01, q0=375.0, q1=315.79, a0=40.0, a1=38.0)
    naive = (
        triple["p0"] * triple["q0"] * (triple["a1"] - triple["a0"])
        + triple["p0"] * triple["a0"] * (triple["q1"] - triple["q0"])
        + triple["q0"] * triple["a0"] * (triple["p1"] - triple["p0"])
    )
    change = triple["p1"] * triple["q1"] * triple["a1"] - triple["p0"] * triple["q0"] * triple["a0"]
    assert abs(naive - change) > 1000
    assert npv.decompose(**triple)["total"] == pytest.approx(change, rel=1e-12)


def test_forest_wood_reproduces_the_published_decomposition_cells():
    """Sheet #13, forest wood provisioning: the workbook's own p, q and a."""
    effects = npv.decompose(
        a0=40.0,
        a1=38.0,
        p0=25.85901098406763,
        p1=28.01392856607326,
        q0=375.0,
        q1=315.7894736842105,
    )
    assert effects["area_effect"] == pytest.approx(-18586.164144798604, abs=MONEY)
    assert effects["volume_effect"] == pytest.approx(-62180.71391234683, abs=MONEY)
    assert effects["price_effect"] == pytest.approx(29048.85608901011, abs=MONEY)


# --------------------------------------------------------------------------------------
# Where the workbook disagrees with itself
# --------------------------------------------------------------------------------------


def test_lake_recreation_workbook_inputs_reproduce_the_workbook_answer():
    """Sheet #13 uses an expected flow of 5 visits for lake recreation; sheet #9 says 4,800.

    5 is the *price* of a visit, not the flow. The mistake cancels in the NPV — the unit value
    is derived as NPV/quantity — so the total change is unaffected, but the whole of it lands in
    the price effect instead of the volume effect.
    """
    workbook = npv.decompose(
        a0=30.0,
        a1=30.0,
        p0=2068.7208787254103,
        p1=2154.9175820056357,
        q0=16.666666666666668,
        q1=16.666666666666668,
    )
    assert workbook["volume_effect"] == pytest.approx(0.0, abs=MONEY)
    assert workbook["price_effect"] == pytest.approx(43098.3516401127, abs=MONEY)


def test_lake_recreation_from_the_flows_sheet_is_a_volume_effect(asset):
    """With the expected visits sheet #9 records (4,800 → 5,000), the price never changes."""
    row = asset.tables["decomposition"].query(
        "et == 'Lake' and service == 'Recreation-related services'"
    ).iloc[0]
    assert (row.q0, row.q1) == pytest.approx((16000.0, 16666.666666666668))
    assert row.p0 == pytest.approx(row.p1)
    assert row.volume_effect == pytest.approx(43098.3516401127, abs=MONEY)
    assert row.price_effect == pytest.approx(0.0, abs=MONEY)
    assert row.npv_change == pytest.approx(43098.3516401127, abs=MONEY)


def test_seagrass_wild_fish_workbook_inputs_reproduce_the_workbook_answer():
    """Sheet #13 opens seagrass wild fish at 20 tonnes; sheets #9 and #12 both say 6.

    20 tonnes is the wetland row's climate-regulation flow. As with lake recreation the total
    is unaffected, but the split becomes a $142k degradation against a $150k revaluation where
    neither the area nor the physical flow moved at all.
    """
    workbook = npv.decompose(
        a0=50.0,
        a1=50.0,
        p0=43.96031867291496,
        p1=159.46390106841704,
        q0=40.0,
        q1=12.0,
    )
    assert workbook["volume_effect"] == pytest.approx(-142396.95381893238, abs=1e-4)
    assert workbook["price_effect"] == pytest.approx(150154.6571141527, abs=1e-4)
    assert workbook["total"] == pytest.approx(7757.70329522033, abs=MONEY)


def test_seagrass_wild_fish_from_the_flows_sheet_is_a_revaluation(asset):
    """6 tonnes at both ends: nothing changed but the price, so the change is revaluation."""
    decomposition = asset.tables["decomposition"]
    seagrass = decomposition[decomposition.et == "Seagrass"]
    row = seagrass[seagrass.service.str.startswith("Wild fish")].iloc[0]
    assert (row.q0, row.q1) == pytest.approx((12.0, 12.0))
    assert row.volume_effect == pytest.approx(0.0, abs=MONEY)
    assert row.price_effect == pytest.approx(7757.70329522033, abs=MONEY)


def test_the_disagreements_do_not_move_any_published_total(asset):
    """Both mistakes cancel within their ET, which is why the published totals still stand."""
    lake = asset.tables["decomposition"].query("et == 'Lake'")
    seagrass = asset.tables["decomposition"].query("et == 'Seagrass'")
    assert lake.npv_change.sum() == pytest.approx(62923.5933945647, abs=MONEY)
    assert seagrass.npv_change.sum() == pytest.approx(-3016.884614807903, abs=MONEY)
