# Outils de développement pour le firmware CircuitPython du réveil.
# `mpremote` et `circup` doivent être disponibles sur le PATH (ex: via .venv/bin).

PORT ?=
MPREMOTE := mpremote $(if $(PORT),connect $(PORT))
CIRCUP := circup $(if $(PORT),--path $(PORT))

# Point de montage USB du Pico sous CircuitPython (label du volume : CIRCUITPY).
CIRCUITPY_MOUNT = $(shell findmnt -nr -o TARGET -S LABEL=CIRCUITPY)

# Carte cible pour le firmware CircuitPython (Raspberry Pi Pico / RP2040, cf. README).
BOARD := raspberry_pi_pico
UF2_TMP := /tmp/circuitpython-$(BOARD).uf2

.PHONY: help deploy deps install-circuitpython test-unit test-integration

help:
	@echo "Cibles disponibles :"
	@echo "  make install-circuitpython - flashe la dernière version stable de CircuitPython sur le Pico"
	@echo "  make deploy                - copie code.py (et lib/ si présent) sur le Pico"
	@echo "  make deps                  - installe les librairies CircuitPython via circup"
	@echo "  make test-unit             - lance les tests unitaires sur l'hôte"
	@echo "  make test-integration      - lance les tests d'intégration sur le Pico"
	@echo ""
	@echo "PORT=<port série> pour cibler un appareil précis (sinon auto-détection)."

install-circuitpython:
	@VERSION=$$(curl -sf https://api.github.com/repos/adafruit/circuitpython/releases/latest | grep -m1 '"tag_name"' | sed -E 's/.*: *"([^"]+)".*/\1/'); \
	if [ -z "$$VERSION" ]; then echo "Impossible de déterminer la dernière version de CircuitPython."; exit 1; fi; \
	URL="https://downloads.circuitpython.org/bin/$(BOARD)/en_US/adafruit-circuitpython-$(BOARD)-en_US-$$VERSION.uf2"; \
	echo "Téléchargement de CircuitPython $$VERSION pour $(BOARD)..."; \
	curl -sfL -o $(UF2_TMP) "$$URL" || { echo "Échec du téléchargement : $$URL"; exit 1; }; \
	MOUNT=$$(findmnt -nr -o TARGET -S LABEL=RPI-RP2); \
	if [ -z "$$MOUNT" ]; then \
		echo "Pico non détecté en mode bootloader (volume RPI-RP2 introuvable)."; \
		echo "Débranchez le Pico, maintenez le bouton BOOTSEL, rebranchez-le, puis relancez 'make install-circuitpython'."; \
		exit 1; \
	fi; \
	echo "Copie de l'UF2 vers $$MOUNT..."; \
	cp $(UF2_TMP) "$$MOUNT/"; \
	echo "Terminé : le Pico va redémarrer sous CircuitPython $$VERSION."

deploy:
	@if [ -z "$(CIRCUITPY_MOUNT)" ]; then \
		echo "Volume CIRCUITPY introuvable. Branchez le Pico sous CircuitPython (voir 'make install-circuitpython')."; \
		exit 1; \
	fi
	cp code.py "$(CIRCUITPY_MOUNT)/code.py"
	@if [ -d lib ]; then cp -r lib "$(CIRCUITPY_MOUNT)/"; fi

deps:
	$(CIRCUP) install -r requirements.txt

test-unit:
	pytest tests/

test-integration:
	$(MPREMOTE) run tests_integration/
