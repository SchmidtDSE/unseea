"""SQL fragments shared between accounts.

SQL is not the interface — it is the returned artifact (`ARCHITECTURE.md`). So the arithmetic
of the standard lives here as SQL text rather than in pandas: what ``acct.sql`` shows is what
computed the account, and the same fragments will run against real h3 tables when the local
executor lands.

Two fragments are shared because two accounts genuinely need them: the asset account needs
extent (area is a factor in the NPV decomposition) and condition (its sign decides whether a
volume effect is degradation or a reappraisal).
"""

from __future__ import annotations


def with_clause(*ctes: str) -> str:
    """Assemble named CTEs into a ``WITH`` clause."""
    return "WITH " + ",\n".join(cte.strip() for cte in ctes) + "\n"


#: Opening and closing extent per ET, derived from the transition table.
#:
#: Row sums of the change matrix are the opening extent and column sums the closing extent, by
#: construction — which is why the extent account and the change matrix cannot disagree.
EXTENT_CTE = """
extent AS (
    SELECT t.et_id,
           t.et,
           coalesce(o.area_ha, 0.0) AS opening_ha,
           coalesce(c.area_ha, 0.0) AS closing_ha
    FROM ecosystem_type t
    LEFT JOIN (SELECT et_from AS et, sum(area_ha) AS area_ha FROM et_change GROUP BY 1) o
           ON o.et = t.et
    LEFT JOIN (SELECT et_to   AS et, sum(area_ha) AS area_ha FROM et_change GROUP BY 1) c
           ON c.et = t.et
)
"""

#: Condition variables joined to their reference levels: the stage 1 account.
CONDITION_VARIABLES_CTE = """
condition_variables AS (
    SELECT v.et, v.ect_code, v.ect_group, v.ect_class, v.variable, v.unit,
           v.opening, v.closing, v.closing - v.opening AS change,
           r.lower_level, r.upper_level
    FROM condition_variable v
    JOIN condition_reference r ON r.et = v.et AND r.variable = v.variable
)
"""

#: Each variable rescaled to [0, 1] against its reference levels: the stage 2 account.
#:
#: The rescaling is clamped, not extrapolated. An observation beyond the upper reference level
#: is in reference condition, not better than it, and one below the lower level is at zero;
#: SEEALand's seagrass patch size falls below its lower level at close of period and the
#: workbook records 0.
CONDITION_INDICATORS_CTE = """
condition_indicators AS (
    SELECT *,
           least(1.0, greatest(0.0, (opening - lower_level) / (upper_level - lower_level)))
               AS indicator_opening,
           least(1.0, greatest(0.0, (closing - lower_level) / (upper_level - lower_level)))
               AS indicator_closing
    FROM condition_variables
)
"""

#: Index weights: one equal vote per ECT class *present*, split equally within the class.
#:
#: The load-bearing word is *present*. An ECT class with no measured variable does not
#: contribute zero — it contributes nothing, and every measured class silently gains weight
#: (`DESIGN.md` §2.4). SEEALand's urban area has no functional-state variable, so its five
#: remaining classes weigh 0.20 rather than 0.167. This is why ECT coverage travels in
#: ``acct.provenance``.
CONDITION_WEIGHTS_CTE = """
condition_weights AS (
    SELECT k.et,
           k.ect_code,
           1.0 / c.n_classes / v.n_variables AS weight
    FROM (SELECT DISTINCT et, ect_code FROM condition_indicators) k
    JOIN (SELECT et, count(DISTINCT ect_code) AS n_classes
            FROM condition_indicators GROUP BY 1) c ON c.et = k.et
    JOIN (SELECT et, ect_code, count(*) AS n_variables
            FROM condition_indicators GROUP BY 1, 2) v ON v.et = k.et AND v.ect_code = k.ect_code
)
"""

#: Weighted index contributions per variable: the stage 3 account.
CONDITION_INDEX_CTE = """
condition_index AS (
    SELECT i.et, i.ect_code, i.ect_group, i.ect_class, i.variable, i.unit,
           i.opening, i.closing, i.change,
           i.lower_level, i.upper_level,
           i.indicator_opening, i.indicator_closing,
           i.indicator_closing - i.indicator_opening AS indicator_change,
           w.weight,
           w.weight * i.indicator_opening AS index_opening,
           w.weight * i.indicator_closing AS index_closing,
           w.weight * (i.indicator_closing - i.indicator_opening) AS index_change
    FROM condition_indicators i
    JOIN condition_weights w ON w.et = i.et AND w.ect_code = i.ect_code
)
"""

#: Net change in the condition index per ET — the sign the asset account classifies against.
CONDITION_NET_CHANGE_CTE = """
condition_net_change AS (
    SELECT et,
           sum(index_opening) AS condition_opening,
           sum(index_closing) AS condition_closing,
           sum(index_change)  AS condition_change
    FROM condition_index
    GROUP BY 1
)
"""

#: The four CTEs that make up the condition account, in dependency order.
CONDITION_CTES: tuple[str, ...] = (
    CONDITION_VARIABLES_CTE,
    CONDITION_INDICATORS_CTE,
    CONDITION_WEIGHTS_CTE,
    CONDITION_INDEX_CTE,
)
