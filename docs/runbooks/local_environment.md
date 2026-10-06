# Local Environment Setup

Use Python 3.11 for the shared development environment. The package also permits Python 3.12, but choosing one version for routine development reduces avoidable differences between teammates and CI.

## Prerequisites

- Git
- Python 3.11 with `venv` and `pip`
- PowerShell on Windows or a POSIX-compatible shell on macOS/Linux

Databricks and Streamlit accounts are not required for local setup.

## Create the environment

### PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Install the larger capability groups only when the work needs them:

```bash
python -m pip install -e ".[data,geo,model,app,dev]"
```

If a geospatial package cannot use a compatible wheel on the local platform, record the problem before changing a shared version or installing an unrelated distribution.

## Configure local settings

Copy `.env.example` to `.env` and fill only the values required for the current source or service. `.env` and Streamlit secrets are ignored by Git. Never paste a token into a notebook, committed configuration, command transcript, or issue.

The first implementation slice should add a typed settings loader. Until then, no project command should assume that optional credentials exist.

## Validate the checkout

```bash
python -m ruff check .
python -m mypy src
python -m pytest
```

The initial repository contains only a package smoke test. These commands become the common fast check as pipeline and application tests are added.

## Expected result

- the `neighborhood_twin` package imports;
- linting and type checks complete without errors;
- tests pass without downloading full source data;
- `git status` does not show `.env`, `.venv`, caches, or generated data.

## Reset and recovery

If the environment becomes inconsistent, deactivate it, remove only the repository's `.venv` directory after confirming its full path, recreate it, and reinstall from `pyproject.toml`. Do not delete source data or project artifacts as part of an environment reset.

