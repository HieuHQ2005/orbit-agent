import math
import pytest

from orbit_agent.tools.finance import runway_months, expected_value


def test_runway_basic_no_growth():
    res = runway_months(cash=180_000, burn_per_month=10_000, revenue_growth=0.0)
    assert math.isclose(res.months, 18.0, rel_tol=1e-6)
    assert res.default_alive is True


def test_runway_with_growth_adjusts_burn():
    res = runway_months(cash=180_000, burn_per_month=10_000, revenue_growth=0.5)
    # factor = 1 - 0.5*0.5 = 0.75
    assert math.isclose(res.months, 180_000 / (10_000 * 0.75), rel_tol=1e-6)
    assert res.default_alive is True


def test_runway_burn_zero_is_infinite():
    res = runway_months(cash=10_000, burn_per_month=0)
    assert res.months == 999.0 and res.default_alive is True


def test_expected_value_normalizes_probabilities():
    # Sums to slightly less than 1 within tolerance
    ev = expected_value(0.5, 100, 0.4995, 50, 0.0005, 0)
    # Normalized expected value ~ 0.5*100 + 0.4995*50
    assert math.isclose(ev, 50 + 24.975, rel_tol=1e-6)


def test_expected_value_rejects_bad_probabilities():
    with pytest.raises(ValueError):
        expected_value(0.6, 100, 0.3, 50, 0.2, 0)

