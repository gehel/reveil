DEVICE    ?= ::
VENV      := .venv
PIP       := $(VENV)/bin/pip
PYTEST    := $(VENV)/bin/pytest
RUFF      := $(VENV)/bin/ruff
CIRCUP    := $(VENV)/bin/circup
CPT       := $(VENV)/bin/circuitpython-tool

.PHONY: all install test lint format upload install-libs console

all: test lint

## Installe les dépendances de développement dans le venv
install:
	$(PIP) install -r requirements-dev.txt

## Lance les tests unitaires
test:
	$(PYTEST) firmware/tests/ -v

## Vérifie le style et les erreurs statiques
lint:
	$(RUFF) check firmware/src/ firmware/tests/

## Formate le code automatiquement
format:
	$(RUFF) format firmware/src/ firmware/tests/

## Copie le firmware sur le Pico
upload:
	$(CPT) upload --dir firmware/src/ $(DEVICE)

## Installe les bibliothèques CircuitPython sur le Pico via circup
install-libs:
	$(CIRCUP) install -r firmware/requirements_circuitpy.txt

## Ouvre la console série du Pico
console:
	$(CPT) connect $(DEVICE)