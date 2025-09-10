# Orbit Agent

A brutally honest "high‑orbit" startup advisor you can text or run from the CLI.
Built with **DSPy**. Opinionated toward YC‑style focus: default‑alive first, do things that don't scale, and optimize for the **$1B vs $0** outcome over marginal dilution.

## Features

- **🎯 Smart Advisor**: Context-aware advice that adapts to your specific situation.
- **📱 Multi-channel**: CLI and SMS interfaces for advice on-the-go.
- **🔧 Financial Tools**: Dilution, runway, EV calculations, funnel analysis.
- **🛡️ Production Ready**: Rate limiting, retries, secure webhooks, and thread-safe SQLite storage.
- **📊 Rich Output**: Beautiful tables and formatted responses in the CLI.
- **🔄 Conversation Memory**: Maintains context across interactions.
- **🧠 Best-of-N + Rerank**: Generate multiple drafts and pick the best via a critic.
- **🧪 Evals & Rubrics**: Personas, rubrics, overlap penalty, and CSV/MD summaries.

<details>
<summary><strong>Recent Improvements</strong></summary>

- **✅ Fixed Critical Issues:**
  - SMS integration now works correctly.
  - Thread-safe SQLite storage replaces fragile JSON files.
  - Proper error handling with retries and timeouts.
  - Secure Twilio webhook validation and rate limiting.
- **✅ Enhanced Experience:**
  - Smarter prompts that adapt to your context vs regurgitating playbooks.
  - Rich CLI with progress indicators and colored output.
  - Conversation memory across sessions.
  - Comprehensive logging and error handling.

</details>

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure your Language Model
# Ollama is used by default if no API key is set
# brew install --cask ollama && ollama run llama3.2:3b

export OPENAI_API_KEY="..."      # For GPT-4o-mini
export ANTHROPIC_API_KEY="..."   # For Claude 3.5 Sonnet

# 3. Run from the CLI
python -m orbit_agent.cli ask "Is YC's 7% dilution worth it for a solo founder?"
python -m orbit_agent.cli focus "Ship a painful user interview plan in 48 hours"
python -m orbit_agent.cli chat

# 4. Use Financial Tools
python -m orbit_agent.cli dilution --pre 6000000 --raise 500000
python -m orbit_agent.cli runway --cash 800000 --burn 55000
```

## Commands

- `ask "<question>"`: Get contextual advice.
- `chat`: Interactive conversation mode.
- `focus "<goal>"`: Generate a ruthless 48h plan.
- `dilution`, `runway`, `ev`, `retention`, `funnel`: Financial and growth tools.
- `context <show|set|edit>`: Manage your personal context.
- `config-info`: Show current configuration.
- `models list [--provider openai|anthropic]`: List available model IDs.
- `eval run --dataset <yaml> --out <jsonl>`: Run evals and save results.
- `eval report <jsonl>`: Show overall summary.
- `eval grade --dataset <yaml> --results-path <jsonl> --out <jsonl>`: Rubric grading.
- `eval summary --input-path <jsonl> [--csv-out <csv>] [--md-out <md>]`: Export summaries.

## Configuration

Configuration is managed via environment variables.

```bash
# --- Required ---
# Pick one, or leave unset to use local Ollama
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=...

# --- Optional ---
# Override the default model
export ORBIT_LM=openai/gpt-4o

# SMS interface
export TWILIO_ACCOUNT_SID=...
export TWILIO_AUTH_TOKEN=...
export TWILIO_NUMBER=+1...
export PERSONAL_NUMBER=+1...

# Usage Tracking (approximate cost logging)
export ORBIT_TRACK_USAGE=true
export ORBIT_COST_PER_1K_PROMPT=0.005
export ORBIT_COST_PER_1K_COMPLETION=0.015

# Generation Quality (optional)
export ORBIT_BEST_OF_N=1               # Number of drafts to generate for reranking
export ORBIT_OVERLAP_ALPHA=2.0         # Penalize templating vs playbook overlap
export ORBIT_CRITIC_LM=openai/o3-mini  # Separate critic LM (default for OpenAI)
```

<details>
<summary><strong>File Structure</strong></summary>

```
orbit_agent/
  ├── cli.py                 # Rich CLI with proper logging
  ├── advisor.py             # Enhanced DSPy orchestration
  ├── config.py              # Structured configuration management
  ├── memory.py              # SQLite storage with fallbacks
  ├── sms_server.py          # Production-ready webhook server
  └── tools/                 # Financial calculation tools
playbooks/
  ├── high_orbit.yaml        # YC-style startup heuristics
  └── bootstrapped_saas.yaml # Alternative playbook
```

</details>

## Production Deployment

The SMS server is production-ready. For production, use Gunicorn and manage secrets securely.

```bash
# Run with Gunicorn (recommended)
gunicorn -w 2 -b 0.0.0.0:5000 orbit_agent.sms_server:app

# Or with Docker
docker build -t orbit-agent .
docker run -p 5000:5000 --env-file .env orbit-agent
```

## Safety & Limitations

- **Model choice**: Use GPT-4o or Claude-3.5-Sonnet for serious advice. Local models are weaker on nuanced judgment.
- **Responsibility**: Advice can be wrong or overly aggressive. You own all decisions.
- **Data privacy**: Conversations are stored locally in SQLite. Enable encryption for sensitive data.
- **Cost control**: Best-of-N and strong critics improve quality but cost more — use `ORBIT_BEST_OF_N` and a lower-cost critic (e.g. `o3-mini`) to balance.

## Evals & Self‑Grading

- Run persona scenarios with rubrics:
  - `python -m orbit_agent.cli models list --provider openai`  # discover models
  - `python -m orbit_agent.cli eval run --dataset evals/scenarios_personas.yaml --out .orbit/evals/personas.jsonl`
  - `python -m orbit_agent.cli eval report .orbit/evals/personas.jsonl`
  - `python -m orbit_agent.cli eval grade --dataset evals/scenarios_personas.yaml --results-path .orbit/evals/personas.jsonl --out .orbit/evals/personas_grades.jsonl`
  - `python -m orbit_agent.cli eval summary --input-path .orbit/evals/personas.jsonl --csv-out reports/personas.csv --md-out reports/personas.md`

- Suggested quality knobs:
  - `ORBIT_LM=openai/gpt-4.1`
  - `ORBIT_CRITIC_LM=openai/o3-mini`
  - `ORBIT_BEST_OF_N=2` and `ORBIT_TEMPERATURE=0.35`
  - `ORBIT_OVERLAP_ALPHA=2.5`

- Tool‑aware analysis: include minimal JSON to auto-run retention/funnel/runway/EV tools.

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

# Optional: set up git hooks (pre-commit)
pre-commit install
# or via Makefile (after bootstrapping venv):
make hooks

# Run all hooks against the repo
pre-commit run -a
```
