from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DilutionResult:
    pre_money: float
    raise_amount: float
    option_pool_add: float
    post_money: float
    new_percent: float
    existing_percent: float


def calc_dilution(
    pre_money: float, raise_amount: float, option_pool_add: float = 0.0
) -> DilutionResult:
    """
    Simple dilution math:
    post = pre + raise
    new investor % = raise / post
    existing % = 1 - new - option_pool_add
    option_pool_add is *post* fraction to top up (e.g., 0.10 to target 10% pool post).
    """
    if pre_money < 0 or raise_amount < 0:
        raise ValueError("pre_money and raise_amount must be non-negative")
    if option_pool_add < 0 or option_pool_add >= 1.0:
        raise ValueError(
            "option_pool_add must be between 0 and 1 (post-money fraction)"
        )

    post = pre_money + raise_amount
    if post <= 0:
        # Degenerate case: no value in the company
        return DilutionResult(
            pre_money, raise_amount, option_pool_add, 0.0, 0.0, 1.0 - option_pool_add
        )

    new_pct = raise_amount / post
    if new_pct + option_pool_add > 1.0:
        raise ValueError(
            "option_pool_add too large for given raise; allocations exceed 100% post"
        )
    existing_pct = 1.0 - new_pct - option_pool_add
    return DilutionResult(
        pre_money, raise_amount, option_pool_add, post, new_pct, existing_pct
    )
