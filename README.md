# Orbit Agent

A brutally honest "high‑orbit" startup advisor you can text or run from the CLI.
Built with **DSPy**. Opinionated toward YC‑style focus: default‑alive first, do things that don't scale, and optimize for the **$1B vs $0** outcome over marginal dilution.

## Features

- **🎯 Smart Advisor**: Context-aware advice that adapts to your specific situation
- **📱 Multi-channel**: CLI and SMS interfaces for advice on-the-go
- **🔧 Financial Tools**: Dilution, runway, EV calculations, funnel analysis
- **🛡️ Production Ready**: Rate limiting, retries, secure webhooks, SQLite storage
- **📊 Rich Output**: Beautiful tables and formatted responses
- **🔄 Conversation Memory**: Maintains context across interactions

## Quick Start

```bash
# 1) Create a venv and install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt

# 2) Configure an LM (choose one)
export OPENAI_API_KEY=...        # Uses gpt-4o-mini by default
export ANTHROPIC_API_KEY=...     # Uses claude-3-5-sonnet by default
# Or use local Ollama (auto-detected if no API keys)
# brew install --cask ollama && ollama run llama3.2:3b

# 3) Try the CLI
python -m orbit_agent.cli ask "I'm considering YC. Is the 7% dilution worth it?"
python -m orbit_agent.cli focus "Ship a painful user interview plan in 48 hours"
python -m orbit_agent.cli chat  # Interactive mode

# Financial tools
python -m orbit_agent.cli dilution --pre 6000000 --raise 500000
python -m orbit_agent.cli runway --cash 800000 --burn 55000
python -m orbit_agent.cli ev --p_upside 0.12 --ev_upside 1200000000 --p_mid 0.25 --ev_mid 150000000 --p_down 0.63 --ev_down 0

# 4) SMS interface (production-ready)
export TWILIO_ACCOUNT_SID=...
export TWILIO_AUTH_TOKEN=...
export TWILIO_NUMBER=+1...
export PERSONAL_NUMBER=+1...
python -m orbit_agent.sms_server
# For production: gunicorn -w 2 -b 0.0.0.0:5000 orbit_agent.sms_server:app

# Optional security toggles (defaults are safer):
# export ORBIT_ALLOW_INSECURE_TWILIO=false   # Require Twilio signature unless true
# export ORBIT_RESTRICT_FROM=true            # Only accept SMS from PERSONAL_NUMBER when set
```

## What's New

**✅ Fixed Critical Issues:**
- SMS integration now works correctly
- Thread-safe SQLite storage replaces fragile JSON files
- Proper error handling with retries and timeouts
- Secure Twilio webhook validation and rate limiting

**✅ Enhanced Experience:**
- Smarter prompts that adapt to your context vs regurgitating playbooks
- Rich CLI with progress indicators and colored output
- Conversation memory across sessions
- Comprehensive logging and error handling

## Commands

- `ask "<question>"` — get contextual advice using your ~/.orbit/context.md
- `chat` — interactive conversation mode with memory
- `focus "<goal>"` — forces a ruthless 24–48h plan with pre-mortem
- `config-info` — show current configuration
- `context show` — display your saved context in ~/.orbit/context.md
- `context set "<text>"` — save/update your context
- `dilution --pre PRE --raise AMOUNT` — post-money and ownership analysis
- `runway --cash C --burn B [--growth G]` — months runway, default‑alive status
- `ev --p_upside P1 --ev_upside V1 ...` — expected value across scenarios
- `retention 'JSON'` — cohort retention analysis
- `funnel 'JSON'` — marketing funnel conversion analysis

## Configuration

All configuration is handled via environment variables:

```bash
# Language Model (auto-detected)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
ORBIT_LM=openai/gpt-4o-mini  # Override model selection

# SMS (optional)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_NUMBER=+1...
PERSONAL_NUMBER=+1...

# Customization
ORBIT_PLAYBOOK=playbooks/custom.yaml
ORBIT_MAX_TOKENS=2048
ORBIT_TEMPERATURE=0.7
ORBIT_LOG_LEVEL=INFO
```

## File Structure

```
orbit_agent/
  ├── cli.py                 # Rich CLI with proper logging
  ├── advisor.py             # Enhanced DSPy orchestration
  ├── config.py              # Structured configuration management
  ├── memory.py              # SQLite storage with fallbacks
  ├── sms_server.py          # Production-ready webhook server
  └── tools/                 # Financial calculation tools
      ├── dilution.py
      ├── finance.py
      ├── retention.py
      └── funnel.py
playbooks/
  ├── high_orbit.yaml        # YC-style startup heuristics
  └── bootstrapped_saas.yaml # Alternative playbook
requirements.txt             # Pinned production dependencies
requirements-dev.txt         # Development tools
```

## Production Deployment

### SMS Webhook
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn (recommended)
gunicorn -w 2 -b 0.0.0.0:5000 orbit_agent.sms_server:app

# Or with Docker
docker build -t orbit-agent .
docker run -p 5000:5000 --env-file .env orbit-agent
```

### Environment Setup
- Use proper secret management (not .env files) in production
- Twilio webhook hardening:
  - Keep `ORBIT_ALLOW_INSECURE_TWILIO=false` (default)
  - Keep `ORBIT_RESTRICT_FROM=true` (default) and set `PERSONAL_NUMBER`
  - Ensure `TWILIO_AUTH_TOKEN` is configured for signature validation
- Set up monitoring and log aggregation
- Configure rate limiting appropriate for your usage

## Safety & Limitations

- **Model choice**: Use GPT-4o or Claude-3.5-Sonnet for serious advice. Local models are weaker on nuanced judgment.
- **Responsibility**: Advice can be wrong or overly aggressive. You own all decisions.
- **Data privacy**: Conversations are stored locally in SQLite. Enable encryption for sensitive data.
- **Cost control**: Monitor token usage with high-tier models. The tool prioritizes advice quality over cost optimization.

## Usage Tracking (Optional)

Enable approximate token and cost logging in stdout with env vars:

```bash
ORBIT_TRACK_USAGE=true
# $ cost per 1K tokens for your selected model
ORBIT_COST_PER_1K_PROMPT=0.005
ORBIT_COST_PER_1K_COMPLETION=0.015
```

This uses rough estimates (≈4 chars per token) and logs latency, estimated tokens in/out, and an approximate cost per call.

## Contributing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -q

# Format and lint
black .
ruff check .
mypy .
```

Built for founders who want honest feedback without the sugar-coating.
