from orbit_agent.config import load_config, TwilioConfig


def test_model_selection_from_env(monkeypatch):
    # Prefer explicit model if provided
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ORBIT_LM", "ollama_chat/llama3.2")
    cfg = load_config()
    assert cfg.lm.model == "ollama_chat/llama3.2"


def test_twilio_is_configured():
    t = TwilioConfig(
        account_sid="sid",
        auth_token="token",
        phone_number="+10000000000",
        personal_number="+19999999999",
    )
    assert t.is_configured is True

    t2 = TwilioConfig()
    assert t2.is_configured is False
