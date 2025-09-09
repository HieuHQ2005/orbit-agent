from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class FunnelStep:
    name: str
    user_count: int


@dataclass
class FunnelAnalysisResult:
    steps: List[FunnelStep]
    conversion_rates: List[float]


def analyze_funnel(steps: List[FunnelStep]) -> FunnelAnalysisResult:
    """
    Analyzes a marketing funnel and calculates the conversion rate between each step.

    Args:
        steps: A list of FunnelStep objects, where each object represents a
               step in the funnel and contains the name of the step and the
               number of users who completed it.

    Returns:
        A FunnelAnalysisResult object, which contains the original funnel steps
        and the calculated conversion rates between each step.
    """
    conversion_rates = []
    for i in range(len(steps) - 1):
        current_step = steps[i]
        next_step = steps[i + 1]
        # Guard against division by zero and negative values
        if current_step.user_count <= 0:
            conversion_rate = 0.0
        else:
            conversion_rate = (next_step.user_count / current_step.user_count) * 100
        conversion_rates.append(conversion_rate)
    return FunnelAnalysisResult(steps=steps, conversion_rates=conversion_rates)
