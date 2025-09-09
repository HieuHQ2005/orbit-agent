import math
import pytest

from orbit_agent.tools.dilution import calc_dilution


def test_calc_dilution_basic():
    res = calc_dilution(pre_money=6_000_000, raise_amount=500_000, option_pool_add=0.10)
    assert res.post_money == 6_500_000
    assert math.isclose(res.new_percent, 500_000 / 6_500_000, rel_tol=1e-9)
    assert math.isclose(res.existing_percent, 1.0 - res.new_percent - 0.10, rel_tol=1e-9)


def test_calc_dilution_invalid_pool():
    # new_pct ~ 0.4737; with pool 0.6 this exceeds 100% of post
    with pytest.raises(ValueError):
        calc_dilution(pre_money=1_000_000, raise_amount=900_000, option_pool_add=0.6)
