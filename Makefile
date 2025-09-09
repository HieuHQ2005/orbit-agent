PY?=python3
VENV?=venv

.PHONY: bootstrap bootstrap-prod test lint fmt ci chat clean

bootstrap:
	@bash scripts/bootstrap_venv.sh dev $(PY)

bootstrap-prod:
	@bash scripts/bootstrap_venv.sh prod $(PY)

test:
	@$(VENV)/bin/python -m pytest -q

lint:
	@$(VENV)/bin/ruff check .

fmt:
	@$(VENV)/bin/black .

ci: lint test

chat:
	@$(VENV)/bin/python -m orbit_agent.cli chat

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache
	find . -name "*.pyc" -delete

