"""The fixture loader: what it reads, what it refuses to read, and what it canonicalises.

If this module silently mis-parses a sheet, every account downstream is confidently wrong, so
the structural facts of the SEEALand workbook are asserted directly.
"""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import FIXTURE_DIR

from unseea import vocab
from unseea.fixtures import seealand


@pytest.fixture(scope="module")
def tables():
    return seealand.load(FIXTURE_DIR)


def test_only_input_sheets_are_read(tables):
    """Derived sheets are what the library computes; reading them back would be circular."""
    assert set(seealand.INPUT_SHEETS) == {
        "change-matrix.csv",
        "condition-stage-1.csv",
        "condition-stage-2.csv",
        "es-flows.csv",
    }
    derived = {"npv-by-et.csv", "npv-decomposition.csv", "monetary-asset-account.csv"}
    assert derived.isdisjoint(seealand.INPUT_SHEETS)


def test_the_change_matrix_has_seven_transitions(tables):
    """Six ETs holding their area, plus the single 2 ha conversion."""
    changes = tables["et_change"]
    assert len(changes) == 7
    assert changes.area_ha.sum() == 250.0
    assert list(changes.columns) == ["et_from", "et_to", "area_ha"]


def test_ecosystem_type_names_are_canonicalised(tables):
    """The workbook writes "Urban areas" on one sheet and "Urban area" on the others."""
    assert set(tables["et_change"].et_from) <= set(vocab.ECOSYSTEM_TYPES)
    assert "Urban area" in set(tables["condition_variable"].et)
    assert vocab.canonical_et("Urban areas") == "Urban area"


def test_service_names_are_canonicalised(tables):
    """Three sheets name the same wild fish service three different ways."""
    assert set(tables["es_flow"].service_id) <= set(vocab.SERVICE_BY_ID)
    for spelling in (
        "Wild fish biomass provisioning",
        "Wild fish provisioning",
        "Wild fish and other natural aquatic biomass provisioning services",
    ):
        assert vocab.canonical_service(spelling).id == "wild_fish_provisioning"


def test_condition_variables_are_read_with_their_ect_class(tables):
    variables = tables["condition_variable"]
    assert len(variables) == 39
    assert set(variables.ect_code) == {"A1", "A2", "B1", "B2", "B3", "C1"}
    counts = variables.groupby("et").size().to_dict()
    assert counts == {
        "Forest": 7,
        "Lake": 7,
        "Cropland": 7,
        "Urban area": 5,
        "Wetland": 6,
        "Seagrass": 7,
    }


def test_a_declared_absence_is_not_read_as_a_variable(tables):
    """Urban area's functional-state row says "No variable selected"; it is an absence, not a 0."""
    urban = tables["condition_variable"].query("et == 'Urban area'")
    assert "B3" not in set(urban.ect_code)
    assert not urban.variable.str.contains("No variable").any()


def test_every_variable_has_reference_levels(tables):
    variables = tables["condition_variable"][["et", "variable"]]
    references = tables["condition_reference"]
    merged = variables.merge(references, on=["et", "variable"], how="left")
    assert len(merged) == len(variables)
    assert merged.lower_level.notna().all()
    assert merged.upper_level.notna().all()


def test_reference_levels_may_be_inverted_for_a_bad_when_high_variable(tables):
    row = tables["condition_reference"].query(
        "et == 'Lake' and variable == 'Nitrogen concentration'"
    ).iloc[0]
    assert row.lower_level > row.upper_level


def test_es_flows_carry_actual_and_expected_flows_with_their_prices(tables):
    flows = tables["es_flow"]
    assert len(flows) == 13
    forest_wood = flows.query("et == 'Forest' and service_id == 'wood_provisioning'").iloc[0]
    assert (forest_wood.actual_flow, forest_wood.price_actual) == (140.0, 60.0)
    assert (forest_wood.expected_opening, forest_wood.price_opening) == (150.0, 60.0)
    assert (forest_wood.expected_closing, forest_wood.price_closing) == (120.0, 65.0)


def test_use_is_read_per_economic_unit(tables):
    uses = tables["es_use"]
    assert dict(zip(uses.user, uses.quantity)) == {
        "Agriculture": 150.0,
        "Forestry": 140.0,
        "Fisheries": 9.0,
        "Energy & water supply": 7.0,
        "Government": 425.0,
        "Households": 9800.0,
    }
    assert set(uses.use_kind) == {"industry", "government", "household"}


def test_a_missing_sheet_is_an_error_naming_the_sheet(tmp_path):
    with pytest.raises(FileNotFoundError, match="change-matrix.csv"):
        seealand.load(tmp_path)


def test_the_two_condition_sheets_are_cross_checked(tmp_path, monkeypatch):
    """Stages 1 and 2 restate the same observations; disagreement means a bad join."""
    original = seealand._read_condition_blocks

    def tampered(path, value_columns):
        frame = original(path, value_columns)
        if "lower_level" in value_columns:
            frame.loc[0, "opening"] = frame.loc[0, "opening"] + 1
        return frame

    monkeypatch.setattr(seealand, "_read_condition_blocks", tampered)
    with pytest.raises(ValueError, match="disagree on observed values"):
        seealand.load(FIXTURE_DIR)


def test_register_makes_the_tables_queryable(tables):
    import duckdb

    connection = duckdb.connect(":memory:")
    registered = seealand.register(connection, FIXTURE_DIR)
    assert set(registered) == set(tables)
    total = connection.execute("SELECT sum(area_ha) FROM et_change").fetchone()[0]
    assert total == 250.0


def test_the_service_vocabulary_covers_every_service_supplied(tables):
    supplied = set(tables["es_flow"].service_id)
    assert supplied == set(tables["service"].service_id)
    assert set(tables["service"].section) <= set(vocab.SERVICE_SECTIONS)


def test_loaded_tables_are_frames_with_no_nulls_in_their_keys(tables):
    for name, frame in tables.items():
        assert isinstance(frame, pd.DataFrame), name
        assert not frame.empty, name
        for column in frame.columns:
            if frame[column].dtype == object:
                assert frame[column].notna().all(), f"{name}.{column}"
