from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

import dspy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Default model configurations
DEFAULT_OPENAI = "openai/gpt-4o-mini"
DEFAULT_ANTHROPIC = "anthropic/claude-3-5-sonnet-20240620"
DEFAULT_OLLAMA = "ollama_chat/llama3.2"


@dataclass
class LMConfig:
    """Language Model configuration"""

    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30


@dataclass
class TwilioConfig:
    """Twilio SMS configuration"""

    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    phone_number: Optional[str] = None
    personal_number: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        return all(
            [self.account_sid, self.auth_token, self.phone_number, self.personal_number]
        )


@dataclass
class AppConfig:
    """Main application configuration"""

    lm: LMConfig
    twilio: TwilioConfig

    # Paths
    data_dir: Path = field(default_factory=lambda: Path.home() / ".orbit")
    playbook_path: Path = field(
        default_factory=lambda: Path("playbooks/high_orbit.yaml")
    )

    # Limits
    max_history_entries: int = 100
    max_sms_length: int = 1000
    rate_limit_per_minute: int = 10

    # Features
    enable_critique: bool = True
    enable_tools: bool = True
    log_level: str = "INFO"
    # Usage tracking (approximate; requires env to enable)
    track_usage: bool = False
    cost_per_1k_prompt: float = 0.0
    cost_per_1k_completion: float = 0.0

    def __post_init__(self):
        """Validate configuration after initialization"""
        self.data_dir.mkdir(exist_ok=True)

        # Validate LM config
        if not self.lm.model:
            raise ValueError("LM model must be specified")

        # Set up logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def _determine_model_and_key() -> tuple[str, Optional[str]]:
    """Determine which model and API key to use"""
    explicit_model = os.getenv("ORBIT_LM")
    provider_hint = os.getenv("LM_PROVIDER")  # Optional compatibility env: openai|anthropic|ollama
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if explicit_model:
        # User explicitly set a model
        if explicit_model.startswith("openai/") and not openai_key:
            raise ValueError(f"Model {explicit_model} requires OPENAI_API_KEY")
        elif explicit_model.startswith("anthropic/") and not anthropic_key:
            raise ValueError(f"Model {explicit_model} requires ANTHROPIC_API_KEY")

        # Determine the right API key
        if explicit_model.startswith("openai/"):
            return explicit_model, openai_key
        elif explicit_model.startswith("anthropic/"):
            return explicit_model, anthropic_key
        else:
            return explicit_model, None

    # Auto-detect based on available keys or provider hint
    if provider_hint:
        hint = provider_hint.lower()
        if hint.startswith("ollama"):
            return DEFAULT_OLLAMA, None
        if hint.startswith("openai"):
            if not openai_key:
                raise ValueError("LM_PROVIDER=openai requires OPENAI_API_KEY")
            return DEFAULT_OPENAI, openai_key
        if hint.startswith("anthropic"):
            if not anthropic_key:
                raise ValueError("LM_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
            return DEFAULT_ANTHROPIC, anthropic_key

    if openai_key:
        return DEFAULT_OPENAI, openai_key
    elif anthropic_key:
        return DEFAULT_ANTHROPIC, anthropic_key
    else:
        logger.info("No API keys found and no provider hint, defaulting to Ollama")
        return DEFAULT_OLLAMA, None


def load_config() -> AppConfig:
    """Load configuration from environment variables"""

    # Determine LM configuration
    model, api_key = _determine_model_and_key()

    # Set API base for local models
    api_base = None
    if model.startswith("ollama"):
        api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")

    lm_config = LMConfig(
        model=model,
        api_key=api_key,
        api_base=api_base,
        max_tokens=int(os.getenv("ORBIT_MAX_TOKENS", "2048")),
        temperature=float(os.getenv("ORBIT_TEMPERATURE", "0.7")),
        timeout=int(os.getenv("ORBIT_TIMEOUT", "30")),
    )

    # Twilio configuration
    twilio_config = TwilioConfig(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        phone_number=os.getenv("TWILIO_NUMBER"),
        personal_number=os.getenv("PERSONAL_NUMBER"),
    )

    # Application configuration
    config = AppConfig(
        lm=lm_config,
        twilio=twilio_config,
        playbook_path=Path(os.getenv("ORBIT_PLAYBOOK", "playbooks/high_orbit.yaml")),
        max_history_entries=int(os.getenv("ORBIT_MAX_HISTORY", "100")),
        max_sms_length=int(os.getenv("ORBIT_MAX_SMS_LENGTH", "1000")),
        rate_limit_per_minute=int(os.getenv("ORBIT_RATE_LIMIT", "10")),
        enable_critique=os.getenv("ORBIT_ENABLE_CRITIQUE", "true").lower() == "true",
        enable_tools=os.getenv("ORBIT_ENABLE_TOOLS", "true").lower() == "true",
        log_level=os.getenv("ORBIT_LOG_LEVEL", "INFO"),
        track_usage=os.getenv("ORBIT_TRACK_USAGE", "false").lower() == "true",
        cost_per_1k_prompt=float(os.getenv("ORBIT_COST_PER_1K_PROMPT", "0")),
        cost_per_1k_completion=float(os.getenv("ORBIT_COST_PER_1K_COMPLETION", "0")),
    )

    return config


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def configure_lm() -> AppConfig:
    """Configure the language model per dspy.ai and return config.

    Uses dspy.LM(model=...) and sets it via dspy.configure. If configuration fails,
    we log and continue so non-LLM commands still work.
    """
    config = get_config()

    try:
        lm = dspy.LM(
            model=config.lm.model,
            temperature=config.lm.temperature,
            max_tokens=config.lm.max_tokens,
        )
        dspy.configure(lm=lm)
        logger.info(f"Configured LM via dspy.LM: {config.lm.model}")
        return config
    except Exception as e:
        logger.error(f"Failed to configure LM via dspy.LM: {e}")
        logger.info("Continuing without LM configuration for non-LLM commands")
        return config


def reload_config():
    """Reload configuration (useful for testing)"""
    global _config
    _config = None
    return get_config()
