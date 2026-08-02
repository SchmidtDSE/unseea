"""Supply-and-use accounts against SEEALand (SEEA EA Ch. 6–7 and Ch. 9).

Expected values: workbook sheets #10 (physical SUT) and #11 (monetary SUT).
"""

from __future__ import annotations

import pytest

#: Sheet #10, total supply per service in physical units.
PHYSICAL_TOTALS = {
    "Crop provisioning services": 150.0,
    "Wood provisioning services": 140.0,
    "Wild fish and other natural aquatic biomass provisioning services": 9.0,
    "Global climate regulation services": 425.0,
    "Water purification services": 7.0,
    "Recreation-related services": 9800.0,
}

#: Sheet #11, total monetary supply per ecosystem type.
SUPPLY_BY_ET = {
    "Forest": 19650.0,
    "Lake": 26050.0,
    "Cropland": 11250.0,
    "Urban area": 12625.0,
    "Wetland": 1200.0,
    "Seagrass": 12350.0,
}

#: Sheet #11, use by economic unit.
USE_BY_SECTOR = {
    "Agriculture": 11250.0,
    "Forestry": 8400.0,
    "Fisheries": 3150.0,
    "Energy & water supply": 700.0,
    "Government": 10625.0,
    "Households": 49000.0,
}

#: The prices SEEALand assumes, per service (sheet #9).
PRICES = {
    "wood_provisioning": 60.0,
    "crop_provisioning": 75.0,
    "wild_fish_provisioning": 350.0,
    "global_climate_regulation": 25.0,
    "water_purification": 100.0,
    "recreation": 5.0,
}


def test_checks_pass(physical, monetary):
    physical.check()
    monetary.check()


@pytest.mark.parametrize("service,expected", PHYSICAL_TOTALS.items())
def test_physical_supply_totals(physical, service, expected):
    supply = physical.table.query("block == 'supply' and service == @service")
    assert supply.flow.sum() == expected


def test_physical_supply_equals_use_for_every_service(physical):
    supply = physical.table.query("block == 'supply'").groupby("service").flow.sum()
    use = physical.table.query("block == 'use'").groupby("service").flow.sum()
    assert supply.to_dict() == pytest.approx(use.to_dict())


def test_services_are_attributed_to_the_ecosystem_types_that_supply_them(physical):
    """Global climate regulation comes from four ETs; wild fish from two."""
    climate = physical.table.query(
        "block == 'supply' and service_id == 'global_climate_regulation'"
    )
    assert dict(zip(climate.counterparty, climate.flow)) == {
        "Forest": 150.0,
        "Urban area": 5.0,
        "Wetland": 20.0,
        "Seagrass": 250.0,
    }
    fish = physical.table.query("block == 'supply' and service_id == 'wild_fish_provisioning'")
    assert dict(zip(fish.counterparty, fish.flow)) == {"Lake": 3.0, "Seagrass": 6.0}


def test_prices_are_the_ones_the_annex_assumes(physical):
    supply = physical.table.query("block == 'supply'")
    assert dict(zip(supply.service_id, supply.price)) == PRICES


def test_gep_is_83125(monetary):
    """The headline number: total supply of final ecosystem services."""
    assert monetary.totals["GEP"] == pytest.approx(83125.0)


@pytest.mark.parametrize("et,expected", SUPPLY_BY_ET.items())
def test_monetary_supply_by_ecosystem_type(monetary, et, expected):
    supply = monetary.table.query("block == 'supply' and counterparty == @et")
    assert supply.value.sum() == pytest.approx(expected)


@pytest.mark.parametrize("sector,expected", USE_BY_SECTOR.items())
def test_monetary_use_by_economic_unit(monetary, sector, expected):
    use = monetary.table.query("block == 'use' and counterparty == @sector")
    assert use.value.sum() == pytest.approx(expected)


def test_the_account_balances(monetary):
    supply = monetary.table.query("block == 'supply'").value.sum()
    use = monetary.table.query("block == 'use'").value.sum()
    assert supply == pytest.approx(use) == pytest.approx(83125.0)


def test_a_price_override_moves_gep_and_is_recorded(engine, eaa):
    """A GEP is meaningless without the prices behind it, so an override travels in provenance."""
    prices = {"global_climate_regulation": 50.0}
    account = engine.services_monetary(eaa, 2020, prices=prices).check()
    # 425 tonnes CO2 supplied, repriced from $25 to $50: GEP rises by 425 * 25.
    assert account.totals["GEP"] == pytest.approx(83125.0 + 425 * 25)
    assert account.provenance.parameters["prices"] == {"global_climate_regulation": 50.0}


def test_gep_definition_is_stated_in_provenance(monetary):
    assert any("intermediate" in note for note in monetary.provenance.notes)
