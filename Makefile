# ──────────────────────────────────────────────
#  ClinicCloud Migration Document Manager
#  Requires: make  (Windows: choco install make)
# ──────────────────────────────────────────────

# Detect OS → correct venv paths
ifeq ($(OS),Windows_NT)
	PYTHON     = python
	VENV_BIN   = .venv\Scripts
	VENV_PY    = $(VENV_BIN)\python.exe
	VENV_PIP   = $(VENV_BIN)\pip.exe
	PYTEST     = $(VENV_BIN)\pytest.exe
	RM         = rmdir /s /q
else
	PYTHON     = python3
	VENV_BIN   = .venv/bin
	VENV_PY    = $(VENV_BIN)/python
	VENV_PIP   = $(VENV_BIN)/pip
	PYTEST     = $(VENV_BIN)/pytest
	RM         = rm -rf
endif

.DEFAULT_GOAL := help
.PHONY: help install venv dev test coverage clean reset

# ── Help ──────────────────────────────────────
help:
	@echo ""
	@echo "  ClinicCloud Migration Document Manager"
	@echo "  ───────────────────────────────────────"
	@echo "  make install    Create virtualenv and install dependencies"
	@echo "  make dev        Start the development server (http://localhost:8080)"
	@echo "  make test       Run the test suite"
	@echo "  make coverage   Run tests and show coverage report"
	@echo "  make clean      Remove cache, build and coverage files"
	@echo "  make reset      Full clean + reinstall from scratch"
	@echo ""

# ── Setup ─────────────────────────────────────
venv:
	$(PYTHON) -m venv .venv

install: venv
	$(VENV_PIP) install --upgrade pip -q
	$(VENV_PIP) install -r requirements.txt
	@echo ""
	@echo "  ✓ Ready. Run 'make dev' to start the server."
	@echo ""

# ── Run ───────────────────────────────────────
dev:
	$(VENV_PY) run.py

# ── Test ──────────────────────────────────────
test:
	$(PYTEST) -v

coverage:
	$(PYTEST) --cov=app --cov-report=term-missing

# ── Clean ─────────────────────────────────────
clean:
	$(RM) .pytest_cache 2>/dev/null || true
	$(RM) htmlcov       2>/dev/null || true
	$(RM) .coverage     2>/dev/null || true
	find . -type d -name __pycache__ -exec $(RM) {} + 2>/dev/null || true

reset: clean
	$(RM) .venv 2>/dev/null || true
	$(MAKE) install
