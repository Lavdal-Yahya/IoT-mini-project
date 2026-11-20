PYTHON ?= .venv/bin/python

.PHONY: audit extract develop freeze evaluate report test reproduce
audit extract develop freeze evaluate report reproduce:
	$(PYTHON) -m bearing_diagnosis.cli $@

test:
	$(PYTHON) -m pytest -q
