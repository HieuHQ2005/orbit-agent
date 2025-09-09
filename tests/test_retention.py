from orbit_agent.tools.retention import calculate_cohort_retention


def test_retention_basic():
    cohorts = [[100, 60, 40]]
    results = calculate_cohort_retention(cohorts)
    assert len(results) == 1
    assert results[0].retention_rates == [100.0, 60.0, 40.0]


def test_retention_handles_zero_size():
    cohorts = [[0, 0, 0]]
    results = calculate_cohort_retention(cohorts)
    assert results[0].retention_rates == [0.0, 0.0, 0.0]
