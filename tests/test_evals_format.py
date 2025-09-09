from orbit_agent.evals import _format_eval


def test_format_eval_happy_path():
    advice = "Do X. Do Y."
    actions = ["1. Call 10 users", "2. Ship MVP", "3. Measure activation"]
    risks = ["No demand", "Wrong ICP", "Channel saturation"]
    ok, a_count, r_count = _format_eval(advice, actions, risks)
    assert ok is True
    assert a_count == 3
    assert r_count == 3


def test_format_eval_too_few_actions_or_risks():
    advice = "Something"
    actions = ["One"]
    risks = ["Risk1", "Risk2"]
    ok, a_count, r_count = _format_eval(advice, actions, risks)
    assert ok is False
    assert a_count == 1
    assert r_count == 2

