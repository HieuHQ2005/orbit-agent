from orbit_agent.tools.funnel import analyze_funnel, FunnelStep


def test_analyze_funnel_basic():
    steps = [
        FunnelStep(name="Visit", user_count=100),
        FunnelStep(name="Signup", user_count=40),
        FunnelStep(name="Activate", user_count=10),
    ]
    result = analyze_funnel(steps)
    assert len(result.conversion_rates) == 2
    assert round(result.conversion_rates[0], 1) == 40.0
    assert round(result.conversion_rates[1], 1) == 25.0


def test_analyze_funnel_handles_zero_users():
    steps = [FunnelStep(name="Visit", user_count=0), FunnelStep(name="Signup", user_count=10)]
    result = analyze_funnel(steps)
    assert result.conversion_rates == [0.0]

