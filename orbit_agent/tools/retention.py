
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass
class CohortRetentionResult:
    cohort: List[int]
    retention_rates: List[float]

def calculate_cohort_retention(cohorts: List[List[int]]) -> List[CohortRetentionResult]:
    """
    Calculates the retention rate for a list of cohorts.

    Args:
        cohorts: A list of lists, where each inner list represents a cohort and
                 contains the number of users retained over time. The first
                 element of each inner list is the initial size of the cohort.

    Returns:
        A list of CohortRetentionResult objects, where each object contains the
        original cohort data and the calculated retention rates.
    """
    results = []
    for cohort in cohorts:
        initial_size = cohort[0] if cohort else 0
        if initial_size <= 0:
            # Avoid divide-by-zero; return zeros for all periods
            retention_rates = [0.0 for _ in cohort]
        else:
            retention_rates = [(retained_users / initial_size) * 100 for retained_users in cohort]
        results.append(CohortRetentionResult(cohort=cohort, retention_rates=retention_rates))
    return results
