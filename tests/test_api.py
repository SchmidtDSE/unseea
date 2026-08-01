"""The library contract: what every account call returns, and what it refuses to do."""

from __future__ import annotations

import duckdb
import pytest
from conftest import FIXTURE_DIR

import unseea
from unseea.fixtures import seealand

ACCOUNT_NAMES = [
    "extent",
    "change_matrix",
    "condition",
    "physical",
    "monetary",
    "asset",
]


@pytest.fixture(params=ACCOUNT_NAMES)
def account(request):
    return request.getfixturevalue(request.param)


def test_every_account_returns_table_sql_checks_and_provenance(account):
    assert not account.table.empty
    assert account.sql.strip()
    assert account.checks
    assert account.provenance is not None
    assert account.ok


def test_every_account_records_its_executor_area_period_and_sources(account):
    provenance = account.provenance
    assert provenance.executor == "fixture"
    assert provenance.eaa == "SEEALand"
    assert provenance.period == "2020 (1 January - 31 December 2020)"
    assert len(provenance.sources) == len(seealand.INPUT_SHEETS)
    assert provenance.unseea_version == unseea.__version__
    assert provenance.to_dict()["nc_encumbered"] is False


def test_returned_sql_re_runs_in_a_bare_duckdb_session(account):
    """``acct.sql`` is the artifact, not a rendering of one: it must actually run.

    For the fixture executor that means against the same tidy tables ``register`` builds; for
    the real-data executors it will mean ``s3://`` rewritten to the public HTTPS endpoint.
    """
    connection = duckdb.connect(":memory:")
    seealand.register(connection, FIXTURE_DIR)
    result = connection.execute(account.sql).df()
    assert not result.empty


def test_a_failing_check_raises_rather_than_warning():
    failing = unseea.Account(
        name="test",
        table=unseea.connect(fixture=FIXTURE_DIR).executor.tables["ecosystem_type"],
        sql="SELECT 1",
        checks=[unseea.Check("total supply = total use", residual=1.5, detail="Wood")],
    )
    assert not failing.ok
    with pytest.raises(unseea.CheckFailure, match="total supply = total use"):
        failing.check()


def test_connect_requires_exactly_one_executor():
    with pytest.raises(ValueError, match="exactly one executor"):
        unseea.connect()
    with pytest.raises(ValueError, match="exactly one executor"):
        unseea.connect(fixture=FIXTURE_DIR, local=True)


def test_the_real_data_executors_name_the_issue_that_blocks_them():
    for engine, issue in (
        (unseea.connect(local=True), "issues/4"),
        (unseea.connect(mcp="https://example.invalid/mcp"), "issues/29"),
    ):
        with pytest.raises(NotImplementedError, match=issue):
            engine.executor.execute("SELECT 1")


def test_the_fixture_has_one_accounting_area_and_says_so(engine):
    with pytest.raises(ValueError, match="one accounting area"):
        engine.eaa(country="CR")


def test_a_period_the_fixture_cannot_compile_is_an_error(engine, eaa):
    """Better an error than an empty account that looks like a finding."""
    with pytest.raises(ValueError, match="covers 2020"):
        engine.extent_account(eaa, date=2019)


def test_a_multi_period_request_is_refused(engine, eaa):
    with pytest.raises(ValueError, match="one period at a time"):
        engine.asset_account(eaa, 2020, 2021)


def test_stratify_by_is_refused_where_there_are_no_strata(engine, eaa):
    with pytest.raises(NotImplementedError, match="stratify_by"):
        engine.condition_account(eaa, 2020, stratify_by="protected_area")


def test_landscape_metric_names_what_it_needs(engine, eaa):
    with pytest.raises(NotImplementedError, match="h3"):
        engine.landscape_metric(eaa, "forest_area_density", k=1)


def test_the_engine_exposes_the_nine_calls(engine):
    for call in (
        "eaa",
        "extent_account",
        "extent_change_matrix",
        "condition_account",
        "landscape_metric",
        "services_physical",
        "services_monetary",
        "asset_account",
    ):
        assert callable(getattr(engine, call))
    assert callable(unseea.connect)


def test_the_eaa_knows_its_area_and_period(eaa):
    assert eaa.name == "SEEALand"
    assert eaa.area_ha == 250.0
    assert eaa.periods == (2020,)


def test_parameter_sets_are_immutable_and_copied_by_with(engine):
    original = engine.parameters
    changed = original.with_(discount_rate=0.05)
    assert original.discount_rate == 0.02
    assert changed.discount_rate == 0.05
    with pytest.raises(Exception):
        original.discount_rate = 0.05  # frozen dataclass


def test_invalid_parameters_are_rejected():
    with pytest.raises(ValueError, match="discount_rate"):
        unseea.ParameterSet(discount_rate=0.0)
    with pytest.raises(ValueError, match="income_timing"):
        unseea.ParameterSet(income_timing="midyear")
