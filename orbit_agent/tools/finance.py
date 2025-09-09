from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RunwayResult:
    months: float
    default_alive: bool


def runway_months(
    cash: float, burn_per_month: float, revenue_growth: float = 0.0
) -> RunwayResult:
    """
    Estimate runway months with a simple burn adjustment for revenue growth.

    Rules and guardrails:
    - If burn_per_month <= 0, treat as effectively infinite runway (999 months) and default-alive.
    - Clamp revenue_growth to [0.0, 1.0] to avoid unrealistic negative burn.
    - Apply a modest reduction: effective_burn = burn * max(0.1, 1 - 0.5 * growth).
      This avoids runaway months from tiny denominators while still reflecting growth.
    """
    if burn_per_month <= 0:
        return RunwayResult(months=999.0, default_alive=True)

    growth = max(0.0, min(1.0, revenue_growth))
    factor = max(0.1, 1.0 - 0.5 * growth)
    effective_burn = max(1e-6, burn_per_month * factor)
    months = cash / effective_burn
    return RunwayResult(months=months, default_alive=months >= 18.0)


def expected_value(
    p_up: float,
    ev_up: float,
    p_mid: float,
    ev_mid: float,
    p_down: float,
    ev_down: float,
) -> float:
    """
    Compute expected value given three scenarios.

    - If probabilities sum to ~1 within 1e-3 tolerance, normalize them to 1 exactly.
    - Otherwise, raise a ValueError with a clear message.
    """
    total_p = p_up + p_mid + p_down
    if abs(total_p - 1.0) <= 1e-3 and total_p > 0:
        p_up, p_mid, p_down = p_up / total_p, p_mid / total_p, p_down / total_p
    else:
        raise ValueError("Probabilities must sum to 1 (±0.001 tolerance)")

    return p_up * ev_up + p_mid * ev_mid + p_down * ev_down
