"""Parameter sets: the assumptions an account is compiled under.

Everything here is a *choice*, not a fact about SEEA, and every choice travels into
``acct.provenance`` so a reader can see what was assumed. `DESIGN.md` §5.2 requires the
discount rate to be stated before any asset value is reported; §5.3 requires the same of
reference levels. Making them a single inspectable object is how that requirement is met in
code rather than in a prompt.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class ParameterSet:
    """Assumptions for one account compilation.

    Args:
        asset_life: Years of expected future service flow entering the NPV (SEEA EA Ch. 10).
        discount_rate: Real discount rate applied to those flows.
        income_timing: ``"end"`` discounts the first year's income by one full year;
            ``"start"`` treats it as received immediately. SEEALand assumes ``"end"``.
        reference_basis: Per-ET reference condition (SEEA EA Table 5.9). Natural and
            anthropogenic bases are not comparable, and SEEA forbids averaging condition
            across them, so this is recorded per ET rather than once per account.
        managed_transitions: ET transitions attributable to management. Anything else
            off-diagonal in the change matrix is recorded as unmanaged.
        prices: Optional per-service price overrides, ``{service_id: price}``.
        condition_change_tolerance: How large a change in the condition index counts as
            evidence that the ecosystem itself changed. Below it, a change in expected service
            flows is recorded as a reappraisal rather than as degradation or enhancement. The
            default of 0 applies the standard's rule strictly, on the sign alone.
        label: Human-readable name for the set, carried into provenance.
    """

    asset_life: int = 100
    discount_rate: float = 0.02
    income_timing: str = "end"
    condition_change_tolerance: float = 0.0
    reference_basis: dict[str, str] = field(default_factory=dict)
    managed_transitions: tuple[tuple[str, str], ...] = ()
    prices: dict[str, float] = field(default_factory=dict)
    label: str = "default"

    def __post_init__(self) -> None:
        if self.income_timing not in ("end", "start"):
            raise ValueError(f"income_timing must be 'end' or 'start', got {self.income_timing!r}")
        if self.asset_life <= 0:
            raise ValueError("asset_life must be positive")
        if self.discount_rate <= 0:
            raise ValueError("discount_rate must be positive")
        if self.condition_change_tolerance < 0:
            raise ValueError("condition_change_tolerance must not be negative")

    def annuity_factor(self) -> float:
        """Present value of one unit of income per year over the asset life."""
        n, r = self.asset_life, self.discount_rate
        factor = (1.0 - (1.0 + r) ** -n) / r
        return factor if self.income_timing == "end" else factor * (1.0 + r)

    def with_(self, **changes: Any) -> ParameterSet:
        """Return a copy with ``changes`` applied — the sensitivity-analysis entry point."""
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "asset_life": self.asset_life,
            "discount_rate": self.discount_rate,
            "income_timing": self.income_timing,
            "condition_change_tolerance": self.condition_change_tolerance,
            "reference_basis": dict(self.reference_basis),
            "managed_transitions": [list(t) for t in self.managed_transitions],
            "prices": dict(self.prices),
        }


#: SEEALand's assumptions, from the SEEA EA annex and the complementary workbook.
#:
#: Asset life and discount rate are stated on every ``npv-by-et.csv`` block. The reference
#: bases are from the annex text: natural for the four natural ETs, anthropogenic for the two
#: human-dominated ones. The single conversion — 2 ha of forest to cropland — is managed.
SEEALAND = ParameterSet(
    asset_life=100,
    discount_rate=0.02,
    income_timing="end",
    reference_basis={
        "Forest": "natural",
        "Lake": "natural",
        "Wetland": "natural",
        "Seagrass": "natural",
        "Cropland": "anthropogenic",
        "Urban area": "anthropogenic",
    },
    managed_transitions=(("Forest", "Cropland"),),
    label="SEEALand (SEEA EA annex)",
)
