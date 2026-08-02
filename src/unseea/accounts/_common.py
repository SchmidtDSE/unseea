"""Shared plumbing for the account compilers: provenance, presentation, guards."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from ..parameters import ParameterSet
from ..results import Provenance
from ..vocab import ECOSYSTEM_TYPES

#: Column label for row totals in the SEEA-shaped presentation tables.
TOTAL = "TOTAL"


def guard_stratify(stratify_by: Any) -> None:
    """Reject ``stratify_by`` where the executor has no strata to group on.

    A fixed nine-call API cannot express "condition by ET *and* by protected-area status", so
    every account call takes ``stratify_by``. The fixture is a 250 ha toy landscape with no
    covariates to stratify on, and silently ignoring the argument would be worse than
    refusing it.
    """
    if stratify_by:
        raise NotImplementedError(
            f"stratify_by={stratify_by!r} needs a real-data executor with covariate layers; "
            "the fixture has none (see https://github.com/SchmidtDSE/unseea/issues/4)"
        )


def build_provenance(
    *,
    account: str,
    engine: Any,
    eaa: Any,
    period: str,
    parameters: ParameterSet,
    bindings: dict[str, Any] | None = None,
    ect_coverage: dict[str, list[str]] | None = None,
    notes: Iterable[str] = (),
) -> Provenance:
    """Assemble the provenance record for one compiled account."""
    from .. import __version__

    described = engine.executor.describe()
    return Provenance(
        account=account,
        executor=described.get("executor", engine.executor.name),
        eaa=eaa.name,
        period=period,
        parameters=parameters.to_dict(),
        bindings=dict(bindings or {}),
        sources=list(described.get("sources", [])),
        licences=list(described.get("licences", [])),
        ect_coverage=dict(ect_coverage or {}),
        notes=[*described.get("notes", []), *notes],
        unseea_version=__version__,
    )


def et_order(frame: pd.DataFrame, column: str = "et") -> list[str]:
    """ETs present in ``frame``, in SEEALand presentation order."""
    present = set(frame[column])
    return [et for et in ECOSYSTEM_TYPES if et in present]


def pivot_et(
    long: pd.DataFrame,
    *,
    index: list[str],
    values: str,
    total: bool = True,
) -> pd.DataFrame:
    """Pivot a long account table into the standard's layout: entries down, ETs across.

    The long table is what SQL returns and what downstream code should join on; this is for
    reading, and for matching the published tables cell for cell.
    """
    ordered = long.sort_values(index)
    wide = ordered.pivot_table(index=index, columns="et", values=values, aggfunc="sum", sort=False)
    wide = wide.reindex(columns=et_order(long)).fillna(0.0)
    if total:
        wide[TOTAL] = wide.sum(axis=1)
    return wide.reset_index()
