.PHONY: setup test lint fetch all figures report clean

PYTHON ?= .venv/Scripts/python.exe
PIP ?= .venv/Scripts/pip.exe

setup:            ## create venv + install package editable
	$(PYTHON) -m pip install -e ".[dev]"

test:             ## run tests (no network) with coverage gate
	$(PYTHON) -m pytest -m "not network" --cov=volsurf --cov-report=term-missing

lint:             ## ruff check + format check
	.venv/Scripts/ruff.exe check .
	.venv/Scripts/ruff.exe format --check .

fetch:            ## MANUAL: live snapshot fetch (network, market hours)
	$(PYTHON) -m volsurf.fetch

all:              ## full pipeline from committed snapshot (offline)
	$(PYTHON) scripts/run_pipeline.py

figures:          ## regenerate figures only
	$(PYTHON) scripts/make_figures.py

report:           ## regenerate report only
	$(PYTHON) scripts/make_report.py

clean:            ## remove caches + generated results
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in list(pathlib.Path('.').rglob('__pycache__')) + [pathlib.Path(d) for d in ('.pytest_cache', '.ruff_cache', 'htmlcov', 'src/volsurf.egg-info')]]; [pathlib.Path(f).unlink(missing_ok=True) for f in ('.coverage',)]"
