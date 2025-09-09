from orbit_agent.advisor import HighOrbitAdvisor


def test_advisor_fallback_on_failure(monkeypatch):
    advisor = HighOrbitAdvisor()

    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure")

    # Force the internal call path to fail so forward() returns fallback
    monkeypatch.setattr(advisor, "_call_llm_with_retry", boom)

    result = advisor(history=[{"role": "user", "content": "Test"}], playbook="")
    assert isinstance(result.advice, str)
    assert "technical difficulties" in result.advice.lower()
    assert result.score == 0

